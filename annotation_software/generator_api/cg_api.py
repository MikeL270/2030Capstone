# Attempt at RESTful CRUD API for crop generator and census server
# Based on https://https://www.digitalocean.com/community/tutorials/create-a-rest-api-using-flask-on-ubuntu 
# because I have never done this before
# Author: Michael B. Lance
# Created: April 7, 2025
# Updated: June 8, 2025

#---------------------------------------------------------------------------------------------------------------------------#

from flask import Flask, jsonify, request, Response, abort, session
from flask_cors import CORS
from flask_caching import Cache
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from dotenv import load_dotenv
import os
import cropgenerator
from cropgenerator import CropgenJSONPRovider
from cropgenerator import Prediction, Box
import json
from functools import wraps
from datetime import datetime
from uuid import uuid4

#---------------------------------------------------------------------------------------------------------------------------#

load_dotenv()

db_config = {
    'database': os.environ.get('DB_NAME'),
    'user': os.environ.get('DB_USER'),              
    'password': os.environ.get('DB_PASS'),    
    'host': os.environ.get('DB_HOST'),           
    'port': '5432'              
}

prefix = len('high-altitude-pronghorn-survey-')
suffix = len('_crop_xx')

root = os.environ.get('ROOT')
herd_unit = os.environ.get('HERD_UNIT')
save_folder = os.path.join(root, 'Images', os.environ.get('CROP_FOLDER')) #type: ignore
os.makedirs(save_folder, exist_ok=True) # type: ignore

#---------------------------------------------------------------------------------------------------------------------------#

app = Flask(__name__)
app.json_provider_class = CropgenJSONPRovider
app.secret_key = os.environ.get('SECERET_KEY')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = True 

CORS(app, resources={
    r'/api/*': {
        'origins': 'http://localhost:5173',
        'supports_credentials': True     
    }
})

cache = Cache()

cache_config={
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_REDIS_HOST': os.environ.get('VALKEY_HOST'),
    'CACHE_REDIS_PORT': 6379,
    'CACHE_REDIS_PASSWORD': os.environ.get('VALKEY_PASS')
}
 
cache.init_app(app, cache_config)

login_manager = LoginManager()
login_manager.init_app(app)

#Initialize image backend
img_backend = cropgenerator.imagebackends.OpencvBackend()
base = cropgenerator.database.Postgres(db_config, root)
base.connect()

#---------------------------------------------------------------------------------------------------------------------------#

batches = {}

#---------------------------------------------------------------------------------------------------------------------------#
# User Management

class User(UserMixin):
    def __init__(self, db_id: int, external_id: str, status: str, role: str, created: datetime.date,
                 updated: datetime.date, locale: str, uuid: uuid4):
        self.db_id = db_id
        self.external_id = str(external_id)
        self.status = status 
        self.role = role
        self.created = created
        self.updated = updated
        self.locale = locale
        self.uuid = uuid
    
    def get_id(self):
        return self.external_id
    
    @staticmethod
    @cache.memoize(300)
    def get(external_id):
        resp_dict = base.get_user(external_id)

        if not resp_dict:
            print(f"----- DEBUG: User.get(): No user found in DB for '{external_id}'. Returning None. -----")
            return None

        return User(
            db_id = resp_dict['db_id'],
            external_id = external_id,
            status = resp_dict['status'],
            role = resp_dict['role'],
            created = resp_dict['created'],
            updated = resp_dict['updated'],
            locale = resp_dict['locale'],
            uuid = resp_dict['uuid']
        )

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@login_manager.unauthorized_handler
def unauthorized_callback():        
    abort(401)

@app.route('/api/v1/authenticate', methods=['POST'])
def authenticate():
    data = request.get_json()

    if not data or 'external-id' not in data:
        abort(400)

    user = User.get(data['external-id'])

    if not user: 
        abort(404)

    else:
        login_user(user)
        base.set_last_login(user.db_id)
        session['bgroupid'] = user.uuid
        batches[session['bgroupid']] = {}
        session.modified = True
        return jsonify(message="success"), 200

@app.route('/api/v1/deauthenticate')
@login_required
def logout():
    user = current_user
    for batch in batches[user.uuid]:
        delete_batch(batch)
    logout_user()
    
#---------------------------------------------------------------------------------------------------------------------------#
# GET requests
# Get request: Test connectivity
@app.route('/api/v1/test', methods=['GET'])
def test_api():
    return jsonify(message='Connected to v1 successfully'), 201

# GET request: Retrieve all batches items
@app.route('/api/v1/batches', methods=['GET'])
@login_required
def get_batches():
    serialized_data = json.dumps(batches,  default=app.json_provider_class(app).default)
    return Response(serialized_data, mimetype='application/json'), 201

# GET request: Retrieve a batch of images
# TODO: modify to work with proper container datastructure
@app.route('/api/v1/batches/<int:batch_id>', methods=['GET'])
@login_required
def get_batch(batch_id):
    batch = batches[session['bgroupid']][batch_id] 
    batch_obj = {batch_id: batch}
    if batch is None: 
        return jsonify({'error': 'Batch not found'}), 404
    serialized_data = json.dumps(batch_obj, default=app.json_provider_class(app).default)
    return Response(serialized_data, mimetype='application/json'), 201

# GET request: get a prediction level crop
@app.route('/api/v1/batches/<int:batch_id>/images/<int:image_id>/pred_crops/<int:crop_id>', methods=['GET'])
def get_pred_crop(batch_id, image_id, crop_id):
    #TODO: Check session level authentication 
    try:
        crop = batches[session['bgroupid']][batch_id][image_id]['pred_crops'][crop_id]
    except Exception as e:
        return jsonify(message='Crop not found')
    
    return Response(crop.serve(), mimetype='image/webp'), 201

# GET request: get batch ids 
@app.route('/api/v1/batches/ids', methods=['GET'])
@login_required
def get_batch_ids():
    return jsonify(list(batches[session['bgroupid']].keys())), 201

# GET request: get a full crop
@app.route('/api/v1/batches/<int:batch_id>/images/<int:image_id>/crops/<int:crop_id>', methods=['GET'])
@login_required
def get_crop(batch_id, image_id, crop_id):
    #TODO: Check session level authentication 
    try:
        crop = batches[session['bgroupid']][batch_id][image_id]['crops'][crop_id]
    except Exception as e:
        return jsonify(message='Crop not found')
    
    return Response(crop.serve(), mimetype='image/webp'), 201


#---------------------------------------------------------------------------------------------------------------------------#
# POST Requests

# POST request: retrieve a batch of images from the database
@app.route('/api/v1/images/create_batch', methods=['POST'])
@login_required
def retrieve_img_batch():
    batch_size = request.json.get('batch_size')
    desired_class = request.json.get('desired_class')
    min_confidence = request.json.get('min_confidence')
    herd_unit_id = request.json.get('herd_unit_id')
    model_Id = request.json.get('model_id')
    batch = base.retrieve_batch(batch_size, desired_class, min_confidence, herd_unit_id, model_Id)
    
    try:
        batch_id = len(batches[session['bgroupid']]) + 1
        new_batch_obj = {batch_id: batch}
        batches[session['bgroupid']][batch_id] = batch
    except KeyError:
        batches[session['bgroupid']] = {}
        batch_id = len(batches[session['bgroupid']]) + 1
        new_batch_obj = {batch_id: batch}
        batches[session['bgroupid']][batch_id] = batch
    serialized_data = json.dumps(new_batch_obj,  default=app.json_provider_class(app).default)
    return Response(serialized_data, mimetype='application/json'), 201 

# POST request: Create prediction level crops
@app.route('/api/v1/batches/<int:batch_id>/images/<int:image_id>/create_pred_crops', methods=['POST'])
@login_required
def create_pred_crops(batch_id: int, image_id: int):
     
    image = batches[session['bgroupid']][batch_id][image_id]['image']
    predictions = batches[session['bgroupid']][batch_id][image_id]['predictions']
    crops = img_backend.create_subcrop(image, predictions)
    batches[session['bgroupid']][batch_id][image_id]['pred_crops'] = {}
    for crop in crops:
        batches[session['bgroupid']][batch_id][image_id]['pred_crops'][crop.pred_crop_id] = crop

    serialized_data = json.dumps(crops, default=app.json_provider_class(app).default)
    return Response(serialized_data, mimetype='application/json'), 201   

# POST request: Create full crops of an image
@app.route('/api/v1/batches/<int:batch_id>/images/<int:image_id>/create_crops', methods=['POST'])
@login_required
def create_crops(batch_id: int, image_id: int):
     
    crop_size = request.json.get('crop_size')
    image = batches[session['bgroupid']][batch_id][image_id]['image']
    predictions = batches[session['bgroupid']][batch_id][image_id]['approved_predictions']
    crops = cropgenerator.auto_crop(image=image, predictions=predictions, crop_size=crop_size)
    serialized_data = json.dumps(crops, default=app.json_provider_class(app).default)
    return Response(serialized_data, mimetype='application/json'), 201

#---------------------------------------------------------------------------------------------------------------------------#
# Put Requests

# Put request: Update an image in a batch with approved predictions
@app.route('/api/v1/batches/<int:batch_id>/images/<int:image_id>/approve_predictions', methods=['PUT'])
@login_required
def approve_predictions(batch_id: int, image_id: int):
     
    batches[session['bgroupid']][batch_id][image_id]['approved_predictions'] = []
    approved_predictions = request.get_json()
    for pred in approved_predictions:
        batches[session['bgroupid']][batch_id][image_id]['approved_predictions'].append(
            Prediction(
                db_id = pred['id'],
                model_id = pred['model_id'],
                dimensions = Box(
                    top_left = pred['dimensions']['top_left'],
                    bottom_right = pred['dimensions']['bottom_right']
                )
            )
        )
    return jsonify( message="success" ),201

#---------------------------------------------------------------------------------------------------------------------------#
# Delete request: Delete a crop
@app.route('/api/v1/batches/<int:batch_id>', methods=['DELETE'])
@login_required
def delete_batch(batch_id):
     
    base.close_batch(batches[session['bgroupid']][batch_id])
    del batches[session['bgroupid']][batch_id]
    return jsonify(message='success'), 201

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')

    