import os
import boto3
from boto3.s3.transfer import TransferConfig
from boto3.s3.transfer import TransferConfig
from botocore.client import Config
from botocore.config import Config
from dotenv import load_dotenv
from flask import Flask
from flask_caching import Cache
from flask_cors import CORS
from flask_login import LoginManager
from flask_session import Session
import redis

import database as db

load_dotenv()

db_config = {
	'dbname': os.environ.get('DB_NAME'),
	'user': os.environ.get('DB_USER'),              
	'password': os.environ.get('DB_PASS'),    
	'host': os.environ.get('DB_HOST'),           
	'port': '5433'              
}

base = None
cache = Cache()

cache_config={
	'CACHE_TYPE': 'RedisCache',
	'CACHE_DEFAULT_TIMEOUT': 300,
	'CACHE_REDIS_HOST': os.environ.get('VALKEY_HOST'),
	'CACHE_REDIS_PORT': 6379,
	'CACHE_REDIS_PASSWORD': os.environ.get('VALKEY_PASS')
}	


def create_app():
	global base
	global login_manager
	global cache
	global pathfinder
	base = db.Database(db_config) #pyright: ignore
	app = Flask(__name__)
	app.secret_key = os.environ.get('SECRET_KEY')
	app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
	app.config['SESSION_COOKIE_SECURE'] = True 
	app.config['SESSION_TYPE'] = 'redis'
	app.config['SESSION_PERMANENT'] = True
	app.config['SESSION_USE_SIGNER'] = True
	app.config['SESSION_REDIS'] = redis.from_url(os.environ.get('SESSION_REDIS'))
	app.config['TESTING'] = True
	app.config['DEBUG'] = True
	url = os.environ.get('ORIGIN_URL')
	print(url)
	CORS(app, resources={
		r'/api/*': {
			'origins': [
				url
			],
			'supports_credentials': True     
		}
	})

	# Cache
	

	BUCKET_NAME = 'mlance4' # Change to production bucket name

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

	cache.init_app(app, cache_config)
	login_manager = LoginManager()
	login_manager.init_app(app)
	server_session = Session(app)

	return app
