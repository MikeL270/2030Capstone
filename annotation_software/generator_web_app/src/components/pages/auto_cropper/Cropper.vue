<script lang="ts">
import { defineComponent, onMounted } from "vue";
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
			console.log('calling');
			await cstore.bootstrap();
		} else {
			console.log('im an idiot');
		}
		
		};
		startup();
		return { cstore, pstore };
	},
	data(): {
		predCropRefs: Record<string, HTMLCanvasElement>,
	} {
		return {
			predCropRefs: {},
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
	methods: {
	render_bounding_boxes() {
		setTimeout(() => {
			this.cstore.CurrentPredictionCrops.forEach((predCrop) => {
				const canvas = this.predCropRefs[predCrop.uuid];
				if (canvas) {
					this.draw_bounding_box(canvas, predCrop);
				}
			});
		}, 0)
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
		ctx.strokeStyle = "red";
		ctx.rect(box.top_left[0], box.top_left[1], box.get_width(), box.get_height());
		ctx.stroke();
	},
	async handle_right_arrow() {
		await this.cstore.next_image();
		//this.render_bounding_boxes();
	},
	async handle_left_arrow() {
		await this.cstore.previous_image();
		//this.render_bounding_boxes();
	},
	handle_key_press(event: KeyboardEvent) {
            switch(event.code) {
                case 'ArrowRight': {
                    this.handle_right_arrow();
                    break;
                };
                case 'ArrowLeft': {
                    this.handle_left_arrow();
                    break;
				};
                // };
                // case 'Space': {
                //     this.approve_all();
                //     break;
                // };
                // case 'Enter': {
                //     this.submit();
                //     break;
                // }
            };
        },
	}
});

</script>
<template>
	<div id="Cropper-Contianer">
		<div id="Predictions-Container" v-if="!cstore.loading">
			<h2> <u> {{ cstore.CurrentImage.name }} </u> </h2>
			<p> {{ cstore.ImageNum }} / {{ cstore.CurrentImages.length }} </p>
			<div id="Predictions-Table">
				<figure v-for="predCrop in cstore.CurrentPredictionCrops" :key="predCrop.uuid" :ref="'crop-' + predCrop.uuid" class="Annotation" :class="{Approved: predCrop.approved == true}">
					<button @click="predCrop.approved = (predCrop.approved) ? false : true">
						<p> Score: {{ predCrop.score?.toFixed(3) }} </p>
						<canvas :ref="(el) => {if (el) {predCropRefs[predCrop.uuid] = el as HTMLCanvasElement}}" :class="{Visible: predCrop.draw_box}"></canvas>
						<img :src="predCrop.url"></img>
					</button>
					<p> Box: </p>
					<input type="checkbox" name="box-toggle" v-model="predCrop.draw_box"/>
				</figure>
			</div>
		</div>
		<div id="Predictions-Container" v-else>
			<Icon icon="eos-icons:three-dots-loading" width="96" height="96"/> 
		</div>
		<div id="Tool-Bar">
			<div class="Tool">
				<button @click="handle_left_arrow()">
					<Icon icon="ooui:next-rtl" width="16" height="16"/>
					Previous Image
				</button>
			</div>
			<div class="Tool">
				<button>
					<Icon icon="uis:space-key" width="16" height="16"/>
					Approve All
				</button>
			</div>
			<div class="Tool" Title="Submit (Enter)">
				<button>
					<Icon icon="vaadin:enter-arrow" width="16" height="16"/>
					Submit
				</button>
			</div>
			<div class="Tool">
				<button @click="handle_right_arrow()">
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
}
#Predictions-Container {
	height: 100%;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
    align-items: center;
	svg {
		justify-self: center;
		align-self: center;
	}
}
#Predictions-Table {
	display: flex; 
    flex-wrap: wrap; 
    justify-content: center; 
    gap: 15px;
	height: 100%;
}
.Annotation {
	display: flex;
	justify-content: center;
	align-items: center;
	border-radius: 8px;
	max-width: fit-content;
	padding: 0.5vw;
	background-color: var(--wygf-bg-blue);
	box-shadow: 0 4px 6px 2px var(--color-background);
	flex-grow: 0;
	flex-shrink: 0;
	img {
		height: 150px;
		width: 150px;
	}
	canvas {
		display: none;
		position: absolute;
		height: 150px;
		width: 150px;
		z-index: 1;
	}
	canvas.Visible {
		display: block;
	}
	button {
		border: none;
		background: none;
		padding-right: 10%;
		padding-left: 10%;
		color: var(--color-heading);
		p {
			margin-bottom: 4%;
		}
	}
	button:hover {
		cursor: pointer;
		color: var(--wygf-yellow);
	}
}
.Approved {
	box-shadow: 0 0 3px 1px var(--wygf-yellow)
}
#Tool-Bar{
	width: 80%;
	height: 5vh;
	justify-self: flex-end;
	border-radius: 8px;
	box-shadow: 0 8px 12px 4px var(--color-background);
	display: flex;
	justify-content: space-between;
	margin-top: auto;
	margin-bottom: 2vh;
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