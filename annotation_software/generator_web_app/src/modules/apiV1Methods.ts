// Methods for interacting with the version 1 of the crop generator API 
// Author: Michael B. Lance
// Created: April 20, 2025
// Updated: June 25, 2025
//---------------------------------------------------------------------------------------------------------------------------//

import _ from 'lodash';
import { Box, Image, Prediction, Crop, PredictionCrop } from '@/types/generatorobjects.ts';
import type { Prediction_intf,  PredictionCrop_intf, CropData, BatchData, BatchesData, 
              Crops, Batch, Batches } from '@/types/generatorobjects.ts';
import { useToast } from 'vue-toastification'

//const api_url: string = 'http://192.168.0.3:8000/api/v1'; //"production"
const api_url: string = 'http://192.168.0.3:5000/api/v1';
const uh_oh: string = 'You did something wrong! status:';

const toast = useToast()


//---------------------------------------------------------------------------------------------------------------------------//
// User authentication
// TODO: Return a promise of an image object
export async function authUser(external_id: string): Promise<any> {   
    try {
        const response = await fetch(`${api_url}/authenticate`, {
            method: 'POST',
            headers: {
                 'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'external-id': external_id
            }),
            credentials: 'include',
        }); 
        if (!response.ok) {
            throw new Error(` ${response.status}`);
        }
        return await response.json()
    } catch (error) {
        console.error("Error: ", error)
    }
}

export async function checkAuth(): Promise<any> {
    try {
        const response = await fetch(`${api_url}/check_auth`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }, 
            credentials: 'include',
        });
        if (!response.ok) {
            throw new Error(` ${response.status}`);
        }
        return await response.json();
    } catch(error) {
        console.error("Error: ", error)
    }
}

//---------------------------------------------------------------------------------------------------------------------------//
// Deserialization functions

function deserialize_predictions(data: Prediction_intf[]): Prediction[] {
    var predictions = [];
    for (const pred of data) {
        predictions.push(new Prediction(pred));
    }
    return predictions
}

function deserialize_batch(data: BatchData): Batch {
    var batch: Batch = {};
    
    for (const image_id in data) {
        const image = data[image_id]['image']
        const predictions: Prediction_intf[] = data[image_id]['predictions'];
        batch[+image_id] = {
        'image': new Image(image),
        'predictions': deserialize_predictions(predictions),
        'approved_predictions': [],
        'pred_crops': [],
        'crops': []
        }
    };
    return batch;
}

function deserialize_batches (data: BatchesData): Batches {
    var batches = {} as Batches
 
    for (const batch_id in data) {
        batches[batch_id] = deserialize_batch(data[batch_id] as BatchData);
    };
    return batches
}

function deserialize_pred_crops(pred_crops_data: PredictionCrop_intf[], batch_id: number, image_id: number) : PredictionCrop[] {
    var pred_crops = []
    
    for (const pred_crop of pred_crops_data) {
  
        pred_crops.push( new PredictionCrop
            (pred_crop,
             `${api_url}/batches/${batch_id}/images/${image_id}/pred_crops/${pred_crop.id}`
        ));
    };
    return pred_crops;
}

function deserialize_crops(crops_data: CropData) : Crops {
    var crops = {} as Crops;
    for (const crop_num in crops_data) {
        var crop_data = crops_data[crop_num]['crop'];
        var prediction_data = crops_data[crop_num]['predictions'];
        var crop_id = crop_data['id'];
        
        crops[crop_id] = {
            'crop' : new Crop(crop_data),
            'predictions': deserialize_predictions(prediction_data)
        };
    };
    return crops;
}

//---------------------------------------------------------------------------------------------------------------------------//
// GET requests:

export async function testApi(): Promise<string> {
    try {
        const response = await(fetch(`${api_url}/test`, {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
        }));

        if (!response.ok) {
            throw new Error(`${uh_oh} ${response.status}`);
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Error:", error);
        toast.error(`${error}`);
        throw error;
    }
};

export async function getBatch(batch_id: number): Promise<Batches> {
// Note: The api always returns a batch with its ID so Batches is always the return type
 try {
    const response = await(fetch(`${api_url}/batches/${batch_id}`, {
        method: 'GET',
        credentials: 'include',
        headers: {
             'Content-Type': 'application/json',
        },
    }));
    if (!response.ok) {
        throw new Error(` ${response.status}`);
    }
    const data = await response.json() as BatchesData;
    const batch = deserialize_batches(data);
    return batch;
 } catch (error) {
    console.error("Error: ", error);
    toast.error(`${error}`);;
    throw error;
 }
};

export async function getBatches(): Promise<Batches> {
    try { 
        const response = await fetch(`${api_url}/batches`, {
            method: 'GET',
            credentials: 'include',
            headers: {
                 'Content-Type': 'application/json',
            },
        }); 
        if (!response.ok) {
            throw new Error(` ${response.status}`);
        }
        const data = await response.json() as BatchData;
        const batches = deserialize_batch(data);   
        return batches;
    } catch (error) {
        console.error("Error: ", error);
        toast.error(`${error}`);;
        throw error;
    }
}

export async function getBatchIds(): Promise<number[]> {
    try {
       const response = await fetch(`${api_url}/batches/ids`, {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
       });
       if (!response.ok) {
        throw new Error(` ${response.status}`)
       }
       const data: unknown = await response.json();
       return data as number[];
    } catch (error) {
        console.error("Error: ", error);
        toast.error(`${error}`);;
        throw error;
    }
}

interface Schema {
    [class_name: string]: {
        'label': number,
        'image_link': string,
    }
}

export async function getSchema(): Promise<Schema> {
    try {
        const response = await fetch(`${api_url}/schema`, {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) throw new Error(`${uh_oh} ${response.status}`);

        return await response.json() as Schema;

    } catch (error: any) {
        console.error("There was an error fetching the data:", error);
        toast.error(`${error}`);;
        throw error;
    }
}
//---------------------------------------------------------------------------------------------------------------------------//
// POST requests:

export async function createBatch(params: Record<string, number>): Promise<Batches> {
    // Note: The api always returns a batch with its ID so Batches is always the return type
    try {
        const response = await fetch(`${api_url}/images/create_batch`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(params),
        });

        if (!response.ok) {
            throw new Error(`${uh_oh} ${response.status}`)
        };

        const data = await response.json() as BatchesData;
        const batches = deserialize_batches(data);

        return batches;
    } catch (error: any) {
        console.error("There was an error fetching the data:", error);
        toast.error(`${error}`);
        throw error;
    }
}

export async function createPredCrops(batch_id:number, image_id: number): Promise<PredictionCrop[]> {
    try {
        const response = await(fetch(`${api_url}/batches/${batch_id}/images/${image_id}/create_pred_crops`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                 
            },
        }));
        if (!response.ok) {
            throw new Error(`${uh_oh} ${response.status}`);
        }
        const data = await response.json() as PredictionCrop_intf[];
        const crops = deserialize_pred_crops(data, batch_id, image_id);
        return crops;
    } catch (error: any) {
        console.error("Error", error);
        toast.error(`${error}`);;
        throw error;
    }
 }

 export async function createFullCrops(batch_id: number, image_id: number, crop_size: number): Promise<any> {
    
    try {
        const response = await(fetch(`${api_url}/batches/${batch_id}/images/${image_id}/create_crops`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                 
            },
            body: JSON.stringify({'crop_size': crop_size}),
        }));
        if (!response.ok) {
            throw new Error(`${uh_oh} ${response.status}`)
        }
        const data = await response.json() as CropData;
        const crops = deserialize_crops(data);
        return crops;
    } catch (error: any) {
        console.error('Error', error);
    }
 }

//---------------------------------------------------------------------------------------------------------------------------//
// PUT requests

export async function approvePredictions(approved_predictions: number[], batch_id: number, image_id: number) : Promise<any> {
    try {
        const response = await(fetch(`${api_url}/batches/${batch_id}/images/${image_id}/approve_predictions`, {
            method: 'PUT',
            credentials: 'include',
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

// Delete requests

export async function deleteBatch(batch_id: number) : Promise<any> {
    try {
        const response = await(fetch(`${api_url}/batches/${batch_id}`, {
            method: 'DELETE',
            credentials: 'include',
            headers: {
                 
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