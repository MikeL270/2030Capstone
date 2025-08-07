// Methods for interacting with the version 1 of the crop generator API 
// Author: Michael B. Lance
// Created: April 20, 2025
// Updated: August 6, 2025
//---------------------------------------------------------------------------------------------------------------------------//

import _ from 'lodash';
import { Box, Image, Prediction, Crop, PredictionCrop, Project, Organization, User, Schema,
         Label, HerdUnit, Survey, Model
        } from '@/types/generatorobjects.ts';
import type { Prediction_intf,  PredictionCrop_intf, CropData, BatchData, BatchesData, 
              Crops, Batch, Batches, User_intf
            } from '@/types/generatorobjects.ts';
import { useToast } from 'vue-toastification'

//const api_url: string = 'http://pronghorn-count.arcc.uwyo.edu/api/v1'; //"production"
const api_url: string = 'http://testing.lancecomputer.com:5000/api/v1';
const uh_oh: string = 'status:';

const toast = useToast()

//---------------------------------------------------------------------------------------------------------------------------//
// User authentication
export async function authUser(external_id: string): Promise<User | undefined> {   
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
        if (!response.ok) throw new Error(`${uh_oh} ${await response.text()}`)
        const user = new User(await response.json() as User_intf);
        return user;
    } catch (error) {
        console.error("Error: ", error)
        return undefined;
    }
}

export async function checkAuth(): Promise<boolean> {
    try {
        const response = await fetch(`${api_url}/check_auth`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }, 
            credentials: 'include',
        });
        if (!response.ok) throw new Error(`${uh_oh} ${await response.text()}`)
        else return true;
    } catch (error) {
        console.error("Error: ", error);
        return false;
    }
}

export async function getCurrentUser(): Promise<User | undefined> {
    try {
        const response = await fetch(`${api_url}/users/get_current_user`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
        });
        if (!response.ok) throw new Error(`${uh_oh} ${await response.text()}`)
        const user = new User (await response.json() as User_intf);
        return user;
    } catch (error) {
        console.error("Error: ", error)
        return undefined;
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
// Organization Crud

export async function getUserOrganizations(): Promise<Organization[] | undefined> {
    try {
        const response = await fetch(`${api_url}/request/organizations/all`, {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        if (!response.ok) throw new Error(`${uh_oh} ${await response.text()}`)
        const resp = await response.json();
        var organizations = [];
        for (const organization of resp) organizations.push(new Organization(JSON.parse(organization)));
        return organizations;
    } catch (error: any) {
        console.error("There was an error fetching the data:", error);
        toast.error(`${error}`);
        return undefined;
    }
}

//---------------------------------------------------------------------------------------------------------------------------//
// Role Crud

//---------------------------------------------------------------------------------------------------------------------------//
//  User Crud

//---------------------------------------------------------------------------------------------------------------------------//
// Project Crud

export async function getProjects(): Promise<Project[] | undefined> {
    try {
        const response = await fetch(`${api_url}/request/projects/all`, {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        if (!response.ok) throw new Error(`${uh_oh} ${await response.text()}`)
        const resp = await response.json();
        var projects = [];
        for (const project of resp) projects.push(new Project(JSON.parse(project)));
        return projects;
    } catch (error: any) {
        console.error("There was an error fetching the data:", error);
        toast.error(`${error}`);
        return undefined;
    }
}

//---------------------------------------------------------------------------------------------------------------------------//
// Schema Crud

export async function getProjectSchemas(project_id: string | undefined): Promise<Schema[] | undefined> {
    try {
        const response = await fetch(`${api_url}/request/projects/${project_id}/schemas/all`, {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        if (!response.ok) throw new Error(`${uh_oh} ${await response.text()}`)
        const resp = await response.json();
        var schemas = [];
        for (const schema of resp) schemas.push(new Schema(JSON.parse(schema)));
        return schemas;
    } catch (error: any) {
        console.error("There was an error fetching the data:", error);
        toast.error(`${error}`);
        return undefined;
    }
}

//---------------------------------------------------------------------------------------------------------------------------//
// Label Crud

export async function getSchemaLabels(project_id: string | undefined, schema_id: string | undefined): Promise<Label[] | undefined> {
    try {
        const response = await fetch(`${api_url}/request/projects/${project_id}/schemas/${schema_id}/labels/all`, {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        if (!response.ok) throw new Error(`${uh_oh} ${await response.text()}`)
        const resp = await response.json();
        var labels = [];
        for (const label of resp) labels.push(new Label(JSON.parse(label)));
        return labels;
    } catch (error: any) {
        console.error("There was an error fetching the data:", error);
        toast.error(`${error}`);
        return undefined;
    }
}

//---------------------------------------------------------------------------------------------------------------------------//
// Herd Unit Crud

export async function getProjectHerdUnits(project_id: string | undefined): Promise<HerdUnit[] | undefined> {
    try {
        const response = await fetch(`${api_url}/request/projects/${project_id}/herd_units/all`, {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        if (!response.ok) throw new Error(`${uh_oh} ${await response.text()}`)
        const resp = await response.json();
        var herd_units = [];
        for (const herd_unit of resp) herd_units.push(new HerdUnit(JSON.parse(herd_unit)));
        return herd_units;
        
    } catch (error: any) {
        console.error("There was an error fetching the data:", error);
        toast.error(`${error}`);
        return undefined;
    }
}

//---------------------------------------------------------------------------------------------------------------------------//
// Model Crud

export async function getProjectModels(project_id: string | undefined): Promise<Model[] | undefined> {
    try {
        const response = await fetch(`${api_url}/request/projects/${project_id}/models/all`, {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        if (!response.ok) throw new Error(`${uh_oh} ${await response.text()}`)
        const resp = await response.json();
        var models = [];
        for (const model of resp) models.push(new Model(JSON.parse(model))); 
        return models;
    } catch (error: any) {
        console.error("There was an error fetching the data:", error);
        toast.error(`${error}`);
        return undefined;
    }
}

//---------------------------------------------------------------------------------------------------------------------------//
// Survey Crud

export async function getProjectSurveys(project_id: string | undefined): Promise<Survey[] | undefined> {
    try {
        const response = await fetch(`${api_url}/request/projects/${project_id}/surveys/all`, {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
         });
        if (!response.ok) throw new Error(`${uh_oh} ${await response.text()}`)
        const resp = await response.json();
        var surveys = [];
        for (const survey of resp) surveys.push(new Survey(JSON.parse(survey)));
        return surveys;
    } catch (error: any) {
        console.error("There was an error fetching the data:", error);
        toast.error(`${error}`);
        return undefined;
    }
}

//---------------------------------------------------------------------------------------------------------------------------//
// 

//---------------------------------------------------------------------------------------------------------------------------//
// GET requests:

// export async function testApi(): Promise<string> {
//     try {
//         const response = await(fetch(`${api_url}/test`, {
//             method: 'GET',
//             credentials: 'include',
//             headers: {
//                 'Content-Type': 'application/json',
//             },
//         }));

//         if (!response.ok) {
//             throw new Error(`${uh_oh} ${response.status}`);
//         }

//         const data = await response.json();
//         return data;
//     } catch (error) {
//         console.error("Error:", error);
//         toast.error(`${error}`);
//         throw error;
//     }
// };

// export async function getBatch(batch_id: number): Promise<Batches> {
// // Note: The api always returns a batch with its ID so Batches is always the return type
//  try {
//     const response = await(fetch(`${api_url}/batches/${batch_id}`, {
//         method: 'GET',
//         credentials: 'include',
//         headers: {
//              'Content-Type': 'application/json',
//         },
//     }));
//     if (!response.ok) {
//         throw new Error(` ${response.status}`);
//     }
//     const data = await response.json() as BatchesData;
//     const batch = deserialize_batches(data);
//     return batch;
//  } catch (error) {
//     console.error("Error: ", error);
//     toast.error(`${error}`);;
//     throw error;
//  }
// };

// export async function getBatches(): Promise<Batches> {
//     try { 
//         const response = await fetch(`${api_url}/batches`, {
//             method: 'GET',
//             credentials: 'include',
//             headers: {
//                  'Content-Type': 'application/json',
//             },
//         }); 
//         if (!response.ok) {
//             throw new Error(` ${response.status}`);
//         }
//         const data = await response.json() as BatchData;
//         const batches = deserialize_batch(data);   
//         return batches;
//     } catch (error) {
//         console.error("Error: ", error);
//         toast.error(`${error}`);;
//         throw error;
//     }
// }

// export async function getBatchIds(): Promise<number[]> {
//     try {
//        const response = await fetch(`${api_url}/batches/ids`, {
//             method: 'GET',
//             credentials: 'include',
//             headers: {
//                 'Content-Type': 'application/json',
//             },
//        });
//        if (!response.ok) {
//         throw new Error(` ${response.status}`)
//        }
//        const data: unknown = await response.json();
//        return data as number[];
//     } catch (error) {
//         console.error("Error: ", error);
//         toast.error(`${error}`);;
//         throw error;
//     }
// }


// //---------------------------------------------------------------------------------------------------------------------------//
// // POST requests:

// export async function createBatch(params: Record<string, number>): Promise<Batches> {
//     // Note: The api always returns a batch with its ID so Batches is always the return type
//     try {
//         const response = await fetch(`${api_url}/images/create_batch`, {
//             method: 'POST',
//             credentials: 'include',
//             headers: {
//                 'Content-Type': 'application/json',
//             },
//             body: JSON.stringify(params),
//         });

//         if (!response.ok) {
//             throw new Error(`${uh_oh} ${response.status}`)
//         };

//         const data = await response.json() as BatchesData;
//         const batches = deserialize_batches(data);

//         return batches;
//     } catch (error: any) {
//         console.error("There was an error fetching the data:", error);
//         toast.error(`${error}`);
//         throw error;
//     }
// }

// export async function createPredCrops(batch_id:number, image_id: number): Promise<PredictionCrop[]> {
//     try {
//         const response = await(fetch(`${api_url}/batches/${batch_id}/images/${image_id}/create_pred_crops`, {
//             method: 'POST',
//             credentials: 'include',
//             headers: {
//                 'Content-Type': 'application/json',
                 
//             },
//         }));
//         if (!response.ok) {
//             throw new Error(`${uh_oh} ${response.status}`);
//         }
//         const data = await response.json() as PredictionCrop_intf[];
//         const crops = deserialize_pred_crops(data, batch_id, image_id);
//         return crops;
//     } catch (error: any) {
//         console.error("Error", error);
//         toast.error(`${error}`);;
//         throw error;
//     }
//  }

//  export async function createFullCrops(batch_id: number, image_id: number, crop_size: number): Promise<any> {
    
//     try {
//         const response = await(fetch(`${api_url}/batches/${batch_id}/images/${image_id}/create_crops`, {
//             method: 'POST',
//             credentials: 'include',
//             headers: {
//                 'Content-Type': 'application/json',
                 
//             },
//             body: JSON.stringify({'crop_size': crop_size}),
//         }));
//         if (!response.ok) {
//             throw new Error(`${uh_oh} ${response.status}`)
//         }
//         const data = await response.json() as CropData;
//         const crops = deserialize_crops(data);
//         return crops;
//     } catch (error: any) {
//         console.error('Error', error);
//     }
//  }

// //---------------------------------------------------------------------------------------------------------------------------//
// // PUT requests

// export async function approvePredictions(approved_predictions: number[], batch_id: number, image_id: number) : Promise<any> {
//     try {
//         const response = await(fetch(`${api_url}/batches/${batch_id}/images/${image_id}/approve_predictions`, {
//             method: 'PUT',
//             credentials: 'include',
//             headers: {
//                 'Content-Type': 'application/json',
                 
//             },
//             body: JSON.stringify(approved_predictions),
//         }));
//         if (!response.ok) {
//             throw new Error(`${uh_oh} ${response.status}`)
//         }
//     } catch (error: any) {
//         console.error('Error', error);
//     }
// }

// //---------------------------------------------------------------------------------------------------------------------------//

// // Delete requests

// export async function deleteBatch(batch_id: number) : Promise<any> {
//     try {
//         const response = await(fetch(`${api_url}/batches/${batch_id}`, {
//             method: 'DELETE',
//             credentials: 'include',
//             headers: {
                 
//             },
//         }));

//         if (!response.ok) {

//             throw new Error(`${uh_oh} ${response.status}`);
//         }
//         const data = await response.json();
//         return data;
//     } catch (error: any) {
//         console.error("Error:", error);
//         throw error;
//     }
// }

// //---------------------------------------------------------------------------------------------------------------------------//

// export default{};