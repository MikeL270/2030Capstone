// Methods for approving predictions in the annotate vue component
// Author: Michael B. Lance
// Created: April 20, 2025
// Updated: May 28, 2025
//---------------------------------------------------------------------------------------------------------------------------//

import _ from 'lodash';
import { Box, Image, Prediction, Crop, PredictionCrop } from '../types/generatorobjects';
import type { Batch, Batches, BatchData, PredCropData, PredictionData, CropsData} from '../types/interfaces';

const api_url: string = 'http://127.0.0.1:5000/api/v1';
const uh_oh: string = 'You did something wrong! status:';
const test_token: string = "h5puC2EbTcYeP7lA7oq9qzXyr0Uoq01uHO9HV7EEJy3fgHT9EbkRZ3O5yC5AYpP3";

//---------------------------------------------------------------------------------------------------------------------------//
// Deserialization functions

function deserialize_predictions(data: PredictionData[]): Prediction[] {
    var predictions = [];
    for (const pred of data) {
        predictions.push( new Prediction(
            pred['pred_id'],
            pred['model_id'],
            new Box(pred['dimensions']['top_left'], 
                    pred['dimensions']['bottom_right'],
                ),
            pred['score'],
            pred['label'],
    ));
    }
    return predictions
}

function deserialize_batch(data: Record<string, any>): Record<string, any> {
    var batch_id = +Object.keys(data)[0];
    var batch_data = Object.values(data)[0];
    var batch: Batch = {};
    var batches: Batches = {};
    batches[batch_id] = batch;

    for (const image_id in batch_data) {
        const image = batch_data[image_id]['image']
        const predictions: PredictionData[] = batch_data[image_id]['predictions'];
        batch[+image_id] = {
        'image': new Image(
            image['image_id'],
            image['image_name'],
            image['herd_unit_id'],
            image['in_training'],
            image['url'],
        ),
        'predictions': deserialize_predictions(predictions),
        'approved_predictions': [],
        'pred_crops': [],
        'crops': []
    }
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

function deserialize_crops(crops_data: Record<string, any>, batch_id: number, image_id: number) : CropsData {
    var crops = {} as CropsData;
    for (const crop_num in crops_data) {
        var crop_data = crops_data[crop_num]['crop'];
        var prediction_data = crops_data[crop_num]['predictions'];
        console.log(crops_data[crop_num])
        var crop_id = crop_data['crop_id'];
        
        crops[crop_id] = {
            'crop' : new Crop(
                crop_data['crop_id'],
                crop_data['image_id'],
                crop_data['name'],
                new Box(
                    crop_data['dimensions']['top_left'],
                    crop_data['dimensions']['bottom_right']
                ),
            `${api_url}/batches/${batch_id}/images/${image_id}/crops/${crops_data['crop_id']}`
        ),
        'predictions': deserialize_predictions(prediction_data)
    }
    };
    return crops;
}

//---------------------------------------------------------------------------------------------------------------------------//
// GET requests:

export async function testApi(): Promise<any> {
    try {
        const response = await(fetch(`${api_url}/test`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': test_token
            },
            
        }));

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
    const response = await(fetch(`${api_url}/batches/${batch_id}`, {
        method: 'GET',
        headers: {
            'Authorization': test_token,
        },
    }));
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
        const response = await(fetch(`${api_url}/batches`, {
            method: 'GET',
            headers: {
                'Authorization': test_token,
            },
        })); 
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

//---------------------------------------------------------------------------------------------------------------------------//
// POST requests:

export async function createBatch(params: Record<string, any>): Promise<any> {
    // This hurt my soul. never delete this because remaking it hurts
    try {
        const response = await fetch(`${api_url}/images/create_batch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': test_token,
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
                'Authorization': test_token,
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

 export async function createFullCrops(batch_id: number, image_id: number, crop_size: number): Promise<any> {
    
    try {
        const response = await(fetch(`${api_url}/batches/${batch_id}/images/${image_id}/create_crops`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': test_token,
            },
            body: JSON.stringify({'crop_size': crop_size}),
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
                'Authorization': test_token,
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
            headers: {
                'Authorization': test_token,
            },
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