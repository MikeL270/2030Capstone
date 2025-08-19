<script lang="ts">
import { useProjectStore } from "@/modules/stores/projectStore";
import { defineComponent } from "vue";

export default defineComponent({
    name: 'Cropper-Configurinator-3000',
    setup() {
        const project_store = useProjectStore();
        return { project_store }
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
                <p> External ID </p> 
            </div>
            <figure>
                <button class="Entry" v-for="schema in project_store.schemas" @click="project_store.set_current_schema(schema)" :class="{Selected: project_store.CurrentSchema?.uuid == schema.uuid}">
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
                    <p> {{ schema.uuid }} </p>
                </button>
            </figure>
        </div>
        <div class="Configuration-Menu" v-if="$route.name == 'auto-cropper'">
            <h2> Label Selection </h2>
            <div class="Table-Title"> 
                <p> Name </p>
                <p> Created </p>
                <p> Modified </p>
                <p> External ID </p> 
            </div>
            <figure v-if="project_store.labels">
                <button class="Entry" v-for="label in project_store.labels" @click="project_store.set_current_label(label)" :class="{Selected: project_store.CurrentLabel?.uuid == label.uuid}">
                    <p> {{ label.name }} </p> 
                    <p> {{ label.created.toLocaleString('en-US', { 
                        year: 'numeric', 
                        month: 'numeric', 
                        day: 'numeric', })}} 
                    </p>
                    <p> {{ label.modified.toLocaleString('en-US', { 
                        year: 'numeric', 
                        month: 'numeric', 
                        day: 'numeric', })}} 
                    </p>
                    <p> {{ label.uuid }} </p>
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
                <p> External ID </p> 
            </div>
            <figure>
                <button class="Entry" v-for="herdunit in project_store.herd_units" @click="project_store.set_current_herd_unit(herdunit) ":class="{Selected: project_store.CurrentHerdUnit?.uuid == herdunit.uuid}">
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
                        <p> {{ herdunit.uuid }} </p>
                </button>
            </figure>
        </div>
        <div class="Configuration-Menu">
            <h2> Model Selection </h2>
            <div class="Table-Title"> 
                <p> Name </p>
                <p> Created </p>
                <p> Modified </p>
                <p> External ID </p> 
            </div>
            <figure>
                <button class="Entry" v-for="model in project_store.models" @click="project_store.set_current_model(model)" :class="{Selected: project_store.CurrentModel?.uuid == model.uuid}">
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
                        <p> {{ model.uuid }} </p>
                </button>
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
</style>