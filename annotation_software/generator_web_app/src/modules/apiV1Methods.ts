// Methods for approving predictions in the annotate vue component
// Author: Michael B. Lance
// Created: April 20, 2025
// Updated: April 22, 2025
//---------------------------------------------------------------------------------------------------------------------------//

import _ from 'lodash';
import { Box, Image, Prediction, Crop } from '../types/generatorobjects';

const api_url: string = 'http://127.0.0.1:5000/api/v1/';

//---------------------------------------------------------------------------------------------------------------------------//

interface PredictionData {
    pred_id: number,
    model_id: number,
    dimensions: number[],
    score: number,
    label: number,

}

//---------------------------------------------------------------------------------------------------------------------------//

export async function testApi(): Promise<any> {
    try {
        const response = await(fetch(`${api_url}test`))

        if (!response.ok) {
            throw new Error('You did something wrong! status ${response.status}')
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error("There was an error fetching the data:", error)
        throw error;
    }
}

//---------------------------------------------------------------------------------------------------------------------------//

async function fetchBatch(params: Record<string, any>): Promise<JSON> {
    try {
        const response = await fetch(`${api_url}create_batch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(params),
        });

        if (!response.ok) {
            throw new Error(`You did something wrong! status ${response.status}`)
        }

        const data  = await response.json();
        return data;
    } catch (error: any) {
        console.error("There was an error fetching the data:", error);
        throw error;
    }
}

//---------------------------------------------------------------------------------------------------------------------------//

export async function createBatch(params: Record<string, any>): Promise<any> {
    // This hurt my soul. never delete this because remaking it hurts
    const data = await fetchBatch(params);
    var batch_id = +Object.values(data)[0];
    var batch_data = Object.values(data)[1];
    var batch: { [key: string]: any} = {};
    batch[batch_id] = {}
    for (const image_id in batch_data) {
        const image = batch_data[image_id]['image']
        batch[batch_id][image_id] = {}
        batch[batch_id][image_id]['image'] = new Image(
            image['image_id'],
            image['image_name'],
            image['herd_unit_id'],
            image['in_training'],
            image['folder_path'],
            );
        batch[batch_id][image_id]['predictions'] = [];
        const predictions: PredictionData[] = batch_data[image_id]['predictions'];
        for (const pred of predictions) {
            batch[batch_id][image_id]['predictions'].push( new Prediction(
                pred['pred_id'],
                pred['model_id'],
                new Box([pred['dimensions'][0], pred['dimensions'][1]], 
                        [pred['dimensions'][2], pred['dimensions'][3]]
                    ),
                pred['score'],
                pred['label'],
            ))       
        }
    }
    return batch;
}

//---------------------------------------------------------------------------------------------------------------------------//

export async function deleteBatch(batch_id: number): Promise<any> {
    try {
        const response = await fetch(`${api_url}batches/${batch_id}`, {
            method: 'DELETE',
        });
        if (!response.ok) {
            throw new Error('You did something wrong! stat')
        }
        const data = response.json();
        return data;
    } catch (error: any) {
        console.error("There was an error deleting the data:", error);
        throw error;
    }
}

//---------------------------------------------------------------------------------------------------------------------------//

export default{};