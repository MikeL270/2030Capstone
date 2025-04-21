<script setup lang="ts">
import { ref } from 'vue'
import { Icon } from '@iconify/vue'
import { RouterLink} from 'vue-router'

const menu_toggled = ref(false)
</script>

<template>

    <div class="Menu" :class= {active:menu_toggled}>
        
        <button class="Toggle-Button" @click="menu_toggled = !menu_toggled"title="Toggle Menu">
            <Icon icon="material-symbols:menu" width="36" height="36"></Icon>
        </button>
        <nav>
            <RouterLink to="/" class="Item" title="Home">
                <Icon icon="uil:home" width="36" height="36" ></Icon>
                <p v-if="menu_toggled"> Home </p>
            </RouterLink>
            <RouterLink to="/annotate" class="Item" title="Annotate">
                <Icon icon="foundation:annotate" width="36" height="36"></Icon>
                <p v-if="menu_toggled"> Annotate </p>
            </RouterLink>
            <RouterLink to="/statistics" class="Item" title="Statistics">
                <Icon icon="uil:statistics" width="36" height="36"></Icon>
                <p v-if="menu_toggled"> Statistics </p>
            </RouterLink>
            <RouterLink to="/profile" class="Item" title="Profile">
                <Icon icon="iconamoon:profile-fill" width="36" height="36"></Icon>
                <p v-if="menu_toggled"> Profile </p>
            </RouterLink>
            <RouterLink to="/api-tester" class="Item"title="API Tester">
                <Icon icon="fluent-mdl2:test-auto-solid" width="36" height="36"></Icon>
                <p v-if="menu_toggled"> API Tester </p>
            </RouterLink>
            <RouterLink to="/settings" class="Item"title="Settings">
                <Icon icon="ic:outline-settings" width="36" height="36"></Icon>
                <p v-if="menu_toggled"> Settings </p>
            </RouterLink>

        </nav>
        <a class="GH-Link" href="https://github.com/benkoger/pronghorn-census" title="Github repo">
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
        justify-content: center;
        height: 100%;
        width: auto;
        background-color: var(--wygf-bg-blue);
        box-shadow: 0 4px 6px 2px rgba(0,0,0,0.25);
        
    }
    nav {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        width: 100%;
    }
  
    .active {
        width: 15vw;
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
        justify-content: flex-start;
        gap: 1vw;
        width: 100%;
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
        border-top: 1px solid var(--vt-c-black-mute);
        width: 100%;
        box-shadow: 0 4px 6px 2px rgba(0,0,0,0.25);
    }
    .GH-Link:hover {
        color: var(--wygf-yellow);
        background-color:  rgba(0,0,0, 0);
    }
</style>

