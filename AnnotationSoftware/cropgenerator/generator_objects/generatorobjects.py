# Class definition for objects used in the crop_generator module
# Author: Michael B. Lance
# Created: April 4, 2025
# Updated: April 4, 2025

#---------------------------------------------------------------------------------------------------------------------------#
import numpy as np
import cv2
import os

#---------------------------------------------------------------------------------------------------------------------------#
class Box:
    """ A Box contains dimensional data for crops and predictions
    
    """
    def __init__(self, tl_x: int=None, tl_y: int=None, br_x: int=None, br_y: int=None):
        self.tl_x = tl_x
        self.tl_y = tl_y
        self.br_x = br_x
        self.br_y = br_y

    def get_center(self):
        x = np.mean(self.tl_x, self.br_x)
        y = np.mean(self.tl_y, self.br_y)

        return (x, y)

    def get_points(self):
        return [self.tl_x, self.tl_y, self.br_x, self.br_y]

    def calc_iou(self, box_2):
        # Slightly modified from https://machinelearningspace.com/intersection-over-union-iou-a-comprehensive-guide/
        #Extract bounding boxes coordinates
        x0_A, y0_A, x1_A, y1_A = self.get_points()
        x0_B, y0_B, x1_B, y1_B = box_2.get_pointS()
        
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

#---------------------------------------------------------------------------------------------------------------------------#

class Image:
    def __init__(self, imageId: int=None, name: str=None, herdUnitId: int=None, inTraining:bool=False, folder_path: str=None):
        self.id = imageId
        self.name = name
        self.herdUnitId = herdUnitId
        self.inTraining = inTraining
        self.folder_path = folder_path
        self.image = None

    def set_image(self, image: np.ndarray):
        self.image = image

    def get_image(self) -> np.ndarray:
        if self.image is not None:
            return self.image
        else:
            self.image = cv2.imread(os.path.join(f"{self.folder_path}", f"{self.name}.JPG"))
            return self.image

#---------------------------------------------------------------------------------------------------------------------------#

class Prediction:
    def __init__(self, pred_id: int, dimensions: Box=None, score: float=None, label: int=None, model_id: int=None):
        self.id = pred_id
        self.dimensions = dimensions
        self.score = score
        self.label = label
        self.model_id = model_id
    
#---------------------------------------------------------------------------------------------------------------------------#

class Crop:
    def __init__(self, crop_id: int=None, image_id: int=None, model_id: int=None, name: str=None, dimensions: Box=None):
        self.id = crop_id 
        self.image_id = image_id
        self.name = name
        self.dimensions = dimensions
        self.image = None
        self.folder_path = None

    def set_image(self, image: np.ndarray):
        self.image = image

    def get_image(self) -> np.ndarray:
        if self.image is not None:
            return self.image
        else:
            self.image = cv2.imread(os.path.join(f"{self.folder_path}", f"{self.name}.JPG"))
            return self.image

    def calc_iou(self, box):
        return self.dimensions.calc_iou(box)