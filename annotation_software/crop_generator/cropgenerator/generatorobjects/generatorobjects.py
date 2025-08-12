# Class definition for objects used in the crop_generator module and database
# Author: Michael B. Lance
# created: April 4, 2025
# updated: August, 2 2025
#---------------------------------------------------------------------------------------------------------------------------#

import numpy as np
import cv2
import os
from flask.json.provider import DefaultJSONProvider
import cv2
from abc import ABC, abstractmethod
from datetime import datetime
import io
import PIL.Image as PillowImage
from dataclasses import dataclass
from uuid import UUID
from flask_login import UserMixin

#---------------------------------------------------------------------------------------------------------------------------#
# ABC for easy serialization of child classes

class CgOBJ(ABC):
	@abstractmethod
	def serialize(self) -> dict:
		pass
	
#---------------------------------------------------------------------------------------------------------------------------#
# Project Management -- For Database use only

@dataclass
class Project(CgOBJ):
	''' Dataclass for representing projects from the databse
	
	'''
	project_id: int
	name: str
	created: datetime
	modified: datetime
	uuid: UUID

	def serialize(self):
		return {
			'name': self.name,
			'created': self.created,
			'modified': self.modified,
			'uuid': self.uuid
		}

@dataclass
class Schema(CgOBJ):
	''' Dataclass for representing scehmas from the databse
	
	'''
	schema_id: int
	name: str
	created: datetime
	modified: datetime
	uuid: UUID

	def serialize(self):
		return {
			'name': self.name,
			'created': self.created,
			'modified': self.modified,
			'uuid': self.uuid
		}

@dataclass
class Label(CgOBJ):
	''' Dataclass for representing labels from the databse
	
	'''
	label_id: int
	schema_id: int
	label: int
	name: str
	image_link: str
	created: datetime
	modified: datetime
	uuid: UUID

	def serialize(self):
		return {
			'label': self.label,
			'name': self.name,
			'image_link': self.image_link,
			'created': self.created,
			'modified': self.modified,
			'uuid': self.uuid
		}

@dataclass
class HerdUnit(CgOBJ):
	''' Dataclass for representing Herd Units from the database
	
	'''
	herd_unit_id: int
	name: str
	created: datetime
	modified: datetime
	uuid: UUID

	def serialize(self):
		return {
			'name': self.name,
			'created': self.created,
			'modified': self.modified,
			'uuid': self.uuid
		}

@dataclass
class Model(CgOBJ):
	''' Dataclass for representing Models from the database
	
	'''
	model_id: int
	name: str
	created: datetime
	modified: datetime
	uuid: UUID

	def serialize(self):
		return {
			'name': self.name,
			'created': self.created,
			'modified': self.modified,
			'uuid': self.uuid
		}
	
@dataclass
class Survey(CgOBJ):
	''' Dataclass for representing Surveys from the database
	
	'''
	survey_id: int
	survey_year: int
	name: str
	additional_info: str
	created: datetime
	modified: datetime
	uuid: UUID

	def serialize(self):
		return {
			'survey_year': self.survey_year,
			'name': self.name,
			'additional_info': self.additional_info,
			'created': self.created,
			'modified': self.modified,
			'uuid': self.uuid
		}
	
#---------------------------------------------------------------------------------------------------------------------------#
# User Management -- For Database use only

class User(UserMixin, CgOBJ):
	def __init__(self, user_id: int, username: str, external_auth_id: str, external_auth_provider: str, status: str,
				 created: datetime.date, modified: datetime.date, last_login: datetime,  locale: str, uuid: UUID, roles: tuple[str] | None = None):
		self.id = str(uuid) # this is this way to make Flask-Login happy
		self.user_id = user_id
		self.username = username
		self.external_auth_id = external_auth_id
		self.external_auth_provider = external_auth_provider
		self.status = status
		self.created = created
		self.modified = modified
		self.last_login = last_login
		self.locale = locale
		self.uuid = uuid
		self.roles = roles
	
	def get_id(self) -> str:
		return self.id
	
	def has_role(self, role_name: str) -> bool:
		return role_name in self.roles

	def serialize(self):
		return {
			'username': self.username,
			'status': self.status,
			'created': self.created,
			'modified': self.modified,
			'last_login': self.last_login,
			'locale': self.locale,
			'uuid': self.id,
			'roles': self.roles
		}
	
@dataclass
class Role(CgOBJ):
	role_id: int
	name: str
	created: datetime
	modified: datetime
	uuid: UUID

	def serialize(self):
		return {
			'name': self.name,
			'created': self.created,
			'modified': self.modified,
			'uuid': self.uuid
		}
	
@dataclass
class Organization(CgOBJ):
	organization_id: int
	name: str
	created: datetime
	modified: datetime
	logo_url: str | None
	uuid: UUID

	def serialize(self):
		return {
			'name': self.name,
			'created': self.created,
			'modified': self.modified,
			'logo_url': self.logo_url,
			'uuid': self.uuid
		}

#---------------------------------------------------------------------------------------------------------------------------#
# Core 

class Box(CgOBJ):
	''' A Box contains dimensional data for crops and predictions
	
	'''
	def __init__(self, top_left: tuple[int]=None, bottom_right: tuple[int]=None):
		self.top_left = top_left
		self.bottom_right = bottom_right

	def get_center(self) -> tuple:
		x = np.mean([self.top_left[0], self.bottom_right[0]])
		y = np.mean([self.top_left[1], self.bottom_right[1]])

		return ((abs(x), abs(y)))

	def get_points(self) -> list[int]:
		return [self.top_left[0], self.top_left[1], self.bottom_right[0], self.bottom_right[1]]

	def calc_iou(self, box_2) -> float:
		# Slightly modified from https://machinelearningspace.com/intersection-over-union-iou-a-comprehensive-guide/
		#Extract bounding boxes coordinates
		x0_A, y0_A, x1_A, y1_A = self.get_points()
		x0_B, y0_B, x1_B, y1_B = box_2.get_points()
		
		# Get the coordinates of the intersection rectangle
		x0_I = max(x0_A, x0_B)
		y0_I = max(y0_A, y0_B)
		x1_I = min(x1_A, x1_B)
		y1_I = min(y1_A, y1_B)
		#Calculate width and height of the intersection area.
		width_I = x1_I - x0_I 
		height_I = y1_I - y0_I

		# Handle the negative value width or height of the intersection area
		width_I = 0 if width_I < 0 else width_I
		height_I = 0 if height_I < 0 else height_I
		# Calculate the intersection area:
		intersection = width_I * height_I
		# Calculate the union area:
		width_A, height_A = x1_A - x0_A, y1_A - y0_A
		width_B, height_B = x1_B - x0_B, y1_B - y0_B
		union = (width_A * height_A) + (width_B * height_B) - intersection
		# Calculate the IoU:
		return intersection/union
	
	def serialize(self) -> dict:
		return {
			'top_left': list(self.top_left),
			'bottom_right': list(self.bottom_right),
		}

@dataclass
class Image(CgOBJ):
	def __init__(self, image_id: int, herd_unit_id: int, survey_id: int, name: str,
				in_training: bool, crops_generated: int, reviewed_by_user_id: int, opened_by_user_id: int,
				created: datetime, modified: datetime, image_length_px: int, image_width_px: int,
				uuid: UUID):
		self.image_id = image_id
		self.herd_unit_id = herd_unit_id
		self.survey_id = survey_id
		self.name = name
		self.in_training = in_training
		self.crops_generated = crops_generated
		self.reviewed_by_user_id = reviewed_by_user_id
		self.opened_by_user_id = opened_by_user_id
		self.created = created
		self.modified = modified
		self.image_length_px = image_length_px
		self.image_width_px = image_width_px
		self.uuid = uuid
		self.image = None

	def set_image(self, image_data: np.ndarray):
		if isinstance(image_data, bytes):
			try:
				pil_image = PillowImage.open(io.BytesIO(image_data))
				pil_image = pil_image.convert('RGB')
				self.image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
			except Exception as e:
				print(f"Error converting bytes to image: {e}")
				self.image = None
		elif isinstance(image_data, np.ndarray):
			self.image = image_data
		else:
			print(f"Unsupported type: {type(image_data)}")
			self.image = None

	def get_image(self) -> np.ndarray:
		if self.image is not None:
			return self.image
		else:
			self.image = cv2.imread(os.path.join(f'{self.local_path}', f'{self.name}.JPG'))
			return self.image

	def delete_image(self):
		del self.image

	def serve(self, img_format: str):
		_, self.img_encoded = cv2.imencode(img_format, self.get_image())
		return self.img_encoded.tobytes()
		
	def serialize(self) -> dict:
		return {
			'name': self.name,
			'in_training': self.in_training,
			'crops_generated': self.crops_generated,
			'created': self.created,
			'modified': self.modified,
			'image_length_px': self.image_length_px,
			'image_width_px': self.image_width_px,
			'uuid': self.uuid
		}

class Prediction(CgOBJ):
	def __init__(self, pred_id: int, image_id: int, model_id: int, score: float, box_tx: int, box_ty: int,
				 box_bx: int, box_by: int, created: datetime | None, modified: datetime | None, uuid: UUID):
		self.pred_id = pred_id
		self.image_id = image_id
		self.model_id = model_id
		self.score = score
		self.dimensions = Box((box_tx, box_ty), (box_bx, box_by))
		self.created = created 
		self.modified = modified
		self.uuid = uuid
	
	def serialize(self) -> dict:
		return {
			'id': self.id,
			'model': self.model.serialize(),
			'dimensions': self.dimensions.serialize(),
			'score': self.score,
			'label': self.label,
		}

class Crop(Image):
	def __init__(self, db_id: int=None, image_id: int=None, name: str=None, dimensions: Box=None):
		super().__init__(db_id, name)
		self.image_id = image_id
		self.crop_dimensions = dimensions

	def calc_iou(self, box):
		return self.crop_dimensions.calc_iou(box)
	
	def serialize(self) -> dict:
		return {
			'id': self.id,
			'image_id': self.image_id,
			'name': self.name,
			'dimensions': self.crop_dimensions.serialize(),
			'url' : self.url,
		}
	
class PredictionCrop(Crop):
	def __init__(self, pred_crop_id: int=None, image_id: int=None, name: str=None, score: float=None, label: int=None, dimensions: Box=None, 
				 url: str=None):
		self.pred_crop_id = pred_crop_id
		self.image_id = image_id
		self.name = name
		self.score = score
		self.label = label 
		self.dimensions = dimensions
		self.approved = False
	
	def serialize(self) -> dict:
		return {
			'id': self.pred_crop_id,
			'image_id': self.image_id,
			'name': self.name,
			'score': self.score,
			'label': self.label,
			'dimensions': self.dimensions.serialize(),
			'approved': self.approved,
		}
#---------------------------------------------------------------------------------------------------------------------------#

class CropgenJSONPRovider(DefaultJSONProvider):
	def default(self, obj):
		if isinstance(obj, CgOBJ):
			return obj.serialize()
		return super().default(obj)


#---------------------------------------------------------------------------------------------------------------------------#