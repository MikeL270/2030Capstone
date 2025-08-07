<script lang="ts">
import { useProjectStore } from "@/modules/stores/projectStore";
import { defineComponent } from "vue";

export default defineComponent({
    name: 'Cropper-Configurinator-3000',
    setup() {
        const project_store = useProjectStore();
        return { project_store }
    },
})
</script>
<template>
    <div id="Configuration-Container">
        <div class="Configuration-Menu">
            <h2> Schema Selection </h2>
            <div class="Table-Title"> 
                <p> Name </p>
                <p> Created </p>
                <p> Modified </p>
                <p> External ID </p> 
            </div>
            <figure>
                <button class="Item" v-for="schema in project_store.schemas" @click="project_store.set_current_schema(schema)" :class="{Selected: project_store.CurrentSchema?.uuid == schema.uuid}">
                    <p> {{ schema.name }} </p> 
                    <p> {{ schema.created.toLocaleString('en-US', { 
                        year: 'numeric', 
                        month: 'numeric', 
                        day: 'numeric', 
                        }) }} 
                    </p>
                    <p> {{ schema.modified.toLocaleString('en-US', { 
                        year: 'numeric', 
                        month: 'numeric', 
                        day: 'numeric', 
                        }) }} 
                    </p>
                    <p> {{ schema.uuid }} </p>
                </button>
            </figure>
        </div>
        <div class="Configuration-Menu">
            <h2> Label Selection </h2>
            <div class="Table-Title"> 
                <p> Name </p>
                <p> Created </p>
                <p> Modified </p>
                <p> External ID </p> 
            </div>
            <figure>
                <button class="Item" v-for="label in project_store.labels" @click="project_store.set_current_label(label)" :class="{Selected: project_store.CurrentLabel?.uuid == label.uuid}" >
                    <p> {{ label.name }} </p> 
                    <p> {{ label.created.toLocaleString('en-US', { 
                        year: 'numeric', 
                        month: 'numeric', 
                        day: 'numeric', })}} 
                    </p>
                    <p> {{ label.modified.toLocaleString('en-US', { 
                        year: 'numeric', 
                        month: 'numeric', 
                        day: 'numeric', })}} 
                    </p>
                    <p> {{ label.uuid }} </p>
                </button>
            </figure>
        </div>
        <div class="Configuration-Menu">
            <h2> Herd Unit Selection </h2>
            <div class="Table-Title"> 
                <p> Name </p>
                <p> Created </p>
                <p> Modified </p>
                <p> External ID </p> 
            </div>
            <figure>
                <button class="Item" v-for="herdunit in project_store.herd_units" @click="project_store.set_current_herd_unit(herdunit) ":class="{Selected: project_store.CurrentHerdUnit?.uuid}">
                    <p> {{ herdunit.name }} </p> 
                        <p> {{ herdunit.created.toLocaleString('en-US', { 
                            year: 'numeric', 
                            month: 'numeric', 
                            day: 'numeric', 
                            }) }} 
                        </p>
                        <p> {{ herdunit.modified.toLocaleString('en-US', { 
                            year: 'numeric', 
                            month: 'numeric', 
                            day: 'numeric', 
                            }) }} 
                        </p>
                        <p> {{ herdunit.uuid }} </p>
                </button>
            </figure>
        </div>
        <div class="Configuration-Menu">
            <h2> Model Selection </h2>
            <div class="Table-Title"> 
                <p> Name </p>
                <p> Created </p>
                <p> Modified </p>
                <p> External ID </p> 
            </div>
            <figure>
                <button class="Item" v-for="model in project_store.models" @click="project_store.set_current_model(model)" :class="{Selected: project_store.CurrentModel?.uuid}">
                    <p> {{ model.name }} </p> 
                        <p> {{ model.created.toLocaleString('en-US', { 
                            year: 'numeric', 
                            month: 'numeric', 
                            day: 'numeric', 
                            }) }} 
                        </p>
                        <p> {{ model.modified.toLocaleString('en-US', { 
                            year: 'numeric', 
                            month: 'numeric', 
                            day: 'numeric', 
                            }) }} 
                        </p>
                        <p> {{ model.uuid }} </p>
                </button>
            </figure>
        </div>
    </div>
</template>
<style scoped>
.Configuration-Menu {
    border-radius: 8px 8px 8px 8px;
    width: 32vw;
    box-shadow: 0 8px 12px 4px var(--color-background);
    border: solid 1px var(--color-background);
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 1%;
    text-align: center;
    max-height: 35vh;
    
    button {
        border: none;
        background: none;
        color: var(--color-text);
        font-size: 1em;
    }
    button:hover {
        color: rgb(255, 255, 255);
    }
}
figure {
    display: flex;
    gap: 10px;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    align-self: center;
    max-height: 35vh;
    overflow-y: auto;
    overflow-x: hidden;
    scrollbar-color: var(--color-text) transparent;
}
.Table-Title {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr 1fr;
    width: 100%;
    justify-content: center;
    text-align: center;
    align-items: center;
    height: 7vh !important;
    font-weight: 900;
    border-radius: 0px !important;
}
#Configuration-Container {
    display: grid;
    gap: 15px;
    width: 67vw;
    height: 100%;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 1fr 1fr;
    }
.Item {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr 1fr;
    min-height: 10vh;
    gap: 5px;
    width: 98%;
    margin: 0% 3% 0% 3%;
    border-radius: 8px;
    border: solid 1px var(--color-background) !important;
    color: var(--color-text);
    background: none;
    font-size: 1.10em;
    p {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        font-size: 0.75em;
    }
}
.Selected {
    color: var(--wygf-yellow) !important;
    box-shadow: 0 2px 4px 2px var(--color-background);
}
</style>