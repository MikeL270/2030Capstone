<script lang="ts">
// https://serversideup.net/blog/file-uploads-using-fetch-api-and-vuejs/
// https://blog.logrocket.com/customizing-drag-drop-file-uploading-vue/#creating-advanced-dropzone
import { defineComponent } from "vue";
import { ref } from "vue";
import { HerdUnit, Project, Survey, Model, Schema } from "@/types/generatorobjects";
import {
  abortMultipartUpload,
  createImage,
  createMultiPartUpload,
  getPresignedUrl,
  completeMultiPartUpload,
} from "@/modules/apiV1Methods";
import { useProjectStore } from "@/modules/stores/projectStore";
import { mapState } from "pinia";
import { Md5 } from "ts-md5";

export default defineComponent({
  name: "Upload-Utility",
  setup() {
    const project_store = useProjectStore();
    if (project_store.CurrentProject && project_store.surveys == undefined)
      project_store.get_surveys();
    const project = ref<Project | undefined>(project_store.CurrentProject);
    const herdunit = ref<HerdUnit | undefined>(project_store.CurrentHerdUnit);
    const model = ref<Model | undefined>(project_store.CurrentModel);
    const survey = ref<Survey | undefined>(project_store.CurrentSurvey);
    const schema = ref<Schema | undefined>(project_store.CurrentSchema);
    if (!project_store.projects) project_store.get_projects();
    return { project_store, project, herdunit, model, survey, schema };
  },
  mounted() {
    if (this.project_store.CurrentProject) {
      this.$router.push({
        name: "upload",
        params: { projects: "projects", uuid: this.project_store.CurrentProject.uuid },
      });
    }
  },
  data() {
    return {
      is_dragging: false,
      files: [] as File[],
    };
  },
  computed: {
    ...mapState(useProjectStore, {
      CurrentProject: "CurrentProject",
    }),
  },
  watch: {
    CurrentProject(newValue: Project, oldValue: Project) {
      if (newValue != oldValue && newValue != undefined) {
        this.project_store.clear_state();
        this.project_store.get_project_children();
        this.$router.push({
          name: "upload",
          params: { projects: "projects", uuid: newValue.uuid },
        });
      } else {
        this.project_store.clear_state();
        this.$router.push({ name: "upload" });
      }
    },
  },
  methods: {
    on_change() {
      // Added typeguard to satisfy typescript's insanity
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
        for (const file of tmp_files) this.files.push(file);
        this.is_dragging = false;
      }
    },
    remove(index: number) {
      this.files.splice(index, 1);
    },
    async upload() {
      // Cache relevant Ids from store (Current objects are computed getters in the store)
      const project_id = this.project_store.CurrentProject?.uuid;
      const survey_id = this.project_store.CurrentSurvey?.uuid;
      const herd_unit_id = this.project_store.CurrentHerdUnit?.uuid;
      const model_id = this.project_store.CurrentModel?.uuid;

      for (const file of this.files) {
        const extension = file.name.toLowerCase().split(".").pop();
        console.log(`Now uploading: ${file.name}...`);
        // Check if file is image (switch case)
        switch (extension) {
          case "jpg":
            // Post image to API store returned uuid for object key
            const img = new window.Image();
            const imageBitmap = await createImageBitmap(file);

            console.log("Creating image in DB...");
            const image = await createImage(
              project_id,
              survey_id,
              herd_unit_id,
              file.name,
              imageBitmap.height,
              imageBitmap.width
            );
            // Create key
            if (image == undefined) throw new Error(`failed to create image!`);
            const image_key = `images/survey/${survey_id}/herd_unit/${herd_unit_id}/image/${image.name}`;
            console.log(image_key);

            // Instantiate list to hold Parts
            const part_list = [];

            // Initiate Mulitpart upload
            console.log("get upload_id");
            const upload_id = await createMultiPartUpload(image_key);
            if (upload_id == undefined)
              throw new Error(`failed to create multipart upload!`);
            // chunk the image file based on size
            const chunkSize = 1024 * 1024 * 5; // (5MB)
            const totalParts = Math.ceil(file.size / chunkSize);
            console.log("uploading image");
            for (let partNumber = 1; partNumber <= totalParts; partNumber++) {
              try {
                // Create file chunk
                const start = (partNumber - 1) * chunkSize;
                const end = Math.min(start + chunkSize, file.size);
                const chunk = file.slice(start, end);

                // Hash the chunk
                let md5 = new Md5();
				md5.appendByteArray(new Uint8Array(await chunk.arrayBuffer()))
				const chunk_hash_hex = md5.end() as string
				
				// Convert the hash to a base64 string
				const chunk_md5_base64 = btoa(
				String.fromCharCode.apply(
					null,
					chunk_hash_hex.match(/.{2}/g)!.map((hex) => parseInt(hex, 16))
				)
				);

                // Request pre-signed url for chuck
                const presigned_url = await getPresignedUrl(
                  upload_id,
                  partNumber,
                  image_key,
                  chunk.size,
                  chunk_md5_base64
                );

                // Post request to pre-signed url with part-num, upload-id
                if (presigned_url == undefined)
                  throw new Error(`failed to create pre-signed url!`);

                const headers = new Headers();
                headers.append("Content-Length", chunk.size.toString());
                headers.append("Content-MD5", chunk_md5_base64);

				console.log(`MD5 hash: ${chunk_md5_base64}`)

                const response = await fetch(presigned_url, {
                  method: "PUT",
                  body: chunk,
                  headers: headers,
                });
                if (!response.ok) {
                  throw new Error(
                    `Upload of part ${partNumber} failed with status: ${response.status}`
                  );
                }
                console.log("Response Headers:", response.headers);
                // Push PartNumber and Etag to list
                part_list.push({
                  PartNumber: partNumber,
                  ETag: response.headers.get("ETag"),
                });
              } catch (error: any) {
                // Abort multipart upload
                console.error(error);
                const response = await abortMultipartUpload(image_key, upload_id);
				return;
              }
            }
            // Complete multipart upload
            const response = await completeMultiPartUpload(
              image_key,
              part_list,
              upload_id
            );

          // Check if file is npy (switch case)

          // Expand switch statement
        }
      }
    },
  },
});
</script>
<template>
  <div class="Page-Container">
    <h2 id="Page-Title">Data Uploader</h2>
    <div id="Uploader-Contianer">
      <div
        id="Upload-DropZone"
        @dragover="drag_over"
        @dragleave="drag_leave"
        @drop="drop"
      >
        <input
          type="file"
          id="File-Input"
          webkitdirectory=""
          style="display: none"
          directory=""
          @change="on_change"
          ref="file"
        />
        <label for="File-Input">
          <Icon icon="material-symbols:upload" width="48" height="48"></Icon>
          <div v-if="is_dragging">Release to drop files here.</div>
          <div v-else>Drop files here or <u>click here</u> to upload.</div>
        </label>
        <div class="preview-container mt-4" v-if="files.length">
          <div v-for="file in files" :key="file.name" class="preview-card">
            <Icon
              icon="file-icons:numpy"
              width="36px"
              height="36px"
              v-if="file.name.toLowerCase().endsWith('.npy')"
            ></Icon>
            <Icon
              icon="material-symbols:image-outline"
              width="36px"
              height="36px"
              v-else-if="file.type.startsWith('image/')"
            ></Icon>
            <p>
              {{ file.name }}
            </p>
            <button
              class="ml-2"
              type="button"
              @click="remove(files.indexOf(file))"
              title="Remove file"
            >
              x
            </button>
          </div>
        </div>
      </div>
      <div id="Uploader-Context">
        <h2>Configuration</h2>
        <p>
          Please ensure you are on a stable (fast) internet connection before attempting
          to upload. Not only would a poor connection cause the upload to take an
          unreasonable amount of time, but you are risking complete failure of the upload.
          In these early days there are no guarantees of robust failure recovery features.
          AWS boto3 will prevent catastrophic failure, but that starts and stops with
          individual images.
        </p>
        <form>
          <label for="Project-Selection"> Project: </label>
          <select
            id="Project-Selection"
            v-if="project_store.projects"
            v-model="project"
            @change="project_store.set_current_project(project)"
          >
            <option v-for="project in project_store.projects" :value="project">
              {{ project.name }} | {{ project.uuid }}
            </option>
          </select>
          <label
            for="Herd-Unit-Selection"
            v-if="project_store.CurrentProject && project_store.herd_units"
          >
            Herd Unit:
          </label>
          <select
            id="Herd-Unit-Selection"
            v-if="project_store.CurrentProject && project_store.herd_units"
            v-model="herdunit"
            @change="project_store.set_current_herd_unit(herdunit)"
          >
            <option v-for="herdunit in project_store.herd_units" :value="herdunit">
              {{ herdunit.name }} | {{ herdunit.uuid }}
            </option>
          </select>
          <label
            for="Survey-Selection"
            v-if="project_store.CurrentProject && project_store.surveys"
          >
            Survey:
          </label>
          <select
            id="Survey-Selection"
            v-if="project_store.CurrentProject && project_store.surveys"
            v-model="survey"
            @change="project_store.set_current_survey(survey)"
          >
            <option v-for="survey in project_store.surveys" :value="survey">
              {{ survey.name }}, {{ survey.survey_year }} | {{ survey.uuid }}
            </option>
          </select>
          <label
            for="Model-Selection"
            v-if="project_store.CurrentProject && project_store.models"
          >
            Model:
          </label>
          <select
            id="Model_Selection"
            v-if="project_store.CurrentProject && project_store.models"
            v-model="model"
            @change="project_store.set_current_model(model)"
          >
            <option v-for="model in project_store.models" :value="model">
              {{ model.name }} | {{ model.uuid }}
            </option>
          </select>
        </form>
        <button
          v-if="
            project_store.CurrentProject &&
            project_store.CurrentHerdUnit &&
            project_store.CurrentSurvey &&
            project_store.CurrentModel
          "
          @click="upload()"
        >
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
#Upload-DropZone {
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
  p {
    margin-bottom: 2%;
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
