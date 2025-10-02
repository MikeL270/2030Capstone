// cross component state management for autocropper functionality
// Author: Michael B. Lance
// Created: July 25, 2025
// Updated: September 11, 2025
//---------------------------------------------------------------------------------------------------------------------------//

import { defineStore } from "pinia";
import { useProjectStore } from "./projectStore";
import { Image, Prediction, PredictionCrop } from "@/types/generatorobjects";
import { autoCrop, getBatch, getPredCrops, submitNoAnnotations, closeCropSession } from "../apiV1Methods";
import { usePreferenceStore } from "./preferencesStore";

//---------------------------------------------------------------------------------------------------------------------------//

const pstore = useProjectStore();
const prefstore = usePreferenceStore();

interface batch {
	'images': Image[];
	'predictions': Prediction[][];
	'prediction_crops': PredictionCrop[][];
}

export const useAutoCropperStore = defineStore('autoCropperStore', {
    state: () => ({
		batches:[{
			'images':[],
            'predictions': [],
            'prediction_crops':[]
		}] as batch[],
		batch_idx: 0,
		image_idx: 0,
		active_pred_idx: 0,
		loading: false,
		bootstrapped: false,
    }),
	getters: {
		CurrentBatch: (state) =>  state.batches[state.batch_idx],
		NextBatch: (state) => (state.batches[state.batch_idx + 1] != undefined) ? true : false,
		LastBatch: (state) => (state.batches[state.batch_idx - 1] != undefined) ? true : false, 
		CurrentImages(): Image[] { return this.CurrentBatch?.images },
		CurrentPredictions(state): Prediction[] { return this.CurrentBatch?.predictions[state.image_idx] },
		CurrentPredictionIds(): string[] {
			const ids: string[] = [];
			for (const pred of this.CurrentPredictions) {
				ids.push(pred.uuid);
			}
			return ids;
		},
		CurrentPredictionCrops(state): PredictionCrop[] { return this.CurrentBatch?.prediction_crops[state.image_idx] },
		CurrentPredictionCrop(): PredictionCrop { return this.CurrentPredictionCrops[this.active_pred_idx] },
		NextPredictionCrops(state): boolean { 
			const predcrops: boolean = (this.CurrentBatch?.prediction_crops[state.image_idx + 1] != undefined) ? true : false; 
			return predcrops;
		},
		LastPredictionCrops(state): boolean { 
			const predcrops: boolean = (this.CurrentBatch?.prediction_crops[state.image_idx - 1] != undefined) ? true : false; 
			return predcrops;
		},
		CurrentImage(state): Image  { return this.CurrentImages[state.image_idx] },
		ImageNum: (state) => state.image_idx + 1,
		ApprovedPredictions():  Prediction[] { 
			const newPredictions: Prediction[] = []; 
			for (let i = 0; i < this.CurrentPredictionCrops.length; i++) {
				if (this.CurrentPredictionCrops[i].approved) {
					let oldPred = this.CurrentPredictions[i];
					oldPred.label = this.CurrentPredictionCrops[i].label;
					newPredictions.push(oldPred)
				}
			}
			return newPredictions;
			}
	},
    actions: {
		async get_batch(batch_index: number) {
			const resp = await getBatch(pstore.CurrentSurvey?.uuid, 
										pstore.CurrentHerdUnit?.uuid, 
										prefstore.batch_size, 
										0.9, 
										pstore.CurrentLabel?.label, 
										pstore.CurrentModel?.uuid)
			if (resp == undefined) return;
			if (!this.batches[batch_index]) this.batches[batch_index] = {
				'images':[],
				'predictions': [],
				'prediction_crops':[]
			} as batch;
			this.batches[batch_index]['images'] = resp[0];
			this.batches[batch_index]['predictions'] = resp[1];
		},
		async bootstrap() {
			this.loading = true;
			await closeCropSession();
			await this.get_batch(0);
			await this.get_prediction_crops(this.batch_idx, this.image_idx);
			this.loading = false;
			this.bootstrapped = true;
			// prefecth next image
			this.get_prediction_crops(this.batch_idx, this.image_idx + 1)
		},
		async next_batch() {
			// clear older batch
			// TODO: instead of just deleting the batch cache it in valkey session in a form of lifo/filo stack
			if (this.batches.length > 3) delete this.batches[0];
			if (!this.NextBatch) {
				await this.get_batch(this.image_idx + 1);
			}
			this.batch_idx++;
			this.image_idx = 0;
			await this.get_prediction_crops(this.batch_idx, this.image_idx + 1);
		},
		async get_prediction_crops(batch_index: number, image_index: number) {
			const predCrops = await getPredCrops(this.batches[batch_index]['images'][image_index].uuid, pstore.CurrentSurvey?.uuid, pstore.CurrentHerdUnit?.uuid, this.batches[batch_index].predictions[image_index]);
			if (predCrops) this.batches[batch_index]['prediction_crops'][image_index] = predCrops;
		},
		async next_image() {
			if (this.loading) return;
			this.loading = true;
			this.active_pred_idx = 0;
			// preload the next batch if halfway through 	
			if (this.image_idx == Math.floor(this.CurrentImages.length / 2)) {
				this.get_batch(this.batch_idx + 1);
			}
			if (this.image_idx + 2 == this.CurrentImages.length && this.NextBatch) {
				this.get_prediction_crops(this.batch_idx + 1, 0)
			}
			if (this.image_idx + 1 >= this.CurrentImages.length) {
				this.next_batch();
				this.loading = false;
				return;
			} 
			// if next prediction crops already exist increase image_idx
			if (this.NextPredictionCrops) {
				this.image_idx++;
			} else {
				await this.get_prediction_crops(this.batch_idx, this.image_idx + 1);
				this.image_idx++;
			}
			// preload the next prediction crops 
			if (this.image_idx + 1 < this.CurrentImages.length && this.NextPredictionCrops == false) {
				this.get_prediction_crops(this.batch_idx, this.image_idx + 1);
			}
			this.loading = false;
		},
		async previous_image() {
			if (this.loading) return;
			this.loading = true;
			this.active_pred_idx = 0;
			// TODO: prefetch last batch from cache (when cache feature is implemented)
			if (this.LastPredictionCrops) {
				this.image_idx--;
			} else if (this.image_idx > 0) {
				await this.get_prediction_crops(this.batch_idx, this.image_idx - 1);
				this.image_idx--;

				this.loading = false;
			} else if (this.image_idx == 0 && this.LastBatch){
				this.batch_idx--;
				this.image_idx = this.CurrentImages.length - 1;
			}
			this.loading = false;
		},
		async next_prediction() {
			if (this.loading) return;
			if (this.active_pred_idx != this.CurrentPredictionCrops.length - 1) this.active_pred_idx++;
		},
		async previous_prediction() {
			if (this.loading) return;
			if (this.active_pred_idx != 0) this.active_pred_idx--;
		},
		async submit() {
			if (this.loading) return;
			this.loading = true;
			if (this.ApprovedPredictions.length == 0) {
				await submitNoAnnotations(this.CurrentImage.uuid, this.CurrentPredictionIds);
			} else {
				if (pstore.CurrentHerdUnit == undefined || pstore.CurrentSurvey == undefined || pstore.labels.length == 0) {
					throw new Error('HerdUnit, Survey, or labels are undefined!');	
				}			
				await autoCrop(this.CurrentImage.uuid, this.ApprovedPredictions, pstore.CurrentHerdUnit?.uuid, pstore.CurrentSurvey?.uuid, pstore.labels)
			}
			await this.next_image();
		},
		async end_session() {
			this.$reset();
			this.bootstrapped = false;
			await closeCropSession();
		}
    }
})