import glob
import json
import os
from dotenv import load_dotenv
import cv2
from matplotlib import image
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

images_folder = "/mnt/nfsshare/WGFD LT 2/Pronghorn Vertical Imagery/2024/PR527/"
research_project = "pronghorn-survey"
model_name = "10-25-2024-16-50-17"

root = os.environ.get("ROOT")

output_folder = os.path.join(root, "data")  # type: ignore
train_json_path = os.path.join(root, "annotations", research_project, "train.json")  # type: ignore

save_folder = "/home/mlance/School/UWYO/Fall_Semester_2024/ProngHornCNN/pronghorn-census/AnnotationSoftware/annotation_crops/"
os.makedirs(save_folder, exist_ok=True)

#---------------------------------------------------------------------------------------------------------------------------#

min_score = .7
draw_box = True
crop_size = 2100
pronghorn_class = 2

#---------------------------------------------------------------------------------------------------------------------------#

def load_image_files() -> list:
    image_files = sorted(glob.glob(os.path.join(images_folder, f"*.[jJ][pP][gG]")))
    print(f"{len(image_files)} files found.")
    return image_files

def load_training_image_names() -> list:
    prefix = len("high-altitude-pronghorn-survey-")
    suffix = len("_crop_xx")
    with open(train_json_path) as f:
        train_json = json.load(f)
    return list(os.path.splitext(image_info['file_name'])[0][prefix:-suffix] for image_info in train_json['images'])

def load_prediction(image_file: str) -> dict:
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

def populate_initial_tables():
    base.create_tables()
    image_names = load_image_files()
    training_image_names = set(load_training_image_names())
    for image_name in image_names:
        prediction = load_prediction(image_name)
        check_image_name = os.path.splitext(os.path.basename(image_name))[0]
        in_training = 1 if (is_in_training_set(check_image_name, training_image_names)) else 0
        base.insert(
            table = "Images",
            columns = ["Name", "InTraining", "Reviewed", "CropsGen", "Status"],
            values = (prediction["image_name"], in_training, 0, 0, 0)
        )
        imageId = base._lastrowid()
        
        for box, score, label in zip(prediction['boxes'], prediction['scores'], prediction['labels']):
            
            base.insert(
                table = "Predictions",
                columns = ["ImageId, BoxTX, BoxTy, BoxBx, BoxBy, Score, Label"],
                values = (imageId, int(box[0]), int(box[1]), int(box[2]), int(
box[3]), float(score), int(label))
            )

    base.commit()

def sort_by_class(predictions: list, pred_class: int) -> list:
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
        if max_score > .7:
            count += 1
    print(f"{count} images with pronghorn above min confidence score.")

    # Sort images based on max pronghorn score
    predictions = sorted(predictions, key=lambda x: x['max_class_score'], reverse=True)
    return predictions

def auto_crop(image: np.ndarray, points: list, crop_size: int, num_clusters: int) -> list:
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
    centers = []
    
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
        kmeans.fit(points_array)
        centers = kmeans.cluster_centers_
    count = 0
    points_in_crop = np.zeros(len(points))
    for center in centers:
        # fix funky crops by moving x and y value for center by difference of shape and crop (padding)
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
    if np.all(points_in_crop >= 1):
        return crops
    elif num_clusters < len(points):
        return auto_crop(image, points, crop_size, num_clusters + 1)
    else:
        print("Could not generate any crops...")
        return crops

def crop_reviewed_predictions(approved_predictions: list, training_image_names: list):
    """ In desperate need of rewrite
    
    """
    # Crop approved predictions
    for pred_num, pred in enumerate(approved_predictions[800:900]):
        image_name = os.path.splitext(os.path.basename(pred['image_file']))[0]
        in_training = is_in_training_set(image_name, training_image_names)
        if in_training:
            print(f"{image_name} is in the training set.")
    
        image = plt.imread(pred['image_file']).copy()
    
        scores = []
        points = [] 
        for box, score, label in zip(pred['boxes'], pred['scores'], pred['labels']):
            if (score < min_score) or (label != pronghorn_class):
                print("skipping")
                continue
            x = np.mean([box[0], box[2]])
            y = np.mean([box[1], box[3]])
            points.append((x, y))       

            cv2.rectangle(image, (box[0], box[1]), (box[2], box[3]), (255, 0, 0), 3)

        if points:
            print(f"{image_name} has {len(points)} points!")
            crops = auto_crop(image, points, 2100, 1)
        
        if len(crops) == 0:
            if not crops:
                print(f"no valid crops for {image_name}")
                continue
            else:
                for count, crop in enumerate(crops):
                    if (crop.shape[0] == 2100) or (crop.shape[1] == 2100): 
                        plt.figure()
                        plt.imshow(crop)
                        plt.title(f"{image_name}_crop_{count}")
                        plt.show()

def approve_annotations(batch_size: int, crop_buffer:int, draw_box: bool):
    # load image names and predictions from database in batches of batch_size
    print(f"The system will now show {batch_size} images and then {crop_buffer}x{crop_buffer} crops containing each prediction made by the model. When shown the crops, press 1 if its a prong horn or 2 if it is not.")
    query = """
        SELECT P.BoxTx, P.BoxTy, P.BoxBx, P.BoxBy, P.Score, P.Label, I.Name, I.InTraining
        FROM Predictions P
        JOIN Images I On P.ImageId = I.ImageId
        WHERE I.Imageid IN (
            SELECT ImageId
            FROM Images
            WHERE Reviewed = 0  
            LIMIT ?
        ) AND P.Label = ? AND P.Score > 0.7
        """
    rows = base.query(query, (batch_size, pronghorn_class))
    predictions = {}

    for row in rows:
        box = [row[0], row[1], row[2], row[3]]
        score = row[4]
        label = row[5]
        image_name = row[6]
        in_training = row[7]
        if image_name not in predictions:
            predictions[image_name] = {
                "in_training": in_training,
                "boxes": [],
                "scores": [],
                "labels": [],
            }
        predictions[image_name]["boxes"].append(box)
        predictions[image_name]["scores"].append(score)
        predictions[image_name]["labels"].append(label)

    for pred_num, (image_name, pred) in enumerate(predictions.items()):
        image_path = os.path.join(f"{images_folder}", f"{image_name}.JPG")

        image = plt.imread(image_path).copy()

        crops = []
        scores = []
        
        
        for box, score, label in zip(pred['boxes'], pred['scores'], pred['labels']):
            approved_boxes = []
            if (score < min_score) or (label != pronghorn_class):
                continue
            if draw_box:
                cv2.rectangle(image, (box[0], box[1]), (box[2], box[3]), (255, 0, 0), 2)
            ymin = np.max([box[1] - crop_buffer, 0])
            ymax = np.min([box[3] + crop_buffer, image.shape[0]])
            xmin = np.max([box[0] - crop_buffer, 0])
            xmax = np.min([box[2] + crop_buffer, image.shape[1]])
            crops.append(image[ymin:ymax, xmin:xmax].copy())
            scores.append(score)
        
            if len(crops) == 0:
                continue
            plt.figure()
            plt.imshow(image)
            plt.title(f"{image_name}")
            plt.show(block=False)

            for crop, score in zip(crops, scores):
                crop_fig = plt.figure()
                plt.imshow(crop)
                plt.title(f"Score: {score:.2f}")
                plt.show(block=False)
                usr_input = int(input("if this is a pronghorn press 1, else press 2: "))
                if usr_input == 1:
                    print("Prediction Approved, Generating Crop!")
                    approved_boxes.append(box)
                elif usr_input == 2:
                    print("Prediction Denied, Showing next Crop!")
                plt.close(crop_fig) 
            
            plt.close()
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

                for crop in annotated_crops:
                    plt.figure()
                    plt.imshow(crop)
                    plt.title("Generated Crop!")
                    plt.show()
 #---------------------------------------------------------------------------------------------------------------------------#
if __name__ == "__main__":
    #populate_initial_tables()
    approve_annotations(50, 100, True) 
    base.close()
