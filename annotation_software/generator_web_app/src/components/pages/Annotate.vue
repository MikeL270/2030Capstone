<script lang="ts">
import { createBatch, deleteBatch, createPredCrops} from '../../modules/apiV1Methods';
import type {Batches, Batch} from '../../types/interfaces';
import {Prediction, Image, Crop, Box, PredictionCrop} from '../../types/generatorobjects';
import { defineComponent } from 'vue'; 
import { Icon } from '@iconify/vue';



export default defineComponent({
    name: 'Annotator',
    data() {
        return {
            loaded: false,
            pred_crops_loaded: false,
            batch_params: {
                batch_size: 10,
                desired_class: 2,
                min_confidence: 0.9,
                herd_unit_id: 4,
                model_id: 3,
            },
            pred_crop_params: {

            },
            batches: {} as Batches,
            image_ids: [] as number[],
            batch_ids:[] as number[],
            image_idx: 0,
            current_batch: 0, // Overwritten on component mount 
            current_image: 0, // Overwritten on component mount
            predictions: [] as Prediction[],
            approved_predictions: [] as Prediction[],
        };
    },
    methods: {
        async create_batch(batch_params: Record<string, any>) {
            const responseData = await createBatch(batch_params);
            const batch_id = Object.keys(responseData)[0];
            this.batches[+batch_id] = Object.values(responseData)[0] as Batch;
            this.batch_ids.push(+batch_id);
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
        },
        async set_current_image(image_id: number) {
            this.pred_crops_loaded = false;
            this.current_image = image_id;
            await this.create_pred_crops(this.current_batch, this.current_image);
            this.predictions = this.batches[this.current_batch][this.current_image]['predictions'];
            this.pred_crops_loaded=true;
        },
         async start_up() {
            await this.create_batch(this.batch_params);
            await this.set_current_batch(+Object.keys(this.batches)[0]);
            this.set_current_image(this.image_ids[this.image_idx]);
            this.loaded = true;
            document.addEventListener('keydown', this.handle_key_press)
        },
        async next_image() {
            if (this.current_image == this.image_ids[this.image_ids.length - 1]) {
                await this.create_batch(this.batch_params);
                await this.set_current_batch(this.current_batch + 1);
                this.image_idx = 0;
                await this.set_current_image(this.image_ids[this.image_idx]);
                return;
            };
            this.image_idx += 1;
            await this.set_current_image(this.image_ids[this.image_idx]);
        },
        async last_image() {
            if (this.current_image == this.image_ids[0] && this.current_batch == this.batch_ids[0]) {
                return;
            }
            else if (this.current_image == this.image_ids[0] && this.current_batch == this.batch_ids[0]) {
                await this.set_current_batch(this.current_batch - 1);
                this.image_idx = this.image_ids.length - 1;
                await this.set_current_image(this.image_ids[this.image_idx]);
                return;
            } else {
                this.image_idx -= 1;
                await this.set_current_image(this.image_ids[this.image_idx]);
            }
        },
        toggle_approval(pred_crop: PredictionCrop) {
            for (const pred of this.predictions) {
                if (pred.id == pred_crop.pred_crop_id) {
                    if (this.approved_predictions.includes(pred)) {
                        delete this.approved_predictions[this.approved_predictions.indexOf(pred)];
                        pred_crop.approved = false;
                        console.log('removed prediction')

                    } else {
                        this.approved_predictions.push(pred);
                        pred_crop.approved = true;
                        console.log('approved prediction')
                    }
                    console.log(pred_crop)

                };
            };
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
                }
            };
        },
    },
    mounted() {
        this.start_up();
    },

    unmounted() {
        for (const batch_id of this.batch_ids) {
            this.delete_batch(+batch_id);
        }
    },
});
</script>

<template>
    <div class="Contianer"> 
        <div class="Tool-Bar" v-if="loaded">
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
                <button>
                    <Icon icon="icon-park-outline:one-key" width="16" height="16"/>
                    Approve All
                </button>
            </div>
            <div class="Tool">
                <button>
                    <Icon icon="icon-park-outline:zero-key" width="16" height="16"/>
                    Reject All
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
            </div @click="submit()">
            <div>

            </div>
        </div>
        <div class="Annotator-Container">
            <figure v-for="crop in batches[current_batch][current_image]['pred_crops']" v-if="pred_crops_loaded"> 
                <button @click="toggle_approval(crop)">
                <h2> Score: {{ crop.score?.toFixed(3) }} </h2>
                <img v-bind:src="crop.url":class="{approved: crop.approved == true}">
                </button>
            </figure>
        </div>
 
    </div>

</template>
<style scoped>
.Contianer {
    display: flex;
    flex-direction: column;
    height: 100%;
    width: 100%;
    align-items: center;
}
.Tool-Bar {
    display: flex;
    background-color: var(--color-background-mute);
    align-self: flex-start;
    width: 100%;
    height: 6vh;
    padding: 4px;
    gap: 10px;
}
.Tool-Bar .Tool {
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 2px;
}
.Tool-Bar .Tool select {
    background-color: none;
}
.Tool-Bar .Tool button {
    display: flex;
    justify-content: center;
    align-items: center;
    background-color: var(--color-background-soft);
    color: var(--color-text);
    border-radius: 4px;
    box-shadow: 0 4px 6px 2px var(--color-background-soft);
    height: 24px;
}
.Annotator-Container {
    align-self: center;
    display: grid;
    grid-auto-columns: 150px;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    align-self: center;
    max-width: 80%;
    gap: 10px;
    justify-content: center;
    align-items: center;
    margin-top: auto;
    margin-bottom: auto;
}
.Annotator-Container figure {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    border-radius: 4px;
}
.Annotator-Container button {
    background-color: var(--color-background-mute);
    color: var(--color-text);
    box-shadow: 0 4px 6px 2px var(--color-background-soft);
    border-radius: 4px;
}
.Annotator-Container img {
    width: 150px;
    height: 150px;
}
.Annotator-Container .approved {
    border: solid 4px rgba(255, 0, 0, 0.571);
}
</style>