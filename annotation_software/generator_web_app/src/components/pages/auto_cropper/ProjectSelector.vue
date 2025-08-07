<script lang="ts">
import { useProjectStore } from "@/modules/stores/projectStore";
import { defineComponent } from "vue";
import { Project } from "@/types/generatorobjects";
import { mapState } from "pinia";

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
  <div id="Projects-Table-Structure">
    <h2> Project Selection </h2>   
    <div id="Table-Title"> 
        <p> Name </p>
        <p> Created </p>
        <p> Modified </p>
        <p> External ID </p> 
    </div>
    <figure>
        <button class="Project" v-for="project in project_store.projects" @click="project_store.set_current_project(project)" :class="{Selected: project_store.CurrentProject?.uuid == project.uuid}">
            <p> {{ project.name }} </p> 
            <p> {{ project.created.toLocaleString('en-US', { 
                    year: 'numeric', 
                    month: 'numeric', 
                    day: 'numeric',  
                    }) }} </p>
            <p> {{ project.modified.toLocaleString('en-US', { 
                    year: 'numeric', 
                    month: 'numeric', 
                    day: 'numeric', 
                    }) }} </p>
            <p> {{ project.uuid }} </p>
        </button>
    </figure>
  </div>
</template>
<style scoped>
    #Table-Title {
        margin-bottom: auto;
        display: grid;
        grid-template-columns: 1fr 1fr 1fr 1fr;
        gap: 5px;
        justify-content: center;
        text-align: center;
        align-items: center;
        height: 7vh !important;
        font-weight: 900;
        font-size: 1.25em;
        border-radius: 0px !important;
    }
    #Projects-Table-Structure {
        width: 67vw;
        height: 100%;
        border-radius: 8px 8px 8px 8px;
        box-shadow: 0 8px 12px 4px var(--color-background);
        border: solid 1px var(--color-background);
        overflow: hidden;
        display: flexbox;
        justify-content: center;
        align-items: center;
        text-align: center;
        overflow-y: auto;
        scrollbar-color: var(--color-text) transparent;
    } 
    .Project {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr 1fr;
        height: 10vh;
        gap: 5px;
        width: 98%;
        margin: 0% 3% 1% 1%;
        border-radius: 8px;
        border: solid 1px var(--color-background);
        color: var(--color-text);
        background: none;
        font-size: 1.10em;
        p {
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
        }
    }
    .Project:hover {
        color: white;
        box-shadow: 0 2px 4px 2px var(--color-background);
    }
    .Selected {
        color: var(--wygf-yellow);
        box-shadow: 0 2px 4px 2px var(--color-background);
    }
    
</style>