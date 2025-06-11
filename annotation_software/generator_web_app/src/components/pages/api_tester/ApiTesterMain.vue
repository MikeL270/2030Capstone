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
    <div class="Page-Container">
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
    .Page-Container {
        flex-direction: column;
    }
    .Tab-Bar {
        display: flex;
        align-items: center;
        gap: 1vw;
        width: 100%;
        height: 5vh;
        min-height: 40px;
        border-bottom: 1px solid var(--color-border);
        background-color: var(--color-background);
        border-radius: 4px;
        padding: .1%;

    }
    .Tab {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 90%;
        width: 20vw;
        background-color: var(--color-background-soft);
        box-shadow: 0 4px 6px 2px rgba(0,0,0,0.25);
        color: var(--color-text);
        border-radius: 4px;
        border: none;
    }   
    .active  {
        background-color: var(--color-border);
    }
    .Page-Content {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        width: 100%;
        max-width: 100%;
        overflow: hidden;
        height: 100%;
        gap: 5px;
    }

</style>