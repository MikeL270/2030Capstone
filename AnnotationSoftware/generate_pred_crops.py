import glob
import json
import os
import sys
from dotenv import load_dotenv
import cv2
import matplotlib.pyplot as plt
import numpy as np
from sklearn.cluster import KMeans
import database
#---------------------------------------------------------------------------------------------------------------------------#
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

#---------------------------------------------------------------------------------------------------------------------------#

draw_box = True
crop_size = 2100
pronghorn_class = 2

#---------------------------------------------------------------------------------------------------------------------------#

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

def load_prediction(image_file: str) -> dict:
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

def sort_by_class_confidence(predictions: list, pred_class: int, min_confidence: float) -> list:
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
    for image_name in image_names:
        prediction = load_prediction(image_name)
        check_image_name = os.path.splitext(os.path.basename(image_name))[0]
        in_training = 1 if (is_in_training_set(check_image_name, training_image_names)) else 0
        query = """
            INSERT INTO Images (Name, InTraining, Reviewed, CropsGen)
            VALUES (?, ?, ?, ?)
        """
        base.query(query, (prediction["image_name"], in_training, 0, 0))
        
        imageId = base._lastrowid()
        
        for box, score, label in zip(prediction['boxes'], prediction['scores'], prediction['labels']):
            
            query = """
                INSERT INTO Predictions (ImageId, BoxTx, BoxTy, BoxBx, BoxBy, Score, Label)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            base.query(query, (imageId, int(box[0]), int(box[1]), int(box[2]), int(box[3]), float(score), int(label)))

    base.commit()

def auto_crop(image: np.ndarray, points: list, crop_size: int, num_clusters: int) -> dict:
    """ Automatically create crops of a given size containing all images with approved annotations 
    
    Args:
        image: source image that predictions were made from
        points: List of coordinate points of the approximate center for each prediction associated with the image
        crop_size: dimension for crop (note only square crops are currently supported)
        num_clusters: number of centers for kmeans to determine clusters 
        
    Returns list of crops based on original image
    TODO: finish implementing boundary checks
    """
    crops = []
    dimensions = []
    centers = []
    print(len(points))
    if len(points) == 1:
        centers.append(points[0])

    
    elif num_clusters == 1:
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
        kmeans.fit(points_array)
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
        
        for p_index, point in enumerate(points):
            if ((point[0] >= x_start) and (point[0] <= x_end)) and ((point[1] >= y_start) and (point[1] <= y_end)):
                count += 1 
                points_in_crop[p_index] += 1

        crops.append(crop)
        dimensions.append([x_start, y_start, x_end, y_end])
    if np.all(points_in_crop >= 1):
        generated_crops = {
            "crops": crops, 
            "dimensions": dimensions
        }
        return generated_crops
    elif num_clusters < len(points):
        return auto_crop(image, points, crop_size, num_clusters + 1)
    else:
        print("Could not generate any crops...")
        return {}

def approve_annotations(batch_size: int, crop_buffer:int, draw_box: bool, min_confidence: float):
    """ Present the user with images and their predictions for validation 

    """
    # load image names and predictions from database in batches of batch_size
    print(f"The system will now show {batch_size} images and then {crop_buffer}x{crop_buffer} crops containing each prediction made by the model. When shown the crops, input whether or not the prediction is correct")
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
    rows = base.query(query, (batch_size, pronghorn_class, min_confidence))
    predictions = {}

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

    last_name = None

    for pred_num, (image_name, pred) in enumerate(predictions.items()):
        if image_name == last_name:
            print("seen before")
            continue
        last_name = image_name
        image_path = os.path.join(f"{images_folder}", f"{image_name}.JPG")
        image = plt.imread(image_path).copy()
        crops = []
        scores = []
        
        for box, score, label in zip(pred['boxes'], pred['scores'], pred['labels']):
            approved_boxes = []
            if (score < min_confidence) or (label != pronghorn_class):
                continue
            if draw_box:
                cv2.rectangle(image, (box[0], box[1]), (box[2], box[3]), (255, 0, 0), 2)

            ymin = np.max([box[1] - crop_buffer, 0])
            ymax = np.min([box[3] + crop_buffer, image.shape[0]])
            xmin = np.max([box[0] - crop_buffer, 0])
            xmax = np.min([box[2] + crop_buffer, image.shape[1]])
            crops.append(image[ymin:ymax, xmin:xmax].copy())
            scores.append(score)
            if draw_box:
                cv2.rectangle(image, (xmax, ymax), (xmin, ymin), (255, 0, 0), 6)
            if len(crops) == 0:
                print("No crops to show")
                continue
            orig_image = plt.figure()
            plt.imshow(image)
            plt.title(f"Name: {image_name}")
            plt.show(block=False)
            
            crops_to_show = len(crops)
            print(f"Showing {crops_to_show} crops for {image_name}")
            for crop_num, (crop, score) in enumerate(zip(crops, scores)):
                crop_fig = plt.figure()
                plt.imshow(crop)
                plt.title(f"Prediction Number {pred_num} | Crop number: {crop_num} | Score: {score:.2f}")
                plt.show(block=False)
                while True:
                    try:
                        usr_input = input("if this is a pronghorn press y, else press n (or q to quit): ") 
                    except:
                        print("Invalid input type, please only enter numbers")
                        continue
                    if usr_input in set(["q", "Q", "quit", "Quit", "QUIT"]):
                        print("saving database and closing")
                        base.commit()
                        base.close()
                        sys.exit()
    
                    if usr_input in set(["y", "Y", "yes", "Yes", "YES"]):
                        print("Prediction Approved, Adding to Approved Predictions")
                        approved_boxes.append(box)
                        plt.close(crop_fig)
                        break
                    elif usr_input in set(["N", "n", "No", "n", "NO"]):
                        print("Prediction Denied, Showing next Crop!")
                        plt.close(crop_fig)
                        break

            plt.close(orig_image)
            
            query = """
                UPDATE Images
                SET Reviewed = ?
                WHERE Name = ?
            """
            base.query(query, (1, f"{image_name}"))
            base.commit()
            if len(approved_boxes) >= 1:
                points = []
                for box in approved_boxes:
                    x = np.mean([box[0], box[2]])
                    y = np.mean([box[1], box[3]])
                    points.append((x, y))

                annotated_crops = auto_crop(image, points, 2100, 1)
                for crop, dimension in zip(annotated_crops["crops"], annotated_crops["dimensions"]):    
                    final_crop = plt.figure()
                    plt.imshow(crop)
                    plt.title("Generated Crop!")
                    plt.show(block = False)

                    while True:
                        try:
                            usr_input = input("Save crop? (y or n): ")
                        except:
                            print("Invalid Input")
                            continue
                        break
                    
                    if usr_input in set(["y", "Y", "yes", "Yes"]):
                        print("Approved")
                        query = """
                            INSERT INTO Crops (PredId, InLabelBox, CropTx, CropTy, CropBx, CropBy)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """
                        base.query(query, (pred["pred_id"], 0, dimension[0], dimension[1], dimension[2], dimension[3]))
                        base.commit()
                        plt.close(final_crop)
                    elif usr_input in set(["n", "N", "no", "No"]):
                        plt.close(final_crop)

                 #---------------------------------------------------------------------------------------------------------------------------#
if __name__ == "__main__":
    if "create_db" in sys.argv:
        populate_initial_tables()
    approve_annotations(100, 100, True, .7) 
    base.close()
