<script lang="ts">
import { defineComponent } from "vue";
import { useAutoCropperStore } from "@/modules/stores/cropperStore";
import { mapState } from "pinia";
import { PredictionCrop } from "@/types/generatorobjects";

export default defineComponent({
	name: 'cropper',
	setup() {
		const cstore = useAutoCropperStore();
		return { cstore };
	},
	data(): {
		predCropRefs: Record<string, HTMLCanvasElement>,
	} {
		return {
			predCropRefs: {},
		}
	},
	// computed: {
	// 	...mapState(useAutoCropperStore, {
	// 		Curr
	// 	})
	// },
	async mounted() {
		if (!this.cstore.images) await this.cstore.get_batch();
		await this.cstore.get_prediction_crops();
		this.render_pred_crops();
		document.addEventListener('keydown', this.handle_key_press);
	},
	methods: {
	draw_crop_to_canvas(canvas: HTMLCanvasElement, url: string) {
		if (!canvas || !url ) return;
		const ctx = canvas.getContext('2d');
		const image = new window.Image()
		image.src = url;
		// pass predcrop to function and access ref by uuid to redraw the image
		// or create 
		image.onload = () => {
			canvas.width = image.width;
			canvas.height = image.height;
			ctx?.drawImage(image, 0, 0)
		};
		image.onerror = () => {
    		console.error(`Failed to load image from URL: ${url}`);
      	};
	},
	render_pred_crops() {
		setTimeout(() => {
			this.cstore.CurrentPredictionCrops?.forEach((predCrop) => {
				const canvas = this.predCropRefs[predCrop.uuid];
				if (canvas) {
					this.draw_crop_to_canvas(canvas, predCrop.url);
				}
			});
		}, 0)
	},
	draw_bounding_box(canvas: HTMLCanvasElement, predCrop: PredictionCrop) {
		if (!canvas || predCrop == undefined) return;
		const box = predCrop.bounding_box;
		const draw = (predCrop.draw_box) ? false : true;
		// Toggle draw box boolean for predcrop object w/ annoying typescript declaration checks
		if (!this.cstore.CurrentPredictionCrops) return;
		this.cstore.CurrentPredictionCrops[this.cstore.CurrentPredictionCrops?.indexOf(predCrop)].draw_box = draw;
		const ctx = canvas.getContext('2d');
		// if disabling 
		if (draw == false) {
			this.draw_crop_to_canvas(canvas, predCrop.url);
			return;
		}
		if (ctx == null) return;
		ctx?.beginPath();
		ctx.lineWidth = 2;
		ctx.strokeStyle = "red";
		ctx?.rect(box.top_left[0], box.top_left[1], box.get_width(), box.get_height());
		ctx?.stroke();

	},
	async handle_right_arrow() {
		await this.cstore.next_image();
		this.render_pred_crops();
	},
	async handle_left_arrow() {
		await this.cstore.previous_image();
		this.render_pred_crops();
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
			<h2> <u> {{ cstore.CurrentImage?.name }} </u> </h2>
			<p> {{ cstore.ImageNum }} / {{ cstore.images?.length }} </p>
			<div id="Predictions-Table">
				<figure v-for="predCrop in cstore.CurrentPredictionCrops" :key="predCrop.uuid" :ref="'crop-' + predCrop.uuid" class="Annotation">
					<button @click="console.log('pressed')">
						<p> Score: {{ predCrop.score?.toFixed(3) }} </p>
						<canvas :ref="(el) => {if (el) {predCropRefs[predCrop.uuid] = el as HTMLCanvasElement}}"></canvas>
					</button>
					<p> Toggle Boxes: </p>
					<input type="checkbox" name="box-toggle" @change="draw_bounding_box(predCropRefs[predCrop.uuid], predCrop)"/>
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
	canvas {
		height: 150px;
		width: 150px;
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