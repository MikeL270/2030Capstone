# Methods for presenting images to users
# Authors: Ben Koger, Michael B. Lance
# Created: February 26, 2025
# Updated: April 4, 2025

#---------------------------------------------------------------------------------------------------------------------------#
from abc import ABC, abstractmethod 
from typing import Any
import os
import numpy as np
import math
import asyncio

#---------------------------------------------------------------------------------------------------------------------------#

class ImageBackend(ABC):
    import cv2
    
    @abstractmethod
    async def show_predictions(self, image: np.ndarray, prediction: dict, desired_class: int, draw_box: bool):
        pass

    def create_subcrop(self, image: np.ndarray, prediction: dict, draw_box: bool):
        crop_size = 150
        crops = []
        if len(prediction["boxes"]) == 0:        
            return False

        for box in prediction["boxes"]:
            ymin = np.max([box[1] - crop_size, 0])
            ymax = np.min([box[3] + crop_size, image.shape[0]])
            xmin = np.max([box[0] - crop_size, 0])
            xmax = np.min([box[2] + crop_size, image.shape[1]])
            crops.append(image[ymin:ymax, xmin:xmax].copy())

            if draw_box:
                self.cv2.rectangle(image, (box[0], box[1]), (box[2], box[3]), (255, 0, 0), 3)

        return crops
    
#---------------------------------------------------------------------------------------------------------------------------#

class MatplotBackend(ImageBackend):
    import matplotlib.pyplot as plt
    def __init__(self, window: Any=None):
        pass

    def prompt_user(self, class_name): 
        if os.name == "posix":
            pass
            os.system("clear")
        else:
            os.system("cls")

        while True: # Show number associated with crop indexes in plot
            user_input = input(f"Please indicate (yes or no) whether any displayed image is of a {class_name}, q to quit: \n")
            try:
                if user_input in set(["q", "Q", "Quit", "quit", "QUIT"]):
                    print("Quitting...")
                    return -999 

                if user_input in set(["y", "Y", "yes", "Yes", "1"]):
                    return True
                elif user_input in set(["n", "N", "no", "No", "0"]):
                    return False
                
            except:
                continue 

    def show_predictions(self, image: np.ndarray, prediction: dict, desired_class: int, class_labels: dict, draw_box: bool = False):     
        crops = self.create_subcrop(image, prediction, draw_box)
        scale_factor = 2
        crop_size = 2
        max_cols = 6
        max_crops = 36
        class_name = class_labels[desired_class]

        crops = crops[:max_crops] #type: ignore
        if len(crops) <= max_cols:
            cols = len(crops)
            rows = 1
        else:
            cols = max_cols
            rows = math.ceil(len(crops) / max_cols)#---------------------------------------------------------------------------------------------------------------------------#

        #     axs = [axs]
        for ax, crop, score in zip(fig.axes[:len(crops)], crops, prediction["scores"]):
            ax.imshow(crop)
            ax.set_title(f"score: {score:.3f}")
            ax.set_axis_off() 
    
        self.plt.figure(figsize=(15,15))
        self.plt.imshow(image)
        self.plt.axis('off')
        self.plt.close() 
        self.plt.show(block=False)
        out = self.prompt_user(class_name)
        self.plt.close(fig)
        if out == -999:
            return -999
        return out #type: ignore
    
#---------------------------------------------------------------------------------------------------------------------------#

class OpencvBackend(ImageBackend):

    def prompt_user(self, key):
        if key == ord('q'):
                self.cv2.destroyAllWindows()
                return -999
            
        if key in set([ord("y"), ord("Y"), ord("1")]):
            return True
        if key in set([ord("n"), ord("N"), ord("0")]):
            return False

    async def show_predictions(self, image: np.ndarray, prediction: dict, desired_class: int, draw_box: bool = False):
        crops = self.create_subcrop(image, prediction, desired_class, draw_box)
        
        if os.name == "posix":
            pass
            os.system("clear")
        else:
            os.system("cls")

        for crop, score in zip(crops, prediction["scores"]): #type: ignore
            self.cv2.imshow(f"score: {score}", self.cv2.cvtColor(crop, self.cv2.COLOR_BGR2RGB))
            
            key = self.cv2.waitKey(0)
            
            out = self.prompt_user(key)
            self.cv2.destroyAllWindows()

            if out == -999:
                return -999
            return out
         
#---------------------------------------------------------------------------------------------------------------------------#
# Returns JSON object of crops to easily build gui applications
class JsonBackend(ImageBackend):
    import json
    async def show_predictions(self, crop):
        return self.json.dumps(crop, indent = 4)

#---------------------------------------------------------------------------------------------------------------------------#

def get_backend(backend_type: str):
    backends = {
    "matplot": MatplotBackend,
    "opencv": OpencvBackend,
    }

    return backends[backend_type]