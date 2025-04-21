<script lang="ts">
import { fetchFromApi, createBatch } from '../../../modules/annotate';
import { defineComponent } from 'vue';
export default defineComponent({
    name: 'V1Tester',
    data() {
        return {
            apiResponse: null as string | null,
            params: {
                batch_size: '',
                desired_class: '',
                min_confidence: '',
            },
        };
    },
    methods: {
        async fetchdata(endpoint: string) {
            const responseData = await fetchFromApi(endpoint);
            this.apiResponse = JSON.stringify(responseData, null, 2);
        },
        async create_batch(params: Record<string, any>) {
            const responseData = await createBatch(params);
            this.apiResponse = JSON.stringify(responseData, null, 2);
        }
    },
});
</script>

<template>

<div>
    <h1> V1 API Tester</h1>
    <h2> Enter batch details:</h2>
    <div>
        <label for="batch_size"> Batch size:</label>
        <br>
        <input type="text" id="batch_size" v-model="params.batch_size">
    </div>
    <div>
        <label for="desired_class"> Desired Class:</label>
        <br>
        <input type="text" id="desired_class" v-model="params.desired_class">
    </div>
    <div>
        <label for="min_confidence"> Minimum Confidence:</label>
        <br>
        <input type="text" id="min_confidence" v-model="params.min_confidence">
    </div>
    <br>
    <button @click="create_batch(params)"> Test_Api</button>
    <div class="Response-Container">
        <pre v-if="apiResponse">{{ apiResponse }}</pre>
        <p v-else> No response yet </p>
    </div>
</div>

</template>