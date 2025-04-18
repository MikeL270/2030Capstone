<script setup lang="ts">
import { ref } from 'vue'
import { Icon } from '@iconify/vue'
import { RouterLink} from 'vue-router'

const menu_toggled = ref(false)
</script>

<template>

    <div class="Menu" :class= {active:menu_toggled}>
        
        <button class="Toggle-Button" @click="menu_toggled = !menu_toggled">
            <Icon icon="material-symbols:menu" width="36" height="36"></Icon>
        </button>
        <nav>
            <RouterLink to="/" class="Item">
                <Icon icon="uil:home" width="36" height="36"></Icon>
                <p v-if="menu_toggled"> Home </p>
            </RouterLink>
            <RouterLink to="/profile" class="Item">
                <Icon icon="qlementine-icons:user-16" width="36" height="36"></Icon>
                <p v-if="menu_toggled"> Profile </p>

            </RouterLink>
        </nav>
        <a class="GH-Link" href="https://github.com/benkoger/pronghorn-census" >
            <Icon icon="fe:github" width="36" height="36"></Icon>
            <p v-if="menu_toggled"> Github </p>
        </a>
    </div>
</template>

<style scoped>
    .Menu {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        height: 100%;
        width: auto;
        background-color: var(--wygf-bg-blue);
        box-shadow: 0 4px 6px 2px rgba(0,0,0,0.25);
    }
    .active {
        width: 10vw;
        align-items: flex-start;
    }
    .Toggle-Button {
        background-color: rgba(0,0,0, 0);
        border: none;
        color: white;
    }
    .Toggle-Button:hover {
        color: var(--wygf-yellow);
    }
    .Item {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1vw;
        border: 1px;
        padding: 1%;
        margin-top: 2px;
    }
    .Item:hover {
        color: var(--wygf-yellow);
        background-color:  rgba(0,0,0, 0);
    }
    .GH-Link {
        padding: 5px;
        margin-top: auto;
        justify-self: flex-end;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1vw;
    }
    .GH-Link:hover {
        color: var(--wygf-yellow);
        background-color:  rgba(0,0,0, 0);
    }
</style>

