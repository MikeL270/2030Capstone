# Perform inference task on images with pretrained model and upload to database
# Authors: Ben Koger, Michael B. Lance
# Created: January 29, 2025
# Updated: February 3, 2025
#---------------------------------------------------------------------------------------------------------------------------#
import glob
import json
import os
import uuid
from dotenv import load_dotenv 
import numpy as np 
from PIL import Image 
import torch 
import matplotlib as plt  
from koger_detection.obj_det.predictors import Predictor #type: ignore 
from koger_detection.obj_det.mydatasets import ImageDataset #type: ignore
from koger_detection.obj_det.engine import collate_fn, worker_init_fn #type: ignore
import database
#---------------------------------------------------------------------------------------------------------------------------#
load_dotenv()
model_name = "10-25-2024-16-50-17"
herd_unit = "pr427"
root = os.environ.get("ROOT")
images_folder = os.path.join(root, os.environ.get("IMAGE_FOLDER")) #type: ignore 
research_project = "pronghorn-survey"
model_folder = os.path.join(root, os.environ.get("MODEL_PATH")) #type: ignore
model_cfg_file = os.path.join(model_folder, "cfg.json")
model_weights_file = os.path.join(model_folder, "final_model.pth")
image_files = sorted(glob.glob(os.path.join(images_folder, f"*.[jJ][pP][gG]")))
print(f"{len(image_files)} files found.")

db_config = {
    "database": os.environ.get("DB_NAME"),
    "user": os.environ.get("DB_USER"),              
    "password": os.environ.get("DB_PASS"),    
    "host": os.environ.get("DB_HOST"),           
    "port": "5432"              
}

base = database.Postgres(db_config)

base.connect()

query = """
INSERT INTO Models (ModelName)
VALUES (?)
"""
base.query(query, (model_name,))
base.commit()
modelId = base.lastrowid()
query = """
INSERT INTO HerdUnit (HerdUnitName)
VALUES (?)
"""
base.query(query, (herd_unit,))
base.commit()
herdID = base.lastrowid()

#---------------------------------------------------------------------------------------------------------------------------#

with open(model_cfg_file) as f:
    cfg = json.load(f)
    model_cfg = cfg['model']
model_cfg['fixed_size'] = [8256, 5504]
model_cfg['model_weights_pth'] = model_weights_file

rgb = True

image_dataset = ImageDataset(image_files, rgb=rgb)
dataloader = torch.utils.data.DataLoader(
            image_dataset, batch_size=1, shuffle=False, 
            num_workers=4)
# TODO!!!!!! rgb being true here actually means it is converted to bgr
# I think should actually stay as rgb
predictor = Predictor(model_cfg, invert_color_channel=False)

#---------------------------------------------------------------------------------------------------------------------------#

for ind, image in enumerate(dataloader):

    if ind % 300 == 0:
        print(ind)

    res = predictor(image['image'][0])
    
    boxes = res['boxes'].to('cpu').numpy().astype(np.uint32)
    scores = res['scores'].to('cpu').numpy()
    labels = res['labels'].to('cpu').detach().numpy()

    image_name = os.path.splitext(os.path.basename(image['filename'][0]))[0]
    
    query ="""
        INSERT INTO Images (Name, HerdUnitId, InTraining, Reviewed, "Error", CropsGen, Open)
        Values (?, ?, ?, ?, ?, ?, ?)
    """
    base.query(query,(image_name, 0, 0, 0, 0, 0))
    imageId = base.lastrowid()

    for box, score, label in zip(boxes, scores, labels):

        query ="""
            INSERT INTO Predictions (ImageId, ModelId, BoxTx, BoxTy, BoxBx, BoBy, Score, Label)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        base.query(query, (imageId, modelId, int(box[0]), int(box[1]), int(box[2]), int(box[3]), float(score), int(label)))

        base.commit()

base.close()


