# Generate high quality crops of training data with model assisted labeling and Kmeans clustering
# Authors: Ben Koger, Michael B. Lance
# Created: November 11, 2024
# Updated: April 5, 2025

#---------------------------------------------------------------------------------------------------------------------------#

import glob
import json
import os
import cv2
import matplotlib.pyplot as plt
import numpy as np
from ..database import database
from ..imagebackends import imagebackends
from ..generatorobjects import generatorobjects
import sys
import signal
import datetime
from sklearn.cluster import KMeans
from dotenv import load_dotenv
import labelbox as lb
from labelbox.data.annotation_types import Label, ObjectAnnotation, Rectangle, Point
from uuid import uuid4
from multiprocessing import Pool, cpu_count
from typing import Any

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
def initialize(db_type: str, image_backend: str, db_configuration: dict):
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
    global img_backend
    global img_folder

    load_dotenv()
    db_config = db_configuration
    base = database.db_types[db_type](db_config)
    base.connect()

    img_backend = imagebackends.get_backend(image_backend)()

    model_name = os.environ.get("MODEL_NAME")
    herd_unit = os.environ.get("HERD_UNIT")
    root = os.environ.get("ROOT")
    predictions_folder = os.path.join(root, model_name, "data")  # type: ignore
    train_json_path = os.path.join(root, model_name, os.environ.get("ANNOTATIONS_FOLDER"), "train.json") #type: ignore
    current_date = datetime.date.today().strftime('%Y-%m-%d')
    save_folder = os.path.join(root, "Images", os.environ.get("CROP_FOLDER")) #type: ignore
    img_folder = os.path.join(root, "Images", herd_unit) #type: ignore
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
# TODO Rework to comply with new datastructure practices
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
    # TODO modify to comply with new memory model
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

def concurrent_populate_images(image_names: list, modelId: int, herdId: int, training_image_names: list, insert_images: bool, insert_predictions: bool):  
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
        if insert_images:   
            query = """
                INSERT INTO Images (Name, HerdUnitID, InTraining, Reviewed, "Error", CropsGen, Open)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            try:
                concurrent_base.query(query, (prediction["image_name"], herdId, in_training, 0, 0, 0, 0))
            except database.Postgres.psycopg2.errors.UniqueViolation:
                print("Image already in database...")
                continue
            
            imageId = concurrent_base.lastrowid()
        else:
            query = """
                    SELECT imageid
                    FROM images
                    WHERE image_name = ?
            """
            imageId = int(base.query(query, (image_name,))[0][0])
        if insert_predictions:
            for box, score, label in zip(prediction['boxes'], prediction['scores'], prediction['labels']):
                # Prediction level IOU would most likely be less efficient than comparing individual crops
                query = """
                    INSERT INTO Predictions (ImageId, ModelId, BoxTx, BoxTy, BoxBx, BoxBy, Score, Label)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                try: 
                    concurrent_base.query(query, (imageId, modelId, int(box[0]), int(box[1]), int(box[2]), int(box[3]), float(score), int(label))) #type: ignore
                except database.Postgres.psycopg2.errors.UniqueViolation:
                    print("Prediction Already in database...")
   # Async await commit from other workers 
    concurrent_base.commit() 
    concurrent_base.close() 

#---------------------------------------------------------------------------------------------------------------------------#

def insert_to_database(bootstrap: bool=False, insert_images: bool=True, insert_predictions: bool=True):
    images_folder = os.path.join(root, "Images", herd_unit) #type: ignore   
    image_names = load_image_files(images_folder) 
    
    training_image_names = load_training_image_names()
    # TODO: Update to use new methods, move all db stuff to database package
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
        tasks.append((image_names[start:end], modelId, herdId, training_image_names, insert_images, insert_predictions))
         
    pool.starmap(concurrent_populate_images, tasks)
    pool.close()
    pool.join()
    if bootstrap:
        insert_manual_crops(modelId)
    update_training(list(load_training_image_names(True)), modelId)
    base.create_indexes()
    base.commit()

#---------------------------------------------------------------------------------------------------------------------------#

def insert_full():
    insert_to_database(bootstrap=False, insert_images=True, insert_predictions=True)

#---------------------------------------------------------------------------------------------------------------------------#

def insert_new_images():
    insert_to_database(bootstrap=False, insert_images=True, insert_predictions=False)

#---------------------------------------------------------------------------------------------------------------------------#

def insert_new_preds():
    insert_to_database(bootstrap=False, insert_images=False, insert_predictions=False)

#---------------------------------------------------------------------------------------------------------------------------#

def bootstrap_database():
    """ Populate a SQL database with image names and predictions

        Returns None, populate tables in a database
    """
    # First part is single threaded for simplicity purposes
    base.create_tables()     
    insert_to_database(bootstrap=True, insert_images=True, insert_predictions=True)

#---------------------------------------------------------------------------------------------------------------------------#

def auto_crop(image: generatorobjects.Image, predictions: list[generatorobjects.Prediction], num_clusters: int=1, crop_size: int=2100) -> dict[generatorobjects.Crop, list[generatorobjects.Prediction]]:
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
    img = image.get_image()

    # Get centers for all predictions 
    for pred in predictions:
        points.append(pred.dimensions.get_center())

    if len(points) == 0:
        print("no points")
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
        crop = generatorobjects.Crop(
            name = f"{image.name}_crop_{crop_num}",
            image_id = image.id,
        )
        crops[crop] = []
        
        x_start = max(0, int(center[0]) - crop_size // 2)
        y_start = max(0, int(center[1]) - crop_size // 2)
        x_end = min(img.shape[1], x_start + crop_size)
        y_end = min(img.shape[0], y_start + crop_size)
        if x_end == img.shape[1]:
            x_start -= (x_start + crop_size) - img.shape[1]

        if y_end == img.shape[0]:
            y_start -= (y_start + crop_size) - img.shape[0]
        
        crop.set_image(img[y_start:y_end, x_start:x_end].copy())

        for p_index, pred in enumerate(predictions):
            tl_x, tl_y, br_x, br_y = pred.dimensions.get_points()
            if ((tl_x >= x_start) and (br_x <= x_end)) and ((tl_y >= y_start) and (br_y <= y_end)): 
                points_in_crop[p_index] += 1
                crops[crop].append(
                    generatorobjects.Prediction(
                        pred_id = pred.id,
                            dimensions = generatorobjects.Box(
                                tl_x = tl_x - x_start,
                                tl_y = tl_y - y_start,
                                br_x = br_x - x_start,
                                br_y = br_y - y_start
                            ),
                        score = pred.score,
                        label = pred.label, 
                        model_id = pred.model_id
                    )  
                )  
        crop.dimensions = generatorobjects.Box(x_start, y_start, x_end, y_end)

    if np.all(points_in_crop >= 1):
        print(f"Finished in {num_clusters} clusters") 
        return crops

    elif num_clusters + 1 <= len(points):
        print("we need more crops")
        return auto_crop(image=image, predictions=predictions, crop_size=crop_size, num_clusters=num_clusters +1)

    else:
        print("Could not generate any crops...")
        plt.figure()
        plt.imshow(image)
        plt.title("Failed to crop")
        plt.show()
        return crops 

#---------------------------------------------------------------------------------------------------------------------------#
def get_batch(batch_size: int, desired_class: int, min_confidence: float) -> dict:
    batch = {}
    rows = base.get_pred_and_images(batch_size, desired_class, min_confidence, herd_unit, model_name)
    herd_unit_id = base.herd_units_reverse[herd_unit]
    model_id = base.models_reverse[model_name]

    for img in rows:
        image = generatorobjects.Image(
            imageId = img["imageid"],
            name = img["name"],
            herdUnitId = herd_unit_id,
            inTraining = True if img["intraining"] == 1 else False,
            folder_path = img_folder,
            )
        batch[image] = []
        for pred in img["predictions"]:
            batch[image].append(
                generatorobjects.Prediction(
                    pred_id = pred["PredId"],
                    dimensions = generatorobjects.Box(
                        tl_x = pred["BoxTx"],
                        tl_y = pred["BoxTy"],
                        br_x = pred["BoxBx"],
                        br_y = pred["BoxBy"],
                    ),
                    score = pred["Score"],
                    label = pred["Label"],
                    model_id = model_id
                    )
            )
    return batch    

#---------------------------------------------------------------------------------------------------------------------------#

def approve_annotations(batch: dict[generatorobjects.Image, generatorobjects.Prediction], desired_class: int, crop_size: int, draw_box: bool):
    """ Present the user with cropped images and their predictions for validation """

    model_id = base.models_reverse[model_name]
    class_name = base.class_labels_forward[desired_class]
  
    for image, predictions in batch.items():
        crops = auto_crop(image=image, predictions=predictions, crop_size=crop_size)

        query = """
            SELECT *
            FROM Crops
            WHERE ModelID != ? AND ImageId = ?
        """
        existing_crops = base.query(query, (model_id, image.id))

        # Perform Iou check to prevent duplicate data
        for crop in crops:
            for ecrop in existing_crops:
                if crop.calc_iou(generatorobjects.Box(ecrop[5], ecrop[6], ecrop[7], ecrop[8])) >= 0.9:
                    print("duplicate crop")
                    crops.pop(crop, None)

        #TODO: Rework image backends for new data structures
        approve_annotations = img_backend.show_predictions(image, predictions, desired_class, class_name)
    

#---------------------------------------------------------------------------------------------------------------------------#
# TODO move to database
def insert_crops(crops: dict[generatorobjects.Crop, list[generatorobjects.Prediction]]):
    for crop, predictions in crops.items():
        query = """
            INSERT INTO Crops (ModelID, ImageId, CropName, InLabelBox, CropTx, CropTy, CropBx, CropBy, Created, GlobalKey)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

        base.query(query, (crop.model_id, crop.image_id, crop.name, 0, crop.dimensions.get_points(), current_date, str(uuid4()))) 
        num_crops += 1

        for pred in predictions:
            query = """
                INSERT INTO CropPredictions (CropId, PredId, ImageId, BoxTx, BoxTy, BoxBx, BoxBy)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            base.query(query, (crop.id, pred.id, crop.image_id, pred.dimensions.get_points())) #type: ignore
        
        # Save with opencv without compression, highest quality score
        cv2.imwrite(f'{save_folder}/{crop.crop_name}.jpg', cv2.cvtColor(crop.get_image(), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 100])
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
        LIMIT 50
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
                            name = base.class_labels_forward[desired_class],
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