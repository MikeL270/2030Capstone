// cross component state management for crop verification functionality
// Author: Michael B. Lance
// Created: October 1, 2025
// Updated: October 28, 2025
//---------------------------------------------------------------------------------------------------------------------------//

import { defineStore } from 'pinia';
import { useProjectStore } from '@/modules/stores/projectStore';
import type { cropVerifierBatch, ReviewedArea } from '@/types/generatorobjects';
import { fetchReviewedArea, getReviewedAreaPresignedGetUrl } from '@/modules/apiV1Methods';
import { useImage } from 'vue-konva';
import { ref } from 'vue';

//---------------------------------------------------------------------------------------------------------------------------//

const pStore = useProjectStore();

export const useCropVerifierStore = defineStore('cropVerifierStore', {
    state: () => ({
        batches: [{
            crops: [],
            annotations: []
        }] as cropVerifierBatch[],
        batchIdx: 0,
        cropIdx: 0,
        loading: false,
        bootStrapped: false,
        testConf: {
            x: 405,
            y: 458,
            width: 20,
            height: 10,
            stroke: 'orange',
            strokeWidth: 2,
            draggable: true
        },

        transformConfig: {

        }
    }),
    getters: {

    },
    actions: {
        async getReviewedArea(batchIndex: number) {
            const resp = await fetchReviewedArea(pStore.CurrentHerdUnit?.uuid, pStore.CurrentSurvey?.uuid);
            if (resp == undefined) return;
            if (!this.batches[batchIndex]) this.batches[batchIndex] = {
                crops: [],
                annotations: []
            } as cropVerifierBatch;
            await this.getReviewedAreaImage(resp);
            this.batches[batchIndex]['crops'].push(resp);
        },
        async getReviewedAreaImage(crop: ReviewedArea) {
            const resp = await getReviewedAreaPresignedGetUrl(crop.ra_key);
            if (resp == undefined) return;
            crop.url = resp;
            crop.image = await useImage(resp);
        },
        async bootStrap() {
            this.loading = true;
            await this.getReviewedArea(0);
            this.loading = false;
            this.bootStrapped = true;
        }
    }
})