import crop_generator
import sys

#---------------------------------------------------------------------------------------------------------------------------#
# Configuration

# Default Values
create_db = False
draw_box = True
crop_size = 2100
pronghorn_class = 2
min_confidence = 0.8
batch_size = 1000
image_backend = "matplot"

#flags to modify default values
if "create_db" in sys.argv:
    create_db = True
if "matplot" in sys.argv:
    image_backend = "matplot"
        
#---------------------------------------------------------------------------------------------------------------------------#
#Program start
crop_generator.setup_interrupt_handler()

if create_db:
    crop_generator.populate_initial_tables()


while True:
    # Load a dictionary of model predictions into memory 
    predictions = crop_generator.get_pred_and_images(batch_size=batch_size, desired_class=pronghorn_class, min_confidence=min_confidence)
    # Approve crops 
    crop_generator.approve_annotations(predictions=predictions, crop_size=2100, draw_box = True, image_backend=image_backend) 

