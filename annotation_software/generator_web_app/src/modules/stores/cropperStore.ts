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


export const useAutoCropperStore = defineStore('autoCropperStore', {
    state: () => ({
        images: undefined as Image[] | undefined,
		image_idx: undefined as number | undefined,
		predictions: undefined as Prediction[][] | undefined,
		predictions_idx: undefined as number | undefined,
		selected_predictions: undefined as number[] | undefined,
		prediction_crops: undefined as PredictionCrop[][] | undefined,
		loading: false,
    }),
	getters: {
		CurrentImage: (state) => (state.images && state.image_idx != undefined) ? state.images[state.image_idx] : undefined,
		ImageNum: (state) => (state.image_idx != undefined) ? (state.image_idx + 1): 0,
		CurrentPredictions: (state) => (state.predictions && state.image_idx != undefined ) ? state.predictions[state.image_idx] : undefined,
		CurrentPredictionCrops: (state) => (state.prediction_crops && state.image_idx != undefined) ? state.prediction_crops[state.image_idx] : undefined,

	},
    actions: {
		async get_batch() {
			this.loading = true;
			const resp = await getBatch(pstore.CurrentSurvey?.uuid, pstore.CurrentHerdUnit?.uuid, prefstore.batch_size, 0.9, pstore.CurrentLabel?.label, pstore.CurrentModel?.uuid)
			if (resp == undefined) return
			this.images = resp[0] as Image[]
			this.image_idx = 0; 
			this.predictions = resp[1] as Prediction[][]
			this.predictions_idx = 0;
			this.loading = false;
		},
		async get_prediction_crops() {
			this.loading = true;
			if (this.CurrentImage && this.CurrentPredictions && this.image_idx != undefined) {
				const predCrops = await getPredCrops(this.CurrentImage.uuid, pstore.CurrentSurvey?.uuid, pstore.CurrentHerdUnit?.uuid, this.CurrentPredictions);
				if (!this.prediction_crops) this.prediction_crops = []
				if (predCrops) this.prediction_crops?.splice(this.image_idx, 0, predCrops)
			}
			
			this.loading = false;
		},
		async submit_no_annotations() {
			if (this.image_idx != undefined && this.images && this.predictions && this.predictions[this.image_idx]) {
				await submitNoAnnotations(this.images[this.image_idx].uuid, this.predictions[this.image_idx]);
			}

		},
		async next_image() {
			if (this.loading) return;
			if (this.image_idx != undefined && this.image_idx < prefstore.batch_size - 1) this.image_idx++;
			if (this.prediction_crops && this.image_idx != undefined && this.prediction_crops[this.image_idx] != undefined)	{
				return;
			} else {
				await this.get_prediction_crops();
			}
		},
		async previous_image() {
			if (this.loading) return;
			if (this.image_idx !=undefined && this.image_idx > 0) this.image_idx--;
			if (this.prediction_crops && this.image_idx != undefined && this.prediction_crops[this.image_idx] != undefined) {
				console.log('using pred crops in memory boss')
				return;
			} else {
				console.log('hitting the api because I am dumb')
				await this.get_prediction_crops();

			}
		}
    }
})