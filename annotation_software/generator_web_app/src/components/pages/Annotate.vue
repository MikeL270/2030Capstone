<script lang="ts">
import { createBatch, deleteBatch, createPredCrops} from '../../modules/apiV1Methods';
import type {Batches, Batch} from '../../types/interfaces';
import { defineComponent } from 'vue'; 

export default defineComponent({
    name: 'Annotator',
    data() {
        return {

        };
    },
    methods: {},
});

</script>

<template>
    <p>Annotate</p>
</template>