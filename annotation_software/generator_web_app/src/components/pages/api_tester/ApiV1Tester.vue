<script lang="ts">
import { set } from 'lodash';
import { testApi, createBatch, deleteBatch } from '../../../modules/apiV1Methods';
import { defineComponent } from 'vue';
import { ref } from 'vue';
import { jsx } from 'vue/jsx-runtime';

var request_type: string = 'POST';
var endpoint: string = 'none';
var batch_id: number;
var batch_ids: number[];

export default defineComponent({
    name: 'V1Tester',
    data() {
        return {
            apiResponse: null as string | null,
            create_batch_params: {
                batch_size: 10,
                desired_class: 2,
                min_confidence: 0.9,
            },
            request_type,
            endpoint,
            batch_id,
        };
    },
    methods: {
        set_request_type(type: string) {
            this.request_type = type;
            this.endpoint = 'none';
        },
        async create_batch(create_batch_params: Record<string, any>) {
            const responseData = await createBatch(create_batch_params);
            this.apiResponse = JSON.stringify(responseData, null, 2);
        },
        async delete_batch(batch_id: number): Promise<any> {
            const responseData = await deleteBatch(batch_id);
            this.apiResponse = JSON.stringify(responseData, null, 2);
        }
    },
});
</script>

<template>
<div class="Tester-Container">
    <div class="Requests-Menu" id="top-menu">
        <h2> Select Route: </h2>
        <button class="Tab" @click="set_request_type('GET')"> GET </button>
        <button class="Tab" @click="set_request_type('POST')"> POST </button>
        <button class="Tab" @click="set_request_type('PUT')"> PUT </button>
        <button class="Tab" @click="set_request_type('DELETE')"> DELETE </button>
    </div>
    <div id="sub-menus">
    <div class="Requests-Menu" id="post-request-menu" v-if="request_type === 'POST'">
        <button class="Tab" @click="endpoint = 'create_batch'"> Create Batch</button>
    </div>
    <div class="Requests-Menu" id="delete-request-menu" v-if="request_type === 'DELETE'">
        <button class="Tab" @click="endpoint = 'delete_batch'"> Delete Batch</button>
    </div>

</div>
    <div class="Requests-Window" >
        <div class="Request-Parameters" v-if="endpoint === 'create_batch'">
            <h2> Create Batch:</h2>
                <label for="batch_size"> Batch size:</label>
                <br>
                <input type="text" id="batch_size" v-model="create_batch_params.batch_size">
                <label for="desired_class"> Desired Class:</label>
                <br>
                <input type="text" id="desired_class" v-model="create_batch_params.desired_class">
                <label for="min_confidence"> Minimum Confidence:</label>
                <br>
                <input type="text" id="min_confidence" v-model="create_batch_params.min_confidence">
                <br>
                <button @click="create_batch(create_batch_params)"> Test_Api</button>
        </div>
        <div class="Request-Parameters" v-if="endpoint === 'delete_batch'">
            <h2> Delete Batch:</h2>
            <label for="batch_id"> Batch ID </label>
            <br>
            <input type="number" id="batch_id" v-model="batch_id">
            <br>
            <button @click="delete_batch(batch_id)"> Delete </button>
        </div>
    </div>
    <div>
    <h2> Response from API</h2>
        <div class="Response-Window">
            <pre v-if="apiResponse">{{ apiResponse }}</pre>
        </div>
    </div>
</div>
</template>

<style scoped>
    .Tester-Container {
        display: flex;
        align-items: flex-start;
        justify-content: flex-start;
        height: 100%;
        width: 100%;
    }
    .Requests-Menu {
        display: flex;
        flex-direction: column;
        width: 11vw;
        background-color: var(--color-background);
        border-radius: 4px;
        gap: 4px;
        padding: 0.5%;
    }
    .Tab {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 4vh;
        background-color: var(--color-background-soft);
        box-shadow: 0 4px 6px 2px rgba(0,0,0,0.25);
        color: var(--color-text);
        border-radius: 4px;
        border: none;
    }
    .Requests-Window {
        display: flex;
        flex-direction: column;
        margin: 1%;
    }
    .Response-Container {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
    
    }
    .Response-Window {
        width: 100%;
        max-height: 50vh;
        height: 50vh;
        background-color: var(--color-background);
        overflow-x: none;
        overflow-y: auto;
        border-radius: 4px;
    }
</style>