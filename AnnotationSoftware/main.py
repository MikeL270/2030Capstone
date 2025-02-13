import crop_generator
import sys
import multiprocessing
#---------------------------------------------------------------------------------------------------------------------------#
# Configuration

# Default Values
create_db = False
draw_box = True
crop_size = 2100
desired_class = 2
min_confidence = 0.50
batch_size = 100
image_backend = "matplot"
approve_predictions = False
upload_to_labelbox = False

#flags to modify default values
if "create_db" in sys.argv:
    create_db = True
if "matplot" in sys.argv:
    image_backend = "matplot"
if "approve_predictions" in sys.argv:
    approve_predictions = True
if "upload_to_labelbox" in sys.argv:
    upload_to_labelbox = True

#---------------------------------------------------------------------------------------------------------------------------#
#Program start
crop_generator.setup_interrupt_handler()

if create_db:
    crop_generator.populate_initial_tables()

if upload_to_labelbox:
    crop_generator.upload_to_labelbox(batch_size=batch_size, desired_class=desired_class)

if approve_predictions:
    num_crops = 0
    while True:
        # Load a dictionary of model predictions into memory 
        predictions = crop_generator.get_pred_and_images(batch_size=batch_size, desired_class=desired_class, min_confidence=min_confidence)
        if len(predictions) == 0:
            continue
        # Approve crops 
        num_crops += crop_generator.approve_annotations(predictions=predictions, desired_class=desired_class, crop_size=2100, draw_box = False, image_backend=image_backend)
        
        if num_crops == batch_size:
            bg_upload = multiprocessing.Process(target=crop_generator.upload_to_labelbox, args=(batch_size, desired_class))
            bg_upload.start()
