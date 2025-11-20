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
			<table>
                <caption><h3>Project Selection</h3></caption>
                <th>Name</th>
                <th>Created</th>
                <th>Modified</th>
            </table>
			<div class="configurationItemsWrapper">
				<button class="entry" v-for="project in pStore.projects" 
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
			</div>
		</div>
		<div class="configurationMenu">
			<table>
                <caption><h3>Survey Selection</h3></caption>
                <th>Name</th>
                <th>Created</th>
                <th>Modified</th>
            </table>
            <div class="configurationItemsWrapper">
                <button class="entry" v-for="survey in pStore.surveys" @click="pStore.set_current_survey(survey)" :class="{Selected: pStore.CurrentSurvey?.uuid == survey.uuid}">
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
            </div>
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
    table {
        width: 100%;
        overflow-y: auto;
    }
    tr {
        width: 100%;
    }
</style>

