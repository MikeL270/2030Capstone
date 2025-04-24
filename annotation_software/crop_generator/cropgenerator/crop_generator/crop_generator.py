# Generate high quality crops of training data with model assisted labeling and Kmeans clustering
# Authors: Ben Koger, Michael B. Lance
# Created: November 11, 2024
# Updated: April 23, 2025

#---------------------------------------------------------------------------------------------------------------------------#

import glob
import json
import os
import cv2
import matplotlib.pyplot as plt
import numpy as np
from ..database import database
from ..imagebackends import imagebackends
from ..generatorobjects.generatorobjects import Box, Prediction, Image, Crop, CropgenJSONPRovider
from sklearn.cluster import KMeans

#---------------------------------------------------------------------------------------------------------------------------#

def load_training_image_names(train_json_path: str, prefix: str, suffix:str, crop_suffix: bool = False) -> set:
    ''' Loads training image names into a list
    
    Returns a set of filenames that were used to train the model 
    ''' 
    with open(train_json_path) as f:
        train_json = json.load(f)
    if crop_suffix:
        return set(os.path.splitext(image_info['file_name'])[0][prefix:] for image_info in train_json['images'])
    else:
        return set(os.path.splitext(image_info['file_name'])[0][prefix:-suffix] for image_info in train_json['images'])

#---------------------------------------------------------------------------------------------------------------------------#

def load_prediction(image_file: str, model_id: int) -> Prediction:
    ''' Load model predictions for a given image name`

    Args:
        image_file: string file path to an image

    Returns a dictionary containing the predictions
    '''
    # Get corresponding box file for image
    box_file = os.path.join(predictions_folder, f'{image_name}_boxes.npy') #type: ignore
    if not os.path.exists(box_file):
        raise Exception(f'{image_file} missing box file.')
    else:
        boxes = np.load(box_file)
    # Get corresponding score file for image
    score_file = os.path.join(predictions_folder, f'{image_name}_scores.npy') #type: ignore
    if not os.path.exists(score_file):
        raise Exception(f'{image_file} missing score file.')
    else:
        scores = np.load(score_file)
    # Get corresponding object class file for image
    label_file = os.path.join(predictions_folder, f'{image_name}_labels.npy') #type: ignore
    if not os.path.exists(label_file):
        raise Exception(f'{image_file} missing labels file.')
    else:
        labels = np.load(label_file)
    # TODO modify to comply with new memory model

    predictions = []


    for box, score, label in zip(boxes, scores, labels):
        pred = Prediction(
            model_id=model_id,
            dimensions=box,
            score=score,
            label=label,
        )
        predictions.append(pred)
    return predictions

#---------------------------------------------------------------------------------------------------------------------------#

def load_from_npy(images_folder: str, herd_unit_id: int, model_id: int) -> dict[Image, Prediction]:
    ''' Create Image and Predictions objects from .npy files

    Returns a dictionary contianing images and predictions
    '''
    training = load_training_image_names()
    image_files = sorted(glob.glob(os.path.join(images_folder, f'*.[jJ][pP][gG]'))) # type: ignore
    print(f'{len(image_files)} files found.')
    images = {}
    for image_file in image_files:
        image_name = os.path.splitext(os.path.basename(image_file))[0]
        #TODO: Derive herd unit id with regex
        image = Image (
            name = image_name,
            herd_unit_id = herd_unit_id,
            in_training= True if image_name in training else False,
            folder_path= images_folder,
        )
        images[image] = load_prediction(image_file, model_id)
    return images

#---------------------------------------------------------------------------------------------------------------------------#

def sort_by_class_confidence(predictions: list, pred_class: int, min_confidence: float) -> list[str]:
    ''' Sort a list of predictions based on confidence scores for a given class (not really useful with database)
    
    Args:
        predictions: list of predictions (dictionary)
        pred_class: integer representing a desired class
        min_confidence: floating point value for the min score to show predictions
    
    Returns a list of predictions sorted by confidence 
    '''
    count = 0
    for pred in predictions:
        pred['max_class_score'] = -1
        if len(pred['labels']) == 0:
            continue
        is_class = pred['labels'] == pred_class
        if not np.any(is_class):
            continue
        max_score = np.max(pred['scores'][is_class])
        pred['max_class_score'] = max_score
        if max_score > min_confidence:
            count += 1
    print(f'{count} images with pronghorn above min confidence score.')

    # Sort images based on max pronghorn score
    predictions = sorted(predictions, key=lambda x: x['max_class_score'], reverse=True)
    return predictions

#---------------------------------------------------------------------------------------------------------------------------#

def auto_crop(image: Image, predictions: list[Prediction], num_clusters: int=1, crop_size: int=2100) -> dict[Crop, list[Prediction]]:
    ''' Automatically create crops of a given size containing all images with approved annotations 
    
    Args:
        image: source image that predictions were made from
        points: List of coordinate points of the approximate center for each prediction associated with the image
        crop_size: dimension for crop (note only square crops are currently supported)
        num_clusters: number of centers for kmeans to determine clusters 

    Returns list of crops based on original image
    TODO: finish implementing boundary checks
    '''
    points = []
    centers = []
    crops = {} # Structure to be returned
    img = image.get_image()

    # Get centers for all predictions 
    for pred in predictions:
        points.append(pred.dimensions.get_center())

    if len(points) == 0:
        print('no points')
        return crops
    elif len(points) == 1:
        centers.append(points[0])

    elif num_clusters == 1:
        x_min = x_max = int(points[0][0])
        y_min = y_max = int(points[0][1])
        for point in points:
            x_min = min(x_min, int(point[0]))
            x_max = max(x_max, int(point[0]))
            y_min = min(y_min, int(point[1]))
            y_max = max(y_max, int(point[1]))

        if (x_max - x_min <= 2100 ) and (y_max - y_min <= 2100):
            x_center = (x_min + x_max) // 2
            y_center = (y_min + y_max) // 2 
            centers.append([x_center, y_center])
    
    elif num_clusters > 1:
        points_array = np.array(points)
        kmeans = KMeans(n_clusters = num_clusters)
        if len(points) >= num_clusters:
            kmeans.fit(points_array)
        else:
            #TODO Raise an error
            return crops 

        centers = kmeans.cluster_centers_

    points_in_crop = np.zeros(len(points))
  
    for crop_num, center in enumerate(centers):
        crop = Crop(
            name = f'{image.name}_crop_{crop_num}',
            image_id = image.id,
        )
        crops[crop_num] = {}
        
        x_start = max(0, int(center[0]) - crop_size // 2)
        y_start = max(0, int(center[1]) - crop_size // 2)
        x_end = min(img.shape[1], x_start + crop_size)
        y_end = min(img.shape[0], y_start + crop_size)
        if x_end == img.shape[1]:
            x_start -= (x_start + crop_size) - img.shape[1]

        if y_end == img.shape[0]:
            y_start -= (y_start + crop_size) - img.shape[0]
        
        crop.set_image(img[y_start:y_end, x_start:x_end].copy())
        crops[crop_num]['crop'] = crop
        crops[crop_num]['predictions'] = []
        for p_index, pred in enumerate(predictions):
            box = pred.dimensions.get_points()
            if ((box[0] >= x_start) and (box[2] <= x_end)) and ((box[1] >= y_start) and (box[3] <= y_end)): 
                points_in_crop[p_index] += 1
                crops[crop_num]['predictions'].append(
                    Prediction(
                        db_id = pred.id,
                        dimensions = Box(
                            top_left = (box[0] - x_start, box[1] - y_start),
                            bottom_right = (box[2] - x_start, box[3] - y_start)
                        ),
                        score = pred.score,
                        label = pred.label, 
                        model_id = pred.model_id
                    )  
                )  
        crop.dimensions = Box(
            top_left = (x_start, y_start), 
            bottom_right = (x_end, y_end)
            )

    if np.all(points_in_crop >= 1):
        return crops

    elif num_clusters + 1 <= len(points):
        return auto_crop(image=image, predictions=predictions, crop_size=crop_size, num_clusters=num_clusters +1)

    else:
        print('Could not generate any crops...')
        plt.figure()
        plt.imshow(image)
        plt.title('Failed to crop')
        plt.show()
        return crops 
    
#---------------------------------------------------------------------------------------------------------------------------#

def generate_crops(image: Image, predictions: list[Prediction], crop_size: int, model_id: int,
                   base: database.Database) -> dict[Crop, list[Prediction]]:
    ''' Present the user with cropped images and their predictions for validation '''

    crops = auto_crop(image=image, predictions=predictions, crop_size=crop_size)  
    query = '''
        SELECT *
        FROM Crops
        WHERE ModelID != ? AND ImageId = ?
    '''
    #TODO: Move IOU check to own function that takes both 
    """
    existing_crops = base.query(query, (model_id, image.id))

    # Perform Iou check to prevent duplicate data
    for crop in crops.keys():
        for ecrop in existing_crops:
            if crop.calc_iou(Box(ecrop[5], ecrop[6], ecrop[7], ecrop[8])) >= 0.9:
                print('duplicate crop')
                crops.pop(crop, None)
    """
    return crops

#---------------------------------------------------------------------------------------------------------------------------#

def save_crop(crop: Crop, save_folder: str):
        cv2.imwrite(f'{save_folder}/{crop.name}.jpg', cv2.cvtColor(crop.get_image(), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 100])

#---------------------------------------------------------------------------------------------------------------------------#
