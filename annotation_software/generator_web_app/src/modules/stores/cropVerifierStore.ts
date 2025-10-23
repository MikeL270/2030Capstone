// cross component state management for crop verification functionality
// Author: Michael B. Lance
// Created: October 1, 2025
// Updated: October 2, 2025
//---------------------------------------------------------------------------------------------------------------------------//

import { Box } from "@/types/generatorobjects";
import type { coord, ReviewedArea, Annotation } from "@/types/generatorobjects"
import { defineStore } from "pinia";

//---------------------------------------------------------------------------------------------------------------------------//

interface batch {
    reviewed_areas: ReviewedArea[],
    annotations: Annotation[][],
}

export const useCropVerifierStore = defineStore('cropVerifierStore', {
    state: () => ({
        batches: [{
            'reviewed_areas': [],
            'annotations': []
        }] as batch[],
        batch_idx: 0,
        ra_idx: 0,
        active_annot_idx: 0,
        loading: false,
        bootstrapped: false,
        drawing: false,
        mousePos: {} as coord,
        boxes: [new Box({ top_left: { x: 0, y: 0 }, bottom_right: { x: 0, y: 0 } })] as Box[],
        box_idx: 0,
    }),
    getters: {
        CurrentBatch: (state) => state.batches[state.batch_idx],
        NextBatch: (state) => (state.batches[state.batch_idx + 1] != undefined) ? true : false,
        LastBatch: (state) => (state.batches[state.batch_idx - 1] != undefined) ? true : false,
        CurrentReviewedAreas(): ReviewedArea[] { return this.CurrentBatch.reviewed_areas },
        CurrentAnnotations(state): Annotation[] { return this.CurrentBatch.annotations[state.ra_idx] },
        currentBox: (state) => state.boxes[state.box_idx]
    },
    actions: {
        getMousePos(e: MouseEvent) {
            this.mousePos.x = e.offsetX;
            this.mousePos.y = e.offsetY;
        },
        setBoxStart() {
            const x = this.mousePos.x;
            const y = this.mousePos.y;
            this.currentBox.top_left = { x, y };
        },
        setBoxEnd() {
            const x = this.mousePos.x;
            const y = this.mousePos.y;
            this.currentBox.bottom_right = { x, y };
        },
        newBox() {
            this.box_idx++;
            this.boxes.push(new Box({ top_left: { x: 0, y: 0 }, bottom_right: { x: 0, y: 0 } }));
        }
    }
})