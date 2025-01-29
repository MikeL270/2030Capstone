# Download annotated dataset from Labelbox and train a CNN with it
# Authors: Ben Koger, Michael B. Lance
# Created: January 28, 2025
# Updated: January 28, 2025
#---------------------------------------------------------------------------------------------------------------------------#
import os
from dotenv import load_dotenv 
from labelbox import Client
import cv2
from datetime import datetime
import numpy as np

# Pyright has a stroke when trying to resolve from koger_detection for some reason, it should be fine -ml
from koger_detection.labelbox.annotations import download_annotation_project
from koger_detection.utils.json import rename_categories
from koger_detection.utils.json import create_train_val_split
from koger_detection.utils.box_coco_utils import print_instances_class_histogram
from koger_detection.obj_det.engine import train, get_detection_model
from koger_detection.obj_det.engine import collate_fn, worker_init_fn
from koger_detection.obj_det.mydatasets import CocoDetection
from koger_detection.obj_det.augementors import RandomCropWithBBox
from koger_detection.utils.dataset import get_ious
from koger_detection.utils.lr_scheduler import get_lr_scheduler
import json

#pytorch
import torch
# Note: also need to install pycocotools
# I dont think we need these since there is no visualization 
"""
from torchvision import datasets
from torchvision.utils import draw_bounding_boxes
from torchvision.ops import box_convert
import torchvision.transforms.functional as F
from torchvision.utils import draw_bounding_boxes
from torchvision.transforms import ToTensor
"""
import albumentations as A
from albumentations.pytorch import ToTensorV2

#---------------------------------------------------------------------------------------------------------------------------#

research_project = "pronghorn-survey"
load_dotenv()
root = os.getcwd() # using cwd since I have no clue about ARCC's path
project_names = ['high-altitude-pronghorn-survey']
image_folder = os.path.join(root, "annotations", research_project, "images")
train_json_path = os.path.join(root, "annotations", research_project, "train.json")
val_json_path = os.path.join(root, "annotations", research_project, "val.json")
annotation_folder = os.path.join(os.environ.get("ROOT"), "annotations", research_project) #type: ignore

model_run_readme = "Training model with .15 val percent. Using full current augmentaion regime." 

now = datetime.now() # current date and time
date_time = now.strftime("%m-%d-%Y-%H-%M-%S")
model_path = os.environ.get("MODEL_PATH")
run_folder = os.path.join(model_path, research_project, "runs", f"{date_time}") #type: ignore
os.makedirs(run_folder)

class_colors = ["b", "r", "w", "g", "k"]

client = Client(api_key=os.environ.get("LABEL_BOX_API_KEY"))

#---------------------------------------------------------------------------------------------------------------------------#
# Load Images and Annotations from labelbox into memory for training

bbox_params = A.BboxParams(
    format='pascal_voc', label_fields=['class_labels', 'area']
)

base_transform  = A.Compose([
    A.ToFloat(max_value=255),
    ToTensorV2()
], bbox_params=bbox_params)

train_dataset = CocoDetection(image_folder,
                              train_json_path,
                              transform=base_transform)

val_dataset = CocoDetection(image_folder,
                            val_json_path,
                            transform=base_transform)

# Find the most annotations in a single image in training set
# Important for setting certain hyperparameters (i.e. rpn_batch_size_per_image etc.)
num_annotations = [d[1]['boxes'].shape[0] for d in train_dataset]
print(f"{len(train_dataset)} training images.")
print(f"max annoations per image {np.max(np.array(num_annotations))}")
class_labels = [int(torch.unique(d[1]['labels'])[0]) for d in train_dataset]
train_class_labels = max(class_labels)

# Find the most annotations in a single image in training set
# Important for setting certain hyperparameters (i.e. rpn_batch_size_per_image etc.)
num_annotations = [d[1]['boxes'].shape[0] for d in val_dataset]
print(f"{len(val_dataset)} validation images.")
print(f"max annoations per image {np.max(np.array(num_annotations))}")
class_labels = [int(torch.unique(d[1]['labels'])[0]) for d in val_dataset]
val_class_labels = max(class_labels)

# Background counts as a class (0) so need the + 1
num_classes = max([val_class_labels, train_class_labels]) + 1

print(f"{num_classes} object classes across the train and val annotations incl. background.")
#---------------------------------------------------------------------------------------------------------------------------#
# Build example and train datasets

# Where info about the training run will be saved (including run cfg)

cfg = {'model':
           {'model_type': "bbox_v2",
            'num_classes': num_classes,
            'trainable_backbone_layers': 5,
            'rpn_batch_size_per_image': 512,
            'rpn_pre_nms_top_n_train': 4000,
            'rpn_post_nms_top_n_train': 2000,
            'rpn_pre_nms_top_n_test': 4000,
            'rpn_post_nms_top_n_test': 2000,
            'box_detections_per_img': 700,
            'box_nms_thresh': .7,
            'box_batch_size_per_image': 512,
            'box_positive_fraction': 0.5,
            'fixed_size': [1024, 1024]
           },
       'training': 
           {'image_folder': image_folder,
            'train_json_path': train_json_path,
            'val_json_path': val_json_path,
            'batch_size': 4,
            'num_workers': 4,
            'num_epochs': 10,
            'run_folder': run_folder,
            'epochs_per_val': 2,
            'optimizer':
                {'name': 'SGD',
                 'lr': 0.005, 
                 'momentum': 0.9,
                 'weight_decay': 0.0005
                },
            'lr_scheduler':
                {'name': 'ReduceOnPlateau',
                 'patience': 4,
                 'factor': .3
                }
           }
      }

#---------------------------------------------------------------------------------------------------------------------------#

train_data_transform = A.Compose([
    RandomCropWithBBox(1024, 1024, p=1.0),
    A.ToFloat(max_value=255),
    A.HorizontalFlip(p=0.5),
    A.VerticalFlip(p=.3),
    A.geometric.resize.RandomScale(.2, interpolation=cv2.INTER_LINEAR, p=.75),
    A.geometric.transforms.PadIfNeeded(min_height=1024, min_width=1024, 
                 border_mode=cv2.BORDER_CONSTANT, value=0, p=1.0),
    RandomCropWithBBox(1024, 1024, p=1.0),
    A.RandomBrightnessContrast(brightness_limit=.3, contrast_limit=.1, 
                                   brightness_by_max=True, p=.75),
    A.Blur(p=.1),
    ToTensorV2()
], bbox_params=bbox_params)

val_data_transform = A.Compose([
    A.ToFloat(max_value=255),
    ToTensorV2()
], bbox_params=bbox_params)

cfg['train_aug'] = train_data_transform.to_dict()
cfg['val_aug'] = val_data_transform.to_dict()

# --------- SAVE CFG ------------------------
cfg['readme'] = model_run_readme #type: ignore

#define the path for your json file
cfg_path = os.path.join(cfg['training']['run_folder'], "cfg.json")

# open your json file and add the dictionary
with open (cfg_path, 'w') as f:
    json.dump(cfg, f, 
              default=lambda o: f"<<non-serializable: {str(o)}>>",
              indent=4)
    
# -------- BUILD TRAINING MODEL BASED ON CFG -------------------

model = get_detection_model(**cfg['model'])
print("Model built.")
params = [p for p in model.parameters() if p.requires_grad]

cfg_t = cfg['training']
cfg_t['optimizer'].pop('name') # TODO use name to choose optimizer in seperate function
optimizer = torch.optim.SGD(params, **cfg_t['optimizer'])
lr_scheduler = get_lr_scheduler(optimizer, **cfg_t['lr_scheduler'])

train_dataset = CocoDetection(image_folder,
                                  train_json_path,
                                  transform=train_data_transform)

#---------------------------------------------------------------------------------------------------------------------------#
# Train the model
train(cfg, model, optimizer, lr_scheduler, train_data_transform,
      val_data_transform)

