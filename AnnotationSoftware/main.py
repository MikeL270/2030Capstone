import cropgenerator
import sys
import multiprocessing
import os
from dotenv import load_dotenv
#---------------------------------------------------------------------------------------------------------------------------#
# Configuration
load_dotenv()
# Default Values
create_db = False
append_to_db = False
draw_box = True
crop_size = 2100
desired_class = 2
min_confidence = 0.80
batch_size = 50
image_backend = "matplot"
approve_predictions = False
upload_to_labelbox = False
update_training = False

#flags to modify default values
if "create_db" in sys.argv:
    create_db = True
if "insert_data" in sys.argv:
    append_to_db = True
if "matplot" in sys.argv:
    image_backend = "matplot"
if "opencv" in sys.argv:
    image_backend = "opencv"

if "approve_predictions" in sys.argv:
    approve_predictions = True
if "upload_to_labelbox" in sys.argv:
    upload_to_labelbox = True
if "update_training" in sys.argv:
    update_training = True

db_config = {
    "database": os.environ.get("DB_NAME"),
    "user": os.environ.get("DB_USER"),              
    "password": os.environ.get("DB_PASS"),    
    "host": os.environ.get("DB_HOST"),           
    "port": "5432"              
}

#---------------------------------------------------------------------------------------------------------------------------#
#Program start
cropgenerator.initialize(db_type="postgres", image_backend=image_backend, db_configuration=db_config)

if create_db:
    cropgenerator.bootstrap_database()

if append_to_db:
    cropgenerator.insert_images_to_database(False)

if upload_to_labelbox:
    cropgenerator.upload_to_labelbox(batch_size=batch_size, desired_class=desired_class)

if update_training:
    print("This function should only be applied to models inserted before 3/7/2025, or if there are issues. Please use caution and test this before using it on using on you production database.")
    cropgenerator.update_training(list(cropgenerator.load_training_image_names(True)), int(input("Please enter the id of the model you are updating training for: ")))

if approve_predictions:
    num_crops = 0
    while True:
        # Load a dictionary of model predictions into memory 
        predictions = cropgenerator.get_pred_and_images(batch_size=batch_size, desired_class=desired_class, min_confidence=min_confidence)
        if len(predictions) == 0:
            continue
        # Approve crops 
        num_crops += cropgenerator.approve_annotations(predictions=predictions, desired_class=desired_class, crop_size=2100, draw_box = False)
        
        if num_crops == batch_size:
            bg_upload = multiprocessing.Process(target=cropgenerator.upload_to_labelbox, args=(batch_size, desired_class))
            bg_upload.start()
