# Attempt at RESTful CRUD API for crop generator and census server
# Based on https://https://www.digitalocean.com/community/tutorials/create-a-rest-api-using-flask-on-ubuntu 
# because I have never done this before
# Author: Michael B. Lance
# Created: April 7, 2025
# Updated: May 28, 2025

#---------------------------------------------------------------------------------------------------------------------------#

from flask import Flask, jsonify, request, Response, abort, session
from flask_cors import CORS
from dotenv import load_dotenv
import os
import cropgenerator
from cropgenerator import CropgenJSONPRovider
from cropgenerator import Prediction, Box
import json
from functools import wraps


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
app.secret_key = os.environ.get("SECERET_KEY")

CORS(app)  

#Initialize image backend
img_backend = cropgenerator.imagebackends.OpencvBackend()
base = cropgenerator.database.Postgres(db_config, root)
base.connect()

#---------------------------------------------------------------------------------------------------------------------------#

batches = {}

#---------------------------------------------------------------------------------------------------------------------------#
# Route decorator


#---------------------------------------------------------------------------------------------------------------------------#
# GET requests
# Get request: Test connectivity
@app.route('/api/v1/test', methods=['GET'])
def test_api():
    return jsonify(message='Connected to v1 successfully'), 201

# GET request: Retrieve all batches items
@app.route('/api/v1/batches', methods=['GET'])
def get_batches():
    serialized_data = json.dumps(batches,  default=app.json_provider_class(app).default)
    return Response(serialized_data, mimetype='application/json'), 201

# GET request: Retrieve a batch of images
# TODO: modify to work with proper container datastructure
@app.route('/api/v1/batches/<int:batch_id>', methods=['GET'])
def get_batch(batch_id):
    print(batches.keys())
    batch = batches[batch_id] 
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
        crop = batches[batch_id][image_id]['pred_crops'][crop_id]
    except Exception as e:
        return jsonify(message='Crop not found')
    
    return Response(crop.serve(), mimetype='image/webp'), 201

# GET request: get a full crop
@app.route('/api/v1/batches/<int:batch_id>/images/<int:image_id>/crops/<int:crop_id>', methods=['GET'])
def get_crop(batch_id, image_id, crop_id):
    #TODO: Check session level authentication 
    try:
        crop = batches[batch_id][image_id]['crops'][crop_id]
    except Exception as e:
        return jsonify(message='Crop not found')
    
    return Response(crop.serve(), mimetype='image/webp'), 201


#---------------------------------------------------------------------------------------------------------------------------#
# POST Requests

# POST request: retrieve a batch of images from the database
@app.route('/api/v1/images/create_batch', methods=['POST'])
def retrieve_img_batch():
    batch_size = request.json.get('batch_size')
    desired_class = request.json.get('desired_class')
    min_confidence = request.json.get('min_confidence')
    herd_unit_id = request.json.get('herd_unit_id')
    model_Id = request.json.get('model_id')
    batch = base.retrieve_batch(batch_size, desired_class, min_confidence, herd_unit_id, model_Id)
    batch_id = len(batches) + 1
    new_batch_obj = {batch_id: batch}
    batches[batch_id] = batch
    serialized_data = json.dumps(new_batch_obj,  default=app.json_provider_class(app).default)
    return Response(serialized_data, mimetype='application/json'), 201 

# POST request: Create prediction level crops
@app.route('/api/v1/batches/<int:batch_id>/images/<int:image_id>/create_pred_crops', methods=['POST'])
def create_pred_crops(batch_id: int, image_id: int):
     
    image = batches[batch_id][image_id]['image']
    predictions = batches[batch_id][image_id]['predictions']
    crops = img_backend.create_subcrop(image, predictions)
    batches[batch_id][image_id]['pred_crops'] = {}
    for crop in crops:
        batches[batch_id][image_id]['pred_crops'][crop.pred_crop_id] = crop

    serialized_data = json.dumps(crops, default=app.json_provider_class(app).default)
    return Response(serialized_data, mimetype='application/json'), 201   

# POST request: Create full crops of an image
@app.route('/api/v1/batches/<int:batch_id>/images/<int:image_id>/create_crops', methods=['POST'])
def create_crops(batch_id: int, image_id: int):
     
    crop_size = request.json.get('crop_size')
    image = batches[batch_id][image_id]['image']
    predictions = batches[batch_id][image_id]['approved_predictions']
    crops = cropgenerator.auto_crop(image=image, predictions=predictions, crop_size=crop_size)
    serialized_data = json.dumps(crops, default=app.json_provider_class(app).default)
    return Response(serialized_data, mimetype='application/json'), 201

#---------------------------------------------------------------------------------------------------------------------------#
# Put Requests

# Put request: Update an image in a batch with approved predictions
@app.route('/api/v1/batches/<int:batch_id>/images/<int:image_id>/approve_predictions', methods=['PUT'])
def approve_predictions(batch_id: int, image_id: int):
     
    batches[batch_id][image_id]['approved_predictions'] = []
    approved_predictions = request.get_json()
    for pred in approved_predictions:
        print(pred)
        batches[batch_id][image_id]['approved_predictions'].append(
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
def delete_batch(batch_id):
     
    base.close_batch(batches[batch_id])
    del batches[batch_id]
    return jsonify(message='success'), 201

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')