<script lang="ts">
import { useProjectStore } from "@/modules/stores/projectStore";
import { defineComponent } from "vue";

export default defineComponent({
    name: 'Cropper-Configurinator-3000',
    setup() {
        const pstore = useProjectStore();
        return { pstore }
    },
})
</script>
<template>
    <div class="Configuration-Container">
        <div class="Configuration-Menu" :class="{'Wide-Configuration-Menu': $route.name == 'upload'}">
            <h2> Schema Selection </h2>
            <div class="Table-Title"> 
                <p> Name </p>
                <p> Created </p>
                <p> Modified </p>
            </div>
            <figure>
                <button class="Entry" v-for="schema in pstore.schemas" @click="pstore.set_current_schema(schema)" :class="{Selected: pstore.CurrentSchema?.uuid == schema.uuid}">
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
        <div class="Configuration-Menu" v-if="$route.name == 'auto-cropper'">
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
            <figure v-if="pstore.labels">
                <button class="Entry" v-for="label in pstore.labels" @click="pstore.set_current_labels(label)" :class="{Selected: pstore.label_idxs.includes(pstore.labels.indexOf(label))}">
                    <img v-bind:src="label?.image_link"></img>
                    <p> {{ label.name }} </p> 
                    <p> {{ label.modified.toLocaleString('en-US', { 
                        year: 'numeric', 
                        month: 'numeric', 
                        day: 'numeric', })}} 
                    </p>
                </button>
            </figure>
			<figure v-else="">
				<p style="margin: 5%;"> 
					<i style="opacity: 50%"> * You must first select a schema before you can select 
					a label. If you cannot see any labels after selecting a 
					schema that is because the schema has no associated labels. </i>
				</p>
			</figure>
        </div>
        <div class="Configuration-Menu">
            <h2> Herd Unit Selection </h2>
            <div class="Table-Title"> 
                <p> Name </p>
                <p> Created </p>
                <p> Modified </p>
            </div>
            <figure>
                <button class="Entry" v-for="herdunit in pstore.herd_units" @click="pstore.set_current_herd_unit(herdunit) ":class="{Selected: pstore.CurrentHerdUnit?.uuid == herdunit.uuid}">
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
        <div class="Configuration-Menu">
            <h2> Model Selection </h2>
            <div class="Table-Title"> 
                <p> Name </p>
                <p> Created </p>
                <p> Modified </p>
            </div>
            <figure v-if="pstore.models">
                <button class="Entry" v-for="model in pstore.models" @click="pstore.set_current_model(model)" :class="{Selected: pstore.CurrentModel?.uuid == model.uuid}">
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
	.Wide-Configuration-Menu {
		grid-column: span 2;
		.Entry {
			width: 100%;
		}
	}
    table {
        width: 100%;
        overflow-y: auto;
    }
    tr {
        width: 100%;
    }
</style>