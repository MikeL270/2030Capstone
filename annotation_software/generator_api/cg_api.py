# Attempt at RESTful CRUD API for crop generator and census server
# Based on https://https://www.digitalocean.com/community/tutorials/create-a-rest-api-using-flask-on-ubuntu 
# because I have never done this before
# Author: Michael B. Lance
# Created: April 7, 2025
# Updated: September 25, 2025

#---------------------------------------------------------------------------------------------------------------------------#

from flask import Flask, jsonify, request, Response, abort, session
from flask_session import Session
import redis
from flask_cors import CORS
from flask_caching import Cache
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from dotenv import load_dotenv 
import os
import io
import cv2
from cropgenerator import auto_crop, create_subcrop
from cropgenerator.generatorobjects import CropgenJSONPRovider, Prediction
import database as db
import json
import boto3
from botocore.client import Config
from boto3.s3.transfer import TransferConfig
from uuid import UUID
from datetime import datetime

#---------------------------------------------------------------------------------------------------------------------------#
# Configuration

load_dotenv()

db_config = {
	'dbname': os.environ.get('DB_NAME'),
	'user': os.environ.get('DB_USER'),              
	'password': os.environ.get('DB_PASS'),    
	'host': os.environ.get('DB_HOST'),           
	'port': '5433'              
}

#---------------------------------------------------------------------------------------------------------------------------#
# Flask Instantiation

app = Flask(__name__)
app.json_provider_class = CropgenJSONPRovider
app.secret_key = os.environ.get('SECRET_KEY')
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
app.config['SESSION_COOKIE_SECURE'] = True 
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_REDIS'] = redis.from_url(os.environ.get('SESSION_REDIS'))
url = os.environ.get('APPLICATION_URL')

server_session = Session(app)

CORS(app, resources={
	r'/api/*': {
		'origins': [
			url
		],
		'supports_credentials': True     
	}
})

# Cache
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
base = db.Database(db_config)

#Initialize s3 object storage

BUCKET_NAME = 'mlance4' # Change to production bucket name

from botocore.config import Config
from boto3.s3.transfer import TransferConfig

s3_config = Config(
    signature_version='s3',  # s3v4 is the standard, s3 is an older version
    s3={
            'payload_signing_enabled': True,
            'addressing_style': 'path',
            'request_checksum_calculation': 'when_required',
            'response_checksum_validation': 'when_required' 
        }
)

pathfinder = boto3.client(
    's3',
    config=s3_config,
    endpoint_url=os.environ.get('AWS_ENDPOINT_URL_S3')
)

transfer_config = TransferConfig(
    use_threads=True,
    multipart_threshold=16 * 1024 * 1024
)  
#---------------------------------------------------------------------------------------------------------------------------#
# User session management

@login_manager.user_loader
@cache.cached(300)
def load_user(session_user_id):
	user = base.get_user(UUID(session_user_id))
	return user 

@login_manager.unauthorized_handler
def unathorizated_callback():
	abort(401, 'unathorized, are you logged in? Should you be accessing this?')

@app.route('/api/v1/authenticate', methods=['POST'])
def authenticate():
	req_data = request.get_json()
	if not req_data or 'external-id' not in req_data:
		abort(400, 'malformed request')
	user = base.get_user(req_data['external-id'])
	if not user:
		abort(401, 'authentication failed')
	else:
		login_user(user)
		if not user.last_login:
			user.last_login = base.login_user(user)
		else:
			base.login_user(user)
		return user.serialize(), 201

@app.route('/api/v1/check_auth', methods=["GET"])
@login_required
def check_auth():
	return Response('true'), 201

@app.route('/api/v1/users/get_current_user', methods = ['GET'])
@login_required
def get_user():
	user = base.get_user(UUID(current_user.id))
	return user.serialize(), 201

@app.route('/api/v1/deauthenticate', methods=["POST"])
@login_required
def logout():
	logout_user()
	return '', 200

#---------------------------------------------------------------------------------------------------------------------------#
# # Organization CRUD
# @app.route('/api/v1/create/organization')
# @login_required
# def create_organization():
# 	pass

@app.route('/api/v1/request/organizations/all')
@login_required
def get_user_organizations():
	organizations = base.get_user_organizations(current_user)
	serialized_organizations = [organization.serialize() for organization in organizations] if organizations else None
	return jsonify(serialized_organizations), 201 

#---------------------------------------------------------------------------------------------------------------------------#
# Role CRUD

#---------------------------------------------------------------------------------------------------------------------------#
# Project CRUD

@app.route('/api/v1/projects/create', methods = ['POST'])
@login_required
def create_project():
	name = request.json.get('project_name') 
	project = base.create_project(name = name, users = current_user)
	return project.serialize(), 201

@app.route('/api/v1/projects/request/<string:project_id>', methods=['GET'])
@login_required
def get_project(project_id: str):
	project = base.get_project(project_id = UUID(project_id))
	if not project:
		abort(404, 'project not found')
	if base.check_user_in_project(current_user, project):
		return project.serialize()
	else:
		abort(401, 'cannot access project!')
	

@app.route('/api/v1/request/projects/all')
@login_required
def get_all_projects():
	projects = base.get_user_projects(current_user)
	serialized_projects = [project.serialize() for project in projects] 
	return jsonify(serialized_projects), 201

# @app.route('/api/v1/projects/update/<string:project_id>', methods = ['PUT'])
# @login_required
# def update_project(project_id: str):
# 	pass

#---------------------------------------------------------------------------------------------------------------------------#
# Schema CRUD

@app.route('/api/v1/request/projects/<string:project_id>/schemas/all', methods=['GET'])
@login_required
def get_project_schemas(project_id: str):
	schemas = base.get_project_schemas(UUID(project_id))
	serialized_schemas = [schema.serialize() for schema in schemas] if schemas else None
	return jsonify(serialized_schemas), 201

#---------------------------------------------------------------------------------------------------------------------------#
# Label CRUD

# @app.route('/api/v1/create/label')
# @login_required
# def create_label():
# 	pass

@app.route('/api/v1/request/projects/<string:project_id>/schemas/<string:schema_id>/labels/all', methods=['GET'])
@login_required
def get_schema_labels(project_id: str, schema_id: str):
	labels = base.get_schema_labels(UUID(schema_id))
	serialized_labels = [label.serialize() for label in labels]
	return jsonify(serialized_labels), 201

#---------------------------------------------------------------------------------------------------------------------------#
# Herd Unit Crud
 
@app.route('/api/v1/request/projects/<string:project_id>/herd_units/all', methods=['GET'])
@login_required
def get_project_herdunits(project_id: str):
	herd_units = base.get_project_herd_units(UUID(project_id))
	serialized_herd_units = [herd_unit.serialize() for herd_unit in herd_units]
	if serialized_herd_units is None:
		abort(404, 'No Herd Units Found')
	return jsonify(serialized_herd_units), 201

@app.route('/api/v1/request/surveys/<string:survey_id>/herd_units/all', methods=['GET'])
@login_required
def get_survey_herdunits(survey_id: str):
	herd_units = base.get_cropping_herd_units(UUID(survey_id))
	serialized_herd_units = [herd_unit.serialize() for herd_unit in herd_units] 
	if serialized_herd_units is None:
		abort(404, 'No Herd Units Found')
	return jsonify(serialized_herd_units), 201

#---------------------------------------------------------------------------------------------------------------------------#
# Model Crud

@app.route('/api/v1/create/model', methods=['POST'])
@login_required
def create_model():
	'''
	
	'''
	data = request.get_json()
	try:
		model = base.create_model(data['name'])
		return model
	except Exception as e:
		abort(500, e)

@app.route('/api/v1/request/projects/<string:project_id>/models/all', methods=['GET'])
@login_required
def get_project_models(project_id: str):
	models = base.get_project_models(UUID(project_id))
	serialized_models = [model.serialize() for model in models]
	if serialized_models is None:
		abort(404, 'No Models Found')
	return jsonify(serialized_models), 201

@app.route('/api/v1/request/surveys/<string:survey_id>/herd_units/<string:herd_unit_id>/schemas/<string:schema_id>/models/all', methods=['GET'])
@login_required
def get_cropper_models(survey_id: str, herd_unit_id: str, schema_id: str):
	models = base.get_cropping_models(UUID(survey_id), UUID(herd_unit_id), UUID(schema_id))
	serialized_models = [model.serialize() for model in models]
	if serialized_models is None:
		abort(404, 'No Models Found')
	return jsonify(serialized_models), 201

#---------------------------------------------------------------------------------------------------------------------------#
# Survey Crud

@app.route('/api/v1/request/projects/<string:project_id>/surveys/all', methods=['GET'])
@login_required
def get_project_surveys(project_id: str):
	surveys = base.get_projects_surveys(UUID(project_id))
	serialized_surveys = [survey.serialize() for survey in surveys]
	if serialized_surveys is None:
		abort(404, 'No Surveys Found')
	return jsonify(serialized_surveys), 201

#---------------------------------------------------------------------------------------------------------------------------#
# Image Crud

@app.route('/api/v1/create/image', methods=['POST'])
@login_required
def upload_image_to_db():
	'''
	'''
	data = request.get_json()
	image = base.create_image(data['name'], UUID(data['herd_unit_id']), UUID(data['survey_id']), data['img_key'], data['image_length'], data['image_width'])
	if image is None:
		abort(500, 'Could not create Image')
	return image.serialize(), 201

# @app.route('/api/v1/get/image', methods=['GET'])
# @login_required
# def get_image():
# 	'''
	
# 	'''
#---------------------------------------------------------------------------------------------------------------------------#
# Prediction Crud

@app.route('/api/v1/create/prediction', methods=['POST'])
def create_prediction():
	'''
	
	'''
	data = request.get_json()
	prediction = base.create_prediction(
		UUID(data['image_id']),
		UUID(data['model_id']),
		data['label'],
		data['score'],
		data['box_tx'],
		data['box_ty'],
		data['box_bx'],
		data['box_by'],
		data['returning']
	)
	return prediction.serialize(), 201


#---------------------------------------------------------------------------------------------------------------------------#
# Image and Prediction Mass Uploader

@app.route('/api/v1/upload/image/presigned-url', methods=['POST'])
@login_required
def get_presigned_url():
	'''
	Generates a pre-signed URL for a single file chunk. 
	This is the core endpoint for offloading data transfer. 
	The client sends a PUT request to this temporary URL with the chunk data.
	'''
	data = request.get_json()
	try: 
		response = pathfinder.generate_presigned_url(
		ClientMethod='upload_part', 
		Params = {
		'Bucket': BUCKET_NAME,
		'Key': data['image_key'], 
		'UploadId': data['upload_id'],
		'PartNumber': data['part_number'],
		'ContentLength': data['chunk_size'],
		'ContentMD5' : data['chunk_md5'],
		},
		ExpiresIn=3600,
		)
	except Exception as e:
		print(e)
		abort(500)
	return jsonify(response), 201


@app.route('/api/v1/upload/image/create_multipart_upload', methods=['POST'])
@login_required
def create_multipart_upload():
	'''
	Initiates a new multipart upload. The client calls this for each file 
	to be uploaded. the API responds with a unique UploadId, which is required 
	for all subsequent chunk uploads for that file.
	'''
   
	image_key = request.json.get('image_key')
	try: 
		response = pathfinder.create_multipart_upload(
			Bucket = BUCKET_NAME,
			Key = image_key,
			ContentType = 'image/jpeg',
		)
		upload_id = response['UploadId']
		return jsonify({'upload_id': upload_id}), 201
	except Exception as e:
		abort(500, e)

@app.route('/api/v1/upload/image/complete', methods=['POST'])
@login_required
def complete_upload():
	'''
	Finalizes a multipart upload. After all chunks have been successfully 
	uploaded, the client calls this endpoint with the UploadId and a list 
	of all part details (PartNumber, ETag) to assemble the file on the 
	storage backend.
	'''
	data = request.get_json()
	try:
		response = pathfinder.complete_multipart_upload(
			Bucket = BUCKET_NAME,
			Key = data['image_key'],
			MultipartUpload={
				'Parts': data['parts']
			},
			UploadId = data['upload_id'],
		)
	except Exception as e:
		abort(500, str(e))
	return jsonify(response), 201

@app.route('/api/v1/upload/image/abort', methods=['POST'])
@login_required 
def abort_upload():
	'''
	Aborts a multipart upload. This endpoint is for cleaning up partial 
	uploads on the storage backend if an upload is canceled or fails
	permanently.
	'''
	data = request.get_json()
	try:
		response = pathfinder.abort_multipart_upload(
			Bucket = BUCKET_NAME,
			Key = data['image_key'],
			UploadId = data['upload_id'],
		)
	except Exception as e: #
		abort(500, e)
	return jsonify(response), 201

#---------------------------------------------------------------------------------------------------------------------------#
# Auto Cropping
@app.route('/api/v1/create/batch', methods=['POST'])
@login_required
def get_batch():
	'''
	
	'''
	data = request.get_json()
	if 'pred_crop_data' in session: # Delete last batch's prediction crops
		for data in session['pred_crop_data']:
			cache.delete(data['uuid'])
		session.pop('pred_crop_data')
	img_batch = base.get_batch(
		UUID(data['survey_id']),
		UUID(data['herd_unit_id']),
		int(data['size']),
		int(data['label']),
		float(data['score']),
		UUID(data['model_id']),
		current_user)
	if img_batch is None:
		abort(404, 'Cannot get batch')
	
	return img_batch, 201
 
@app.route('/api/v1/create/prediction_crops', methods=['POST'])
@login_required
def create_prediction_crops():
	'''
	
	'''
	data = request.get_json()
	image = base.get_image(UUID(data['image_id']))
	img_data = cache.get(image.uuid)

	if not img_data:
		img_key = f'images/survey/{data['survey_id']}/herd_unit/{data['herd_unit_id']}/image/{image.name}'
		img_data = pathfinder.get_object(Bucket=BUCKET_NAME, Key=img_key)['Body'].read()
		cache.set(image.uuid, img_data, 360) 
	 
	image.set_image(img_data)
	pred_crops = create_subcrop(image, data['predictions'])
	serialized_pred_crops = [] 

	for crop in pred_crops: # Save crop image data into the session cache
		cache.set(crop.uuid,  crop.get_image(), 3600)
		serialized_pred_crops.append(crop.serialize())
	
	json_pred_crop_data = jsonify(serialized_pred_crops)
	
	if 'pred_crop_data' not in session:
		session['pred_crop_data'] = []
	
	session['pred_crop_data'] + serialized_pred_crops
	return json_pred_crop_data, 201

@app.route('/api/v1/request/image/<string:image_id>/pred_crop/<string:pred_crop_id>', methods=['GET'])
def get_pred_crop(image_id: str, pred_crop_id: str):
	'''
	
	'''
	crop = cache.get(pred_crop_id)
	if crop is None:
		abort(404, 'crop not found')

	_, encoded_img = cv2.imencode('.webp', crop)
	return Response(encoded_img.tobytes(), mimetype='image/webp'), 201

@app.route('/api/v1/update/image/no-annotations', methods=["POST"])
@login_required
def no_annotations():
	'''
	
	'''
	data = request.get_json()
	res_1 = base.close_image(UUID(data['image_id']))
	res_2 = base.set_predictions_reviewed([UUID(pred_id) for pred_id in data['prediction_ids']], current_user.user_id)	 	
	return '', 201 if res_1 and res_2 else abort(500, 'Update failed!')

@app.route('/api/v1/create/reviewed-area-and-annotations', methods=["PUT"])
@login_required
def create_reviewed_area_and_annotations():
	'''
	
	'''
	data = request.get_json()
	# Request image object from data in request
	image = base.get_image(UUID(data['image_uuid']))
	img_data = cache.get(image.uuid)

	if not img_data:
		img_key = f'images/survey/{data['survey_id']}/herd_unit/{data['herd_unit_id']}/image/{image.name}'
		img_data = pathfinder.get_object(Bucket=BUCKET_NAME, Key=img_key)['Body'].read()
		cache.set(image.uuid, img_data, 360) 
	image.set_image(img_data)

	# get label - id for schema
	label_ids = { lbl['label'] : lbl['label_id'] for lbl in data['labels'] }
	
	# (re)Construct prediction objects from data in request
	predictions = [Prediction(pred_id = pred['pred_id'], 
						   	  image_id = pred['image_id'],
							  model_id = pred['model_id'],
							  label = pred['label'],
							  score = pred['score'],
							  box_tx = pred['dimensions']['top_left'][0],
							  box_ty = pred['dimensions']['top_left'][1],
							  box_bx = pred['dimensions']['bottom_right'][0],
							  box_by = pred['dimensions']['bottom_right'][1],
							  created = datetime.fromisoformat(pred['created'].replace("Z", "+00:00")),
							  modified = datetime.fromisoformat(pred['modified'].replace("Z", "+00:00")),
							  uuid = pred['uuid']) for pred in data['predictions']]
  
	# Create reviewed area(s) from auto_crop() funchtion
	reviewed_areas = auto_crop(image=image, predictions=predictions, labels_ids=label_ids)

	#Create reviewed area and predictions objects  
	for area_set in reviewed_areas: 
		reviewed_area = area_set[0]
		annotations = area_set[1] 
		
		reviewed_area_ids = base.insert_reviewed_areas(reviewed_area)
		annotation_ids = base.insert_annotations(annotations, current_user)
		res_1 = base.add_reviewed_area_annotations(reviewed_area_ids, annotation_ids)
		
		ra_key = f'reviewed_areas/survey/{data['survey_id']}/herd_unit/{data['herd_unit_id']}/reviewed_area/{reviewed_area.name}'
		
		#pathfinder.upload_fileobj(io.BytesIO(reviewed_area.serve('.JPG')), BUCKET_NAME, ra_key)
		pathfinder.put_object(
			Bucket=BUCKET_NAME,
			Key=ra_key,
			Body=io.BytesIO(reviewed_area.serve('.JPG')),
			ContentType='image/jpeg'
		)

	res_2 = base.set_predictions_reviewed(predictions, current_user.user_id)
	res_3 = base.close_image(image)

	return '', 201 if res_1 and res_2 and res_3 else abort(500, 'Cropping failed!')

@app.route('/api/v1/end/crop_session', methods=['POST'])
@login_required
def close_crop_session():
	'''
	
	'''
	try:
		base.set_user_open_images_closed(current_user.user_id)
	except Exception as e:
		abort(500, e)
	return '', 201 

#---------------------------------------------------------------------------------------------------------------------------#
# Inference

@app.route('/api/v1/get/survey/<string:survey_id>/images/all')
@login_required
def get_survey_images(survey_id: str):
	'''
	
	'''
	try:
		images = base.get_survey_images(UUID(survey_id))
		serialized_images = [image.serialize() for image in images]
	except Exception as e:
		print(e)
		abort(500, e)
	return jsonify(serialized_images), 201
 
#---------------------------------------------------------------------------------------------------------------------------#
# Error Handling

@app.errorhandler(404)
def not_found(error): 
	return f'404: {error.description}', 404

@app.errorhandler(500)
def internal_service_error(error): 
	return f'500: {error.description}', 500

#---------------------------------------------------------------------------------------------------------------------------#


if __name__ == "__main__":
	app.run(debug=True, host='0.0.0.0')

	