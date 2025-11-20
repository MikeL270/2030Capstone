<script lang="ts">
import { useProjectStore } from "@/modules/stores/projectStore";
import { defineComponent } from "vue";

export default defineComponent({
    name: 'Cropper-Configurinator-3000',
    setup() {
        const pStore = useProjectStore();
        return { pStore }
    },
})
</script>
<template>
    <div class="configurationContainer" :class="{ 'tallConfigurationContainer': $route.name == 'crop-verifier' || $route.name == 'upload' }">
        <div class="configurationMenu" :class="{ 'tallConfigurationMenu': $route.name == 'crop-verifier' || $route.name == 'upload'}">
            <table>
                <caption><h3>Schema Selection</h3></caption>
                <th>Name</th>
                <th>Created</th>
                <th>Modified</th>
            </table>
            <div class="configurationItemsWrapper">
                <button class="entry" v-for="schema in pStore.schemas" @click="pStore.set_current_schema(schema)" :class="{Selected: pStore.CurrentSchema?.uuid == schema.uuid}">
                    <p> {{ schema.name }} </p> 
                    <p> {{ schema.created.toLocaleString('en-US', { 
                        year: 'numeric', 
                        month: 'numeric', 
                        day: 'numeric', 
                        }) }} 
                    </p>
                    <p> {{ schema.modified.toLocaleString('en-US', { 
                        year: 'numeric', 
                        month: 'numeric', 
                        day: 'numeric', 
                        }) }} 
                    </p>
                </button>
            </div>
        </div>
        <div class="configurationMenu" v-if="$route.name == 'auto-cropper'">
            <table>
                <caption><h3>Label Selection</h3></caption>
                <th>Image</th>
                <th>Name</th>
                <th>Created</th>
            </table>
            <div class="configurationItemsWrapper">
                <button class="entry" v-for="label in pStore.labels" @click="pStore.set_current_labels(label)" :class="{Selected: pStore.label_idxs.includes(pStore.labels.indexOf(label))}">
                    <img v-bind:src="label?.image_link"></img>
                    <p>{{ label.name }} </p> 
                    <p> {{ label.modified.toLocaleString('en-US', { 
                        year: 'numeric', 
                        month: 'numeric', 
                        day: 'numeric', })}} 
                    </p>
                    </button>
            </div>
            
        </div>
        <div class="configurationMenu" :class="{ 'tallConfigurationMenu': $route.name == 'crop-verifier' || 'upload'}">
            <table>
                <caption><h3>Herd Unit Selection</h3></caption>
                <th>Name</th>
                <th>Created</th>
                <th>Modified</th>
            </table>
            <div class="configurationItemsWrapper">
                <button class="entry" v-for="herdunit in pStore.herd_units" @click="pStore.set_current_herd_unit(herdunit) ":class="{Selected: pStore.CurrentHerdUnit?.uuid == herdunit.uuid}">
                    <p> {{ herdunit.name }} </p> 
                    <p> {{ herdunit.created.toLocaleString('en-US', { 
                        year: 'numeric', 
                        month: 'numeric', 
                        day: 'numeric', 
                        }) }} 
                    </p>
                    <p> {{ herdunit.modified.toLocaleString('en-US', { 
                        year: 'numeric', 
                        month: 'numeric', 
                        day: 'numeric', 
                        }) }} 
                    </p>
                </button>
            </div>
                
        </div>
        <div class="configurationMenu" v-if="$route.name == 'auto-cropper'">
            <table>
                <caption><h3>Label Selection</h3></caption>
                <th>Name</th>
                <th>Created</th>
                <th>Modified</th>
            </table>
            <div class="configurationItemsWrapper">
                <button class="entry" v-for="model in pStore.models" @click="pStore.set_current_model(model)" :class="{Selected: pStore.CurrentModel?.uuid == model.uuid}">
                <p> {{ model.name }} </p> 
                <p> {{ model.created.toLocaleString('en-US', { 
                    year: 'numeric', 
                    month: 'numeric', 
                    day: 'numeric', 
                    }) }} 
                </p>
                <p> {{ model.modified.toLocaleString('en-US', { 
                    year: 'numeric', 
                    month: 'numeric', 
                    day: 'numeric', 
                    }) }} 
                </p>
            </button>
            </div>
            
        </div>
    </div>
</template>
<style scoped>
    table {
        width: 100%;
        overflow-y: auto;
    }
    tr {
        width: 100%;
    }
</style>