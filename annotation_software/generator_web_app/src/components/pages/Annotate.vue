<script lang="ts">
import { createBatch, deleteBatch, createPredCrops} from '../../modules/apiV1Methods';
import type {Batches, Batch} from '../../types/interfaces';
import { defineComponent } from 'vue'; 
import { Icon } from '@iconify/vue';

export default defineComponent({
    name: 'Annotator',
    data() {
        return {
            batches: {} as Batches,

        };
    },
    methods: {},
});

</script>

<template>
   <div style="width: 50px; height: 50px; border: 1px solid blue;">
    <Icon icon="material-symbols:menu" width="36" height="36"></Icon>   </div>
</template>

<style scoped>
</style>