<script lang="ts">
import { useProjectStore } from "@/modules/stores/projectStore";
import { defineComponent } from "vue";

export default defineComponent({
    name: 'Project-Selector',
    setup() {
        const project_store = useProjectStore();
        if (!project_store.projects) project_store.get_projects();
        return { project_store};
    },
})
</script>
<template>
	<div class="Configuration-Container">
		<div class="Configuration-Menu">
			<h2> Project Selection </h2>
			<div class="Table-Title"> 
                <p> Name </p>
                <p> Created </p>
                <p> Modified </p>
                <p> External ID </p> 
            </div>
			<figure>
				<button class="Entry" v-for="project in project_store.projects" @click="project_store.set_current_project(project)" :class="{Selected: project_store.CurrentProject?.uuid == project.uuid}">
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
                    <p> {{ project.uuid }} </p>
				</button>
			</figure>
		</div>
		<div class="Configuration-Menu">
			<h2> Survey Selection </h2>
            <div class="Table-Title"> 
                <p> Name </p>
                <p> Created </p>
                <p> Modified </p>
                <p> External ID </p> 
            </div>
            <figure v-if="project_store.surveys">
                <button class="Entry" v-for="survey in project_store.surveys" @click="project_store.set_current_survey(survey)" :class="{Selected: project_store.CurrentSurvey?.uuid == survey.uuid}">
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
                    <p> {{ survey.uuid }} </p>
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
	.Configuration-Container {
		grid-template-columns: 1fr 1fr;
		grid-template-rows: auto;
    }
	.Configuration-Menu {
		height: 100% !important;
		max-height: 100%;
	}
</style>

