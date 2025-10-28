<script lang="ts">
import { useProjectStore } from "@/modules/stores/projectStore";
import { defineComponent } from "vue";

export default defineComponent({
    name: 'Project-Selector',
    setup() {
        const pStore = useProjectStore();
        if (pStore.projects.length == 0) pStore.get_projects();
        return { pStore};
    },
})
</script>
<template>
	<div class="configurationContainer">
		<div class="configurationMenu">
			<h2> Project Selection </h2>
			<div class="Table-Title"> 
                <p> Name </p>
                <p> Created </p>
                <p> Modified </p>
            </div>
			<figure>
				<button class="Entry" v-for="project in pStore.projects" 
				@click="pStore.set_current_project(project)" 
				:class="{Selected: pStore.CurrentProject?.uuid == project.uuid}">
					<p> {{ project.name }} </p> 
                    <p> {{ project.created.toLocaleString('en-US', { 
                        year: 'numeric', 
                        month: 'numeric', 
                        day: 'numeric', 
                        }) }} 
                    </p>
                    <p> {{ project.modified.toLocaleString('en-US', { 
                        year: 'numeric', 
                        month: 'numeric', 
                        day: 'numeric', 
                        }) }} 
                    </p>
				</button>
			</figure>
		</div>
		<div class="configurationMenu">
			<h2> Survey Selection </h2>
            <div class="Table-Title"> 
                <p> Name </p>
                <p> Created </p>
                <p> Modified </p>
            </div>
            <figure v-if="pStore.surveys">
                <button class="Entry" v-for="survey in pStore.surveys" @click="pStore.set_current_survey(survey)" :class="{Selected: pStore.CurrentSurvey?.uuid == survey.uuid}">
                    <p> {{ survey.name }} </p> 
                    <p> {{ survey.created.toLocaleString('en-US', { 
                        year: 'numeric', 
                        month: 'numeric', 
                        day: 'numeric', 
                        }) }} 
                    </p>
                    <p> {{ survey.modified.toLocaleString('en-US', { 
                        year: 'numeric', 
                        month: 'numeric', 
                        day: 'numeric', 
                        }) }} 
                    </p>

                </button>
            </figure>
			<figure v-else>
				<p style="margin: 5%;"> 
					<i style="opacity: 50%"> * You must first select a project before you can select 
					a survey. If you cannot see any surveys after selecting a 
					project that is because the project has no associated surveys </i>
				</p>
			</figure>
		</div>
	</div>
</template>
<style scoped>
	.configurationContainer {
		grid-template-columns: 1fr 1fr;
		grid-template-rows: auto;
    }
	.configurationMenu {
		height: 100% !important;
		max-height: 100%;
	}
</style>

