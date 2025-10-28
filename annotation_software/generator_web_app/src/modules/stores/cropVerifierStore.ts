// cross component state management for crop verification functionality
// Author: Michael B. Lance
// Created: October 1, 2025
// Updated: October 28, 2025
//---------------------------------------------------------------------------------------------------------------------------//

import { defineStore } from 'pinia';
import { useProjectStore } from '@/modules/stores/projectStore';
import { usePreferenceStore } from '@/modules/stores/preferencesStore';
import type { cropVerifierBatch } from '@/types/generatorobjects';
import { fetchReviewedAreaBatch } from '@/modules/apiV1Methods';

//---------------------------------------------------------------------------------------------------------------------------//

const pStore = useProjectStore();
const prefStore = usePreferenceStore();

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
    }),
    getters: {

    },
    actions: {
        async getbatch(batch_index: number) {
            const resp = await fetchReviewedAreaBatch(pStore.CurrentHerdUnit?.uuid, pStore.CurrentSurvey?.uuid, prefStore.batch_size)
        }
    }
})