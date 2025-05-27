// Methods for approving predictions in the annotate vue component
// Author: Michael B. Lance
// Created: April 20, 2025
// Updated: May 14, 2025
//---------------------------------------------------------------------------------------------------------------------------//

import _ from 'lodash';
import { Box, Image, Prediction, Crop, PredictionCrop } from '../types/generatorobjects';
import type { Batch, Batches, BatchData, PredCropData, PredictionData} from '../types/interfaces';

const api_url: string = 'http://192.168.0.3:5000/api/v1';
const uh_oh: string = 'You did something wrong! status:';

//---------------------------------------------------------------------------------------------------------------------------//
// Deserialization functions

function deserialize_batch(data: Record<string, any>): Record<string, any> {
    var batch_id = +Object.keys(data)[0];
    var batch_data = Object.values(data)[0];
    var batch: Batch = {};
    var batches: Batches = {};
    batches[batch_id] = batch;

    for (const image_id in batch_data) {
        const image = batch_data[image_id]['image']
        const img_id_num = +image_id;
        batch[img_id_num] = {
        
        'image': new Image(
            image['image_id'],
            image['image_name'],
            image['herd_unit_id'],
            image['in_training'],
            image['url'],
        ),
        'predictions': [],
        'approved_predictions': [],
        'pred_crops': []
    }
    const predictions: PredictionData[] = batch_data[image_id]['predictions'];
    for (const pred of predictions) {
        batch[img_id_num]['predictions'].push( new Prediction(
            pred['pred_id'],
            pred['model_id'],
            new Box(pred['dimensions']['top_left'], 
                    pred['dimensions']['bottom_right'],
                ),
            pred['score'],
            pred['label'],
        ));       
    };
    };
    batches[batch_id] = batch;
    return batches;
}

function deserialize_pred_crops(crops_data: Record<string, any>, batch_id: number, image_id: number) : Record<string, any> {
    var pred_crops = []
    
    for (const crop_id in crops_data) {
        const crop_data = crops_data[crop_id];
  
        pred_crops.push( new PredictionCrop(
            crop_data['pred_crop_id'],
            crop_data['image_id'],
            crop_data['score'],
            crop_data['label'],
            new Box(
                crop_data['dimensions']['top_left'],
                crop_data['dimensions']['bottom_right']
            ),
            `${api_url}/batches/${batch_id}/images/${image_id}/pred_crops/${crop_data['pred_crop_id']}`
            )
        );
    };
    return pred_crops;
}

function deserialize_crops(crops_data: Record<string, any>, batch_id: number, image_id: number) : Record<string, any> {
    var crops = []
    for (const crop_id in crops_data) {
        var crop_data = crops_data[crop_id];
        crops.push( new Crop(
            crop_data['crop_id'],
            crop_data['image_id'],
            crop_data['name'],
            new Box(
                crop_data['dimensions']['top_left'],
                crop_data['dimensions']['bottom_right']
            ),
            `${api_url}/batches/${batch_id}/images/${image_id}/crops/${crops_data['crop_id']}`
        )
        );
    };
    return crops;
}

//---------------------------------------------------------------------------------------------------------------------------//
// GET requests:

export async function testApi(): Promise<any> {
    try {
        const response = await(fetch(`${api_url}/test`))

        if (!response.ok) {
            throw new Error(`${uh_oh} ${response.status}`);
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Error:", error);
        throw error;
    }
};

export async function getBatch(batch_id: number): Promise<any> {
 try {
    const response = await(fetch(`${api_url}/batches/${batch_id}`));
    if (!response.ok) {
        throw new Error(` ${response.status}`);
    }
    const data = await response.json() as Record<string, BatchData>;
    const batches = deserialize_batch(data);
    return batches;
 } catch (error) {
    console.error("Error: ", error);
 }
};

export async function getBatches(): Promise<any> {
    try { 
        const response = await(fetch(`${api_url}/batches`)); 
        if (!response.ok) {
            throw new Error(` ${response.status}`);
        }
        const data = await response.json() as Record<string, BatchData>;
        console.log(data)
        const batches = deserialize_batch(data);   
        return batches;
    } catch (error) {
        console.error("Error: ", error);
    }
}

export async function get_pred_crop(): Promise<any> {
    try {
        

    } catch (error) {
        console.error("Error: " + error)
    }
}

//---------------------------------------------------------------------------------------------------------------------------//
// POST requests:

export async function createBatch(params: Record<string, any>): Promise<any> {
    // This hurt my soul. never delete this because remaking it hurts
    try {
        const response = await fetch(`${api_url}/images/create_batch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(params),
        });

        if (!response.ok) {
            throw new Error(`${uh_oh} ${response.status}`)
        };

        const data = await response.json() as Record<string, BatchData>;
        const batches = deserialize_batch(data);

        return batches;
    } catch (error: any) {
        console.error("There was an error fetching the data:", error);
        throw error;
    }
}

export async function createPredCrops(batch_id:number, image_id: number): Promise<any> {
    try {
        const response = await(fetch(`${api_url}/batches/${batch_id}/images/${image_id}/create_pred_crops`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        }));
        if (!response.ok) {
            throw new Error(`${uh_oh} ${response.status}`);
        }
        const data = await response.json() as Record<string, any>;
        const crops = deserialize_pred_crops(data, batch_id, image_id);
        return crops;
    } catch (error: any) {
        console.error("Error", error);
    }
 }

 export async function createFullCrops(params: Record<string, any>, batch_id: number, image_id: number): Promise<any> {
    try {
        const response = await(fetch(`${api_url}/batches/${batch_id}/images/${image_id}/create_crops`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(params),
        }));
        if (!response.ok) {
            throw new Error(`${uh_oh} ${response.status}`)
        }
        const data = await response.json() as Record<string, any>;
        const crops = deserialize_crops(data, batch_id, image_id);
        return crops;
    } catch (error: any) {
        console.error('Error', error);
    }
 }

//---------------------------------------------------------------------------------------------------------------------------//
// PUT request

export async function approvePredictions(approved_predictions: Prediction[], batch_id: number, image_id: number) : Promise<any> {
    try {
        const response = await(fetch(`${api_url}/batches/${batch_id}/images/${image_id}/approve_predictions`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(approved_predictions),
        }));
        if (!response.ok) {
            throw new Error(`${uh_oh} ${response.status}`)
        }
    } catch (error: any) {
        console.error('Error', error);
    }
}

//---------------------------------------------------------------------------------------------------------------------------//

export async function deleteBatch(batch_id: number) : Promise<any> {
    try {
        const response = await(fetch(`${api_url}/batches/${batch_id}`, {
            method: 'DELETE',
        }));

        if (!response.ok) {

            throw new Error(`${uh_oh} ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error: any) {
        console.error("Error:", error);
        throw error;
    }
}

//---------------------------------------------------------------------------------------------------------------------------//

export default{};