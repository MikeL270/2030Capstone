# Attempt at RESTful CRUD API for crop generator and census server
# Based on https://https://www.digitalocean.com/community/tutorials/create-a-rest-api-using-flask-on-ubuntu 
# because I have never done this before
# Author: Michael B. Lance
# Created: April 7, 2025
# Updated: July 23, 2025

#---------------------------------------------------------------------------------------------------------------------------#

from flask import Flask, jsonify, request, Response, abort, session
from flask_session import Session
import redis
from flask_cors import CORS
from flask_caching import Cache
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from dotenv import load_dotenv 
import os
import cv2
from cropgenerator import auto_crop, create_subcrop, save_crop
from cropgenerator.generatorobjects import CropgenJSONPRovider
import database as db
import json
import boto3
from botocore.client import Config
from boto3.s3.transfer import TransferConfig
from uuid import UUID

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

use_s3 = True

#---------------------------------------------------------------------------------------------------------------------------#
# Flask Instantiation

app = Flask(__name__)
app.json_provider_class = CropgenJSONPRovider
app.secret_key = os.environ.get('SECRET_KEY')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False 
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_REDIS'] = redis.from_url(os.environ.get('SESSION_REDIS'))

server_session = Session(app)

CORS(app, resources={
	r'/api/*': {
		'origins': [
			'http://testing.lancecomputer.com:5173', # Development
			#'http://192.168.0.3:6900', # Production
			#'http://localhost:5173',
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
    signature_version='s3v4',  # s3v4 is the standard, s3 is an older version
    s3={'addressing_style': 'path',
		'payload_signing_enabled': True
		}, 
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
@cache.memoize(300)
def load_user(session_user_id):
	user = base.get_user(UUID(session_user_id))
	print(session_user_id) 
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
	print(user)#
	if not user:
		abort(401, 'authentication failed')
	else:
		login_user(user)
		if not user.last_login:
			user.last_login = base.login_user(user)
		else:
			base.login_user(user)
		serialized_user = json.dumps(user, default=app.json_provider_class(app).default)
		return Response(serialized_user, mimetype='application/json'), 201

@app.route('/api/v1/check_auth', methods=["GET"])
@login_required
def check_auth():
	return Response('true'), 201

@app.route('/api/v1/users/get_current_user', methods = ['GET'])
@login_required
def get_user():
	user = base.get_user(UUID(current_user.id))
	serialized_user = json.dumps(user, default=app.json_provider_class(app).default)
	return Response(serialized_user, mimetype='application/json'), 201

@app.route('/api/v1/deauthenticate', methods=["POST"])
@login_required
def logout():
	logout_user()

#---------------------------------------------------------------------------------------------------------------------------#
# Organization CRUD
@app.route('/api/v1/create/organization')
@login_required
def create_organization():
	pass

@app.route('/api/v1/request/organizations/all')
@login_required
def get_user_organizations():
	organizations = base.get_user_organizations(current_user)
	serialized_organizations = [json.dumps(organization, defalut=app.json_provider_class(app).default) for organization in organizations] if organizations else None
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
	serialized_project = json.dumps(project, default=app.json_provider_class(app).default)
	return Response(serialized_project, mimetype='application/json'), 201

@app.route('/api/v1/projects/request/<string:project_id>', methods=['GET'])
@login_required
def get_project(project_id: str):
	project = base.get_project(project_id = UUID(project_id))
	if not project:
		abort(404, 'project not found')
	user_can_access_proj = base.check_user_in_project(current_user, project)
	print(user_can_access_proj)
	serialized_project = json.dumps(project, default=app.json_provider_class(app).default)
	return Response(serialized_project, mimetype='application/json'), 201 if user_can_access_proj else abort(401, 'unauthorized')

@app.route('/api/v1/request/projects/all')
@login_required
def get_all_projects():
	projects = base.get_user_projects(current_user)
	serialized_projects = [json.dumps(project, default=app.json_provider_class(app).default) for project in projects] if projects else None
	return jsonify(serialized_projects), 201

@app.route('/api/v1/projects/update/<string:project_id>', methods = ['PUT'])
@login_required
def update_project(project_id: str):
	pass

#---------------------------------------------------------------------------------------------------------------------------#
# Schema CRUD

@app.route('/api/v1/request/projects/<string:project_id>/schemas/all', methods=['GET'])
@login_required
def get_project_schemas(project_id: str):
	schemas = base.get_project_schemas(UUID(project_id))
	serialized_schemas = [json.dumps(schema, default=app.json_provider_class(app).default) for schema in schemas] if schemas else None
	return jsonify(serialized_schemas), 201

#---------------------------------------------------------------------------------------------------------------------------#
# Label CRUD

@app.route('/api/v1/create/label')
@login_required
def create_label():
	pass

@app.route('/api/v1/request/projects/<string:project_id>/schemas/<string:schema_id>/labels/all', methods=['GET'])
@login_required
def get_schema_labels(project_id: str, schema_id: str):
	labels = base.get_schema_labels(UUID(schema_id))
	serialized_labels = [json.dumps(label, default=app.json_provider_class(app).default) for label in labels] if labels else None
	return jsonify(serialized_labels), 201

#---------------------------------------------------------------------------------------------------------------------------#
# Herd Unit Crud
 
@app.route('/api/v1/request/projects/<string:project_id>/herd_units/all', methods=['GET'])
@login_required
def get_project_herdunits(project_id: str):
	herd_units = base.get_project_herd_units(UUID(project_id))
	serialized_herd_units = [json.dumps(herd_unit, default=app.json_provider_class(app).default) for herd_unit in herd_units] if herd_units else None
	if serialized_herd_units is None:
		abort(404, 'No Herd Units Found')
	return jsonify(serialized_herd_units), 201

@app.route('/api/v1/request/surveys/<string:survey_id>/herd_units/all', methods=['GET'])
@login_required
def get_survey_herdunits(survey_id: str):
	herd_units = base.get_cropping_herd_units(UUID(survey_id))
	serialized_herd_units = [json.dumps(herd_unit, default=app.json_provider_class(app).default) for herd_unit in herd_units] if herd_units else None
	if serialized_herd_units is None:
		abort(404, 'No Herd Units Found')
	return jsonify(serialized_herd_units), 201

#---------------------------------------------------------------------------------------------------------------------------#
# Model Crud

@app.route('/api/v1/request/projects/<string:project_id>/models/all', methods=['GET'])
@login_required
def get_project_models(project_id: str):
	models = base.get_project_models(UUID(project_id))
	serialized_models = [json.dumps(model, default=app.json_provider_class(app).default) for model in models] if models else None
	if serialized_models is None:
		abort(404, 'No Models Found')
	return jsonify (serialized_models), 201

@app.route('/api/v1/request/surveys/<string:survey_id>/herd_units/<string:herd_unit_id>/schemas/<string:schema_id>/models/all', methods=['GET'])
@login_required
def get_cropper_models(survey_id: str, herd_unit_id: str, schema_id: str):
	models = base.get_cropping_models(UUID(survey_id), UUID(herd_unit_id), UUID(schema_id))
	serialized_models = [json.dumps(model, default=app.json_provider_class(app).default) for model in models] if models else None
	if serialized_models is None:
		abort(404, 'No Models Found')
	return jsonify (serialized_models), 201

#---------------------------------------------------------------------------------------------------------------------------#
# Survey Crud

@app.route('/api/v1/request/projects/<string:project_id>/surveys/all', methods=['GET'])
@login_required
def get_project_surveys(project_id: str):
	surveys = base.get_projects_surveys(UUID(project_id))
	serialized_surveys = [json.dumps(survey, default=app.json_provider_class(app).default) for survey in surveys] if surveys else None
	if serialized_surveys is None:
		abort(404, 'No Surveys Found')
	return jsonify(serialized_surveys), 201

#---------------------------------------------------------------------------------------------------------------------------#
# Image Crud

@app.route('/api/v1/create/image', methods=['POST'])
@login_required
def upload_image_to_db():
	data = request.get_json()
	image = base.create_image(data['name'], UUID(data['herd_unit_id']), UUID(data['survey_id']), data['image_length'], data['image_width'])
	serialized_image = json.dumps(image, default=app.json_provider_class(app).default)
	if serialized_image is None:
		abort(500, 'Could not create Image')
	return jsonify(serialized_image), 201

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
	for crop in pred_crops: # Save crop image data into the cache
		cache.set(crop.uuid, crop.get_image(), timeout=0) # prediction crops don't expire, the MUST be deleted
		serialized_pred_crops.append(json.dumps(crop, default=app.json_provider_class(app).default))
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
	_, encoded_img = cv2.imencode('.webp', crop)

	return Response(encoded_img.tobytes(), mimetype='image/webp'), 201

#---------------------------------------------------------------------------------------------------------------------------#
# Error Handling
@app.errorhandler(404)
def not_found(error):
	return f'404: {error.description}', 404

@app.errorhandler(500)
def internal_service_error(error):
	return f'500: {error.description}', 500

#---------------------------------------------------------------------------------------------------------------------------#

# batches = {}

# #---------------------------------------------------------------------------------------------------------------------------#
# # User Management

# class User(UserMixin, CgOBJ):
#     def __init__(self, db_id: int, external_id: str, status: str, role: str, created: datetime.date,
#                  updated: datetime.date, locale: str, uuid: uuid4, userName: str):
#         self.db_id = db_id
#         self.external_id = str(external_id)
#         self.status = status 
#         self.role = role
#         self.created = created
#         self.updated = updated
#         self.locale = locale
#         self.uuid = uuid
#         self.userName = userName
	
#     def get_id(self):
#         return self.external_id
	
#     @staticmethod
#     @cache.memoize(300)
#     def get(external_id):
#         resp_dict = base.get_user(external_id)

#         if not resp_dict:
#             return None

#         return User(
#             db_id = resp_dict['db_id'],
#             external_id = external_id,
#             status = resp_dict['status'],
#             role = resp_dict['role'],
#             created = resp_dict['created'],
#             updated = resp_dict['updated'],
#             locale = resp_dict['locale'],
#             uuid = resp_dict['uuid'],
#             userName = resp_dict['userName']
#         )

#     def serialize(self):
#         return {
#             'db_id': self.db_id,
#             'status': self.status,
#             'role': self.role,
#             'created': self.created,
#             'updated': self.updated,
#             'locale': self.locale,
#             'userName': self.userName
#         }

# @login_manager.user_loader
# def load_user(user_id_in_session):
#     db_id = int(user_id_in_session)
	
#     return User.get(user_id)

# @login_manager.unauthorized_handler
# def unauthorized_callback():        
#     abort(401, 'unathorized, are you logged in? Should you be accessing this?')

# @app.route('/api/v1/authenticate', methods=['POST'])
# def authenticate():
#     data = request.get_json()

#     if not data or 'external-id' not in data:
#         abort(400, 'malformed request')

#     user = User.get(data['external-id'])

#     if not user: 
#         abort(404, 'user not found')

#     else:
#         login_user(user)
#         base.set_last_login(user.db_id)
#         session['bgroupid'] = user.uuid
#         batches[session['bgroupid']] = {}
#         session.modified = True
#         serialized_user = json.dumps(user, default=app.json_provider_class(app).default)
#         return Response(serialized_user, mimetype='application/json'), 201
#     1
# @app.route('/api/v1/check_auth', methods=["GET"])
# @login_required
# def check_auth():
#     serialized_user = json.dumps(current_user, default=app.json_provider_class(app).default)

#     return Response(serialized_user, mimetype='application/json'), 201

# @app.route('/api/v1/deauthenticate', methods=["POST"])
# @login_required
# def logout():
#     user = current_user

#     for batch in batches[user.uuid]:
#         delete_batch(batch)
#     logout_user()
	
# #---------------------------------------------------------------------------------------------------------------------------#
# # Error Handling
# @app.errorhandler(404)
# def not_found(error):
#     return f'Error 404: {error.description}', 404

# #---------------------------------------------------------------------------------------------------------------------------#
# # GET requests
# # Get request: Test connectivity
# @app.route('/api/v1/test', methods=['GET'])
# def test_api():
#     return jsonify(message='Connected to v1 successfully'), 201

# # GET request: Retrieve all batches items
# @app.route('/api/v1/batches', methods=['GET'])
# @login_required
# def get_batches():
#     serialized_data = json.dumps(batches[session['bgroupid']],  default=app.json_provider_class(app).default)
#     return Response(serialized_data, mimetype='application/json'), 201

# # GET request: Retrieve a batch of images
# # TODO: modify to work with proper container datastructure
# @app.route('/api/v1/batches/<int:batch_id>', methods=['GET'])
# @login_required
# def get_batch(batch_id):
#     batch = batches[session['bgroupid']][batch_id] 
#     batch_obj = {batch_id: batch}
#     if batch is None: 
#         return jsonify({'error': 'Batch not found'}), 404
#     serialized_data = json.dumps(batch_obj, default=app.json_provider_class(app).default)
#     return Response(serialized_data, mimetype='application/json'), 201

# # GET request: get a prediction level crop
# @app.route('/api/v1/batches/<int:batch_id>/images/<int:image_id>/pred_crops/<int:crop_id>', methods=['GET'])
# def get_pred_crop(batch_id, image_id, crop_id):
#     #TODO: Check session level authentication 
#     try:
#         crop = batches[session['bgroupid']][batch_id][image_id]['pred_crops'][crop_id]
#     except Exception as e:
#         return jsonify(message='Crop not found')
	
#     return Response(crop.serve('.webp'), mimetype='image/webp'), 201

# # GET request: get batch ids 
# @app.route('/api/v1/batches/ids', methods=['GET'])
# @login_required
# def get_batch_ids():
#     try:
#         batches[session['bgroupid']]
#     except KeyError:
#         batches[session['bgroupid']] = {}
#     return jsonify(list(batches[session['bgroupid']].keys())), 201

# # GET request: get a full crop
# @app.route('/api/v1/batches/<int:batch_id>/images/<int:image_id>/crops/<int:crop_id>', methods=['GET'])
# @login_required
# def get_crop(batch_id, image_id, crop_id):
#     #TODO: Check session level authentication 
#     try:
#         crop = batches[session['bgroupid']][batch_id][image_id]['crops'][crop_id]
#     except KeyError:
#         abort(404, 'crop not found')

#     return Response(crop.serve('.webp'), mimetype='image/webp'), 201

# # GET request: get the schema information for the current project
# @app.route('/api/v1/schema', methods=['GET'])
# @login_required
# def get_schema():
#     return jsonify(base.schema), 201

# #---------------------------------------------------------------------------------------------------------------------------#
# # POST Requests

# # POST request: retrieve a batch of images from the database
# @app.route('/api/v1/images/create_batch', methods=['POST'])
# @login_required
# def retrieve_img_batch():
#     batch_size = request.json.get('batch_size')
#     desired_class = request.json.get('desired_class')
#     min_confidence = request.json.get('min_confidence')
#     herd_unit_id = request.json.get('herd_unit_id')
#     model_Id = request.json.get('model_id')
#     try:
#         batch = base.retrieve_batch(batch_size, desired_class, min_confidence, herd_unit_id, model_Id)
#     except db.BatchError as e:
#         print(e)
#         abort(418, f'{db.BatchError}, also I am a teapot.')
#     try:
#         batch_id = len(batches[session['bgroupid']]) + 1
#         new_batch_obj = {batch_id: batch}
#         batches[session['bgroupid']][batch_id] = batch
#     except KeyError:
#         batches[session['bgroupid']] = {}
#         batch_id = len(batches[session['bgroupid']]) + 1
#         new_batch_obj = {batch_id: batch}
#         batches[session['bgroupid']][batch_id] = batch

#     serialized_data = json.dumps(new_batch_obj,  default=app.json_provider_class(app).default)
#     return Response(serialized_data, mimetype='application/json'), 201 

# # POST request: Create prediction level crops
# @app.route('/api/v1/batches/<int:batch_id>/images/<int:image_id>/create_pred_crops', methods=['POST'])
# @login_required
# def create_pred_crops(batch_id: int, image_id: int):
#     try:
#         image = batches[session['bgroupid']][batch_id][image_id]['image']
#     except KeyError:
#         abort(404, f'Image {image_id} not found')
#     predictions = batches[session['bgroupid']][batch_id][image_id]['predictions']
#     if use_s3:
#         image_key = f'images/{2024}/{image.herd_unit.name.lower()}/{image.name}.JPG'
#         image.set_image(pathfinder.get_object(Bucket=BUCKET_NAME, Key=image_key)['Body'].read())
#     crops = create_subcrop(image, predictions)
#     batches[session['bgroupid']][batch_id][image_id]['pred_crops'] = {}
#     for crop in crops:
#         batches[session['bgroupid']][batch_id][image_id]['pred_crops'][crop.pred_crop_id] = crop

#     serialized_data = json.dumps(crops, default=app.json_provider_class(app).default)
#     return Response(serialized_data, mimetype='application/json'), 201   

# # POST request: Create full crops of an image
# @app.route('/api/v1/batches/<int:batch_id>/images/<int:image_id>/create_crops', methods=['POST'])
# @login_required
# def create_crops(batch_id: int, image_id: int):
#     batch = batches[session['bgroupid']][batch_id][image_id]
#     crop_size = request.json.get('crop_size')
#     image = batch['image']
#     base_key = f'crops/{image.herd_unit.survey_year}/{image.name}/'
#     predictions = [pred for pred in batch['predictions'] if pred.id in set(batch['approved_predictions'])]
#     crops = auto_crop(image=image, predictions=predictions, crop_size=crop_size)

#     if use_s3:
#        for crop_id in crops:
#         crop = crops[crop_id]['crop']
#         object_key = base_key + f'{crop.name}.JPG'
#         pathfinder.upload_fileobj(io.BytesIO(crop.serve('.JPG')), BUCKET_NAME, object_key, ExtraArgs=extra_args)
#     else: 
#         for crop_id in crops:
#             crop = crops[crop_id]['crop']
#             save_crop(crop, save_folder)
	
#     base.upload_crops(crops) # upload crops to database and set image reviewed

#     serialized_data = json.dumps(crops, default=app.json_provider_class(app).default)
#     return Response(serialized_data, mimetype='application/json'), 201

# #---------------------------------------------------------------------------------------------------------------------------#
# # Put Requests

# # Put request: Update an image in a batch with approved predictions
# @app.route('/api/v1/batches/<int:batch_id>/images/<int:image_id>/approve_predictions', methods=['PUT'])
# @login_required
# def approve_predictions(batch_id: int, image_id: int):
#     try:
#         batches[session['bgroupid']][batch_id][image_id]['approved_predictions'] = request.get_json()
#         base.set_reviewed(image_id)
#     except KeyError:
#         abort(404, 'Image Not Found')

#     return jsonify( message="success" ), 201

# #---------------------------------------------------------------------------------------------------------------------------#
# # Delete request: Delete a crop
# @app.route('/api/v1/batches/<int:batch_id>', methods=['DELETE'])
# @login_required
# def delete_batch(batch_id):
	 
#     base.close_batch(batches[session['bgroupid']][batch_id])
#     del batches[session['bgroupid']][batch_id]
#     return jsonify(message='success'), 201

if __name__ == "__main__":
	app.run(debug=True, host='0.0.0.0')

	