// Typescript Class definition analogues for crop_generator objects 
// Author: Michael B. Lance
// Created: April 9, 2025
// Updated: April 9, 2025
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
            top_left: this.top_left,
            bottom_right: this.bottom_right,
        };
    }
}

//---------------------------------------------------------------------------------------------------------------------------//

export class Image implements CgOBJ {
    id: number | null = null;
    name: string | null = null;
    herd_unit_id: number | null = null;
    in_training: boolean | null = null;
    folder_path: string | null = null;
    //image_data: ImageData | null

    constructor(id: number | null = null, name: string | null = null, herd_unit_id: number | null = null, in_training: boolean | null = null, folder_path: string | null = null) {
        this.id = id;
        this.name = name;
        this.herd_unit_id = herd_unit_id;
        this.in_training = in_training;
        this.folder_path = folder_path;
        
    }
    
    serialize(): object {
        return {
            image_id: this.id,
            image_name: this.name,
            herd_unit_id: this.herd_unit_id,
            folder_path: this.folder_path,
            in_training: this.in_training ? 1 : 0,
        };
    }
}

//---------------------------------------------------------------------------------------------------------------------------//

export class Prediction implements CgOBJ {
    id: number | null = null;
    model_id: number | null = null;
    dimensions: Box | null = null;
    score: number | null = null;
    label: number | null = null;

    constructor(db_id: number | null, model_id: number | null = null, dimensions: Box | null = null, score: number | null = null, label: number | null = null) {
        this.id = db_id;
        this.model_id = model_id;
        this.dimensions = dimensions;
        this.score = score;
        this.label = label;    
    }


    serialize(): object {
        return {
            pred_id: this.id,
            model_id: this.model_id,
            dimensions: this.dimensions,
            score: this.score,
            label: this.label,
        }
    }
}

//---------------------------------------------------------------------------------------------------------------------------//

export class Crop extends Image implements CgOBJ {
    image_id: number | null = null;
    crop_dimensions: Box | null = null;

    constructor(db_id: number | null = null, image_id: number | null = null, name: string | null = null, diemsons: Box | null = null) {
        super(db_id, name);
        this.image_id = image_id;
        this.crop_dimensions = diemsons;
    }

    serialize(): object {
        return {}
    }
}