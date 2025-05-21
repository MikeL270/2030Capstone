// Interfaces to calm typescript down
// Author: Michael B. Lance
// Created: May 5, 2025
// Updated: May 14, 2025
//---------------------------------------------------------------------------------------------------------------------------//
 import { Box, Image, Prediction, Crop, PredictionCrop} from'../types/generatorobjects';
//---------------------------------------------------------------------------------------------------------------------------//
// Interface for deserialization
export interface PredictionData {
    pred_id: number;
    model_id: number;
    dimensions:{
        'top_left': number[],
        'bottom_right': number[]
    };
    score: number,
    label: number,
}

export interface ImageData {
    image: {
        image_id: number; 
        image_name: string;
        herd_unit_id: number;
        in_training: boolean;
        url: string;
    };
    predictions: PredictionData[];

}

export interface BatchData {
    [key: string]: ImageData;
}

export interface PredCropData {
    [pred_crop_id: number]: {
        'crop_id': number,
        'pred_crop_id': number,
        'image_id': number,
        'crop_name': string,
        'dimensions': number[],
        'herd_unit_id': number,

    }
}

//---------------------------------------------------------------------------------------------------------------------------//
// Interfaces describing the expected structure of a batch and containers of said batches (sorry)
export interface Batch {
    [image_id: number]: {
        image: Image;
        predictions: Prediction[];
        approved_predictions: Prediction[];
        pred_crops: PredictionCrop[]; 
    };
}

export interface Batches {
    [batch_id: number]: Batch
}

//---------------------------------------------------------------------------------------------------------------------------//

export default{};