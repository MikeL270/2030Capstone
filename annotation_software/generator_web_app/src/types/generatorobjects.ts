// Typescript Class definition analogues for crop_generator objects 
// Author: Michael B. Lance
// Created: April 9, 2025
// Updated: August 8, 2025
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
    name: string;
    created: Date;
    modified: Date;
    uuid: string;
}

export class HerdUnit implements HerdUnit_intf {
    name: string;
    created: Date;
    modified: Date;
    uuid: string;

    
    constructor(herdunit: HerdUnit_intf) {
        this.name = herdunit.name;
        this.created = new Date(herdunit.created);
        this.modified = new Date(herdunit.modified);
        this.uuid = herdunit.uuid;
    }
}

//---------------------------------------------------------------------------------------------------------------------------//

export interface Image_intf {
	name: string;
	in_training: boolean;
	crops_generated: number;
	reviewed_by_user_id: string | undefined;
	opened_by_user_id: string | undefined;
	created: Date;
	modified: Date;
	image_length_px: number;
	image_width_px: number;
	uuid: string;
}

export class Image implements Image_intf {
    name: string;
	in_training: boolean;
	crops_generated: number;
	reviewed_by_user_id: string | undefined;
	opened_by_user_id: string | undefined;
	created: Date;
	modified: Date;
	image_length_px: number;
	image_width_px: number;
	uuid: string;
  
    constructor(img: Image_intf) {
        this.name = img.name;
		this.in_training = img.in_training;
		this.crops_generated = img.crops_generated;
		this.reviewed_by_user_id = img.reviewed_by_user_id;
		this.opened_by_user_id = img.opened_by_user_id;
		this.created = new Date(img.created);
		this.modified = new Date(img.modified);
		this.image_length_px = img.image_length_px;
		this.image_width_px = img.image_width_px;
		this.uuid = img.uuid
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

export interface Role_intf {
    name: string;
    created: Date;
    modified: Date;
    uuid: string;
}

export class Role implements Role_intf {
    name: string;
    created: Date;
    modified: Date;
    uuid: string;

    constructor(role: Role_intf) {
        this.name = role.name;
        this.created = new Date(role.created);
        this.modified = new Date(role.modified);
        this.uuid = role.uuid;
    }
}

//---------------------------------------------------------------------------------------------------------------------------//

export interface User_intf {
    username: string;
    status: string;
    created: Date;
    modified: Date;
    last_login: Date;
    locale: string;
    uuid: string;
    roles: Role_intf[];
}

export class User {
    username: string;
    status: string;
    created: Date;
    modified: Date;
    last_login: Date;
    locale: string;
    roles: Role[];
    uuid: string;

    constructor(usr: User_intf) {
        this.username = usr.username;
        this.status = usr.status;
        this.created = new Date(usr.created);
        this.modified = new Date(usr.modified);
        this.last_login = new Date(usr.last_login);
        this.locale = usr.locale;
        this.roles = [];
        for (const role of usr.roles) this.roles.push(new Role(role));
        this.uuid = usr.uuid;
    }
}

//---------------------------------------------------------------------------------------------------------------------------//

export interface Organization_intf {
    name: string;
    created: Date;
    modified: Date;
    logo_url: string | undefined;
    uuid: string;
}

export class Organization implements Organization_intf {
    name: string;
    created: Date;
    modified: Date;
    logo_url: string | undefined;
    uuid: string;

    constructor(Org: Organization_intf) {
        this.name = Org.name;
        this.created = new Date(Org.created);
        this.modified = new Date(Org.modified);
        this.logo_url = Org.logo_url;
        this.uuid = Org.uuid;
    }
}

//---------------------------------------------------------------------------------------------------------------------------//

export interface Project_intf {
    name: string;
    created: Date;
    modified: Date;
    uuid: string;
}

export class Project implements Project_intf {
    name: string;
    created: Date;
    modified: Date;
    uuid: string;

    constructor(Proj: Project_intf) {
        this.name = Proj.name;
        this.created = new Date(Proj.created);
        this.modified = new Date(Proj.modified);
        this.uuid = Proj.uuid;
    }
}

//---------------------------------------------------------------------------------------------------------------------------//

export interface Schema_intf {
    name: string;
    created: Date;
    modified: Date;
    uuid: string;
}

export class Schema implements Schema_intf {
    name: string;
    created: Date;
    modified: Date;
    uuid: string;

    constructor(Schem: Schema_intf) {
        this.name = Schem.name;
        this.created = new Date(Schem.created);
        this.modified = new Date(Schem.modified);
        this.uuid = Schem.uuid;
    }
}

//---------------------------------------------------------------------------------------------------------------------------//

export interface Label_intf {
    label: number;
    name: string;
    image_link: string;
    created: Date;
    modified: Date;
    uuid: string;
}

export class Label implements Label_intf {
    label: number;
    name: string;
    image_link: string;
    created: Date;
    modified: Date;
    uuid: string;

    constructor(lbl: Label_intf) {
        this.label = lbl.label;
        this.name = lbl.name;
        this.image_link = lbl.image_link;
        this.created = new Date(lbl.created);
        this.modified = new Date(lbl.modified);
        this.uuid = lbl.uuid;
    }
}

//---------------------------------------------------------------------------------------------------------------------------//

export interface Survey_intf {
    survey_year: number;
    name: string;
    additional_info: string;
    created: Date;
    modified: Date;
    uuid: string;
}

export class Survey implements Survey_intf {
    survey_year: number;
    name: string;
    additional_info: string;
    created: Date;
    modified: Date;
    uuid: string;

    constructor(srvy: Survey_intf) {
        this.survey_year = srvy.survey_year;
        this.name = srvy.name;
        this.additional_info = srvy.additional_info;
        this.created = new Date(srvy.created);
        this.modified = new Date(srvy.modified);
        this.uuid = srvy.uuid;
    }
}

//---------------------------------------------------------------------------------------------------------------------------//

export interface Model_intf {
    name: string;
    created: Date;
    modified: Date;
    uuid: string;
}

export class Model implements Model_intf {
    name: string;
    created: Date;
    modified: Date;
    uuid: string;
    constructor(mdl: Model_intf) {
        this.name = mdl.name;
        this.created = new Date(mdl.created);
        this.modified = new Date(mdl.modified);
        this.uuid = mdl.uuid
    }
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