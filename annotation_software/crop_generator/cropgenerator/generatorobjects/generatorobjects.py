# Class definition for objects used in the crop_generator module
# Author: Michael B. Lance
# Created: April 4, 2025
# Updated: April 9, 2025
#---------------------------------------------------------------------------------------------------------------------------#
import numpy as np
import cv2
import os
from flask.json.provider import DefaultJSONProvider
from abc import ABC, abstractmethod
from typing import Any
#---------------------------------------------------------------------------------------------------------------------------#

class CgOBJ(ABC):
    @abstractmethod
    def serialize(self) -> dict:
        pass
    
#---------------------------------------------------------------------------------------------------------------------------#

class Box(CgOBJ):
    ''' A Box contains dimensional data for crops and predictions
    
    '''
    def __init__(self, top_left: tuple[int]=None, bottom_right: tuple[int]=None):
        self.top_left = top_left
        self.bottom_right = bottom_right

    def get_center(self):
        x = np.mean([self.top_left[0], self.bottom_right[0]])
        y = np.mean([self.top_left[1], self.bottom_right[1]])

        return ((abs(x), abs(y)))

    def get_points(self):
        return [self.top_left[0], self.top_left[1], self.bottom_right[0], self.bottom_right[1]]

    def calc_iou(self, box_2):
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

#---------------------------------------------------------------------------------------------------------------------------#

class Image(CgOBJ):
    def __init__(self, db_id: int=None, name: str=None, herd_unit_id: int=None, in_training:bool=False, folder_path: str=None):
        self.id = db_id
        self.name = name
        self.herd_unit_id = herd_unit_id
        self.in_training = in_training
        self.folder_path = folder_path
        self.image = None

    def set_image(self, image: np.ndarray):
        self.image = image

    def get_image(self) -> np.ndarray:
        if self.image is not None:
            return self.image
        else:
            self.image = cv2.imread(os.path.join(f'{self.folder_path}', f'{self.name}.JPG'), cv2.IMREAD_COLOR_RGB)
            return self.image
        
    def serialize(self) -> dict:
        return {
            'image_id': self.id,
            'image_name': self.name,
            'herd_unit_id': self.herd_unit_id,
            'folder_path' : self.folder_path,
        }

#---------------------------------------------------------------------------------------------------------------------------#

class Prediction(CgOBJ):
    def __init__(self, db_id: int, dimensions: Box=None, score: float=None, label: int=None, model_id: int=None):
        self.id = db_id
        self.model_id = model_id
        self.dimensions = dimensions
        self.score = score
        self.label = label
    
    def serialize(self) -> dict:
        return {
            'pred_id': self.id,
            'model_id': self.model_id,
            'dimensions': self.dimensions.serialize(),
            'score': self.score,
            'label': self.label,
            
        }

#---------------------------------------------------------------------------------------------------------------------------#

class Crop(Image):
    def __init__(self, db_id: int=None, image_id: int=None, name: str=None, dimensions: Box=None):
        super().__init__(db_id, name)
        self.image_id = image_id
        self.crop_dimensions = dimensions

    def calc_iou(self, box):
        return self.dimensions.calc_iou(box)
    
    def serialize(self) -> dict:
        return {
            'crop_id': self.id,
            'image_id': self.image_id,
            'crop_name': self.name,
            'dimensions': self.dimensions.serialize(),
            'herd_unit_id': self.herd_unit_id,
            'folder_path' : self.folder_path,
        }
    
#---------------------------------------------------------------------------------------------------------------------------#

class CropgenJSONPRovider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, CgOBJ):
            return obj.serialize()
        return super().default(obj)


#---------------------------------------------------------------------------------------------------------------------------#