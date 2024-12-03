import glob
import json
import os
import cv2
import matplotlib.pyplot as plt
import numpy as np
import database
import sys
import signal
import datetime
from sklearn.cluster import KMeans
from dotenv import load_dotenv
#---------------------------------------------------------------------------------------------------------------------------#
# TODO: Move this into main.py and modify dependent functions to take them as arguments
# Paths and other environment related things 
base = database.SQLite("testing.db")
base.connect()

# Assumes we have a local .env file that stores things like ROOT
load_dotenv()

images_folder = os.environ.get("IMAGE_FOLDER") 
research_project = os.environ.get("RESEARCH_PROJECT")
model_name = "10-25-2024-16-50-17"

root = os.environ.get("ROOT")

output_folder = os.path.join(root, "data")  # type: ignore
train_json_path = os.path.join(root, "annotations", research_project, "train.json")  # type: ignore

save_folder = os.environ.get("SAVE_FOLDER")
os.makedirs(save_folder, exist_ok=True) # type: ignore

current_date = datetime.date.today().strftime('%Y-%m-%d')

#---------------------------------------------------------------------------------------------------------------------------#
# Function Definitions
def load_image_files() -> list:
    """ Loads image file names into a List

    Returns a list of file names
    """
    image_files = sorted(glob.glob(os.path.join(images_folder, f"*.[jJ][pP][gG]"))) # type: ignore
    print(f"{len(image_files)} files found.")
    return image_files

def load_training_image_names() -> list:
    """ Loads training image names into a list
    
    Returns a list of filenames that were used to train the model 
    """
    prefix = len("high-altitude-pronghorn-survey-")
    suffix = len("_crop_xx")
    with open(train_json_path) as f:
        train_json = json.load(f)
    return list(os.path.splitext(image_info['file_name'])[0][prefix:-suffix] for image_info in train_json['images'])

def load_prediction(image_file: str) -> dict[str, str]:
    """ Load model predictions for a given image name

    Args:
        image_file: string file path to an image

    Returns a dictionary containing the predictions
    """
    image_name = os.path.splitext(os.path.basename(image_file))[0]
    # Get corresponding box file for image
    box_file = os.path.join(output_folder, f"{image_name}_boxes.npy")
    if not os.path.exists(box_file):
        print(f"{image_name} missing box file.")
        boxes = None
    else:
        boxes = np.load(box_file)
    # Get corresponding score file for image
    score_file = os.path.join(output_folder, f"{image_name}_scores.npy")
    if not os.path.exists(score_file):
        print(f"{image_name} missing score file.")
        scores = None
    else:
        scores = np.load(score_file)
    # Get corresponding object class file for image
    label_file = os.path.join(output_folder, f"{image_name}_labels.npy")
    if not os.path.exists(label_file):
        print(f"{image_name} missing labels file.")
        labels = None
    else:
        labels = np.load(label_file)
    
    image_info = {
        "image_name": image_name,
        "boxes": boxes,
        "scores": scores,
        "labels": labels
    }
    return image_info

def is_in_training_set(image_name, training_names):
    """ Check if image name is origin of one of the training images. 
    
    Args:
        image_name: name of target image with extension removed
        training_names: list of all image names in the training set
        
    Returns true if image_name is origin of one of the training images.
    """
    return image_name in training_names

def sort_by_class_confidence(predictions: list, pred_class: int, min_confidence: float) -> list[str]:
    """ Sort a list of predictions based on confidence scores for a given class (not really useful with database)
    
    Args:
        predictions: list of predictions (dictionary)
        pred_class: integer representing a desired class
        min_confidence: floating point value for the min score to show predictions
    
    Returns a list of predictions sorted by confidence 
    """
    count = 0
    for pred in predictions:
        pred["max_class_score"] = -1
        if len(pred['labels']) == 0:
            continue
        is_class = pred['labels'] == pred_class
        if not np.any(is_class):
            continue
        max_score = np.max(pred['scores'][is_class])
        pred['max_class_score'] = max_score
        if max_score > min_confidence:
            count += 1
    print(f"{count} images with pronghorn above min confidence score.")

    # Sort images based on max pronghorn score
    predictions = sorted(predictions, key=lambda x: x['max_class_score'], reverse=True)
    return predictions

def populate_initial_tables():
    """ Populate a SQL database with image names and predictions

        Returns None, populate tables in a database
    """
    base.create_tables()
    image_names = load_image_files()
    training_image_names = set(load_training_image_names())
    query = """
        INSERT INTO Models (ModelName)
        VALUES (?)
    """
    base.query(query, (model_name,))

    query = """
        SELECT 
    """

    for image_name in image_names:
        # add max score to image table, insert score based on prediction values
        prediction = load_prediction(image_name)
        check_image_name = os.path.splitext(os.path.basename(image_name))[0]
        in_training = 1 if (is_in_training_set(check_image_name, training_image_names)) else 0
        query = """
            INSERT INTO Images (Name, InTraining, Reviewed, CropsGen)
            VALUES (?, ?, ?, ?)
        """
        base.query(query, (prediction["image_name"], in_training, 0, 0))
        
        imageId = base.lastrowid()
        
        for box, score, label in zip(prediction['boxes'], prediction['scores'], prediction['labels']):
            
            query = """
                INSERT INTO Predictions (ImageId, BoxTx, BoxTy, BoxBx, BoxBy, Score, Label)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            base.query(query, (imageId, int(box[0]), int(box[1]), int(box[2]), int(box[3]), float(score), int(label)))
    base.commit()

def auto_crop(image: np.ndarray, prediction: dict, crop_size: int, num_clusters: int)-> dict[str, list]:
    """ Automatically create crops of a given size containing all images with approved annotations 
    
    Args:
        image: source image that predictions were made from
        points: List of coordinate points of the approximate center for each prediction associated with the image
        crop_size: dimension for crop (note only square crops are currently supported)
        num_clusters: number of centers for kmeans to determine clusters 
        
    Returns list of crops based on original image
    TODO: finish implementing boundary checks
    """
    points = []
    for box in prediction['boxes']:
        x = np.mean([box[0], box[2]])
        y = np.mean([box[1], box[3]])
        points.append((x, y))
    crops = []
    dimensions = []
    centers = []
    
    if len(points) == 0:
        return {
            "crops": [0],
            "dimensions": [0],
            "predictions": [0]
        }
    if len(points) == 1:
        centers.append(points[0])

    if num_clusters == 1:
        print("Attempting without clustering...")
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
            print("First attempt successful...")
    
    if num_clusters > 1:
        print("Now attempting with clustering...")
        points_array = np.array(points)
        kmeans = KMeans(n_clusters = num_clusters)
        if len(points) >= num_clusters:
            kmeans.fit(points_array)
        else:
            return {
                "crops": [0],
                "dimensions": [0],
                "predictions": [0]
            }
        centers = kmeans.cluster_centers_
    count = 0
    points_in_crop = np.zeros(len(points))

    for center in centers:
        x_start = max(0, int(center[0]) - crop_size // 2)
        y_start = max(0, int(center[1]) - crop_size // 2)
        x_end = min(image.shape[1], x_start + crop_size)
        y_end = min(image.shape[0], y_start + crop_size)
        
        if x_end == image.shape[1]:
            print(f"difference x_end = {(x_start + crop_size) - image.shape[1]}")
            x_start -= (x_start + crop_size) - image.shape[1]

        if y_end == image.shape[0]:
            print(f"difference y_end = {(y_start + crop_size) - image.shape[0]}")
            y_start -= (y_start + crop_size) - image.shape[0]
        
        crop = image[y_start:y_end, x_start:x_end].copy()
        new_boxes = []
        for box in prediction['boxes']:
            box[0] -= x_start
            box[1] -= y_start
            box[2] -= x_start
            box[3] -= y_start

            box[0] = max(0, box[0])
            box[1] = max(0, box[1])
            box[2] = min(crop_size, box[2])
            box[3] = min(crop_size, box[3])
            if box[0] < box[2] and box[1] < box[3]:
                new_boxes.append(box)
        
        prediction['boxes'] = new_boxes
        for p_index, point in enumerate(points):
            if ((point[0] >= x_start) and (point[0] <= x_end)) and ((point[1] >= y_start) and (point[1] <= y_end)):
                count += 1 
                points_in_crop[p_index] += 1

        crops.append(crop)
        dimensions.append([x_start, y_start, x_end, y_end])

    if np.all(points_in_crop >= 1):
        generated_crops = {
            "crops": crops, 
            "dimensions": dimensions,
            "predictions": prediction
        }
        return generated_crops

    elif num_clusters + 1 < len(points):
        return auto_crop(image, prediction, crop_size, num_clusters + 1)

    else:
        print("Could not generate any crops...")
        return {
            "crops": [],
            "dimensions": [],
            "predictions": []
        }

def get_pred_and_images(batch_size: int, desired_class: int, min_confidence: float) -> dict:
    predictions = {}
    query = """
        SELECT P.PredId, P.BoxTx, P.BoxTy, P.BoxBx, P.BoxBy, P.Score, P.Label, I.Name, I.InTraining
        FROM Predictions P
        JOIN Images I On P.ImageId = I.ImageId
        WHERE I.Imageid IN (
            SELECT ImageId
            FROM Images
            WHERE Reviewed = 0  
            LIMIT ?
        ) AND P.Label = ? AND P.Score > ?
        ORDER BY P.Score DESC
        """
    rows = base.query(query, (batch_size, desired_class, min_confidence))
    for row in rows:
        pred_id = row[0]
        box = [row[1], row[2], row[3], row[4]]
        score = row[5]
        label = row[6]
        image_name = row[7]
        in_training = row[8]
        if image_name not in predictions:
            predictions[image_name] = {
                "in_training": in_training,
                "pred_id": pred_id,
                "boxes": [],
                "scores": [],
                "labels": [],
            }
        predictions[image_name]["boxes"].append(box)
        predictions[image_name]["scores"].append(score)
        predictions[image_name]["labels"].append(label)
    return predictions

def prompt_user(crop_indices: list) -> bool:
    approved_preds = []
    while True: # Show number associated with crop indexes in plot
        
        user_input = input("Please enter the number associated with each crop that contains a pronghorn (ex: 1, 2, etc...), if none of them do enter 0: ").split(' ')
              
        for num in user_input:  
            if int(num) in set(crop_indices):
                approved_preds.append(num)
            elif int(num) == 0:
                break
        
        break
    return len(approved_preds) > 0
    

def show_predictions_matplot(image: np.ndarray, prediction: dict, dimensions: list, desired_class: int, min_confidence: float, draw_box: bool):
    crop_buffer = 100
    crops = []
    scores = []
    if len(prediction) == 1:
        return
    for (box, score, label) in zip(prediction['boxes'], prediction['scores'], prediction['labels']):
        if (score < min_confidence) or (label != desired_class):
            continue
        ymin = np.max([box[1] - crop_buffer, 0])
        ymax = np.min([box[3] + crop_buffer, image.shape[0]])
        xmin = np.max([box[0] - crop_buffer, 0])
        xmax = np.min([box[2] + crop_buffer, image.shape[1]])
        if xmax == image.shape[1]:
            print("Transforming Crop on X")
            #xmin -= (xmin + crop_buffer) - image.shape[1]

        if ymax == image.shape[0]:
            print("Transforming crop on Y")
            #ymin -= (ymin + crop_buffer) - image.shape[0]

        crops.append(image[ymin:ymax, xmin:xmax].copy())
        scores.append(score)
    
    if len(crops) > 0:
        fig, axs = plt.subplots(1, len(crops))
        if len(crops) == 1:
            axs = [axs] 

        crop_indices = []
        for crop_num, (ax, crop, score) in enumerate(zip(axs, crops, scores)):
            crop_indices.append(crop_num + 1)
            ax.imshow(crop)
            ax.set_title(f"Crop Number: {crop_num + 1}")
            ax.set_axis_off()

        plt.show(block=False)
        final_crop = prompt_user(crop_indices)
        plt.close()
        if final_crop:
            query = """
                INSERT INTO Crops (PredId, InLabelBox, CropTx, CropTy, CropBx, CropBy, Created) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            base.query(query, (prediction['pred_id'], 0, dimensions[0][0], dimensions[0][1], dimensions[0][2], dimensions[0][3], current_date))
            plt.figure()
            plt.imshow(image)
            plt.title("testing crop")
            plt.show()
        else:
            print("no preds in crop")

def approve_annotations(predictions: dict, desired_class: int, crop_size: int, min_confidence: float, draw_box: bool, image_backend: str):
    """ Present the user with cropped images and their predictions for validation 

    """
    for image_name, pred in predictions.items():
        image_path = os.path.join(f"{images_folder}", f"{image_name}.JPG")
        image = plt.imread(image_path).copy()
        image_crops = auto_crop(image, pred, crop_size, 1)
        if len(image_crops['crops']) == 0:
            continue
        for crop in image_crops["crops"]:
            if image_backend in image_backends:
                image_backends[image_backend](crop, image_crops["predictions"], image_crops["dimensions"], desired_class, min_confidence, draw_box) #type: ignore
            else:
                raise Exception("Image backend not supported (Did you write an integration? Is it in the backends dict?)")
            
        query = """
                UPDATE Images
                SET Reviewed = ?
                WHERE Name = ?
            """
        base.query(query, (1, f"{image_name}"))
        base.commit()   
                
def interrupt_handler(signum, frame):
    usr_input = input(f"Interrupt signal: {signum} in {frame} recieved | IMPORTANT DON'T SAVE IF THERE WAS A PROBLEM | Save work? (Y or N): ")
    if usr_input in set(["y", "Y", "yes", "Yes", "s", "S", "Save", "save"]):
        try:
            base.commit()
            base.close()
        except Exception as e:
            print(f"Exception {e} encountered")
            sys.exit(1) # exit with error
        else:
            sys.exit(0)
    else:    
        base.rollback()
        base.close()
        sys.exit(0) # exit gracefully

def setup_interrupt_handler():
    """ Gracefully handle ^C interrupts regarding the database
    
    """
    signal.signal(signal.SIGINT, interrupt_handler)
#---------------------------------------------------------------------------------------------------------------------------#
# Dictionary of function calls to determine which version of a function to use. 
image_backends = {
    "matplot": show_predictions_matplot,
}
