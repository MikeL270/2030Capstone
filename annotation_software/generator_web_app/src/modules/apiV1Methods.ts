// Methods for interacting with the version 1 of the crop generator API 
// Author: Michael B. Lance
// Created: April 20, 2025
// Updated: September 11, 2025
//---------------------------------------------------------------------------------------------------------------------------//

import { Box, Image, Prediction, Crop, PredictionCrop, Project, Organization, User, Schema,
         Label, HerdUnit, Survey, Model } from '@/types/generatorobjects.ts';
import type { Prediction_intf, User_intf, Image_intf, PredictionCrop_intf } from '@/types/generatorobjects.ts';
import { useToast } from 'vue-toastification'

//const api_url: URL = new URL('https://pronghorn-count.arcc.uwyo.edu/api/v1'); //"production"
const api_url: URL = new URL('http://testing.lancecomputer.com:5000/api/v1');
//const api_url: URL = new URL('http://testing.lancecomputer.com:8000/api/v1');
const uh_oh: string = 'status: ';

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
        for (const organization of resp) organizations.push(new Organization(organization));
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
        for (const project of resp) projects.push(new Project(project));
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
        for (const schema of resp) schemas.push(new Schema(schema));
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
        for (const label of resp) labels.push(new Label(label));
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
        for (const herd_unit of resp) herd_units.push(new HerdUnit(herd_unit));
        return herd_units;
    } catch (error: any) {
        console.error("There was an error fetching the data:", error);
        toast.error(`${error}`);
        return undefined;
    }
}

export async function getCropperHerdUnits(survey_id: string | undefined): Promise<HerdUnit[] | undefined> {
	try {
		const response = await fetch(`${api_url}/request/surveys/${survey_id}/herd_units/all`, {
			method: 'GET',
			credentials: 'include',
			headers: {
				'Content-Type': 'application/json',
			},
		});
		if (!response.ok) throw new Error(`${uh_oh} ${await response.text()}`)
        const resp = await response.json();
        var herd_units = [];
        for (const herd_unit of resp) herd_units.push(new HerdUnit(herd_unit));
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
        for (const model of resp) models.push(new Model(model)); 
        return models;
    } catch (error: any) {
        console.error("There was an error fetching the data:", error);
        toast.error(`${error}`);
        return undefined;
    }
}

export async function getCropperModels(survey_id: string | undefined, herd_unit_id: string | undefined, schema_id: string | undefined): Promise<Model[] | undefined> {
	try {
		const response = await fetch(`${api_url}/request/surveys/${survey_id}/herd_units/${herd_unit_id}/schemas/${schema_id}/models/all`, {
			method: 'GET',
			credentials: 'include',
			headers: {
				'Content-Type': 'application/json'
			},
		});
		if (!response.ok) throw new Error(`${uh_oh} ${await response.text()}`)
		const resp = await response.json();
		var models = [];
		for (const model of resp) models.push(new Model(model));
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
        if (!response.ok) throw new Error(`${uh_oh} ${await response.text()}`);
        const resp = await response.json();
        var surveys = [];
        for (const survey of resp) surveys.push(new Survey(survey));
        return surveys;
    } catch (error: any) {
        console.error("There was an error fetching the data:", error);
        toast.error(`${error}`);
        return undefined;
    }
}

//---------------------------------------------------------------------------------------------------------------------------//
// Image Crud

export async function createImage(project_id: string | undefined, survey_id: string | undefined,
	herd_unit_id: string | undefined, name: string, img_key: string, image_length: number, image_width: number
): Promise<Image | undefined> {
	try {
		const response = await fetch(`${api_url}/create/image`, {
			method: 'POST',
			credentials: 'include',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				'project_id': project_id,
				'survey_id': survey_id,
				'herd_unit_id': herd_unit_id,
				'img_key': img_key,
				'name': name,
				'image_length': image_length,
				'image_width': image_width,
			}),
		});
		if (!response.ok) throw new Error(`${uh_oh} ${await response.text()}`)	
		const resp = await response.json();
		const image = new Image(resp)
		return image;
	} catch (error: any) {
        console.error("There was an error fetching the data:", error);
        toast.error(`${error}`);
        return undefined;
    }
}

//---------------------------------------------------------------------------------------------------------------------------//
 // Multipart image upload

 export async function createMultiPartUpload(image_key: string): Promise<string | undefined> {
	try {
		const response = await fetch(`${api_url}/upload/image/create_multipart_upload`, {
			method: 'POST',
			credentials: 'include',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				'image_key': image_key,
			}),
		});
		if (!response.ok) throw new Error(`${uh_oh} ${await response.text()}`)
			const resp = await response.json();
		return resp.upload_id as string;
	} catch (error: any) {
        console.error("There was an error creating the upload:", error);
        toast.error(`${error}`);
        return undefined;
    }
 }

export async function getPresignedUrl(upload_id: string, part_number: number, image_key: string, chunk_size: number, chunk_md5: string): Promise<string | undefined> {
	try {
		const response = await fetch(`${api_url}/upload/image/presigned-url`, {
			method: 'POST',
			credentials: 'include',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				'upload_id': upload_id,
				'part_number': part_number,
				'image_key': image_key,
				'chunk_size': chunk_size,
				'chunk_md5': chunk_md5,
			}),
		});
		if (!response.ok) throw new Error(`${uh_oh} ${await response.text()}`)
		const resp = await response.json();
		return resp as string;
	} catch (error: any) {
        console.error("There was an error creating the presigned url:", error);
        toast.error(`${error}`);
        return undefined;
    }
}

export async function abortMultipartUpload(image_key: string, upload_id: string): Promise<string | undefined> {
	try {
		const response = await fetch(`${api_url}/upload/image/abort`, {
			method: 'POST',
			credentials: 'include',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				'image_key': image_key,
				'upload_id': upload_id,
			}),
		});
		if (!response.ok) throw new Error(`${uh_oh} ${await response.text()}`)
		const resp = await response.json()
		return resp as string;
	} catch (error: any) {
        console.error("There was an error aborting the multipart upload:", error);
        toast.error(`${error}`);
        return undefined;
    }
}

export async function completeMultiPartUpload(image_key: string, parts: any[], upload_id: string): Promise<string | undefined> {
	try {
		const response = await fetch(`${api_url}/upload/image/complete`, {
			method: 'POST',
			credentials: 'include',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				'image_key': image_key,
				'parts': parts,
				'upload_id': upload_id
			}),
		});
		if (!response.ok) throw new Error(`${uh_oh} ${await response.text()}`)
		return await response.json() as string;
	} catch (error: any) {
        console.error("There was an error completeing the multipart upload:", error);
        toast.error(`${error}`);
        return undefined;
    }

}

//---------------------------------------------------------------------------------------------------------------------------//
// Auto Cropping

export async function getBatch(survey_id: string | undefined, herd_unit_id: string | undefined, size: number,
	score: number, label: number | undefined, model_id: string | undefined): Promise<[Image[], Prediction[][]] | undefined> {
	try {
		const response = await fetch(`${api_url}/create/batch`, {
			method: 'POST',
			credentials: 'include',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				'survey_id': survey_id,
				'herd_unit_id': herd_unit_id,
				'size': size,
				'score': score,
				'label': label,
				'model_id': model_id,
			}),
		});
		if (!response.ok) throw new Error(`${uh_oh} ${await response.text()}`);
		const resp = await response.json();
		const images: Image[] = [];
		const predictions: Prediction[][] = [];
		for (const img of resp) {
			images.push(new Image(img as Image_intf));
			const preds: Prediction[] = []
			for (const pred of img['predictions']) {
				preds.push(new Prediction(pred as Prediction_intf))
			}
			predictions.push(preds)
		}
		return [images as Image[], predictions as Prediction[][]];
	} catch (error: any) {
        console.error("There was an error fetching the batch", error);
        toast.error(`${error}`);
        return undefined;
    }

}

export async function getPredCrops(image_id: string | undefined, survey_id: string | undefined, 
	herd_unit_id: string | undefined, predictions: Prediction[] | undefined): Promise<PredictionCrop[] | undefined> {
		try {
		const response = await fetch(`${api_url}/create/prediction_crops`, {
			method: 'POST',
			credentials: 'include',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				'image_id': image_id,
				'survey_id': survey_id,
				'herd_unit_id': herd_unit_id,
				'predictions': predictions,
			}),
		});
		if (!response.ok) throw new Error(`${uh_oh} ${await response.text()}`);
		const resp = await response.json();
		const pred_crops: PredictionCrop[] = []
		for (const row of resp) {
			const predCrop = row as PredictionCrop_intf
			pred_crops.push(new PredictionCrop(
				predCrop,
				`${api_url}/request/image/${image_id}/pred_crop/${predCrop.uuid}`));
		}
		return pred_crops;
	} catch (error: any) {
        console.error("There was an error creating pred crops:", error);
        toast.error(`${error}`);
        return undefined;
    }
}

export async function submitNoAnnotations(image_id: string, prediction_ids: string[]): Promise<boolean> {
	try {
		const response = await fetch(`${api_url}/update/image/no-annotations`, {
			method: 'POST',
			credentials: 'include',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				'image_id': image_id,
				'prediction_ids': prediction_ids
			}),
		});
		if (!response.ok) {
			throw new Error(`${uh_oh} ${await response.text()}`);
		} else {
			return true;
		}
	} catch (error: any) {
        console.error("There was an error closing the image and predictions:", error);
        toast.error(`${error}`);
        return false;
    }
}

export async function autoCrop(image_uuid: string, predictions: Prediction[], herd_unit_id: string, survey_id: string, labels: Label[]): Promise<boolean> {
	try {
		const response = await fetch(`${api_url}/create/reviewed-area-and-annotations`, {
			method: 'PUT',
			credentials: 'include',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				'image_uuid': image_uuid,
				'predictions': predictions,
				'herd_unit_id': herd_unit_id,
				'survey_id': survey_id,
				'labels': labels
			}),
		});
		if (!response.ok) {
			throw new Error(`${uh_oh} ${await response.text()}`)
		} else {
			return true;
		}
	} catch (error: any) {
        console.error("There was an error creating crops:", error);
        toast.error(`${error}`);
        return false;
    }
}

export async function closeCropSession(): Promise<boolean> {
	try {
		const response = await fetch(`${api_url}/end/crop_session`, {
			method: 'POST',
			credentials: 'include',
			headers: {
				'Content-Type': 'application/json'
			}
		});
		if (!response.ok) {
			throw new Error(`${uh_oh} ${await response.text()}`)
		} else {
			return true;
		}

	} catch (error: any) {
		console.error("There was an error closing images:", error);
        toast.error(`${error}`);
        return false;
	}

}
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