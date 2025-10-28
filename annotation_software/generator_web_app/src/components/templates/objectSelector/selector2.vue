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
    <div class="configurationContainer" :class="{ 'tallConfigurationContainer': $route.name == 'crop-verifier' }">
        <div class="configurationMenu" :class="{ 'wideConfigurationMenu': $route.name == 'upload', 'tallConfigurationMenu': $route.name == 'crop-verifier'}">
            <h2> Schema Selection </h2>
            <div class="Table-Title"> 
                <p> Name </p>
                <p> Created </p>
                <p> Modified </p>
            </div>
            <figure>
                <button class="Entry" v-for="schema in pStore.schemas" @click="pStore.set_current_schema(schema)" :class="{Selected: pStore.CurrentSchema?.uuid == schema.uuid}">
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
            </figure>
        </div>
        <div class="configurationMenu" v-if="$route.name == 'auto-cropper'">
            <!-- <h2> Label Selection </h2>
            <div class="Table-Title"> 
                <p> Image </p>
                <p> Name </p>
                <p> Modified </p>
            </div> -->
            <table>
                <caption><h2>Label Selection</h2></caption>
                <th>Image</th>
                <th>Name</th>
                <th>Created</th>
            </table>
            <figure v-if="pStore.labels">
                <button class="Entry" v-for="label in pStore.labels" @click="pStore.set_current_labels(label)" :class="{Selected: pStore.label_idxs.includes(pStore.labels.indexOf(label))}">
                    <img v-bind:src="label?.image_link"></img>
                    <p> {{ label.name }} </p> 
                    <p> {{ label.modified.toLocaleString('en-US', { 
                        year: 'numeric', 
                        month: 'numeric', 
                        day: 'numeric', })}} 
                    </p>
                </button>
            </figure>
			<figure v-else>
				<p style="margin: 5%;"> 
					<i style="opacity: 50%"> * You must first select a schema before you can select 
					a label. If you cannot see any labels after selecting a 
					schema that is because the schema has no associated labels. </i>
				</p>
			</figure>
        </div>
        <div class="configurationMenu" :class="{ 'tallConfigurationMenu': $route.name == 'crop-verifier'}">
            <h2> Herd Unit Selection </h2>
            <div class="Table-Title"> 
                <p> Name </p>
                <p> Created </p>
                <p> Modified </p>
            </div>
            <figure>
                <button class="Entry" v-for="herdunit in pStore.herd_units" @click="pStore.set_current_herd_unit(herdunit) ":class="{Selected: pStore.CurrentHerdUnit?.uuid == herdunit.uuid}">
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
            </figure>
        </div>
        <div class="configurationMenu" v-if="$route.name != 'crop-verifier'">
            <h2> Model Selection </h2>
            <div class="Table-Title"> 
                <p> Name </p>
                <p> Created </p>
                <p> Modified </p>
            </div>
            <figure v-if="pStore.models">
                <button class="Entry" v-for="model in pStore.models" @click="pStore.set_current_model(model)" :class="{Selected: pStore.CurrentModel?.uuid == model.uuid}">
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
            </figure>
			<figure v-else="">
				<p style="margin: 5%;"> 
					<i style="opacity: 50%"> * You must first select a schema and Herd Unit before you can select 
					a model. If you cannot see any models after selecting a schema and Herd Unit that is because the selection has no viable models.
					Conisder double checking you survey selection if you aren't seeing a model you think you should. </i>
				</p>
			</figure>
        </div>
    </div>
</template>
<style scoped>
	.wideConfigurationMenu {
		grid-column: span 2;
		.Entry {
			width: 100%;
		}
	}
    .tallConfigurationMenu {
        height: 100% !important; 
        max-height: 100%
    }
    .tallConfigurationContainer {
		grid-template-columns: 1fr 1fr;
		grid-template-rows: auto;
    }
    table {
        width: 100%;
        overflow-y: auto;
    }
    tr {
        width: 100%;
    }
</style>