// Typescript Class definition analogues for crop_generator objects 
// Author: Michael B. Lance
// Created: April 9, 2025
// Updated: June 17, 2025
//---------------------------------------------------------------------------------------------------------------------------//

import { mean } from 'lodash';

//---------------------------------------------------------------------------------------------------------------------------//

export interface Box_intf {
    top_left: number[],
    bottom_right: number[],
}

export class Box implements Box_intf {
    top_left: number[];
    bottom_right: number[];
    constructor (box: Box_intf) {
        this.top_left = box.top_left;
        this.bottom_right = box.bottom_right;
    }

    get_center(): number[] {
        let x = mean([this.top_left[0], this.bottom_right[0]]);
        let y = mean([this.top_left[1], this.bottom_right[1]]);
        return [x, y];
    }

    get_points(): number[] {
        return [this.top_left[0], this.top_left[1], this.bottom_right[0], this.bottom_right[1]];
    }

    serialize(): object {
        return {
            'top_left': this.top_left,
            'bottom_right': this.bottom_right,
        };
    }
}

//---------------------------------------------------------------------------------------------------------------------------//

export interface HerdUnit_intf {
    id: number,
    name: string,
    survey_year: string,
}

export class HerdUnit implements HerdUnit_intf {
    id: number;
    name: string;
    survey_year: string; 
    
    constructor(herd_unit: HerdUnit_intf) {
        this.id = herd_unit.id;
        this.name = herd_unit.name;
        this.survey_year = herd_unit.survey_year;
    }
}

//---------------------------------------------------------------------------------------------------------------------------//

export interface Model_intf {
    id: number,
    name: string,
}

export class Model implements Model_intf {
    id: number;
    name: string;

    constructor(model: Model_intf) {
        this.id = model.id;
        this.name = model.name;
    }
}

//---------------------------------------------------------------------------------------------------------------------------//

export interface Image_intf {
    id: number,
    name: string,
    herd_unit: HerdUnit,
    in_training: boolean, 
    url: string,
}

export class Image implements Image_intf {
    id: number;
    name: string;
    herd_unit: HerdUnit;
    in_training: boolean;
    url: string;
  
    constructor(img: Image_intf) {
        this.id = img.id;
        this.name = img.name;
        this.herd_unit = img.herd_unit;
        this.in_training = img.in_training;
        this.url = img.url;
    }
}

//---------------------------------------------------------------------------------------------------------------------------//

export interface Prediction_intf { 
    id: number,
    model: Model,
    dimensions: Box,
    score: number,
    label: number,
}

export class Prediction implements Prediction_intf {
    id: number;
    model: Model;
    dimensions: Box;
    score: number;
    label: number;

    constructor(pred: Prediction_intf) {
        this.id = pred.id;
        this.model = pred.model;
        this.dimensions = pred.dimensions;
        this.score = pred.score;
        this.label = pred.label;    
    }
}

//---------------------------------------------------------------------------------------------------------------------------//

export interface Crop_intf {
    id: number,
    image_id: number,
    name: string,
    dimensions: Box,
    url: string,
}

export class Crop implements Crop_intf {
    id: number;
    image_id: number;
    name: string;
    dimensions: Box;
    url: string;

    constructor(crop: Crop_intf) {
        
        this.id = crop.id;
        this.image_id = crop.image_id;
        this.name = crop.name;
        this.dimensions = crop.dimensions;
        this.url = crop.url;
    }
}

//---------------------------------------------------------------------------------------------------------------------------//

export interface PredictionCrop_intf {
    id: number,
    image_id: number,
    name: string,
    score: number,
    label: number,
    dimensions: Box,
    approved: boolean,
}

export class PredictionCrop implements PredictionCrop_intf {
    id: number;
    image_id: number;
    name: string;
    score: number;
    label: number;
    approved: boolean;
    dimensions: Box;
    url: string;
    
    constructor(predcrop: PredictionCrop_intf, url: string) { 
        this.id = predcrop.id;
        this.image_id = predcrop.image_id;
        this.name = predcrop.name;
        this.score = predcrop.score;
        this.label = predcrop.label;
        this.dimensions = predcrop.dimensions;
        this.approved = predcrop.approved;
        this.url = url;
    }
}
//---------------------------------------------------------------------------------------------------------------------------//

export interface User {
    db_id: number | undefined, 
    status: string | undefined, 
    role: string | undefined, 
    created: Date | undefined, 
    updated: Date | undefined, 
    locale: string | undefined,
    userName: string | undefined, 
}

//---------------------------------------------------------------------------------------------------------------------------//
// Expected structures for data from the API
export interface CropData {
    [crop_id: number]: {
        'crop': Crop_intf,
        'predictions': Prediction_intf[],
    }
}

export interface BatchData {
    [image_id: number]: {
        image: Image_intf,
        predictions: Prediction_intf[],
        approved_predictions: number[] | undefined,
        pred_crops: PredictionCrop_intf[] | undefined,
        crops: CropData | undefined
    }
}

export interface BatchesData {
    [batch_id: number]: BatchData
}

//---------------------------------------------------------------------------------------------------------------------------//

//Structures to be returned upon deserializing

export interface Crops {
    [crop_id: number]: {
        'crop': Crop,
        'predictions': Prediction[],
    }
}

export interface Batch {
    [image_id: number]: {
        image: Image,
        predictions: Prediction[],
        approved_predictions: number[],
        pred_crops: PredictionCrop[],
        crops: Crops,
    };
}

export interface Batches {
    [batch_id: number]: Batch
}
//---------------------------------------------------------------------------------------------------------------------------//

export default {};