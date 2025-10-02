<script lang="ts">
import '@/assets/selector.css';
import { defineComponent, defineAsyncComponent, ref } from 'vue';
import { useProjectStore } from '@/modules/stores/projectStore';
import { Project, Schema } from '@/types/generatorobjects';
import { mapState } from 'pinia';

var crumb_num = ref<number>(0);
export default defineComponent({
	name: "Uploader-Utility",
	components: {
		Selector_1:  defineAsyncComponent(() => import("../object_selector/Selector_1.vue")),
		Selector_2: defineAsyncComponent(() => import("../object_selector/Selector_2.vue")),
		Upload: defineAsyncComponent(() => import("./Uploader.vue")),
	},
	setup() {
		const project_store = useProjectStore();
		return { project_store };
	},
	mounted() {
		if(this.project_store.CurrentProject) {
			this.$router.push({name: 'upload', params: { projects: 'projects', uuid: this.project_store.CurrentProject.uuid }})
		}
	},
	data() {
		return {
			current_crumb: crumb_num,
		};
	},
	computed: {
		...mapState(useProjectStore, {
			CurrentProject: 'CurrentProject',
			CurrentSchema: 'CurrentSchema',
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
		},
		CurrentSchema(newValue: Schema, oldValue: Schema) {
			const currentQuery = {...this.$route.query };
			if(newValue != oldValue && newValue != undefined) {
				const newQuery = {
					...currentQuery,
					schema: newValue.uuid,
				};
				this.$router.push({query: newQuery})
			} else {
				const newQuery = {
					...currentQuery,
					schema: undefined,
				}
				this.project_store.labels = [];
				this.project_store.label_idx = undefined;
				this.$router.push({query: newQuery});
			}
		},
	},
	methods: {
		increment_crumb() {
			if (this.current_crumb == 0 && !this.project_store.CurrentProject) return;
			else if (this.current_crumb == 0 && !this.project_store.CurrentSurvey) return;
			else if (this.current_crumb == 1 && !this.project_store.CurrentSchema) return;
			else if (this.current_crumb == 1 && !this.project_store.CurrentHerdUnit) return;
			else if (this.current_crumb == 1 && !this.project_store.CurrentModel) return;
			else if (this.current_crumb <=3 && this.current_crumb != 2) this.current_crumb+=1;
		},
		decrement_crumb() {
			if (this.current_crumb >= 0 && this.current_crumb !=0) this.current_crumb-=1;
		}
	}
});
</script> 

<template>
	<div class="Page-Container">
		<h2 class="Utility-Title">
			Upload Utility 
			<button @click="current_crumb = 0" title="Project and Survey">
				&gt;
				Project and Survey 
			</button>
			<button @click="current_crumb = 1" title="Herdunit, Model, and Schema" v-if="current_crumb >= 1">
				&gt;
				Schema, Herd Unit, and Model
			</button>
			<button @click="current_crumb = 2" Title="Uploader" v-if="current_crumb == 2">
				&gt;
				Uploader
			</button>
		</h2>
		<div class="Component-Container">
			<Selector_1 v-if="current_crumb == 0"/>
			<Selector_2 v-if="current_crumb == 1"/>
			<Upload v-if="current_crumb == 2"/>
			<div class="Instructions" v-if="current_crumb < 2">
				<h1 style="align-self: center"> <u> Upload Utility </u> </h1>
				<br/>
				<details>
					<summary style="font-weight: bold"> Description: </summary>
					<p>
					The upload utility is used to upload imagery (and prediction)
					data to the server. This data is categorized to allow for
					more than one project to be worked on using this tool. Before
					you can upload any data you must select the appropriate 
					categories to ensure the data ends up in the correct place. 
					</p>
				</details>
				<br/>
				<div v-if="current_crumb == 0" style="width: 100%">
					<h2> Projects and Surveys </h2>					
					<ol>
						<li>
							<details>
								<summary style="font-weight: bold"> Projects: </summary>
								<p>
									Projects are simple categories that allow you to 
									separate different census 'projects' and easily 
									maintain separate computer vision models specialized 
									for different animals in different geographical regions. 
								</p>
							</details>
						</li>
						<li>
							<details>
								<summary style="font-weight: bold"> Surveys: </summary>
								<p>
								Surveys provide separation for datasets (herd units) by year. 
								This is important for the actual census process, as imagery 
								from the prior year should not be used to produce the population
								estimation for the current year. It also enables finer control 
								over the data used to train a given computer vision model.
								</p>
							</details>
						</li>
					</ol>
				</div>
				<div v-if="current_crumb == 1" style="width: 100%"> 
					<h2> Schemas, Herd Units, Models  </h2>
					<ol>
						<li>
							<details>
								<summary style="font-weight: bold"> Schemas: </summary>
								<p>
									Schemas are containers for human readable interfaces
									between computer vision model labels and the objects
									(animals) they represent. 
								</p>
							</details>
						</li>
						<li>
							<details>
								<summary style="font-weight: bold"> Herd Units: </summary>
								<p>
									Herd Units identify individual herds (and the area 
									they inhabit) allowing for models to be specialized
									to specific geographical regions and to track the 
									population of individual herds.
								</p>
							</details>
						</li>
						<li>
							<details>
								<summary style="font-weight: bold"> Models: </summary>
								<p>
									Models are containers for predictions that represent the 
									computer vision model used to produce them. This tool's
									models and their predictions are not ran real time. In 
									order to use a model it must have first been trained and 
									then "ran" over a dataset (herdunit) in order to access it's
									predictions. 
								</p>
							</details>
						</li>
					</ol>
				</div>
				<div id="NavigationButtons">
					<button @click="decrement_crumb()">
						<Icon icon="ooui:next-rtl" width="16" height="16"/>
						Back
					</button>
					<button @click="increment_crumb()" v-if="current_crumb < 1">
						Next
						<Icon icon="ooui:next-ltr" width="16" height="16"/>
					</button>
					<button @click="increment_crumb()" v-else>
						Start
						<Icon icon="majesticons:rocket-3-start-line" width="16" height="16"/>
					</button>
				</div>
			</div>
		</div>
	</div>
</template>