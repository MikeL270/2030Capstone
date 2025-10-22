<script lang="ts">
import { defineComponent } from 'vue';
import { useCropVerifierStore } from '@/modules/stores/cropVerifierStore';

export default defineComponent({
    name: 'crop-verifier',
    setup() {
        const cvs = useCropVerifierStore();

        return { cvs }
    },
    methods: {
        startDrawingBox(e: MouseEvent) {
            this.cvs.drawing = true;
            this.cvs.getMousePos(e);
            this.cvs.setBoxStart();
        },
        stopDrawingBox() {
            this.cvs.drawing = false;
            this.cvs.newBox();
        },
        reDrawBoxes(ctx: CanvasRenderingContext2D) {
            for (const box of this.cvs.boxes) {
                ctx.beginPath();
				ctx.lineWidth = 2;
				ctx.strokeStyle = "red";
				ctx.rect(
				box.top_left.x,
				box.top_left.y,
				box.get_width(),
				box.get_height(),
                );
            ctx.stroke();
            }
        },
        drawBox(e: MouseEvent) {
            if (!this.cvs.drawing) return;
            this.cvs.getMousePos(e);
            this.cvs.setBoxEnd();
            const canvas = (this.$refs.drawArea as HTMLCanvasElement);
            const ctx = canvas.getContext('2d');
            const rect = canvas.getBoundingClientRect();
            if (ctx == undefined) return;
            ctx.reset();
            this.reDrawBoxes(ctx);
            ctx.beginPath();
            ctx.lineWidth = 2;
            ctx.strokeStyle = 'red';
            ctx.rect(
                this.cvs.currentBox.top_left.x,
                this.cvs.currentBox.top_left.y,
                this.cvs.currentBox.get_width(),
				this.cvs.currentBox.get_height(),
            );
            ctx.stroke();
        },
        resize(canvas: HTMLCanvasElement) {
            const ctx = canvas.getContext('2d');
            if (ctx == undefined) return;
            ctx.canvas.width = (this.$refs.canvasWrapper as HTMLDivElement).clientWidth;
            ctx.canvas.height = (this.$refs.canvasWrapper as HTMLDivElement).clientHeight;
        }
    },
    mounted() {
        (this.$refs.drawArea as HTMLCanvasElement).addEventListener('mousedown', this.startDrawingBox);
        (this.$refs.drawArea as HTMLCanvasElement).addEventListener('mouseup', this.stopDrawingBox);
        (this.$refs.drawArea as HTMLCanvasElement).addEventListener('mousemove', this.drawBox);
}
})

</script>
<template>
    <canvas id="drawArea" width="800px" height="800px" ref="drawArea"/>
</template>
<style scoped>
.Page-Container {
    flex-direction: column;
}
#canvasWrapper {
	margin: 5%;
    width: 100%;
    height: 100%;
	justify-content: center;
	align-items: center;
}
#drawArea {
	box-shadow: 0 8px 12px 4px black;
	border-radius: 8px;
	cursor: crosshair;
	background-color: white;
}
</style>