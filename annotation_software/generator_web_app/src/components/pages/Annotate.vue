<script lang="ts">
import { getBatchIds, createBatch, deleteBatch, createPredCrops, approvePredictions, createFullCrops} from '../../modules/apiV1Methods';
import type {Batches, Batch} from '../../types/interfaces';
import {Prediction, Image, Crop, Box, PredictionCrop} from '../../types/generatorobjects';
import { defineComponent } from 'vue'; 
import { ref } from 'vue';


export default defineComponent({
    name: 'Annotator',
    data() {
        return {
            loaded: false,
            pred_crops_loaded: false,
            toggle_boxes: false, 
            batch_params: {
                batch_size: 10,
                desired_class: 2,
                min_confidence: 0.9,
                herd_unit_id: 4,
                model_id: 3,
            },
            batches: {} as Batches,
            image_ids: [] as number[],
            image_idx: 0,
            current_batch: 0, // Overwritten on component mount 
            current_image: 0, // Overwritten on component mount
            predictions: [] as Prediction[],
            approved_predictions: [] as Prediction[],
            crop_size: 2100,
            cv: null as null | any,
        };
    },
    methods: {
         async get_batch_ids() {
            const batch_ids = await getBatchIds();
            return batch_ids;
        },
        async create_batch(batch_params: Record<string, any>) {
            const responseData = await createBatch(batch_params);
            const batch_id = Object.keys(responseData)[0];
            this.batches[+batch_id] = Object.values(responseData)[0] as Batch;
            this.image_ids = Object.values(this.batches[+batch_id])
        },
        async create_pred_crops(batch_id: number, image_id: number) {

            const responseData = await createPredCrops(batch_id, image_id);
            this.batches[batch_id][image_id]['pred_crops'] = responseData;
        },
        async delete_batch(batch_id: number) {
            await deleteBatch(batch_id);
            delete this.batches[batch_id];
        },
        async set_current_batch(batch_id: number) {
            this.pred_crops_loaded = false;
            this.current_batch = batch_id;
            this.image_ids = Object.keys(this.batches[this.current_batch]).map(Number);
            this.set_current_image(this.image_ids[0]);
        },
        draw_pred_box(crop: PredictionCrop, image_ref: HTMLCanvasElement) {
            const image = ref(image_ref);

        },
        async set_current_image(image_id: number) {
            this.pred_crops_loaded = false;
            this.current_image = image_id;
            await this.create_pred_crops(this.current_batch, this.current_image);
            this.predictions = this.batches[this.current_batch][this.current_image]['predictions'];
            if (this.toggle_boxes) {
                for (const crop of this.batches[this.current_batch][this.current_image]['pred_crops']) {

                }
            }
            this.pred_crops_loaded=true;
        },
         async start_up() {
            const batch_ids = await this.get_batch_ids()
            console.log(batch_ids.length)
            if (batch_ids.length > 0) {
                for (const batch_id of batch_ids) {
                this.delete_batch(+batch_id);
                }
            }
            await this.create_batch(this.batch_params);
            await this.set_current_batch(+Object.keys(this.batches)[0]);
            this.set_current_image(this.image_ids[this.image_idx]);
            this.loaded = true;
            document.addEventListener('keydown', this.handle_key_press)
        },
        async next_image() {
            if (this.approved_predictions.length > 0) {
                await this.submit();
            };
            if (this.current_image == this.image_ids[this.image_ids.length - 1]) {
                await this.create_batch(this.batch_params);
                await this.set_current_batch(this.current_batch + 1);
                this.image_idx = 0;
                await this.set_current_image(this.image_ids[this.image_idx]);
                return;
            };
            this.image_idx += 1;
            await this.set_current_image(this.image_ids[this.image_idx]);
            this.approved_predictions = [];
        },
        async last_image() {
            if (this.approved_predictions.length > 0) {
                this.approved_predictions = [];
            };
            if (this.current_image == this.image_ids[0] && this.current_batch == 1) {
                console.log("cant go back")
                return;
            }
            else if (this.current_image == this.image_ids[0] && this.current_batch > 1) {
                await this.set_current_batch(this.current_batch - 1);
                this.image_idx = this.image_ids.length - 1;
                await this.set_current_image(this.image_ids[this.image_idx]);
                return;
            } else {
                this.image_idx -= 1;
                await this.set_current_image(this.image_ids[this.image_idx]);
            };
        },
        toggle_approval(pred_crop: PredictionCrop) {
            for (const pred of this.predictions) {
                if (pred.id == pred_crop.pred_crop_id) {
                    if (this.approved_predictions.includes(pred)) {
                        delete this.approved_predictions[this.approved_predictions.indexOf(pred)];
                        pred_crop.approved = false;
                    } else {
                        this.approved_predictions.push(pred);
                        pred_crop.approved = true;
                    }
                };
            };
        },
        async approve_all() {
            this.approved_predictions = [...this.predictions];
            this.next_image();
        },
        async submit() {
            await approvePredictions(this.approved_predictions, this.current_batch, this.current_image);
            await this.create_full_crops();
        },
        async create_full_crops() {
            var responseData = await createFullCrops(this.current_batch, this.current_image, this.crop_size);
            this.batches[this.current_batch][this.current_image]['crops'] = responseData;
        },
        handle_key_press(event: KeyboardEvent) {
            switch(event.code) {
                case 'ArrowRight': {
                    this.next_image();
                    break;
                };
                case 'ArrowLeft': {
                    this.last_image();
                    break;
                };
                case 'Digit1': {
                    this.approve_all();
                }
            };
        },
    },
    mounted() {
        this.start_up();
    },
    async unmounted() {
        var batch_ids: number[] = await this.get_batch_ids();
         for (const batch_id of batch_ids) {
             this.delete_batch(+batch_id);
         }
    },
});
</script>

<template>
    <div class="Page-Container"> 
        <div id="Tool-Bar" v-if="loaded">
            <div class="Tool">
                <label for="batches-explorer"> Batch: </label>
                <select id="batches-explorer" v-model="current_batch" @change="set_current_batch(+current_batch)">
                    <option v-for="batch_id in Object.keys(batches)">
                        {{ batch_id }}
                    </option>
                </select>
            </div>
            <div class="Tool">
                <label for="image-explorer"> Image: </label>
                <select id="image-explorer" v-model="current_image" @change="set_current_image(+current_image)">
                    <option v-for="image_id in Object.keys(batches[current_batch])">
                            {{ image_id }}
                    </option>
                </select>
                
            </div>
            <div class="Tool">
                <label for="boxes_toggle">Toggle Boxes: </label>
                <input type="checkbox" id="boxes_toggle" v-model="toggle_boxes">
                
            </div>
            <div class="Tool">
                <button @click="approve_all()">
                    <Icon icon="icon-park-outline:one-key" width="16" height="16"/>
                    Approve All
                </button>
            </div>
            <div class="Tool">
                <button @click="last_image()">
                    <Icon icon="ooui:next-rtl" width="16" height="16"/>
                    Previous Image
                </button>
            </div>
            <div class="Tool">
                <button @click="next_image()">
                    <Icon icon="ooui:next-ltr" width="16" height="16"/>
                    Next Image
                </button>
            </div>
        </div>
        <div id="Annotator-Container" v-if="pred_crops_loaded">
            <figure v-for="predCrop in batches[current_batch][current_image]['pred_crops']" :key="predCrop.pred_crop_id"> 
                <button @click="toggle_approval(predCrop)">
                <h2> Score: {{ predCrop.score?.toFixed(3) }} </h2>
                <img v-bind:src="predCrop.url":class="{approved: predCrop.approved == true}">
                </button>
            </figure>
        </div>
        <div id="Annotator-Placeholder" v-else>
            <Icon icon="eos-icons:three-dots-loading" width="96" height="96" />
        </div>
 
    </div>

</template>
<style scoped>
.Page-Container {
    display: flex;
    flex-direction: column;
}
#Tool-Bar {
    display: flex;
    justify-content: center;
    align-items: center;
    background-color: var(--wygf-bg-blue);
    align-self: flex-start;
    border-radius: 4px 4px 0px 0px;
    width: 100%;
    height: 7vh;
}
#Tool-Bar .Tool {
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    min-width: 10vw;
    margin: none;
 }
#Tool-Bar .Tool select {
    border-radius: 4px;
}
#Tool-Bar .Tool label {
    color: var(--wygf-yellow);
    margin-right: 5%;
}
#Tool-Bar .Tool input {
    accent-color: var(--color-background-mute);
}
#Tool-Bar .Tool button {
    display: flex;
    justify-content: center;
    align-items: center;
    background-color: var(--wygf-bg-blue);
    color: var(--wygf-yellow);
    border-radius: 4px;
    width: 100%;
    border: none;
    padding: 0px;
}
#Tool-Bar .Tool button:hover {
    color: var(--color-text);
    border: 1px var(--color-text);
}
#Tool-Bar .Tool button svg {
    margin-right: 5%;
}

#Annotator-Container {
    align-self: center;
    display: grid;
    grid-auto-columns: 10.5vw;
    grid-template-columns: repeat(auto-fit, minmax(10.5vw, 1fr));
    align-self: center;
    max-width: 70%;
    gap: 15px;
    justify-content: center;
    align-items: center;
    margin-top: auto;
    margin-bottom: auto;
    overflow: auto;
}
#Annotator-Container figure {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    border-radius: 4px;
}
#Annotator-Container button {
    background-color: var(--wygf-bg-blue);
    border: none;
    color: var(--wygf-yellow);
    box-shadow: 0 4px 6px 2px var(--color-background);
    border-radius: 4px;
    
}
#Annotator-Container button:hover {
    color: var(--color-text)
}
#Annotator-Container button h2 {
    padding: 2%;
}
 #Annotator-Container img {
    width: 10.5vw;
    height: 10.5vw;
    margin: 1%;
} 
#Annotator-Container .approved {
    border: solid 4px var(--wygf-yellow);
}
#Annotator-Placeholder {
    height: 100%;
    width: 80%;
    display: flex;
    justify-content: center;
    align-items: center;
}
</style>