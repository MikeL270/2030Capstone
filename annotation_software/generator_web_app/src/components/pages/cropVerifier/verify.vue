<!-- Heavily adapted from this demo: https://codesandbox.io/p/sandbox/wwyjl2 -->
<script lang="ts">
import { defineComponent, reactive, ref } from 'vue';
import type { Ref } from 'vue';
import { useCropVerifierStore } from '@/modules/stores/cropVerifierStore';
import Konva from 'konva';

interface konvaBoxConf {
    width: number;
    height: number;
    x: number;
    y: number;
    rotation: number;
}

export default defineComponent({
    name: 'crop-verifier',
    setup() {
        const cvs = useCropVerifierStore();
        const testAngles = ref([
            { x: 60, y: 60, width: 100, height: 90, id: 'testangle1', rotation: 0 },
            { x: 250, y: 100, width: 150, height: 90, id: 'rect2', rotation: 0 },
        ]);
        const rectRefs = ref([]);
        const selectedIds = ref<string[]>([]); 
        const isSelecting = ref(false); 
        const selectionRectangle = reactive({ 
            visible: false, x1: 0, y1: 0, x2: 0, y2: 0,
        });

        const stageConfig = {
            width: 700,
            height: 700,
        };

        return {
            cvs,
            stageConfig,
            testAngles,
            selectedIds,
            rectRefs,
            isSelecting,
            selectionRectangle,
        };
    },
    data() {
        return {
            stageConfig: {
                width: 700,
                height: 700,
            }
        }
    },
    mounted() {
        if (this.cvs.bootStrapped == false) this.cvs.bootStrap();
    },
    methods: {
        degToRad: (angle: number) => (angle / 180) * Math.PI,
        getCorner(pivotX: number, pivotY: number, diffX: number, diffY: number, angle: number) {
            const distance = Math.sqrt(diffX * diffX + diffY * diffY);
            angle += Math.atan2(diffY, diffX);
            const x = pivotX + distance * Math.cos(angle);
            const y = pivotY + distance * Math.sin(angle);
            return { x, y };
        },
        getClientRect(element: konvaBoxConf) {
            const { x, y, width, height, rotation = 0 } = element;
            const rad = this.degToRad(rotation);

            const p1 = this.getCorner(x, y, 0, 0, rad);
            const p2 = this.getCorner(x, y, width, 0, rad);
            const p3 = this.getCorner(x, y, width, height, rad);
            const p4 = this.getCorner(x, y, 0, height, rad);

            const minX = Math.min(p1.x, p2.x, p3.x, p4.x);
            const minY = Math.min(p1.y, p2.y, p3.y, p4.y);
            const maxX = Math.max(p1.x, p2.x, p3.x, p4.x);
            const maxY = Math.max(p1.y, p2.y, p3.y, p4.y);

            return {
                x: minX,
                y: minY,
                width: maxX - minX,
                height: maxY - minY,
            };
        },
        handleStageClick(e: MouseEvent) {
            if (this.selectionRectangle.visible) return;
            // @ts-ignore
            if (e.target === e.target.getStage()) {
                this.selectedIds = [];
                return;
            }
            // @ts-ignore
            if (!e.target.hasName('rect')) return;
            // @ts-ignore
            const clickedId = e.target.attrs.id;

            const metaPressed = e.shiftKey || e.ctrlKey || e.metaKey;
            const isSelected = this.selectedIds.includes(clickedId)

            if (!metaPressed && !isSelected) {
                this.selectedIds = [clickedId];
            } else if (metaPressed && isSelected) {
                this.selectedIds = this.selectedIds.filter(id => id !== clickedId);
            } else if (metaPressed && !isSelected) {
                this.selectedIds = [...this.selectedIds, clickedId];
            }
        },
        handleTransformEnd(e: MouseEvent, index: number) {
            // @ts-ignore
            const node = e.target; 
            // @ts-ignore
            const scaleX = node.scaleX();
            // @ts-ignore
            const scaleY = node.scaleY();

            // @ts-ignore
            node.scaleX(1);

            // @ts-ignore
            node.scaleY(1);
            
            const rects = [...this.testAngles];
            rects[index] = {
                ...rects[index],
                // @ts-ignore
                x: node.x(),
                // @ts-ignore
                y: node.y(),
                // @ts-ignore
                width: Math.max(5, node.width() * scaleX),
                // @ts-ignore
                height: Math.max(5, node.height() * scaleY), 
                // @ts-ignore
                rotation: node.rotation(),
            };
         // To update the ref correctly in the Options API context:
            this.testAngles = rects;
        },
        handleMouseDown(e: MouseEvent) {
            // @ts-ignore
            if (e.target != e.target.getStage()) {
                console.log(e.target)
                return;
            }

            this.isSelecting = true;
            // @ts-ignore
            const pos = e.target.getStage().getPointerPosition();
            this.selectionRectangle.visible = true;
            this.selectionRectangle.x1 = pos.x;
            this.selectionRectangle.y1 = pos.y;
            this.selectionRectangle.x2 = pos.x;
            this.selectionRectangle.y2 = pos.y;
        },
        handleMouseMove(e: MouseEvent) {
            if (!this.isSelecting) return;
            // @ts-ignore
            const pos = e.target.getStage().getPointerPosition();
            this.selectionRectangle.x2 = pos.x;
            this.selectionRectangle.y2 = pos.y;
        },
        handleMouseUp(e: MouseEvent) {
            if (!this.isSelecting) return;
            this.isSelecting = false;

            const selectionRect = this.selBox;
            const newSelectedIds: string[] = [];

            this.testAngles.forEach((rect) => {
                const rectClientBox = this.getClientRect(rect); 

                if (Konva.Util.haveIntersection(selectionRect, rectClientBox)) {
                    newSelectedIds.push(rect.id);
                }
            });

            this.selectedIds = newSelectedIds;

            setTimeout(() => {
                this.selectionRectangle.visible = false;
            });
        },
        handleDragEnd(e: MouseEvent, index: number) {
            if (e.target == undefined) return;
            const rects = [...this.testAngles];
            rects[index] = {
                ...rects[index],
                // @ts-ignore
                x: e.target.x(),
                // @ts-ignore
                y: e.target.y(),
            }
        },
        handleWheel(e: Event) {
            e.preventDefault();
            // @ts-ignore
            const stage = (this.$refs.stageRef as Konva.Stage).value.getNote();

        }
    },
    computed: {
        selBox() {
            return {
                x: Math.min(this.selectionRectangle.x1, this.selectionRectangle.x2),
                y: Math.min(this.selectionRectangle.y1, this.selectionRectangle.y2),
                width: Math.abs(this.selectionRectangle.x2 - this.selectionRectangle.x1),
                height: Math.abs(this.selectionRectangle.y2 - this.selectionRectangle.y1)
            }
        },
    },
    watch: {
        selectedIds: function (newSelectedIds: string[]) {
            // @ts-ignore 
            const transformerNode = this.$refs.transformerRef?.getNode();

            if (!transformerNode) return;

            // @ts-ignore
            const rectNodes = this.rectRefs.map(ref => ref.getNode());

            const nodesToAttach = rectNodes
                .filter((node: Konva.Node) => newSelectedIds.includes(node.attrs.id));

            transformerNode.nodes(nodesToAttach);
        }
    }
});

</script>
<template>
    <div v-if="cvs.bootStrapped" id="cropContainer">
        <v-stage :config="stageConfig"
        @mousedown="handleMouseDown"
        @mousemove="handleMouseMove"
        @mouseup="handleMouseUp"
        @click="handleStageClick"
        @wheel="handleWheel"
        ref="stageRef"
        >
            <v-layer ref="imageLayer" :config="{listening: false}">
                <!-- TODO: modify the v-if to not be so terrifying -->
                <v-image
                v-if="cvs.batches[0].crops[0].image && cvs.batches[0].crops[0].image[1].value === 'loaded'" 
                :config="{
                    image: cvs.batches[0].crops[0].image[0].value,
                    scaleX: 0.35,
                    scaleY: 0.35,
                }"
                />
            </v-layer>
            <v-layer ref="annotationLayer">
                <v-rect
                    v-for="(angle, i) in testAngles"
                    :key="i"
                    :config="{
                        ...angle,
                        name: 'rect',
                        draggable: true,
                        stroke: 'red',
                        strokeWidth: 2
                    }"
                    @dragend="(e: MouseEvent) => handleDragEnd(e, i)"
                    @transformend="(e: MouseEvent) => handleTransformEnd(e, i)"
                    ref="rectRefs"
                />
                <v-transformer
                    ref="transformerRef"
                    :config="{
                        boundingBoxFunc: (oldBox: konvaBoxConf, newBox: konvaBoxConf) => {
                            if (newBox.width < 5 || newBox.height < 5) {
                                return oldBox;
                            }
                            return newBox;
                        },
                        rotateEnabled: false
                    }"
                    />
                <v-rect
                    v-if="selectionRectangle.visible"
                    :config = "{
                        x: Math.min(selectionRectangle.x1, selectionRectangle.x2),
                        y: Math.min(selectionRectangle.y1, selectionRectangle.y2),
                        width: Math.abs(selectionRectangle.x2 - selectionRectangle.x1),
                        height: Math.abs(selectionRectangle.y2 - selectionRectangle.y1),
                        fill: 'rgba(0,0,255,0.5)'
                    }"
                />
            </v-layer>
        </v-stage>
    </div>
</template>
<style scoped>
    #cropContainer {
        display: flex;
        justify-content: center;
        width: 100%;

    }

</style>