<script lang="ts">
// https://serversideup.net/blog/file-uploads-using-fetch-api-and-vuejs/
// https://blog.logrocket.com/customizing-drag-drop-file-uploading-vue/#creating-advanced-dropzone
import { defineComponent } from 'vue';
import { ref } from 'vue';
import { HerdUnit, Project, Survey, Model, Schema } from '@/types/generatorobjects';
import { getProjectHerdUnits, getProjectSurveys, getProjectModels } from '@/modules/apiV1Methods';
import { useProjectStore } from '@/modules/stores/projectStore';
import { mapState } from 'pinia';

interface UploadContext {
    project: Project | undefined;
    herd_unit: HerdUnit | undefined;
    survey: Survey | undefined;
    model: Model | undefined;
}

export default defineComponent({
    name: "Upload-Utility",
    setup() {
        const project_store = useProjectStore();
		if(project_store.CurrentProject && project_store.surveys == undefined) project_store.get_surveys();
        const project = ref<Project | undefined>(project_store.CurrentProject);
		const herdunit = ref<HerdUnit | undefined>(project_store.CurrentHerdUnit);
		const model = ref<Model | undefined>(project_store.CurrentModel);
		const survey = ref<Survey | undefined>(project_store.CurrentSurvey);
		const schema = ref<Schema | undefined>(project_store.CurrentSchema);
        if (!project_store.projects) project_store.get_projects();
        return { project_store, project, herdunit, model, survey, schema };
    },
	mounted() {
		if(this.project_store.CurrentProject) {
			this.$router.push({name: 'upload', params: { projects: 'projects', uuid: this.project_store.CurrentProject.uuid }})
		}
	},
    data() {
        return {
        is_dragging: false,
        files: [] as File[],
        upload_context: {
            project: undefined,
            herd_unit: undefined, 
            survey: undefined,
            model: undefined,
        } as UploadContext,
        herd_units: [] as HerdUnit[] | undefined,
        surveys: [] as Survey[] | undefined,
        models: [] as Model[] | undefined,
        }
    },
	computed: {
		...mapState(useProjectStore, {
			CurrentProject: 'CurrentProject'
		})
	},
	watch: {
		CurrentProject(newValue: Project, oldValue: Project) {
			if(newValue != oldValue && newValue != undefined) {
				this.project_store.clear_state();
				this.project_store.get_project_children();
				this.$router.push({name: 'upload', params: { projects: 'projects', uuid: newValue.uuid }})
			} else {
				this.project_store.clear_state();
				this.$router.push({name: 'upload'});
			}
		}
	},
    methods: {
        on_change() { // Added typeguard to satisfy typescript's insanity
            if (this.$refs.file) {
                const fileInput = this.$refs.file as HTMLInputElement;
                if (fileInput.files) {
                    this.files.push(...fileInput.files);
                }
            }
        },
        drag_over(event: Event) {
            event.preventDefault();
            this.is_dragging = true;
            console.log('drag me')
        },
        drag_leave() {
            this.is_dragging = false;
        },
        drop(event: Event) {
            event.preventDefault();
            const drag_event = event as DragEvent;
            if (drag_event.dataTransfer) {
                (this.$refs.file as HTMLInputElement).files = drag_event.dataTransfer.files;
                const tmp_files = Array.from(drag_event.dataTransfer.files);
                for(const file of tmp_files) this.files.push(file);
                this.is_dragging = false;
            }
        },
        remove(index: number) {
            this.files.splice(index, 1);
        },
        upload() {
            for (const file of this.files) console.log(file.name)
        },
    },
})
</script>
<template>
<div class="Page-Container">
         <h2 id="Page-Title"> Data Uploader </h2>
         <div id="Uploader-Contianer">
            <div id="Upload-DropZone" @dragover="drag_over" @dragleave="drag_leave" @drop="drop">
                <input type="file" id="File-Input" webkitdirectory="" style="display:none" directory="" @change="on_change" ref="file"/>
                <label for="File-Input">
                    <Icon icon="material-symbols:upload" width="48" height="48"></Icon>
                    <div v-if="is_dragging">Release to drop files here.</div>
                    <div v-else>Drop files here or <u>click here</u> to upload.</div>
                </label>
                <div class="preview-container mt-4" v-if="files.length">
                    <div v-for="file in files" :key="file.name" class="preview-card">
                        <Icon icon="file-icons:numpy" width="36px" height="36px" v-if="file.name.toLowerCase().endsWith('.npy')"></Icon>
                        <Icon icon="material-symbols:image-outline" width="36px" height="36px" v-else-if="file.type.startsWith('image/')"></Icon>
                        <p>
                            {{ file.name }}
                        </p>
                        <button class="ml-2" type="button" @click="remove(files.indexOf(file))" title="Remove file">
                            x
                        </button>
                    </div>
                </div>
            </div>
            <div id="Uploader-Context">
                <h2> Configuration </h2>
                <form>
                    <label for="Project-Selection"> Project: </label>
                    <select id="Project-Selection" v-if="project_store.projects" v-model="project" @change="project_store.set_current_project(project)">
                        <option v-for="project in project_store.projects" :value="project">
                            {{ project.name }} | {{ project.uuid }}
                        </option>
                    </select>
                    <label for="Herd-Unit-Selection" v-if="project_store.CurrentProject && project_store.herd_units"> Herd Unit: </label>
                    <select id="Herd-Unit-Selection" v-if="project_store.CurrentProject && project_store.herd_units" v-model="herdunit" @change="project_store.set_current_herd_unit(herdunit)">
                        <option v-for="herdunit in project_store.herd_units" :value="herdunit">
                            {{ herdunit.name }} | {{ herdunit.uuid }}
                        </option>        
                    </select>
                    <label for="Survey-Selection" v-if="project_store.CurrentProject && project_store.surveys"> Survey: </label>
                    <select id="Survey-Selection" v-if="project_store.CurrentProject && project_store.surveys" v-model="survey" @change="project_store.set_current_survey(survey)">
                        <option v-for="survey in project_store.surveys" :value="survey">
                            {{ survey.name }}, {{ survey.survey_year }} | {{ survey.uuid }}
                        </option>
                    </select>
                    <label for="Model-Selection" v-if="project_store.CurrentProject && project_store.models"> Model: </label>
                    <select id="Model_Selection" v-if="project_store.CurrentProject && project_store.models" v-model="model" @change="project_store.set_current_model(model)">
                        <option v-for="model in project_store.models" :value="model">
                            {{  model.name }} | {{ model.uuid }}
                        </option>
                    </select>
                </form>
                <button 
                v-if="project_store.CurrentProject
                      && project_store.CurrentHerdUnit
                      && project_store.CurrentSurvey
                      && project_store.CurrentModel"
                      @click="upload()">
                    Upload
                </button>
            </div>
         </div>
    </div>
</template>
<style scoped>
.Page-Container {
    flex-direction: column;
}
#Page-Title {
    margin-bottom: auto;
    width: 100%;
    display: flex;
    justify-content: center;
    border-radius: 4px 4px 0px 0px;
    background-color: var(--wygf-bg-blue);
    padding: 0.5%;
}
#Uploader-Contianer {
    display: flex;
    width: 100%;
    height: 100%;
    gap: 10px;
    padding: 1%;
}
#Upload-DropZone{
    height: 100%;
    width: 70%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    border-radius: 8px;
    box-shadow: 0 8px 12px 4px var(--color-background);
    border: solid 1px var(--color-background);
    label {
        width: 100%;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
    }
    ::file-selector-button {
        background: none;
        border: none;
    }
}
#Uploader-Context {
    height: 100%;
    width: 30%;
    display: flex;
    flex-direction: column;
    padding: 1%;
    align-items: center;
    border-radius: 8px;
    box-shadow: 0 8px 12px 4px var(--color-background);
    border: solid 1px var(--color-background);
    h2 {
        margin-bottom: 5%;
    }
    form {
        width: 100%;
        height: 100%;
    }
    label {
        font-weight: bold;
    }
    select {
        border-radius: 4px;
        width: 100%;
        margin-bottom: 10px;
    }
    button {
        margin-top: auto;
        width: 100%;
        height: 5vh;
        border-radius: 8px;
    }
}
.file-label {
    font-size: 20px;
    display: block;
    cursor: pointer;
}
.preview-container {
    display: grid;
    grid-template-rows: auto auto;
    grid-auto-flow: column;
    justify-content: center;
    align-items: center;
    overflow-x: scroll;
    overflow-y: hidden;
    scrollbar-color: var(--color-text) transparent;
    height: 30vh;
    gap: 5px;
    width: 98%;
    border: 1px solid var(--color-background);
    border-radius: 8px;
    padding: 1%;
    margin: 2%;
    background-color: var(--color-background);

}
.preview-card {
    display: flex;
    justify-content: center;
    align-items: center;
    border: 1px solid var(--color-background);
    background-color: var(--color-background-soft);
    border-radius: 8px;
    padding: 2%;
    width: 10vw;
    height: 5vw;
    p {
        width: 8vw;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        text-align: center;
    }
    button {
        border: none;
        background: none;
        color: var(--color-text);
        margin-bottom: auto;
    }
    svg {
        margin-right: 5%;
    }
}
</style>