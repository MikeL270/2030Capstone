# Attempt at RESTful CRUD API for crop generator and census server
# Based on https://https://www.digitalocean.com/community/tutorials/create-a-rest-api-using-flask-on-ubuntu 
# because I have never done this before
# Author: Michael B. Lance
# Created: April 7, 2025
# Updated: April 7, 2025

#---------------------------------------------------------------------------------------------------------------------------#

from flask import Flask, jsonify, request
from dotenv import load_dotenv
import os
import cropgenerator
from cropgenerator import Image, Crop, Prediction, Box

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

@app.route('/')
def hello_workd():
    return jsonify(message='Hello Gamers!')    

# In memory item store, list of dicts for now
# TODO make proper container object with ids and such

objects = []

#---------------------------------------------------------------------------------------------------------------------------#
# GET requests

# GET request: Retrieve all objects items
@app.route('/api/objects', methods=['GET'])
def get_objects():
    return jsonify(objects)

# GET request: Retrieve a batch of images
# TODO: modify to work with proper container datastructure
@app.route('/api/objects/<int:batch_id>', methods=['GET'])
def get_batch(batch_id):
    batch = next((batch for batch in objects if batch['batch_id'] == batch_id), None) 
    if batch is None:
        return jsonify({'error': 'Batch not found'}), 404
    return jsonify(batch)

# GET request: Retrives crops of an image
# TODO: modify to work with proper container datastructure
@app.route('/api/objects/<int:crops_id>', methods=['GET'])
def get_crops(image_id):
    crops = next((batch for batch in objects if batch['crops_id'] == image_id), None)
    if crops is None:
        return jsonify({'error': 'crops not found'}), 404
    return jsonify(crops)

#---------------------------------------------------------------------------------------------------------------------------#
# POST Requests

# POST request: retrieve a batch of images from the database
@app.route('/api/objects', methods=['POST'])
def retrieve_batch():
    batch_size = request.json.get('batch_size')
    desired_class = request.json.get('desired_class')
    min_confidence = request.json.get('min_confidence')
    batch = cropgenerator.retrieve_batch(batch_size, desired_class, min_confidence)
    new_batch_obj = {'batch_id': len(objects) + 1, 'batch': batch}
    objects.append(new_batch_obj)

    out = {}

    for image_id in batch.keys():
        image = batch[image_id]['image']
        predictions = batch[image_id]['predictions']

        out[image_id] = {}
        out[image_id]['image'] = image.serialize()
        out[image_id]['predictions'] = [p.serialize() for p in predictions]

    return jsonify(out), 201

# POST request: create a bath of crops based on an image
@app.route('/api/objects', methods=['POST'])
def create_crops():
    batch_id = request.json.get('batch_id')
    image_id = request.json.get('image_id')
    desired_class = request.json.get('desired_class')
    batch = next((batch for batch in objects if batch['batch_id'] == batch_id), None)
    image = batch[image_id]['image']
    predictions = batch[image_id]['predictions']
    crops = cropgenerator.generate_crops(image, predictions, desired_class)
    

if __name__ == "__main__":
    app.run(debug=True)