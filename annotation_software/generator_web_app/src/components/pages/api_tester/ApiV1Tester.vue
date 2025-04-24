<script lang="ts">
import { set } from 'lodash';
import { testApi, createBatch, deleteBatch } from '../../../modules/apiV1Methods';
import { defineComponent } from 'vue';
import { ref } from 'vue';
import { jsx } from 'vue/jsx-runtime';

var request_type: string = 'GET';
var endpoint: string = 'none';
var batch_id: number;

export default defineComponent({
    name: 'V1Tester',
    data() {
        return {
            apiResponse: null as string | null,
            create_batch_params: {
                batch_size: 10,
                desired_class: 2,
                min_confidence: 0.9,
                herd_unit_id: 1,
                model_id: 1,
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
        },
        async test_api(): Promise<any> {
            const responseData = await testApi()
            this.apiResponse = JSON.stringify(responseData, null, 2);
        }
    },
});
</script>

<template>
    <div class="Tester-Container">
        <div class="Requests-Menu Box" id="top-menu">
            <h2> Select Route: </h2>
            <button class="Tab" @click="set_request_type('GET')":class="{active: request_type=='GET'}"> GET </button>
            <button class="Tab" @click="set_request_type('POST')":class="{active: request_type=='POST'}"> POST </button>
            <button class="Tab" @click="set_request_type('PUT')":class="{active: request_type=='PUT'}"> PUT </button>
            <button class="Tab" @click="set_request_type('DELETE')":class="{active: request_type=='DELETE'}"> DELETE </button>
        </div>
        <div class="Requests-Menu Box" id="get-request-menu" v-if="request_type === 'GET'">
            <h2> Get Requests: </h2>
            <button class="Tab" @click="endpoint = 'test'":class="{active: endpoint=='test'}"> Test </button>
        </div>
        <div class="Requests-Menu Box" id="post-request-menu" v-if="request_type === 'POST'">
            <h2> POST Requests: </h2>
            <button class="Tab" @click="endpoint = 'create_batch'":class="{active: endpoint=='create_batch'}"> Create Batch</button>
            <button class="Tab" @click="endpoint = 'create_full_crops'":class="{active: endpoint=='create_full_crops'}"> Create Full Crops</button>
        </div>
        <div class="Requests-Menu Box" id="delete-request-menu" v-if="request_type === 'DELETE'">
            <h2> DELETE Requests: </h2>
            <button class="Tab" @click="endpoint = 'delete_batch'":class="{active: endpoint=='delete_batch'}"> Delete Batch</button>
        </div>
    <div class="Request-Parameters Box" v-if="endpoint === 'none'">
        <h2> API Tester </h2>
        <br>
        <p>
            Select a route to the left to reveal the endpoints available through the API.
            The select a route you would like test. You will be presented with the available
            parameters for thre request. Please be aware of the lifecycle of objects you create.
        </p>
    </div>
    <div class="Request-Parameters Box" v-if="endpoint === 'test'">
        <h2> Test API connection: </h2>
        <button @click="test_api()">Test</button>
    </div>
    <div class="Request-Parameters Box" v-if="endpoint === 'create_batch'">
        <h2> Create Batch:</h2>
            <label for="batch_size"> Batch size:
                <input type="number" id="batch_size" v-model="create_batch_params.batch_size">
            </label>
            <label for="desired_class"> Desired Class:
                <input type="number" id="desired_class" v-model="create_batch_params.desired_class">
            </label>
            <label for="min_confidence"> Minimum Confidence:
                <input type="number" id="min_confidence" v-model="create_batch_params.min_confidence">
            </label>
            <label for="herd_unit_id"> Herd Unit Id: 
                <input type="number" id="herd_unit_id" v-model="create_batch_params.herd_unit_id">
            </label>
            <label for="modle_id"> Model Id:
                <input type="number" id="model_id" v-model="create_batch_params.model_id">
            </label>
            <br>
            <button @click="create_batch(create_batch_params)"> Create Batch </button>
    </div>
    <div class="Request-Parameters Box" v-if="endpoint === 'create_full_crops'">
        <h2> Create Full Crops: </h2>
    </div>
    <div class="Request-Parameters Box" v-if="endpoint === 'delete_batch'">
        <h2> Delete Batch:</h2>
        <label for="batch_id"> Batch ID </label>
        <input type="number" id="batch_id" v-model="batch_id">
        <button @click="delete_batch(batch_id)"> Delete </button>
    </div>
        <div class="Response-Container Box">
        <h2> Response Json: </h2>
            <div class="Response-Window">
                <pre v-if="apiResponse">{{ apiResponse }}</pre>
            </div>
        </div>
    </div>
</template>

<style scoped>
    .Tester-Container {
        display: flex;
        height: 100%;
        width: 100%;
        gap: 5px;
        
    }
    .Box {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 11vw;
        height: 100%;
        gap: 2.5px;
        background-color: var(--color-background-mute);
        border: solid 1px var(--color-background);
        padding: 1%;
    }
    .Requests-Menu {
        min-width: 200px;
    }
    .Tab {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 4vh;
        min-width: 100px;
        width: 100%;
        background-color: var(--color-background-soft);
        box-shadow: 0 4px 6px 2px rgba(0,0,0,0.25);
        color: var(--color-text);
        border-radius: 4px;
        border: none;
        margin: 2.5%;
    }
    .active  {
        background-color: var(--color-border);
    }

    .Request-Parameters {
        width: 30vw;
        align-items: flex-start;
        input {
            width: 100%;
        }
    }
    .Response-Container {
        width: 100%;
    }
    .Response-Window {
        display: flex;
        width: 90%;
        max-width: 90%;
        height: 100%;
        max-height: 50vh;
        background-color: var(--color-background);
        overflow-y: auto;
        border-radius: 4px;
        padding: 1%;
    }
</style>