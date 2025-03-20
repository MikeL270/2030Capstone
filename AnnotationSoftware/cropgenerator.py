# Generate high quality crops of training data with model assisted labeling and Kmeans clustering
# Authors: Ben Koger, Michael B. Lance
# Created: November 11, 2024
# Updated: March 7, 2025

#---------------------------------------------------------------------------------------------------------------------------#

import glob
import json
import os
import cv2
import matplotlib.pyplot as plt
import numpy as np
import database
import imagebackends
import classnames
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

#---------------------------------------------------------------------------------------------------------------------------#

def setup_interrupt_handler():
    """ Gracefully handle ^C interrupts regarding the database
    
    """
    signal.signal(signal.SIGINT, interrupt_handler)

#---------------------------------------------------------------------------------------------------------------------------#
# Since crop_generator is intended as a module it is good practice to not have it execute anything not called in a function
def initialize(db_type: str, db_configuration: dict):
    """ Initialize the module and with the specified database backend and environment variables

    """
    # Global Variables needed for variable things
    global base
    global root
    global model_name
    global herd_unit
    global predictions_folder
    global train_json_path
    global current_date
    global save_folder
    global uploading
    global db_config
    global prefix
    global suffix

    load_dotenv()
    db_config = db_configuration
    base = database.db_types[db_type](db_config)
    base.connect()

    model_name = os.environ.get("MODEL_NAME")
    herd_unit = os.environ.get("HERD_UNIT")
    root = os.environ.get("ROOT")
    predictions_folder = os.path.join(root, model_name, "data")  # type: ignore
    train_json_path = os.path.join(root, model_name, os.environ.get("ANNOTATIONS_FOLDER"), "train.json") #type: ignore
    current_date = datetime.date.today().strftime('%Y-%m-%d')
    save_folder = os.path.join(root, "Images", os.environ.get("CROP_FOLDER")) #type: ignore
    os.makedirs(save_folder, exist_ok=True) # type: ignore
    uploading = False 
    prefix = len("high-altitude-pronghorn-survey-")
    suffix = len("_crop_xx")

    setup_interrupt_handler() 

#---------------------------------------------------------------------------------------------------------------------------#

def load_image_files(images_folder: str) -> list:
    """ Loads image file names into a List

    Returns a list of file names
    """
    image_files = sorted(glob.glob(os.path.join(images_folder, f"*.[jJ][pP][gG]"))) # type: ignore
    print(f"{len(image_files)} files found.")
    return image_files

#---------------------------------------------------------------------------------------------------------------------------#

def load_training_image_names(crop_suffix: bool = False) -> set:
    """ Loads training image names into a list
    
    Returns a set of filenames that were used to train the model 
    """ 
    with open(train_json_path) as f:
        train_json = json.load(f)
    if crop_suffix:
        return set(os.path.splitext(image_info['file_name'])[0][prefix:] for image_info in train_json['images'])
    else:
        return set(os.path.splitext(image_info['file_name'])[0][prefix:-suffix] for image_info in train_json['images'])

#---------------------------------------------------------------------------------------------------------------------------#

def load_prediction(image_file: str) -> dict[str, str]:
    """ Load model predictions for a given image name

    Args:
        image_file: string file path to an image

    Returns a dictionary containing the predictions
    """
    image_name = os.path.splitext(os.path.basename(image_file))[0]
    # Get corresponding box file for image
    box_file = os.path.join(predictions_folder, f"{image_name}_boxes.npy") #type: ignore
    if not os.path.exists(box_file):
        raise Exception(f"{image_name} missing box file.")
    else:
        boxes = np.load(box_file)
    # Get corresponding score file for image
    score_file = os.path.join(predictions_folder, f"{image_name}_scores.npy") #type: ignore
    if not os.path.exists(score_file):
        raise Exception(f"{image_name} missing score file.")
    else:
        scores = np.load(score_file)
    # Get corresponding object class file for image
    label_file = os.path.join(predictions_folder, f"{image_name}_labels.npy") #type: ignore
    if not os.path.exists(label_file):
        raise Exception(f"{image_name} missing labels file.")
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

def update_training(image_names: list, modelId):
    for name in image_names:
        query = """
            SELECT CropId, imageID
            FROM Crops
            WHERE CropName = ?
        """
        ids = base.query(query, (name,))
        if len(ids) == 0:
            continue
        query = """ 
            INSERT INTO TRAINING (CropId, ModelId)
            VALUES (?, ?)
            ON CONFLICT (CropId, ModelId) DO NOTHING
        """
        base.query(query, (ids[0][0], modelId))
        query = """
                UPDATE Images
                SET intraining = 1 
                WHERE Imageid = ?
        """
        base.query(query, (ids[0][1],))
        base.commit()

#---------------------------------------------------------------------------------------------------------------------------#

def insert_manual_crops(model_id: int):
    with open(train_json_path) as f:
        train_json = json.load(f)

    for image_info in train_json['images']:
        query = """
            SELECT ImageId 
            FROM Images
            WHERE Name = ?
        """
        image_id = base.query(query, (os.path.splitext(image_info['file_name'])[0][prefix:-suffix],))[0][0]
        query = """
            INSERT INTO Crops (ImageId, modelId, CropName, InLabelBox, CropTx, CropTy, CropBx, CropBy, Created, GlobalKey)
            Values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(CropName) DO NOTHING
        """
        base.query(query, (image_id, model_id, os.path.splitext(image_info['file_name'])[0][prefix:], 1, 0, 0, 0, 0, current_date, str(uuid4()),))

#---------------------------------------------------------------------------------------------------------------------------#

def concurrent_populate_images(image_names: list, modelId: int, herdId: int, training_image_names: list):  
    concurrent_base = type(base)(db_config)

    concurrent_base.connect()
 
    for image_name in image_names:
        # add max score to image table, insert score based on prediction values
        try:
            prediction = load_prediction(image_name)
        except Exception as e:
            print(e)
            continue
 
        check_image_name = os.path.splitext(os.path.basename(image_name))[0]
        in_training = 1 if (is_in_training_set(check_image_name, training_image_names)) else 0
            
        query = """
            INSERT INTO Images (Name, HerdUnitID, InTraining, Reviewed, "Error", CropsGen, Open)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        try:
            concurrent_base.query(query, (prediction["image_name"], herdId, in_training, 0, 0, 0, 0))
        except database.Postgres.psycopg2.errors.UniqueViolation:
            print("Image already in database")
            # add flow control to handle new predictions for a new model
            continue
        
        imageId = concurrent_base.lastrowid()
       
        for box, score, label in zip(prediction['boxes'], prediction['scores'], prediction['labels']):
            query = """
                INSERT INTO Predictions (ImageId, ModelId, BoxTx, BoxTy, BoxBx, BoxBy, Score, Label)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            concurrent_base.query(query, (imageId, modelId, int(box[0]), int(box[1]), int(box[2]), int(box[3]), float(score), int(label))) #type: ignore
   # Async await commit from other workers 
    concurrent_base.commit() 
    concurrent_base.close() 

#---------------------------------------------------------------------------------------------------------------------------#

def insert_images_to_database(bootstrap: bool):
    images_folder = os.path.join(root, "Images", herd_unit) #type: ignore   
    image_names = load_image_files(images_folder) 
    
    training_image_names = load_training_image_names()
    # TODO: This still does not work as intended, but I have no clue why
    query = """
        INSERT INTO Models (ModelName)
        VALUES (?)
        ON CONFLICT(ModelName) DO NOTHING
    """ 
    base.query(query, (model_name,))   
    base.commit()

    query = """
        SELECT ModelId 
        FROM Models
        WHERE ModelName = ?
    """
    modelId = int(base.query(query, (model_name,))[0][0])

    query = """
        INSERT INTO HerdUnits (HerdUnitName)
        VALUES (?)
        ON CONFLICT(HerdUnitName) DO NOTHING
    """
    
    base.query(query, (herd_unit,))
    base.commit()

    query = """
        SELECT HerdUnitId 
        FROM HerdUnits
        WHERE HerdUnitName = ?
    """
    herdId = int(base.query(query, (herd_unit,))[0][0])
    
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
        tasks.append((image_names[start:end], modelId, herdId, training_image_names))
         
    pool.starmap(concurrent_populate_images, tasks)
    pool.close()
    pool.join()
    if bootstrap:
        insert_manual_crops(modelId)
    update_training(list(load_training_image_names(True)), modelId)
    base.create_indexes()
    base.commit()

#---------------------------------------------------------------------------------------------------------------------------#

def bootstrap_database():
    """ Populate a SQL database with image names and predictions

        Returns None, populate tables in a database
    """
    # First part is single threaded for simplicity purposes
    base.create_tables()     
    insert_images_to_database(True)

#---------------------------------------------------------------------------------------------------------------------------#

def auto_crop(image: np.ndarray, image_name: str, prediction: dict, crop_size: int, num_clusters: int) -> dict[str, dict[str, np.ndarray]]:
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
                    "boxes": [],
                    "scores": []
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

        for p_index, (box, pred_id, score) in enumerate(zip(prediction["boxes"], prediction["pred_ids"], prediction["scores"])):
            if ((box[0] >= x_start) and (box[2] <= x_end)) and ((box[1] >= y_start) and (box[3] <= y_end)): 
                points_in_crop[p_index] += 1
                crops[crop_name]["prediction"]["id"] = pred_id 
                crops[crop_name]["prediction"]["boxes"].append([
                    box[0] - x_start,
                    box[1] - y_start,
                    box[2] - x_start,
                    box[3] - y_start
                ])
                crops[crop_name]["prediction"]["scores"].append(score)

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
    print("Querying database...")
    predictions = {}
    rows = []
    query = """
        SELECT P.PredId, P.BoxTx, P.BoxTy, P.BoxBx, P.BoxBy, P.Score, P.Label, I.Name, I.InTraining, I.ImageId, H.HerdUnitName
        FROM Predictions P
        JOIN Images I On P.ImageId = I.ImageId
        JOIN HerdUnits H On I.HerdUnitId = H.HerdUnitId
        WHERE I.Imageid IN (
            SELECT ImageId
            FROM Images
            WHERE Reviewed = 0 AND Open = 0
            ORDER BY Reviewed ASC 
        ) AND P.Label = ? AND P.Score > ?
        ORDER BY P.Score DESC
        LIMIT ?
    """
    rows = base.query(query, (desired_class, min_confidence, batch_size)) #type: ignore
    
    if len(rows) == 0:
        print("No results returned, try lowering min confidence!")
    
    for row in rows: #type: ignore
        pred_id = row[0]
        box = [row[1], row[2], row[3], row[4]]
        score = row[5]
        label = row[6]
        image_name = row[7]
        in_training = row[8]
        image_id = row[9]
        herd_unit = row[10]

        if image_name not in predictions:
            predictions[image_name] = {
                "pred_ids": [],
                "boxes": [],
                "scores": [],
                "labels": [],
                "in_training": in_training,
                "image_id": image_id,
                "herd_unit": herd_unit
            }
        predictions[image_name]["pred_ids"].append(pred_id)
        predictions[image_name]["boxes"].append(box)
        predictions[image_name]["scores"].append(score)
        predictions[image_name]["labels"].append(label)
        # More efficent way to update images (set of image ids )
        query = """
            UPDATE Images
            SET Open = 1 
            WHERE ImageId = ?
        """
        base.query(query, (image_id,)) #type: ignore
    
    base.commit() #type: ignore
    return predictions

#---------------------------------------------------------------------------------------------------------------------------#

def approve_annotations(predictions: dict, desired_class: int, crop_size: int, draw_box: bool, image_backend: str) -> int:
    """ Present the user with cropped images and their predictions for validation 

    """
    query = """
        SELECT ModelId 
        FROM Models
        WHERE ModelName = ?
    """
    modelId = int(base.query(query, (model_name,))[0][0])

    num_crops = 0
    for image_name, pred in predictions.items():
        images_folder = os.path.join(root, "Images", pred['herd_unit']) #type: ignore
        image_path = os.path.join(f"{images_folder}", f"{image_name}.JPG")
        image = plt.imread(image_path).copy()
        image_crops = auto_crop(image, image_name, pred, crop_size, 1)
        if len(image_crops) == 0:
            continue
        for crop_name, crop in image_crops.items():
            imagebackend = imagebackends.backends[image_backend]()
            approved_predictions = imagebackend.show_predictions(image=crop["crop"], prediction=crop["prediction"], desired_class=desired_class, draw_box=draw_box) #type: ignore
            if approved_predictions == -999:
                quit_app()

            if approved_predictions:
                query = """
                    INSERT INTO Crops (ModelID, ImageId, CropName, InLabelBox, CropTx, CropTy, CropBx, CropBy, Created, GlobalKey)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                base.query(query, (modelId, pred["image_id"], crop_name, 0, crop["dimensions"][0], crop["dimensions"][1], crop["dimensions"][2], crop["dimensions"][3], current_date, str(uuid4()))) 
                base.commit() 
                num_crops += 1
                crop_id = base.lastrowid() 

                for box in crop["prediction"]["boxes"]:
                    query = """
                        INSERT INTO CropPredictions (CropId, PredId, ImageId, BoxTx, BoxTy, BoxBx, BoxBy)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """
                    base.query(query, (crop_id, crop["prediction"]["id"], pred["image_id"], box[0], box[1], box[2], box[3])) #type: ignore
                
                # Save with opencv without compression, highest quality score
                cv2.imwrite(f'{save_folder}/{crop_name}.jpg', cv2.cvtColor(crop["crop"], cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 100])
                base.commit() #type: ignore
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
    if task.errors:
        print(task.errors)

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
        LIMIT 199
        """
    crops = base.query(query,(batch_size,)) #type: ignore
    
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
                            name = classnames.label_name[desired_class],
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
    base.commit() #type: ignore
    # Request data rows associated with global_ids we generated for labelbox shenannigans
    res = client.get_data_row_ids_for_global_keys(global_keys)
    
    # loop over the dict to append the actual ids to a list that is useful to us
    for id in res["results"]:
        row_ids.append(id)
    
    project.create_batch(
        name = f"high-altitude-pronghorn-survey-{str(uuid4())}", # add model n/exceame to batch
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

