<script lang="ts">
import { defineComponent } from "vue";
import { useAutoCropperStore } from "@/modules/stores/cropperStore";
import { mapState } from "pinia";
import { PredictionCrop } from "@/types/generatorobjects";
import { useProjectStore } from "@/modules/stores/projectStore";

export default defineComponent({
	name: 'cropper',
	setup() {
		const cstore = useAutoCropperStore();
		const pstore = useProjectStore();
		const startup = async () => {
			if (!cstore.bootstrapped) {
			await cstore.bootstrap();
		} else {
			return
		}
		
		};
		startup();
		return { cstore, pstore };
	},
	data(): {
		predCropRefs: Record<string, HTMLCanvasElement>,
		predictionRefs: Record<string, HTMLDivElement>,
	} {
		return {
			predCropRefs: {},
			predictionRefs: {} 
		}
	},
	computed: {
		...mapState(useAutoCropperStore, {
			CurrentPredictionCrops: 'CurrentPredictionCrops'
		})
	},
	watch: {
		CurrentPredictionCrops(newValue: PredictionCrop[], oldValue: PredictionCrop[]) {
			if (newValue != oldValue && newValue != undefined) {
				this.render_bounding_boxes();
			} 
		}
	},
	async mounted() { 
		document.addEventListener('keydown', this.handle_key_press);
	},
	async unmounted() {
		await this.cstore.end_session();
	},
	methods: {
	render_bounding_boxes() {
		setTimeout(() => {
			this.CurrentPredictionCrops.forEach((predCrop) => {
				const canvas = this.predCropRefs[predCrop.uuid];
				if (canvas) {
					this.draw_bounding_box(canvas, predCrop);
				}
			});
		}, 0);
	},
	draw_bounding_box(canvas: HTMLCanvasElement, predCrop: PredictionCrop) {
		if (!canvas || predCrop == undefined) return;
		const box = predCrop.bounding_box;
		canvas.width = predCrop.dimensions.get_width();
		canvas.height = predCrop.dimensions.get_height();
		const ctx = canvas.getContext('2d');
		if (ctx == null) return;
		ctx.beginPath();
		ctx.lineWidth = 2;
		const label_color_hex = this.pstore.labels?.find((label) => label.label == predCrop.label)?.color;
		ctx.strokeStyle = (label_color_hex != undefined) ? label_color_hex : 'white'
		ctx.fillStyle = (label_color_hex != undefined) ? label_color_hex + '54' : '#ffffff54'
		ctx.fillRect(box.top_left.x, box.top_left.y, box.get_width(), box.get_height());
		ctx.rect(box.top_left.x, box.top_left.y, box.get_width(), box.get_height());
		ctx.stroke();
		ctx.closePath();
	},
	toggle_all_boxes() {
		setTimeout(() => {
			this.CurrentPredictionCrops.forEach((predCrop) => {
				predCrop.draw_box = (predCrop.draw_box) ? false : true
			})
		})
	},
	async handle_right_arrow() {
		await this.cstore.next_image();
	},
	async handle_left_arrow() {
		await this.cstore.previous_image();
	},
	async handle_left_bracket() {
		await this.cstore.previous_prediction();
		this.predictionRefs[this.cstore.CurrentPredictionCrop.uuid].scrollIntoView({ behavior: 'smooth' });
	},
	async handle_right_bracket() {
		await this.cstore.next_prediction();
		this.predictionRefs[this.cstore.CurrentPredictionCrop.uuid].scrollIntoView({ behavior: 'smooth' });
	},
	handle_s_key() {
		this.cstore.CurrentPredictionCrop.approved = (this.cstore.CurrentPredictionCrop.approved) ? false : true;
		this.draw_bounding_box(this.predCropRefs[this.cstore.CurrentPredictionCrop.uuid], this.cstore.CurrentPredictionCrop);
	},
	async handle_enter() {
		await this.cstore.submit();
	}, 
	async handle_space() {
		setTimeout(() => {
			this.CurrentPredictionCrops.forEach((predCrop) => {
				predCrop.approved = true;
			});
		}, 0)
	},
	decode_digit(event: KeyboardEvent) {
		const label_num = +event.key;
		this.cstore.CurrentPredictionCrop.label = (this.pstore.labels?.find((label) => label.label == label_num) != undefined) ? label_num : this.cstore.CurrentPredictionCrop.label;
		this.draw_bounding_box(this.predCropRefs[this.cstore.CurrentPredictionCrop.uuid], this.cstore.CurrentPredictionCrop)
		this.cstore.CurrentPredictionCrop.approved = true;
		this.handle_right_bracket();
	},
	handle_key_press(event: KeyboardEvent) {
		switch(true) {
			case event.code === 'ArrowRight': {
				this.handle_right_arrow();
				break;
			};
			case event.code === 'ArrowLeft': {
				this.handle_left_arrow();
				break;
			};
			case event.code === 'KeyB': {
				this.toggle_all_boxes();
				break;
			};
			case event.code.startsWith('Digit'): {
				this.decode_digit(event);
				break;
			};
			case event.code === 'BracketLeft': {
				this.handle_left_bracket();
				break;
			};
			case event.code === 'BracketRight': {
				this.handle_right_bracket();
				break;
			};
			case event.code === 'KeyS': {
				this.handle_s_key();
				break;
			};
			case event.code === 'Enter': {
				this.handle_enter();
				break;
			};
			case event.code === 'Space': {
				this.handle_space()
			};
			default: {
				console.log('none matched');
				break;
			};
		};
	},
	}
});

</script>
<template>
	<div id="Cropper-Contianer">
		<div id="Predictions-Container" v-if="!cstore.loading">
			<div id="Predictions-Carosuel" v-if="!cstore.loading" :class="{Overflow : cstore.CurrentPredictionCrops.length > 2}">
				<div v-for="predCrop in cstore.CurrentPredictionCrops" 
					:key="predCrop.uuid" 
					class="Prediction-Object" 
					:class="{Approved: predCrop.approved == true, Selected: cstore.active_pred_idx == cstore.CurrentPredictionCrops.indexOf(predCrop)}"  
					:title="'Prediction: ' + predCrop.uuid"
					:ref="(el) => {if (el) {predictionRefs[predCrop.uuid] = el as HTMLDivElement}}">
					<h2> Score: {{ predCrop.score?.toFixed(3) }} </h2>
					<button @click="predCrop.approved = (predCrop.approved) ? false : true" tabindex="-1">
						<canvas :ref="(el) => {if (el) {predCropRefs[predCrop.uuid] = el as HTMLCanvasElement}}" :class="{Visible: predCrop.draw_box}" tabindex="-1"></canvas>
						<img :src="predCrop.url" tabindex="-1"></img>
					</button>
					<div class="Prediction-Object-Options">
						<section>
						<label for="label-select-{{ predCrop.uuid }}">Label:</label>
						<select id="label-select-{{ predCrop.uuid }}" v-model="cstore.CurrentPredictionCrops[cstore.CurrentPredictionCrops.indexOf(predCrop)].label" @change="draw_bounding_box(predCropRefs[predCrop.uuid], predCrop)">
							<option v-for="label in pstore.labels" :value="label.label" :key="label.label">
								{{ label.name }}
							</option>
						</select>
						</section>
						<section>
							<label for="box-toggle-{{ predCrop.uuid }}"> Box: </label>
							<input type="checkbox" id="box-toggle-{{ predCrop.uuid }}" name="box-toggle" v-model="predCrop.draw_box" tabindex="-1"/>
						</section>
					</div>
				</div>
			</div>
		</div>
		<div id="Predictions-Container" v-else>
			<Icon icon="eos-icons:three-dots-loading" width="96" height="96"/> 
		</div>
		<div id="Tool-Bar">
			<div class="Tool">
				<button @click="handle_left_arrow()" tabindex="-1">
					<Icon icon="ooui:next-rtl" width="16" height="16"/>
					Previous Image
				</button>
			</div>
			<div class="Tool">
				<button @click="handle_space()" tabindex="-1">
					<Icon icon="uis:space-key" width="16" height="16"/>
					Approve All
				</button>
			</div>
			<div class="Tool" Title="Submit (Enter)">
				<button tabindex="-1">
					<Icon icon="vaadin:enter-arrow" width="16" height="16"/>
					Submit
				</button>
			</div>
			<div class="Tool">
				<button @click="handle_right_arrow()" tabindex="-1">
					Next Image
					<Icon icon="ooui:next-ltr" width="16" height="16"/> 
				</button>
			</div>
		</div>
	</div>
</template>
<style scoped>
#Cropper-Contianer {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	height: 100%;
	width: 100%;
	overflow: hidden;
}
#Predictions-Container {
	height: 100%;
	display: flex;
	width: 100%;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 0 5% 0 5%;
	svg {
		justify-self: center;
		align-self: center;
	}
	overflow: hidden;
}
#Predictions-Carosuel {
	display: flex; 
	align-items: center;
	justify-content: center;
    gap: 2.5%;
	max-width: 80vw;
	width: fit-content;
	margin: 0 2% 0 2%;
	padding: 2%;
}
.Overflow {		
	overflow-x: auto;
	justify-content: flex-start !important;
	scrollbar-color: var(--color-text) transparent;
	scroll-padding-inline: 10%;
}
.Prediction-Object {
	display: flex;
	flex-direction: column;
	justify-content: center;
	align-items: center;
	border-radius: 8px;
	padding: 1vw;
	background-color: var(--wygf-bg-blue);
	box-shadow: 0 4px 6px 2px var(--color-background);
}
	.Prediction-Object img {
		width: 100%;
		height: 100%;
		object-fit: cover;
		display: block;
	}
	.Prediction-Object canvas {
		object-fit: cover;
		display: none;
		position: absolute;
		top: 0;
		z-index: 1;
	}

	.Prediction-Object canvas.Visible {
		width: 100%;
		height: 100%;
		display: block;
		z-index: 999;
	}
	.Prediction-Object button {
		display: flex;
		flex-direction: column;
		justify-content: center;
		width: 22vw;
		height: auto;
		align-items: center;
		border: none;
		background: none;
		position: relative;
		color: var(--color-heading);
	}


.Prediction-Object-Options {
	display: flex;
	width: 100%;
	height: 100%;
	margin: 2%;
	justify-content: center;
	align-items: center;
	gap: 1vw;
}
.Prediction-Object-Options section {
	display: flex; 
	align-items: center;
	gap: 5%;
	width: 100%;
	height: 100%;
	label {
		font-size: 1.5em;
		margin-right: 5px;
		text-align: center;
	}
	select {
		border-radius: 8px;
		cursor: pointer;
		width: 10vw;
		height: 2vh;
	}
	select > option:hover {
		cursor: pointer;
	}
	input[type='checkbox'] {
		cursor: pointer;
		width: 2vh;
		height: 2vh;
	}
}
.Prediction-Object.Selected {
	box-shadow: 0 0 3px 1px white;
}
.Prediction-Object.Approved {
	box-shadow: 0 0 3px 1px var(--wygf-yellow);
}
#Tool-Bar{
	width: 80%;
	height: 5vh;
	justify-self: flex-end;
	border-radius: 8px;
	box-shadow: 0 8px 12px 4px var(--color-background);
	display: flex;
	justify-content: space-between;
	margin-bottom: 2% 0 2% 0;
	align-items: center;
	background-color: var(--wygf-bg-blue)
}
#Tool-Bar .Tool {
	display: flex;
	justify-content: center;
	align-items: center;
	height: 100%;
	max-height: 5vh;
	display: flex;
	color: var(--color-heading);
	justify-content: center;
	align-items: center;
	min-width: 12vw;
	font-size: 1em;
	padding: 1%;
	border: None;
}
#Tool-Bar .Tool:hover {
	color: var(--wygf-yellow);
 }
#Tool-Bar .Tool button {
	background: none;
	display: flex;
	justify-content: center;
	align-items: center;
	color: inherit;
	border-radius: 4px;
	width: 100%;
	height: 100%;
	border: none;
	font-size: 1em;
}
#Tool-Bar .Tool button:hover {
	cursor: pointer;
}
#Tool-Bar .Tool  svg {
    margin: 2%;
}

</style>