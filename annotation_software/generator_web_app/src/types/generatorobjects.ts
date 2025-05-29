// Typescript Class definition analogues for crop_generator objects 
// Author: Michael B. Lance
// Created: April 9, 2025
// Updated: May 28, 2025
//---------------------------------------------------------------------------------------------------------------------------//

import { mean } from 'lodash';

//---------------------------------------------------------------------------------------------------------------------------//

interface CgOBJ {
    serialize(): void;
}

//---------------------------------------------------------------------------------------------------------------------------//

export class Box implements CgOBJ {
    top_left: number[];
    bottom_right: number[];
    constructor (top_left: number[], bottom_right: number[]) {
        this.top_left = top_left;
        this.bottom_right = bottom_right;
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

export class Image implements CgOBJ {
    id: number | undefined = undefined;
    name: string | undefined = undefined;
    herd_unit_id: number | undefined = undefined;
    in_training: boolean | undefined = undefined;
    url: string | undefined = undefined;
  

    constructor(id: number | undefined = undefined, name: string | undefined = undefined, herd_unit_id: number | undefined = undefined, 
        in_training: boolean | undefined = undefined, url: string | undefined = undefined) {
        this.id = id;
        this.name = name;
        this.herd_unit_id = herd_unit_id;
        this.in_training = in_training;
        this.url = url;
    }
    
    serialize(): object {
        return {
            'image_id': this.id,
            'image_name': this.name,
            'herd_unit_id': this.herd_unit_id,
            'url': this.url,
            'in_training': this.in_training ? 1 : 0,
        };
    }
}

//---------------------------------------------------------------------------------------------------------------------------//

export class Prediction implements CgOBJ {
    id: number | undefined = undefined;
    model_id: number | undefined = undefined;
    dimensions: Box | undefined = undefined;
    score: number | undefined = undefined;
    label: number | undefined = undefined;

    constructor(db_id: number | undefined, model_id: number | undefined = undefined, dimensions: Box | undefined = undefined, 
        score: number | undefined = undefined, label: number | undefined = undefined) {
        this.id = db_id;
        this.model_id = model_id;
        this.dimensions = dimensions;
        this.score = score;
        this.label = label;    
    }


    serialize(): object {
        return {
            'pred_id': this.id,
            'model_id': this.model_id,
            'dimensions': this.dimensions,
            'score': this.score,
            'label': this.label,
        }
    }
}

//---------------------------------------------------------------------------------------------------------------------------//

export class Crop extends Image implements CgOBJ {
    image_id: number | undefined = undefined;
    crop_dimensions: Box | undefined = undefined;

    constructor(db_id: number | undefined = undefined, image_id: number | undefined = undefined, 
        name: string | undefined = undefined, diemsons: Box | undefined = undefined, url: string | undefined = undefined) {
        super(db_id, name);
        this.image_id = image_id;
        this.crop_dimensions = diemsons;
        this.url = url;
       
    }

    serialize(): object {
        return {
            'crop_id': this.id,
            'image_id': this.image_id,
            'crop_name': this.name,
            'herd_unit_id': this.herd_unit_id,
            'url': this.url,
        }
    }
}

//---------------------------------------------------------------------------------------------------------------------------//

export class PredictionCrop extends Crop implements CgOBJ {
    pred_crop_id: number | undefined = undefined;
    image_id: number | undefined = undefined;
    score: number | undefined = undefined;
    label: number | undefined = undefined;
    dimensions: Box | undefined = undefined;
    url: string | undefined = undefined;
    approved: boolean = false;

    constructor(pred_crop_id: number | undefined = undefined, image_id: number | undefined = undefined, score: number | undefined = undefined,
                label: number | undefined = undefined, dimensions: Box | undefined = undefined, url: string | undefined = undefined) {
        super(); // Super is required for child classes because reasons.
        this.pred_crop_id = pred_crop_id;
        this.image_id = image_id;
        this.score = score;
        this.label = label;
        this.dimensions = dimensions;
        this.url = url;
        this.approved = false;
    }

    serialize(): object {
        return {
            'pred_crop_id': this.pred_crop_id,
            'image_id': this.image_id,
            'score': this.score,
            'label': this.label,
            'dimensions': this.dimensions?.serialize(),
        }
    }
}

//---------------------------------------------------------------------------------------------------------------------------//

export default {};