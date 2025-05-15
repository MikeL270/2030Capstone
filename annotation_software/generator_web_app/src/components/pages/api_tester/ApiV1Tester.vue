<script lang="ts">
import { set } from 'lodash';
import { testApi, getBatch, getBatches, createBatch, deleteBatch,
         createPredCrops,
 } from '../../../modules/apiV1Methods';
 import type {Batches, Batch} from '../../../types/interfaces.ts';
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
            batches: {} as Batches,
            resp_checkbox: false,
            create_batch_params: {
                batch_size: 10,
                desired_class: 2,
                min_confidence: 0.9,
                herd_unit_id: 4,
                model_id: 3,
            },
            crops_requested: false,
            create_pred_crop_params: {
                batch_id: 1,
                image_id: 1,
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
        toggle_response_type() {
            this.resp_checkbox = !this.resp_checkbox;
            this.$emit('setCheckboxVal', this.resp_checkbox);
        },
        async test_api(): Promise<any> {
            const responseData = await testApi()
            this.apiResponse = JSON.stringify(responseData, null, 2);
        },
        async get_batch(batch_id: number) {
            const responseData = await getBatch(batch_id);
            this.apiResponse = JSON.stringify(responseData, null, 2);
        },
        async get_batches() {
            const responseData = await getBatches();
            this.apiResponse = JSON.stringify(responseData, null, 2);
        },
        async create_batch(create_batch_params: Record<string, any>) {
            const responseData = await createBatch(create_batch_params);
            console.log(Object.keys(responseData)[0])
            const batch_id = Object.keys(responseData)[0];
            this.batches[+batch_id] = Object.values(responseData)[0] as Batch;
            this.apiResponse = JSON.stringify(responseData, null, 2);
        },
        async create_pred_crops(create_pred_crops_params: Record<string, any>, batch: Batch) {
            const responseData = await createPredCrops(create_pred_crops_params, batch);
            this.batches[create_pred_crops_params.batch_id] = responseData;
            this.apiResponse = JSON.stringify(responseData, null, 2);
            this.crops_requested = true;

        },  
        async delete_batch(batch_id: number): Promise<any> {
            const responseData = await deleteBatch(batch_id);
            this.apiResponse = JSON.stringify(responseData, null, 2);
        },

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
        <div class="Requests-Menu Box" id="get-request-menu" v-if="request_type == 'GET'">
            <h2> Get Requests: </h2>
            <button class="Tab" @click="endpoint = 'test'":class="{active: endpoint=='test'}"> Test </button>
            <button class="Tab" @click="endpoint = 'get_batch'":class="{active: endpoint=='get_batch'}"> Get Batch </button>
            <button class="Tab" @click="endpoint = 'get_batches'":class="{active: endpoint=='get_batches'}"> Get Batches</button>
        </div>
        <div class="Requests-Menu Box" id="post-request-menu" v-if="request_type == 'POST'">
            <h2> POST Requests: </h2>
            <button class="Tab" @click="endpoint = 'create_batch'":class="{active: endpoint=='create_batch'}"> Create Batch</button>
            <button class="Tab" @click="endpoint = 'create_full_crops'":class="{active: endpoint=='create_full_crops'}"> Create Full Crops</button>
            <button class="Tab" @click="endpoint = 'create_pred_crops'":class="{active: endpoint=='create_pred_crops'}"> Create Pred Crops</button>
        </div>
        <div class="Requests-Menu Box" id="delete-request-menu" v-if="request_type == 'DELETE'">
            <h2> DELETE Requests: </h2>
            <button class="Tab" @click="endpoint = 'delete_batch'":class="{active: endpoint=='delete_batch'}"> Delete Batch</button>
        </div>
    <div class="Request-Parameters Box" v-if="endpoint == 'none'">
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
    <div class="Request-Parameters Box" v-if="endpoint == 'get_batch'">
        <h2> Get Batch: </h2>
        <label for="batch_id"> Batch ID
            <input type="number" id="batch_id_get" v-model="batch_id">
        </label>
        <button @click="get_batch(batch_id)"> Get Batch </button>
    </div>
    <div class="Request-Parameters Box" v-if="endpoint == 'get_batches'">
        <h2> Get Batches: </h2>
        <button @click="get_batches()"> Get Batches </button>

    </div>
    <div class="Request-Parameters Box" v-if="endpoint == 'create_batch'">
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
    <div class="Request-Parameters Box" v-if="endpoint == 'create_full_crops'">
        <h2> Create Full Crops: </h2>
       
    </div>
    <div class="Request-Parameters Box" v-if="endpoint =='create_pred_crops'">
        <h2> Create Prediction Crops: </h2>
        <label for="batch_id"> Batch Id:
            <input type="number" id="batch_id" v-model="create_pred_crop_params.batch_id">
        </label>
        <label for="image_id"> Image Id:
            <input type="number" id="image_id" v-model="create_pred_crop_params.image_id">
        </label>
        <button @click="create_pred_crops(create_pred_crop_params, batches[create_pred_crop_params.batch_id])"> Create Crops </button>
    </div>
    <div class="Request-Parameters Box" v-if="endpoint == 'delete_batch'">
        <h2> Delete Batch:</h2>
        <label for="batch_id"> Batch ID 
            <input type="number" id="batch_id_delete" v-model="batch_id">
        </label>
        <button @click="delete_batch(batch_id)"> Delete </button>
    </div>
        <div class="Response-Container Box">
        <h2> Response: </h2>
            <div class="Response-Window" v-if="!resp_checkbox">
                <pre v-if="apiResponse">{{ apiResponse }}</pre>
            </div>
            <div class="Response-Window Image-Contianer Box" v-else> 
                <figure v-for="crop in batches[create_pred_crop_params.batch_id][create_pred_crop_params.image_id]['pred_crops']" v-if="crops_requested">
                    <h2> {{ crop.score?.toFixed(4) }} </h2>
                    <img v-bind:src="crop.url">   
                </figure>
            </div>
            <label class="switch">
                <input type="checkbox" @click="toggle_response_type"> 
                <div class="slider round"></div>
            </label> Toggle Output
        </div>
    </div>
</template>

<style scoped>
    .Tester-Container {
        display: flex;
        height: 100%;
        width: 100%;
        max-width: 100%;
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
        overflow-x: hidden;
        border-radius: 4px;
        padding: 1%;
    }
    .Image-Contianer {
        display: grid;
        grid-template-columns: 150px 150px 150px;
        column-gap: 25px;
        row-gap: 5px;
        justify-content: center;
    }
    .Image-Contianer img {
        width: 150px;
        height: 150px;
    }
    .Image-Contianer h2 {
        justify-self: center;
    }
    .switch {
        position: relative;
        display: inline-block;
        width: 60px;
        height: 24px;
        margin: 1%;
    }
    .switch input {
        display: none;
    }
    .slider {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: #ccc;
        -webkit-transition: 0.4s;
         transition: 0.4s;
}
    .slider:before {
        position: absolute;
        content: "";
        height: 16px;
        width: 16px;
        left: 4px;
        bottom: 4px;
        background-color: var(--color-border);
        -webkit-transition: 0.4s;
        transition: 0.4s;
    }

    input:focus + .slider {
        box-shadow: 0 0 1px #101010;
    }
    input:checked + .slider:before {
        -webkit-transform: translateX(26px);
        -ms-transform: translateX(26px);
        transform: translateX(26px);
    }
    .slider.round {
        border-radius: 34px;
    }
    .slider.round:before {
        border-radius: 50%;
    }
</style>