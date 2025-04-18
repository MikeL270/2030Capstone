# Attempt at RESTful CRUD API for crop generator and census server
# Based on https://https://www.digitalocean.com/community/tutorials/create-a-rest-api-using-flask-on-ubuntu 
# because I have never done this before
# Author: Michael B. Lance
# Created: April 7, 2025
# Updated: April 9, 2025

#---------------------------------------------------------------------------------------------------------------------------#

from flask import Flask, jsonify, request, Response
from dotenv import load_dotenv
import os
import cropgenerator
from cropgenerator import CropgenJSONPRovider
import json

#---------------------------------------------------------------------------------------------------------------------------#
load_dotenv()


db_config = {
    'database': os.environ.get('DB_NAME'),
    'user': os.environ.get('DB_USER'),              
    'password': os.environ.get('DB_PASS'),    
    'host': os.environ.get('DB_HOST'),           
    'port': '5432'              
}

cropgenerator.initialize(db_type='postgres', db_configuration=db_config, image_backend=None)


app = Flask(__name__)
app.json_provider_class = CropgenJSONPRovider  


@app.route('/')
def hello_world():

    return jsonify(message='Hi mom!')    

# In memory item store, list of dicts for now
# TODO make proper container object with ids and such

batches = {}

#---------------------------------------------------------------------------------------------------------------------------#
# GET requests

# GET request: Retrieve all batches items
@app.route('/api/v1/batches', methods=['GET'])
def get_batches():
    serialized_data = json.dumps(batches,  default=app.json_provider_class(app).default)
    return Response(serialized_data, mimetype='application/json'), 201

# GET request: Retrieve a batch of images
# TODO: modify to work with proper container datastructure
@app.route('/api/v1/batch/<int:batch_id>', methods=['GET'])
def get_batch(batch_id):
    print(batches.keys())
    batch = batches[batch_id] 
    if batch is None:
        return jsonify({'error': 'Batch not found'}), 404
    return jsonify(batch)

#---------------------------------------------------------------------------------------------------------------------------#
# POST Requests

# POST request: retrieve a batch of images from the database
@app.route('/api/v1/batches', methods=['POST'])
def retrieve_batch():
    batch_size = request.json.get('batch_size')
    desired_class = request.json.get('desired_class')
    min_confidence = request.json.get('min_confidence')
    batch = cropgenerator.retrieve_batch(batch_size, desired_class, min_confidence)
    batch_id = len(batches) + 1
    new_batch_obj = {'batch_id': batch_id, 'batch': batch}
    batches[batch_id] = batch
    serialized_data = json.dumps(new_batch_obj,  default=app.json_provider_class(app).default)
    return Response(serialized_data, mimetype='application/json'), 201

# POST request: create a batch of crops based on an image
@app.route('/api/v1/crops', methods=['POST'])
def create_crops():
    batch_id = request.json.get('batch_id')
    image_id = request.json.get('image_id')
    crop_size = request.json.get('crop_size')
    image = batches[batch_id][image_id]['image']
    predictions = batches[batch_id][image_id]['predictions']
    crops = cropgenerator.generate_crops(image, predictions, crop_size)
    crops_obj = {'image_id': image_id, 'crops': crops}
    
    serialized_data = json.dumps(crops_obj, default=app.json_provider_class(app).default)
    return Response(serialized_data, mimetype='application/json'), 201

#---------------------------------------------------------------------------------------------------------------------------#
# Delete request: Delete a crop
@app.route('/api/v1/batches/<int:batch_id>', methods=['DELETE'])
def delete_batch(batch_id):
    cropgenerator.close_batch(batches[batch_id])
    del batches[batch_id]


if __name__ == "__main__":
    app.run(debug=True)