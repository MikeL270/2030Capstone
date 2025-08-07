<script lang="ts">
import { defineComponent } from "vue";
import { defineAsyncComponent } from "vue";
import { ref } from "vue";
import { useProjectStore } from "@/modules/stores/projectStore";
import { mapState } from "pinia";
import { Project, Schema } from "@/types/generatorobjects";
import { useRoute } from "vue-router";
import { useRouter } from "vue-router";

const Cropper = defineAsyncComponent(() => import("./auto_cropper/Cropper.vue"));
	var crumb_num = ref<number>(0);
	export default defineComponent({
	name: "Auto-Cropper",
	setup() {
		const project_store = useProjectStore();
		const route = useRoute();
		const router = useRouter();
		return { project_store, router, route };
	},
	mounted() {
		if(this.project_store.CurrentProject) {
			this.$router.push({name: 'auto-cropper', params: { projects: 'projects', uuid: this.project_store.CurrentProject.uuid }})
		}
	},
	components: {
		ProjectSelect:  defineAsyncComponent(() => import("./auto_cropper/ProjectSelector.vue")),
		CropConfig: defineAsyncComponent(() => import("./auto_cropper/CropperConfiguration.vue")),
		Crop: defineAsyncComponent(() => import("./auto_cropper/CropperConfiguration.vue")),
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
				this.$router.push({name: 'auto-cropper', params: { projects: 'projects', uuid: newValue.uuid }})
			} else {
				this.project_store.clear_state();
				this.$router.push({name: 'auto-cropper'});
			}
		},
		CurrentSchema(newValue: Schema, oldValue: Schema) {
			const currentQuery = {...this.$route.query };
			if(newValue != oldValue && newValue != undefined) {
				const newQuery = {
					...currentQuery,
					schema: newValue.uuid,
					label: undefined
				};
				this.$router.push({query: newQuery})
				this.project_store.get_labels();
			} else {
				const newQuery = {
					...currentQuery,
					schema: undefined,
					label: undefined,
				}
				this.project_store.labels = undefined;
				this.project_store.label_idx = undefined;
				this.$router.push({query: newQuery});
			}
		},
	},
	methods: {
		increment_crumb() {
			if (this.current_crumb == 0 && !this.project_store.CurrentProject) return;
			if (this.current_crumb <=3 && this.current_crumb != 2) this.current_crumb+=1;
		},
		decrement_crumb() {
			if (this.current_crumb >= 0 && this.current_crumb !=0) this.current_crumb-=1;
		}
	},
});
</script>

<template>
<div class="Page-Container">
	<h2 id="Bread-Crumb">
		Auto Cropper 
		<button @click="current_crumb = 0" title="Project Selection">
			&gt;
			Project Selection
		</button>
		<button @click="current_crumb = 1" title="Cropper Configuration" v-if="current_crumb >= 1"> 
			&gt;
			Cropper Configuration
		</button>
		<button @click="current_crumb = 2" title="Cropper" v-if="current_crumb  == 2">
			&gt;
			Cropper
		</button>
	</h2>
	<div id="Component-Container">
		<ProjectSelect v-if="current_crumb == 0"/>
		<CropConfig v-if="current_crumb == 1" />
		<Crop v-if="current_crumb == 2" />
		<div id="Instructions" v-if="current_crumb < 2">
			<div v-if="current_crumb == 0">
				<h2> Step 1 of 2: Project Selection </h2>
				<hr/>
				<br/>
				<p>
					Please select one of the projects available
					to the left. Note that if you cannot see a 
					project, or cannot see the project you are 
					looking for, that you must contact your 
					organization's administrator.
				</p>
			</div>
			<div v-if="current_crumb == 1">
				<h2> Step 2 of 2: Label Selection </h2>
				<hr>
				<br>
				<p>
					Please select the schema, and appropriate label
					for which you would like to validate Images for.
				</p>
				<div id="Configuration-Verification" v-if="project_store.CurrentLabel">
					<img v-bind:src="project_store.CurrentLabel?.image_link"></img>
				</div> 
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
<style scoped>
	#Bread-Crumb {
		margin-bottom: auto;
		width: 100%;
		display: flex;
		justify-content: center;
		border-radius: 4px 4px 0px 0px;
		background-color: var(--wygf-bg-blue);
		padding: 0.5%;
		button {
			background: none;
			color: var(--color-text);
			border: none;
			font-size: 1em;
		}
		button:hover {
			color: var(--wygf-yellow)
		}
	}
	.Page-Container {
		display: flex;
		flex-direction: column;
		gap: 1vw;
		justify-content: center;
		align-items: center;
	}
	#Instructions {
		width: 25%;
		height: 100%;
		border-radius: 8px;
		box-shadow: 0 8px 12px 4px var(--color-background);
		border: solid 1px var(--color-background);
		text-align: center;
		padding: 0.5%;
		display: flex;
		flex-direction: column;
		align-items: center;
		h2 {
			width: 100%;
		}
	}
	#Configuration-Verification {
		margin: 2%; 
		img {
			border-radius: 8px;
			max-width: 20vw;
			max-height: 20vh;
			pointer-events: none;
			user-select: none;
		}
	}
	#Component-Container {
		display: flex;
		width: 100%;
		height: 100%;
		gap: 1vw;
		padding: 1.5%;
	}
	#NavigationButtons {
		margin-top: auto;
		display: flex;
		width: 100%;
		button {
			border-radius: 8px; 
			width: 100%;
			min-height: 5vh;
			background-color: var(--wygf-bg-blue );
			color: var(--color-text);
			margin: 1%;
			display: flex;
			justify-content: center;
			align-items: center;
			border: none;
			svg {
				margin-right: 3%;
				margin-left: 3%;
			}
		}
		button:hover {
			color: var(--wygf-yellow)
		}
		.Active_Crumb {
			color: var(--wygf-yellow)
		}
	}
</style>
