// cross component state management for autocropper functionality
// Author: Michael B. Lance
// Created: July 25, 2025
// Updated: July 28, 2025
//---------------------------------------------------------------------------------------------------------------------------//

import { defineStore } from "pinia";
import { Project, Schema, Label, Model, HerdUnit } from "@/types/generatorobjects";
import { getProjectSchemas, getSchemaLabels, getProjectHerdUnits, getProjectModels } from "../apiV1Methods";

//---------------------------------------------------------------------------------------------------------------------------//

export const useAutoCropperStore = defineStore('autoCropperStore', {
    state: () => ({
        project: undefined as Project | undefined,
        schemas: undefined as Schema[] | undefined,
        labels: undefined as Label[] | undefined,
        models: undefined as Model[] | undefined,
        herd_units: undefined as HerdUnit[] | undefined,
        schema: undefined as Schema | undefined,
        label: undefined as Label | undefined,
        model: undefined as Model | undefined,
        herd_unit: undefined as HerdUnit | undefined,
    }),
    actions: {
        async get_project_schemas(): Promise<boolean> {
            this.schemas = await getProjectSchemas(this.project?.uuid);
            if (this.schemas) { return true; } else { return false; }
        },
        async get_schema_labels(): Promise<boolean> {
            this.labels = await getSchemaLabels(this.project?.uuid, this.schema?.uuid);
            if (this.labels) { return true; } else { return false; }
        },

        async get_project_herd_units(): Promise<boolean> {
            this.herd_units = await getProjectHerdUnits(this.project?.uuid);
            if (this.herd_units) { return true; } else { return false; }
        },
        async get_project_models(): Promise<boolean> {
            this.models = await getProjectModels(this.project?.uuid);
            if (this.models) { return true; } else { return false; }
        },
        clear_selectables() {
            this.schemas = undefined;
            this.labels = undefined;
            this.models = undefined;
            this.herd_units = undefined;
        },
        clear_selection() {
            this.schema = undefined;
            this.label = undefined;
            this.model = undefined;
            this.herd_unit = undefined;
        }
    }
})