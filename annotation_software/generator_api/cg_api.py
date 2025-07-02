# Attempt at RESTful CRUD API for crop generator and census server
# Based on https://https://www.digitalocean.com/community/tutorials/create-a-rest-api-using-flask-on-ubuntu 
# because I have never done this before
# Author: Michael B. Lance
# Created: April 7, 2025
# Updated: June 27, 2025

#---------------------------------------------------------------------------------------------------------------------------#

from flask import Flask, jsonify, request, Response, abort, session
from flask_cors import CORS
from flask_caching import Cache
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from dotenv import load_dotenv
import os
import io
from cropgenerator import auto_crop, create_subcrop, save_crop
from cropgenerator.generatorobjects import CgOBJ, CropgenJSONPRovider, Prediction, Box
import database as db
import json
from datetime import datetime
from uuid import uuid4

#---------------------------------------------------------------------------------------------------------------------------#
# Configuration

load_dotenv()

db_config = {
    'dbname': os.environ.get('DB_NAME'),
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
use_s3 = True

#---------------------------------------------------------------------------------------------------------------------------#
# Flask Instantiation

app = Flask(__name__)
app.json_provider_class = CropgenJSONPRovider
app.secret_key = os.environ.get('SECRET_KEY')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False 

CORS(app, resources={
    r'/api/*': {
        'origins': [
            'http://192.168.0.3:5173', # Development
            #'http://192.168.0.3:6900', # Production
            'http://localhost:5173',
        ],
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

#Initialize image backend and database
base = db.Postgres(db_config, root)
base.connect()

#Initialize s3 object storage
if use_s3:
    import boto3
    from botocore.client import Config
    from boto3.s3.transfer import TransferConfig

    BUCKET_NAME = 'mlance4' # Change to production bucket name

    extra_args = {
        'ContentType': 'image/jpg',
    }

    s3_config = Config(
        signature_version='s3',
        s3={
            'payload_signing_enabled': False,
            'addressing_style': 'virtual',
            'request_checksum_calculation': 'when_required',
            'response_checksum_validation': 'when_required' 
        }
    )

    pathfinder = boto3.client(
        's3',
        config = s3_config,
        endpoint_url = os.environ.get('AWS_ENDPOINT_URL_S3') 
    )

    transfer_config = TransferConfig(
        use_threads = True, #experimentally changed this to true, change to false if this things gets mad 
        multipart_threshold = 16 * 1024 * 1024
    )   
#---------------------------------------------------------------------------------------------------------------------------#

batches = {}

#---------------------------------------------------------------------------------------------------------------------------#
# User Management

class User(UserMixin, CgOBJ):
    def __init__(self, db_id: int, external_id: str, status: str, role: str, created: datetime.date,
                 updated: datetime.date, locale: str, uuid: uuid4, userName: str):
        self.db_id = db_id
        self.external_id = str(external_id)
        self.status = status 
        self.role = role
        self.created = created
        self.updated = updated
        self.locale = locale
        self.uuid = uuid
        self.userName = userName
    
    def get_id(self):
        return self.external_id
    
    @staticmethod
    @cache.memoize(300)
    def get(external_id):
        resp_dict = base.get_user(external_id)

        if not resp_dict:
            return None

        return User(
            db_id = resp_dict['db_id'],
            external_id = external_id,
            status = resp_dict['status'],
            role = resp_dict['role'],
            created = resp_dict['created'],
            updated = resp_dict['updated'],
            locale = resp_dict['locale'],
            uuid = resp_dict['uuid'],
            userName = resp_dict['userName']
        )

    def serialize(self):
        return {
            'db_id': self.db_id,
            'status': self.status,
            'role': self.role,
            'created': self.created,
            'updated': self.updated,
            'locale': self.locale,
            'userName': self.userName
        }

@login_manager.user_loader
def load_user(user_id_in_session):
    db_id = int(user_id_in_session)
    
    return User.get(user_id)

@login_manager.unauthorized_handler
def unauthorized_callback():        
    abort(401, 'unathorized, are you logged in? Should you be accessing this?')

@app.route('/api/v1/authenticate', methods=['POST'])
def authenticate():
    data = request.get_json()

    if not data or 'external-id' not in data:
        abort(400, 'malformed request')

    user = User.get(data['external-id'])

    if not user: 
        abort(404, 'user not found')

    else:
        login_user(user)
        base.set_last_login(user.db_id)
        session['bgroupid'] = user.uuid
        batches[session['bgroupid']] = {}
        session.modified = True
        serialized_user = json.dumps(user, default=app.json_provider_class(app).default)
        return Response(serialized_user, mimetype='application/json'), 201
    1
@app.route('/api/v1/check_auth', methods=["GET"])
@login_required
def check_auth():
    serialized_user = json.dumps(current_user, default=app.json_provider_class(app).default)

    return Response(serialized_user, mimetype='application/json'), 201

@app.route('/api/v1/deauthenticate', methods=["POST"])
@login_required
def logout():
    user = current_user

    for batch in batches[user.uuid]:
        delete_batch(batch)
    logout_user()
    
#---------------------------------------------------------------------------------------------------------------------------#
# Error Handling
@app.errorhandler(404)
def not_found(error):
    return f'Error 404: {error.description}', 404

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
    serialized_data = json.dumps(batches[session['bgroupid']],  default=app.json_provider_class(app).default)
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
    
    return Response(crop.serve('.webp'), mimetype='image/webp'), 201

# GET request: get batch ids 
@app.route('/api/v1/batches/ids', methods=['GET'])
@login_required
def get_batch_ids():
    try:
        batches[session['bgroupid']]
    except KeyError:
        batches[session['bgroupid']] = {}
    return jsonify(list(batches[session['bgroupid']].keys())), 201

# GET request: get a full crop
@app.route('/api/v1/batches/<int:batch_id>/images/<int:image_id>/crops/<int:crop_id>', methods=['GET'])
@login_required
def get_crop(batch_id, image_id, crop_id):
    #TODO: Check session level authentication 
    try:
        crop = batches[session['bgroupid']][batch_id][image_id]['crops'][crop_id]
    except KeyError:
        abort(404, 'crop not found')

    return Response(crop.serve('.webp'), mimetype='image/webp'), 201

# GET request: get the schema information for the current project
@app.route('/api/v1/schema', methods=['GET'])
@login_required
def get_schema():
    return jsonify(base.schema), 201

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
    try:
        batch = base.retrieve_batch(batch_size, desired_class, min_confidence, herd_unit_id, model_Id)
    except db.BatchError as e:
        print(e)
        abort(418, f'{db.BatchError}, also I am a teapot.')
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
    try:
        image = batches[session['bgroupid']][batch_id][image_id]['image']
    except KeyError:
        abort(404, f'Image {image_id} not found')
    predictions = batches[session['bgroupid']][batch_id][image_id]['predictions']
    if use_s3:
        image_key = f'images/{2024}/{image.herd_unit.name.lower()}/{image.name}.JPG'
        image.set_image(pathfinder.get_object(Bucket=BUCKET_NAME, Key=image_key)['Body'].read())
    crops = create_subcrop(image, predictions)
    batches[session['bgroupid']][batch_id][image_id]['pred_crops'] = {}
    for crop in crops:
        batches[session['bgroupid']][batch_id][image_id]['pred_crops'][crop.pred_crop_id] = crop

    serialized_data = json.dumps(crops, default=app.json_provider_class(app).default)
    return Response(serialized_data, mimetype='application/json'), 201   

# POST request: Create full crops of an image
@app.route('/api/v1/batches/<int:batch_id>/images/<int:image_id>/create_crops', methods=['POST'])
@login_required
def create_crops(batch_id: int, image_id: int):
    batch = batches[session['bgroupid']][batch_id][image_id]
    crop_size = request.json.get('crop_size')
    image = batch['image']
    base_key = f'crops/{image.herd_unit.survey_year}/{image.name}/'
    predictions = [pred for pred in batch['predictions'] if pred.id in set(batch['approved_predictions'])]
    crops = auto_crop(image=image, predictions=predictions, crop_size=crop_size)

    if use_s3:
       for crop_id in crops:
        crop = crops[crop_id]['crop']
        object_key = base_key + f'{crop.name}.JPG'
        pathfinder.upload_fileobj(io.BytesIO(crop.serve('.JPG')), BUCKET_NAME, object_key, ExtraArgs=extra_args)
    else: 
        for crop_id in crops:
            crop = crops[crop_id]['crop']
            save_crop(crop, save_folder)
    
    base.upload_crops(crops) # upload crops to database and set image reviewed

    serialized_data = json.dumps(crops, default=app.json_provider_class(app).default)
    return Response(serialized_data, mimetype='application/json'), 201

#---------------------------------------------------------------------------------------------------------------------------#
# Put Requests

# Put request: Update an image in a batch with approved predictions
@app.route('/api/v1/batches/<int:batch_id>/images/<int:image_id>/approve_predictions', methods=['PUT'])
@login_required
def approve_predictions(batch_id: int, image_id: int):
    try:
        batches[session['bgroupid']][batch_id][image_id]['approved_predictions'] = request.get_json()
        base.set_reviewed(image_id)
    except KeyError:
        abort(404, 'Image Not Found')

    return jsonify( message="success" ), 201

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

    