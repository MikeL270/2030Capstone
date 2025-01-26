# Generate high quality crops of training data with model assisted labeling and Kmeans clustering
# Authors: Ben Koger, Michael B. Lance
# Created: November 11, 2024
# Updated: January 25, 2025
#---------------------------------------------------------------------------------------------------------------------------#
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
import labelbox as lb
from labelbox.data.annotation_types import Label, ObjectAnnotation, Rectangle, Point
from uuid import uuid4
from multiprocessing import Pool, cpu_count
import json
#---------------------------------------------------------------------------------------------------------------------------#
load_dotenv()

db_config = {
    "database": os.environ.get("DB_NAME"),
    "user": os.environ.get("DB_USER"),              
    "password": os.environ.get("DB_PASS"),    
    "host": os.environ.get("DB_HOST"),           
    "port": "5432"              
}

db_file = os.environ.get("DB_NAME")

base = database.Postgres(db_config)
#base = database.SQLite("testing.db")
base.connect()

images_folder = os.environ.get("IMAGE_FOLDER") 
research_project = os.environ.get("RESEARCH_PROJECT")
model_name = "10-25-2024-16-50-17"

root = os.environ.get("ROOT")
output_folder = os.path.join(root, "data")  # type: ignore
train_json_path = os.path.join(root, "annotations", research_project, "train.json")  # type: ignore
current_date = datetime.date.today().strftime('%Y-%m-%d')
save_folder = f'{os.environ.get("SAVE_FOLDER")}'
os.makedirs(save_folder, exist_ok=True) # type: ignore

uploading = False 

#---------------------------------------------------------------------------------------------------------------------------#

def quit_app(value: int = 0):
    global uploading
    
    query = """
        UPDATE Images
        SET Open = 0
        WHERE Open = 1
    """
    base.query(query,())
    base.commit()

    if value > 0:
        sys.exit(value)
    if uploading:
        print("Waiting for upload to finish, program will exit once complete!")
        while uploading:
            pass
        base.commit()
        base.close()
        quit()
    else:
        base.commit()
        base.close()
        quit()

#---------------------------------------------------------------------------------------------------------------------------#

def interrupt_handler(signum, frame):
    usr_input = input(f"Interrupt signal: {signum} in {frame} recieved | IMPORTANT DON'T SAVE IF THERE WAS A PROBLEM | Save work? (Y or N): ")
    if usr_input in set(["y", "Y", "yes", "Yes", "s", "S", "Save", "save"]):
        try:
            base.commit()
            base.close()
        except Exception as e:
            print(f"Exception {e} encountered")
            quit_app(1)
    else:    
        base.rollback()
        base.close()
        quit_app()

def load_image_files() -> list:
    """ Loads image file names into a List

    Returns a list of file names
    """
    image_files = sorted(glob.glob(os.path.join(images_folder, f"*.[jJ][pP][gG]"))) # type: ignore
    print(f"{len(image_files)} files found.")
    return image_files

#---------------------------------------------------------------------------------------------------------------------------#

def load_training_image_names() -> list:
    """ Loads training image names into a list
    
    Returns a list of filenames that were used to train the model 
    """
    prefix = len("high-altitude-pronghorn-survey-")
    suffix = len("_crop_xx")
    with open(train_json_path) as f:
        train_json = json.load(f)
    return list(os.path.splitext(image_info['file_name'])[0][prefix:-suffix] for image_info in train_json['images'])

#---------------------------------------------------------------------------------------------------------------------------#
def load_prediction(image_file: str) -> dict[str, str]:
    """ Load model predictions for a given image name

    Args:
        image_file: string file path to an image

    Returns a dictionary containing the predictions
    """
    image_name = os.path.splitext(os.path.basename(image_file))[0]
    # Get corresponding box file for imagemblance.twingate.com
    box_file = os.path.join(output_folder, f"{image_name}_boxes.npy") #type: ignore
    if not os.path.exists(box_file):
        print(f"{image_name} missing box file.")
        boxes = None
    else:
        boxes = np.load(box_file)
    # Get corresponding score file for image
    score_file = os.path.join(output_folder, f"{image_name}_scores.npy") #type: ignore
    if not os.path.exists(score_file):
        print(f"{image_name} missing score file.")
        scores = None
    else:
        scores = np.load(score_file)
    # Get corresponding object class file for image
    label_file = os.path.join(output_folder, f"{image_name}_labels.npy") #type: ignore
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

#---------------------------------------------------------------------------------------------------------------------------#

def is_in_training_set(image_name, training_names):
    """ Check if image name is origin of one of the training images. 
    
    Args:
        image_name: name of target image with extension removed
        training_names: list of all image names in the training set
        
    Returns true if image_name is origin of one of the training images.
    """
    return image_name in training_names

#---------------------------------------------------------------------------------------------------------------------------#

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

#---------------------------------------------------------------------------------------------------------------------------#

def concurrent_populate(image_names, start, end, modelId, training_image_names):  
    db_type = type(base)
    concurrent_base = db_type(db_config)

    concurrent_base.connect()

    for image_name in image_names[start:end]:
        # add max score to image table, insert score based on prediction values
        prediction = load_prediction(image_name)
        check_image_name = os.path.splitext(os.path.basename(image_name))[0]
        in_training = 1 if (is_in_training_set(check_image_name, training_image_names)) else 0
        query = """
            INSERT INTO Images (Name, InTraining, Reviewed, "Error", CropsGen)
            VALUES (?, ?, ?, ?, ?)
        """
        
        concurrent_base.query(query, (prediction["image_name"], in_training, 0, 0, 0))
        
        imageId = concurrent_base.lastrowid()
        
        for box, score, label in zip(prediction['boxes'], prediction['scores'], prediction['labels']):
            
            query = """
                INSERT INTO Predictions (ImageId, ModelId, BoxTx, BoxTy, BoxBx, BoxBy, Score, Label)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            concurrent_base.query(query, (imageId, modelId, int(box[0]), int(box[1]), int(box[2]), int(box[3]), float(score), int(label)))
    
    concurrent_base.commit()
    concurrent_base.close()

#---------------------------------------------------------------------------------------------------------------------------#

def populate_initial_tables():
    """ Populate a SQL database with image names and predictions

        Returns None, populate tables in a database
    """
    # First part is single threaded for simplicity purposes
    base.create_tables()
    image_names = load_image_files()
    training_image_names = set(load_training_image_names())
    query = """
        INSERT INTO Models (ModelName)
        VALUES (?)
    """
    base.query(query, (model_name,))
    base.commit()
    modelId = base.lastrowid()
    
    # Actual row insertion uses multiple processes to greatly speed up data insertion
    process_count = max(1, cpu_count())
    print(f"Inserting into the database on {process_count} threads...")
    total_images = len(image_names)
    chunk_size = (total_images + process_count - 1) // process_count # Size of each block of
    pool = Pool(processes = process_count)
    tasks = []

    # delegate chunks of total images to threads evenly
    for i in range(process_count):
        start = i * chunk_size
        end = (i + 1) * chunk_size if i != process_count - 1 else total_images

        tasks.append((image_names, start, end, modelId, training_image_names))
        
    pool.starmap(concurrent_populate, tasks)
    pool.close()
    pool.join()

    base.create_indexes()
#---------------------------------------------------------------------------------------------------------------------------#

def auto_crop(image: np.ndarray, image_name: str, prediction: dict, crop_size: int, num_clusters: int) -> dict[str, dict[str, np.ndarray]]:
    """ Automatically create crops of a given size containing all images with approved annotations 
    
    Args:
        image: source image that predictions were made from
        points: List of coordinatTY), 85])e points of the approximate center for each prediction associated with the image
        crop_size: dimension for crop (note only square crops are currently supported)
        num_clusters: number of centers for kmeans to determine clusters 
        
    Returns list of crops based on original image
    TODO: finish implementing boundary checks
    """
    points = []
    centers = []
    crops = {} # Structure to be returned

    for box in prediction['boxes']:
        x = np.mean([box[0], box[2]])
        y = np.mean([box[1], box[3]])
        points.append((x, y))
   
    if len(points) == 0:
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
            return crops 

        centers = kmeans.cluster_centers_

    points_in_crop = np.zeros(len(points))
    for crop_num, center in enumerate(centers):
        crop_name = f"{image_name}_crop_{crop_num}"
        if crop_name not in crops:
            crops[crop_name] = {
                "crop": None,
                "dimesions": [],
                "prediction": {
                    "id": int,
                    "boxes": []
                }
            }
        x_start = max(0, int(center[0]) - crop_size // 2)
        y_start = max(0, int(center[1]) - crop_size // 2)
        x_end = min(image.shape[1], x_start + crop_size)
        y_end = min(image.shape[0], y_start + crop_size)
        if x_end == image.shape[1]:
            x_start -= (x_start + crop_size) - image.shape[1]

        if y_end == image.shape[0]:
            y_start -= (y_start + crop_size) - image.shape[0]
        
        crop = image[y_start:y_end, x_start:x_end].copy()

        for p_index, (box, pred_id) in enumerate(zip(prediction["boxes"], prediction["pred_ids"])):
            if ((box[0] >= x_start) and (box[2] <= x_end)) and ((box[1] >= y_start) and (box[3] <= y_end)): 
                points_in_crop[p_index] += 1
                crops[crop_name]["prediction"]["id"] = pred_id 
                crops[crop_name]["prediction"]["boxes"].append([
                    box[0] - x_start,
                    box[1] - y_start,
                    box[2] - x_start,
                    box[3] - y_start
                ])

        crops[crop_name]["crop"] = crop
        crops[crop_name]["dimensions"] = [x_start, y_start, x_end, y_end] 

    if np.all(points_in_crop >= 1):
        print(f"Finished in {num_clusters} clusters") 
        return crops

    elif num_clusters + 1 <= len(points):
        return auto_crop(image, image_name, prediction, crop_size, num_clusters + 1)

    else:
        print("Could not generate any crops...")
        plt.figure()
        plt.imshow(image)
        plt.title("Failed to crop")
        plt.show()
        return crops 

#---------------------------------------------------------------------------------------------------------------------------#

def get_pred_and_images(batch_size: int, desired_class: int, min_confidence: float) -> dict:
    predictions = {}
    offset = 0
    rows = []
    query = """
        SELECT P.PredId, P.BoxTx, P.BoxTy, P.BoxBx, P.BoxBy, P.Score, P.Label, P.ModelId, I.Name, I.InTraining, I.ImageId
        FROM Predictions P
        JOIN Images I On P.ImageId = I.ImageId
        WHERE I.Imageid IN (
            SELECT ImageId
            FROM Images
            WHERE Reviewed = 0 AND Open = 0
            ORDER BY Reviewed ASC
            LIMIT ? OFFSET ?
        ) AND P.Label = ? AND P.Score > ?
        ORDER BY P.Score DESC
        """
    # query the database until results are returned
    while len(rows) < 1: #type: ignore
        try:
            rows = base.query(query, (batch_size, offset, desired_class, min_confidence))
        except Exception as e:
            print(f"Exception: {e} has ouccured")
        
        offset += batch_size

    for row in rows: #type: ignore
        pred_id = row[0]
        box = [row[1], row[2], row[3], row[4]]
        score = row[5]
        label = row[6]
        model_id = row[7]
        image_name = row[8]
        in_training = row[9]
        image_id = row[10]
        if image_name not in predictions:
            predictions[image_name] = {
                "pred_ids": [],
                "boxes": [],
                "scores": [],
                "labels": [],
                "model_id": model_id,
                "in_training": in_training,
                "image_id": image_id,
            }
        predictions[image_name]["pred_ids"].append(pred_id)
        predictions[image_name]["boxes"].append(box)
        predictions[image_name]["scores"].append(score)
        predictions[image_name]["labels"].append(label)

        query = """
            UPDATE Images
            SET Open = 1 
            WHERE ImageId = ?
        """
        base.query(query, (image_id,))
    
    base.commit()
    return predictions

#---------------------------------------------------------------------------------------------------------------------------#

def prompt_user(desired_class: int):
    if os.name == "posix":
        pass
        os.system("clear")
    else:
        os.system("cls")
    while True: # Show number associated with crop indexes in plot
        user_input = input(f"Please indicate (yes or no) whether any displayed image is of a {class_names[desired_class]}, q to quit: \n")
        try:
            if user_input in set(["q", "Q", "Quit", "quit", "QUIT"]):
                print("Quitting...")
                return "q" 

            if user_input in set(["y", "Y", "yes", "Yes", "1"]):
                return True
            elif user_input in set(["n", "N", "no", "No", "0"]):
                return False
                
        except:
            continue

#---------------------------------------------------------------------------------------------------------------------------#

def show_predictions_matplot(image: np.ndarray, prediction: dict, desired_class: int, draw_box: bool) -> bool:
    crop_size = 100
    crops = []
    if len(prediction["boxes"]) == 0:
        return False
    for box in prediction["boxes"]:
        ymin = np.max([box[1] - crop_size, 0])
        ymax = np.min([box[3] + crop_size, image.shape[0]])
        xmin = np.max([box[0] - crop_size, 0])
        xmax = np.min([box[2] + crop_size, image.shape[1]])
        if draw_box:
            cv2.rectangle(image, (box[0], box[1]), (box[2], box[3]), (255, 0, 0), 3)
        
        crops.append(image[ymin:ymax, xmin:xmax].copy())
    
    if len(crops) > 0:
        fig, axs = plt.subplots(1, len(crops))
        if len(crops) == 1:
            axs = [axs] 

        crop_indices = []
        for crop_num, (ax, crop) in enumerate(zip(axs, crops)):
            crop_indices.append(crop_num + 1)
            ax.imshow(crop)
            ax.set_title(f"Crop Number: {crop_num + 1}")
            ax.set_axis_off()

        plt.show(block=False)
        out = prompt_user(desired_class)
        plt.close(fig)
        
        if out == "q":
            quit_app()
            return False # only exists to appease pyright
        else:
            return out
    return False
    
#---------------------------------------------------------------------------------------------------------------------------#

def approve_annotations(predictions: dict, desired_class: int, crop_size: int, draw_box: bool, image_backend: str) -> int:
    """ Present the user with cropped images and their predictions for validation 

    """
    num_crops = 0
    for image_name, pred in predictions.items():
        image_path = os.path.join(f"{images_folder}", f"{image_name}.JPG")
        image = plt.imread(image_path).copy()
        image_crops = auto_crop(image, image_name, pred, crop_size, 1)
        if len(image_crops) == 0:
            continue
        for crop_name, crop in image_crops.items():
            if image_backend in image_backends:
                approved_predictions = image_backends[image_backend](crop["crop"], crop["prediction"], desired_class, draw_box) #type: ignore
            
            if approved_predictions:
                query = """
                    INSERT INTO Crops (ImageId, CropName, InLabelBox, CropTx, CropTy, CropBx, CropBy, Created, GlobalKey)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                base.query(query, (pred["image_id"], crop_name, 0, crop["dimensions"][0], crop["dimensions"][1], crop["dimensions"][2], crop["dimensions"][3], current_date, str(uuid4())))
                base.commit()
                num_crops += 1
                crop_id = base.lastrowid()
                
                for box in crop["prediction"]["boxes"]:
                    query = """
                        INSERT INTO CropPredictions (CropId, PredId, ImageId, BoxTx, BoxTy, BoxBx, BoxBy)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """
                    base.query(query, (crop_id, crop["prediction"]["id"], pred["image_id"], box[0], box[1], box[2], box[3]))
                
                # Save with opencv without compression, highest quality score
                cv2.imwrite(f'{save_folder}/{crop_name}.jpg', cv2.cvtColor(crop["crop"], cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 100])
                base.commit()
            query = """
                UPDATE Images
                SET Reviewed = 1, Open = 0, CropsGen = ?
                WHERE ImageId = ?
            """
            base.query(query, (num_crops, pred["image_id"]))
            base.commit()
    
    return num_crops 
#---------------------------------------------------------------------------------------------------------------------------#

def concurrent_upload(data_rows, start, end, dataset):
    task = dataset.create_data_rows(data_rows[start:end])
    task.wait_until_done()

#---------------------------------------------------------------------------------------------------------------------------#
    
def upload_to_labelbox(batch_size, desired_class: int):
    global uploading
    if uploading:
        return 
    uploading = True
    client = lb.Client(os.environ.get("API_KEY"))
    project = client.get_project(os.environ.get("PROJECT_ID"))
    dataset = client.get_dataset(os.environ.get("DATASET_ID"))

    data_rows = []
    global_keys = []
    row_ids = []
    labels = []

    query = """
        SELECT C.CropId, C.CropName, C.GlobalKey
        FROM Crops C 
        WHERE C.InLabelBox = 0
        """
    crops = base.query(query,())
    
    if len(crops) == 0: #type: ignore
        print("No valid crops to upload, please approve predictions first!") #type: ignore
        return
    else:
        print(f"\n{len(crops)} valid crops not yet uploaded to labelbox, working!") #type: ignore

    for crop_info in crops: #type: ignore
        data_rows.append({
            "row_data": f'{save_folder}/{crop_info[1]}.jpg',
            "global_key": crop_info[2],
            "external_id": crop_info[1]
        })
        query = """
            UPDATE Crops 
            SET InLabelBox = 1 
            WHERE CropId = ?
            """
        base.query(query, (crop_info[0],))
        global_keys.append(crop_info[2])
        query = """
            SELECT CP.BoxTx, BoxTy, BoxBx, BoxBy
            FROM CropPredictions CP
            WHERE ? = CP.CropId
        """
        crop_preds = base.query(query,(crop_info[0],))
        for pred_info in crop_preds: #type: ignore 
            labels.append(
                Label(
                    data = {"global_key": crop_info[2]}, #type: ignore
                    annotations = [
                        ObjectAnnotation(
                            name = class_names[desired_class],
                            value = Rectangle(
                                start = Point(x = pred_info[0], y = pred_info[1]),
                                end = Point( x = pred_info[2], y = pred_info[3])
                            )
                        )
                    ]
                ) 
            )
   
    # determine chunk_size from number of data_rows
    num_data_rows = len(data_rows)
    # Multiprocessing configuration
    process_count = max(1, cpu_count())

    if num_data_rows < process_count:
        process_count = num_data_rows

    print(f"Uploading to labelbox on {process_count} threads...")

    chunk_size = (num_data_rows + process_count - 1) // process_count 
    pool = Pool(processes = process_count)
    tasks = []

    for i in range(process_count):
        start = i * chunk_size
        end = (i + 1) * chunk_size if i != process_count - 1 else num_data_rows

        tasks.append((data_rows, start, end, dataset))

    pool.starmap(concurrent_upload, tasks)
    pool.close()
    pool.join()
    base.commit()
    # Request data rows associated with global_ids we generated for labelbox shenannigans
    res = client.get_data_row_ids_for_global_keys(global_keys)
    
    # loop over the dict to append the actual ids to a list that is useful to us
    for id in res["results"]:
        row_ids.append(id)
    
    project.create_batch(
        name = f"high-altitude-pronghorn-survey-{str(uuid4())}", # add model name to batch
        data_rows = row_ids, #type_ignore
        priority = 5,
    )
   # Upload MAL label for this data row in project
    lb.MALPredictionImport.create_from_objects(
        client = client, 
        project_id = project.uid, #type: ignore 
        name="mal_job"+str(uuid4()), 
        predictions=labels
    )
    print("Upload complete!")
    uploading = False

#---------------------------------------------------------------------------------------------------------------------------#

def setup_interrupt_handler():
    """ Gracefully handle ^C interrupts regarding the database
    
    """
    signal.signal(signal.SIGINT, interrupt_handler)

#---------------------------------------------------------------------------------------------------------------------------#
# Dictionary of function calls to determine which version of a function to use. 
image_backends = {
    "matplot": show_predictions_matplot,
}
class_names = {
    2: "pronghorn",
}

