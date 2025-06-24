<script lang="ts">
import { getBatchIds, createBatch, deleteBatch, createPredCrops, approvePredictions, createFullCrops,
         getSchema, } from '../../modules/apiV1Methods';
import type { Batches, Batch } from '@/types/generatorobjects';
import {Prediction, Image, Crop, Box, PredictionCrop} from '@/types/generatorobjects';
import { defineComponent, computed, ref } from 'vue'; 

// Typescript is proving to be very annoying when doing basically anything

export default defineComponent({
    name: 'Auto-Cropper',
    data() {
        return {
            ready: false,
            loading: false,
            pred_crops_loaded: false,
            batch_loaded: false,
            toggle_boxes: false, 
            selected_class_name: 'pronghorn',
            batch_params: {
                batch_size: 50,
                desired_class: 2,
                min_confidence: 0.90,
                herd_unit_id: 5,
                model_id: 4,
            },
            batches: {} as Batches,
            image_ids: [] as number[],
            image_idx: 0,
            current_batch: 0, // Overwritten on component mount 
            current_image: 0, // Overwritten on component mount
            predictions: [] as Prediction[],
            approved_predictions: [] as number[],
            crop_size: 2100,
        };
    },
    methods: {
         async get_batch_ids() {
            const batch_ids = await getBatchIds();
            return batch_ids;
        },
        async create_batch(batch_params: Record<string, number>) {
            this.loading = true;
            const responseData = await createBatch(batch_params);
            const batch_id = Object.keys(responseData)[0];
            this.batches[+batch_id] = Object.values(responseData)[0] as Batch;
            this.image_ids = Object.values(this.batches[+batch_id])
        },
        async create_pred_crops(batch_id: number, image_id: number) {
            this.loading = true;
            const responseData = await createPredCrops(batch_id, image_id);
            this.batches[batch_id][image_id]['pred_crops'] = responseData;
            this.loading = false;
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
            this.loading=true;
            this.current_image = image_id;
            await this.create_pred_crops(this.current_batch, this.current_image);
            this.predictions = this.batches[this.current_batch][this.current_image]['predictions'];
            // if (this.toggle_boxes) {
            //     for (const crop of this.batches[this.current_batch][this.current_image]['pred_crops']) {

            //     }
            // }
            this.pred_crops_loaded=true;
            this.loading=false;
        },
         async start_up() {
            const batch_ids = await this.get_batch_ids()
            if (batch_ids.length > 0) {
                for (const batch_id of batch_ids) {
                this.delete_batch(+batch_id);
                }
            }
            await this.create_batch(this.batch_params);
            await this.set_current_batch(+Object.keys(this.batches)[0]);
            this.set_current_image(this.image_ids[this.image_idx]);
            document.addEventListener('keydown', this.handle_key_press);
            this.ready = true;
        },
        async next_image() {
           if (this.loading) {
                console.log('action blocked!');
                return;
            }
            this.loading = true;
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
            this.loading = false;
        },
        async last_image() {
            if (this.loading) {
                console.log('action blocked!');
                return;
            }
            this.loading = true;
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
                if (pred.id == pred_crop.id) {
                    if (this.approved_predictions.includes(pred.id)) {
                        delete this.approved_predictions[this.approved_predictions.indexOf(pred.id)];
                        pred_crop.approved = false;
                    } else {
                        this.approved_predictions.push(pred.id);
                        pred_crop.approved = true;
                    }
                }
            };
        },
        async submit() {
            await approvePredictions(this.approved_predictions, this.current_batch, this.current_image);
            if (this.approved_predictions.length > 0) {
                console.log('Cropping')
                await this.create_full_crops();
            }
            await this.next_image();
        },
        async approve_all() {
            if (this.loading) {
                console.log('action blocked!');
                return;
            }
            this.loading = true;
            for (const pred of this.predictions) this.approved_predictions.push(pred.id);
            this.loading = false;
            await this.submit();
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
                case 'Space': {
                    this.approve_all();
                    break;
                };
                case 'Enter': {
                    this.submit();
                    break;
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
    <div class="Page-Container" > 
        <div id="Tool-Bar" v-if="ready">
            <div class="Tool">
                <label for="batches-explorer"> 
                    <Icon icon="carbon:batch-job-step" width="16" height="16"/>
                    Batch:
                </label>
                <select id="batches-explorer" v-model="current_batch" @change="set_current_batch(+current_batch)">
                    <option v-for="batch_id in Object.keys(batches)">
                        {{ batch_id }}
                    </option>
                </select>
            </div>
            <div class="Tool">
            <label for="image-explorer">
                    <Icon icon="material-symbols:image" width="16" height="16"/>
                    Image: 
                </label>
                <select id="image-explorer" v-model="current_image" @change="set_current_image(+current_image)">
                    <option v-for="image_id in Object.keys(batches[current_batch])">
                            {{ image_id }}
                    </option>
                </select>
                
            </div>
            <div class="Tool">
                <label for="boxes_toggle">
                    <Icon icon="foundation:annotate" width="16" height="16"/>
                    Outlines:
                 </label>
                <input type="checkbox" id="boxes_toggle" v-model="toggle_boxes">
                
            </div>
            <div class="Tool">
                <button @click="approve_all()">
                    <Icon icon="uis:space-key" width="16" height="16"/>
                    Approve All
                </button>
            </div>  
            <div class="Tool">
                <button @click="submit()">
                    <Icon icon="vaadin:enter-arrow" width="16" height="16"/>
                    Submit
                </button>
            </div>
            <div class="Tool">
                <button @click="last_image()">
                    <Icon icon="ooui:next-rtl" width="16" height="16"/>
                    Previous 
                </button>
            </div>
            <div class="Tool">
                <button @click="next_image()">
                    <Icon icon="ooui:next-ltr" width="16" height="16"/>
                    Next 
                </button>
            </div>
        </div>
        <div id="Annotator-Container" v-if="pred_crops_loaded">
            <figure v-for="predCrop in batches[current_batch][current_image]['pred_crops']" :key="predCrop.id"> 
                <button @click="toggle_approval(predCrop)">
                <h2> Score: {{ predCrop.score?.toFixed(3) }} </h2>
                <img v-bind:src="predCrop.url":class="{approved: predCrop.approved == true} ">
                </button>
            </figure>
        </div>
        <div id="Annotator-Placeholder" v-else-if="loading ">
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
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
    justify-content: center;
    align-items: center;
    background-color: var(--wygf-bg-blue);
    align-self: flex-start;
    border-radius: 4px 4px 0px 0px;
    width: 100%;
    min-height: 8vh;
    max-height: 20vh;
    padding: 0.5%;
    gap: 1%;
    grid-row-gap: 10px;
}
#Tool-Bar .Tool {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    max-height: 5vh;
    display: flex;
    color: var(--wygf-yellow);
    justify-content: center;
    align-items: center;
    min-width: 10vw;
    font-size: 1em;
    padding: 1%
 }
 #Tool-Bar .Tool:hover {
    color: var(--color-text);
 }
#Tool-Bar .Tool select {
    border-radius: 4px;
}
#Tool-Bar .Tool label {
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: inherit;
    color: inherit;
    margin-right: 5%;
}
#Tool-Bar .Tool input {
    accent-color: var(--color-background-mute);
}
#Tool-Bar .Tool button {
    background: none;
    display: flex;
    justify-content: center;
    align-items: center;
    color: inherit;
    border-radius: 4px;
    width: 100%;
    height: 100%;
    border: none;
    font-size: 1em;
}
#Tool-Bar .Tool button:active {
        box-shadow: 0 2px 3px 1px var(--color-background);
}
#Tool-Bar .Tool  svg {
    margin-right: 5%;
}
#Annotator-Container {
    align-self: center;
    display: grid;
    grid-auto-columns: 11.5vw;
    grid-template-columns: repeat(auto-fit, minmax(11.5vw, 1fr));
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
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    background-color: var(--wygf-bg-blue);
    border: none;
    color: var(--wygf-yellow);
    box-shadow: 0 4px 6px 2px var(--color-background);
    padding: 3%;
    border-radius: 4px;
    
}
#Annotator-Container button:hover {
    color: var(--color-text)
}
#Annotator-Container button h2 {
    padding: 2%;
    font-size: 1.2em;
}
 #Annotator-Container img {
    width: 10.5vw;
    height: 10.5vw;
    border-radius: 4px;
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