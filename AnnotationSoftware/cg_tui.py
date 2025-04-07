# Command line utility built on top of cropgenerator module
# Authors: Michael B. Lance
# Created: Nov 21, 2024
# Updated: March 24, 2025

#---------------------------------------------------------------------------------------------------------------------------#

import cropgenerator
import sys
import os
from dotenv import load_dotenv
#---------------------------------------------------------------------------------------------------------------------------#
# Configuration
# TODO: Rework flow control into scaleable argument parsing module
load_dotenv()
# Default Values

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

if "create_db" in sys.argv:
    cropgenerator.bootstrap_database()
elif "append_full" in sys.argv:
    cropgenerator.insert_full()
elif "insert_images" in sys.argv:
    cropgenerator.insert_new_images()
elif "insert_preds" in sys.argv:
    cropgenerator.insert_new_preds()

if upload_to_labelbox:
    cropgenerator.upload_to_labelbox(batch_size=batch_size, desired_class=desired_class)

if update_training:
    print("This function should only be applied to models inserted before 3/7/2025, or if there are issues. Please use caution and test this before using it on using on you production database.")
    cropgenerator.update_training(list(cropgenerator.load_training_image_names(True)), int(input("Please enter the id of the model you are updating training for: ")))

if approve_predictions:
    num_crops = 0
    while True:
        # Load a dictionary of model predictions into memory 
        batch = cropgenerator.get_batch(batch_size=batch_size, desired_class=desired_class, min_confidence=min_confidence)
        if len(batch) == 0:
            continue

        for image, predictions in batch.items():
            crops = cropgenerator.generate_crops(image, predictions, crop_size=crop_size)

            approved_crops = cropgenerator.evaluate_crops(crops, desired_class)

            #cropgenerator.upload_crops(approved_crops)