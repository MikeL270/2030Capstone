// cross component state management for autocropper functionality
// Author: Michael B. Lance
// Created: July 25, 2025
// Updated: July 28, 2025
//---------------------------------------------------------------------------------------------------------------------------//

import { defineStore } from "pinia";
import { useProjectStore } from "./projectStore";
import { Image, Prediction, PredictionCrop } from "@/types/generatorobjects";
import { getBatch, getPredCrops, submitNoAnnotations } from "../apiV1Methods";
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
		selected_predictions: [] as number[],
		loading: false,
		bootstrapped: false,
    }),
	getters: {
		CurrentBatch: (state) =>  state.batches[state.batch_idx],
		NextBatch: (state) => (state.batches[state.batch_idx + 1] != undefined) ? true : false,
		LastBatch: (state) => (state.batches[state.batch_idx - 1] != undefined) ? true : false, 
		CurrentImages(): Image[] { return this.CurrentBatch?.images },
		CurrentPredictions(state): Prediction[] { return this.CurrentBatch?.predictions[state.image_idx] },
		CurrentPredictionCrops(state): PredictionCrop[] { return this.CurrentBatch?.prediction_crops[state.image_idx] },
		NextPredictionCrops(state): boolean { const predcrops = (this.CurrentBatch?.prediction_crops[state.image_idx + 1] != undefined) ? true : false; return predcrops;},
		LastPredictionCrops(state): boolean { const predcrops = (this.CurrentBatch?.prediction_crops[state.image_idx - 1] != undefined) ? true : false; return predcrops;},
		CurrentImage(state): Image  { return this.CurrentImages[state.image_idx] },
		ImageNum: (state) => state.image_idx + 1,
	},
    actions: {
		async get_batch(batch_index: number) {
			const resp = await getBatch(pstore.CurrentSurvey?.uuid, pstore.CurrentHerdUnit?.uuid, prefstore.batch_size, 0.9, pstore.CurrentLabel?.label, pstore.CurrentModel?.uuid)
			if (resp == undefined) return;
			if (!this.batches[batch_index]) this.batches[batch_index] = {
				'images':[],
				'predictions': [],
				'prediction_crops':[]
			} as batch;
			this.batches[batch_index]['images'] = resp[0];
			this.image_idx = 0; 
			this.batches[batch_index]['predictions'] = resp[1];
		},
		async bootstrap() {
			console.log('called')
			this.loading = true;
			await this.get_batch(0);
			await this.get_prediction_crops(this.image_idx);
			this.loading = false;
			this.bootstrapped = true;
			// prefecth next batch
			this.get_batch(1);
		},
		async next_batch() {
			if (this.NextBatch) {
				this.batch_idx++;
				this.image_idx = 0;
				return;
			} else {
				// clear older batch
				// TODO: instead of just deleting the batch cache it in valkey session in a form of lifo/filo stack
				if (this.batches.length > 3) delete this.batches[0];

			}
		
		},
		async get_prediction_crops(image_index: number) {
			const predCrops = await getPredCrops(this.CurrentImage.uuid, pstore.CurrentSurvey?.uuid, pstore.CurrentHerdUnit?.uuid, this.CurrentPredictions);
			if (predCrops) this.batches[this.batch_idx]['prediction_crops'][image_index] = predCrops;
		},
		async submit_no_annotations() {
			if (this.loading) return;
			this.loading = true;
			await submitNoAnnotations(this.CurrentImage.uuid, this.CurrentPredictions);
			this.loading = false;
		},
		async next_image() {
			if (this.loading) return;
			// preload the next batch if halfway through 	
			if (this.image_idx == Math.floor(this.CurrentImages.length / 2)) {
				this.get_batch(this.image_idx + 1);
			}
			// if next prediction crops already exist increase image_idx
			if (this.NextPredictionCrops) {
				console.log('I broke it')
				this.image_idx++;
				return;
			} else {
				this.loading = true;
				this.image_idx++;
				await this.get_prediction_crops(this.image_idx);
				this.loading = false;
				// preload the next prediction crops 
				//this.get_prediction_crops(this.image_idx++);
			}
		},
		async previous_image() {
			if (this.loading) return;
			// TODO: prefetch last batch from cache (when cache feature is implemented)
			if (this.LastPredictionCrops) {
				this.image_idx--;
				return;
			} else {
				this.loading = true;
				this.image_idx--;
				await this.get_prediction_crops(this.image_idx);
				this.loading = false;
			}
		}
    }
})