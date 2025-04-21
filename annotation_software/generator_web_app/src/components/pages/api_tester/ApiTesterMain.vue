<script  lang="ts">
import { ref } from 'vue'
import { defineAsyncComponent } from 'vue';

var tab_num = ref<number>(0);
const V1Tester = defineAsyncComponent(() => import('./ApiV1Tester.vue'));
const V2Tester = defineAsyncComponent(() => import('./ApiV2Tester.vue'))
export default {
    components: {
        V1Test: V1Tester,
        v2Test: V2Tester,
    },

    data() {
        return {
            active_tab: tab_num,
        }
    }
};


</script>
<template>
    <div class="Page-Content">
        <div class="Tab-Bar">
            <button class="Tab" @click="active_tab = 0" title="V1 Testing tab" :class="{active: active_tab==0}">V1 </button>
            <button class="Tab" @click="active_tab = 1" title="V2 Testing tab":class="{active: active_tab==1}">V2 </button>
        </div>
        <br>
        <V1Test v-if="active_tab == 0" />
        <v2Test v-else-if="active_tab == 1"/>    
    </div>


</template>

<style scoped>
    .Tab-Bar {
        display: flex;
        align-items: center;
        gap: 5px;
        width: 100%;
        height: 5vh;
    }
    .Tab {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100%;
        width: 20vw;
        background-color: var(--color-background-soft);
        box-shadow: 0 4px 6px 2px rgba(0,0,0,0.25);
        color: var(--color-text);
        border-radius: 4px;
        border: none;
    }   
    .active  {
        background-color: var(--color-background-mute);
        box-shadow: 0 4px 6px 2px rgba(77, 77, 77, 0.25);

    }
    .Contnet {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        width: 100%;
        height: 100%;
        gap: 5px;
    }
    .Response-Container {
        display: flex;
        width: 75vw;
        min-height: 25vh;
        height: auto;
        overflow: auto;
        background-color: black;
    }
</style>