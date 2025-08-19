<script lang="ts">
import { defineComponent } from 'vue';
import { ref } from 'vue';
import { Icon } from '@iconify/vue';
import { RouterLink} from 'vue-router';
import { useUserStore } from '@/modules/stores/userStore';
import { usePreferenceStore } from '@/modules/stores/preferencesStore';


export default defineComponent({
    name: 'Menu',
    setup() {
        const menu_toggled = ref(false);
        const user_store = useUserStore();
		const pref_store = usePreferenceStore();
        return { menu_toggled, user_store, pref_store }
    }
})
</script>

<template>
    <div class="Menu" :class= {active:menu_toggled} @mouseenter="menu_toggled=true" @mouseleave="menu_toggled=false">     
        <nav>
            <RouterLink to="/" class="Item" title="Dashboard">
                <Icon icon="ic:round-dashboard" width="36" height="36" ></Icon>
                <p v-if="menu_toggled"> Dashboard </p>
            </RouterLink>
            <RouterLink to="/auto-cropper/" :class="['Item', {'router-link-active': $route.path.startsWith('/auto-cropper')}]" title="Auto Crop">
                <Icon icon="fluent:crop-sparkle-24-filled" width="36" height="36"></Icon>
                <p v-if="menu_toggled"> Auto Crop </p>
            </RouterLink>
            <RouterLink to="/upload" class="Item" :class="['Item', {'router-link-active': $route.path.startsWith('/upload')}]" title="Upload">
                <Icon icon="material-symbols:upload" width="36" height="36"></Icon>
                <p v-if="menu_toggled"> Upload </p>
            </RouterLink>
            <RouterLink to="/statistics" class="Item" title="Statistics">
                <Icon icon="wpf:statistics" width="36" height="36"></Icon>
                <p v-if="menu_toggled"> Statistics </p>
            </RouterLink>
            <RouterLink v-if="user_store.logged_in" :to="{ name: 'user', params: { uuid: user_store.user?.uuid}}" class="Item" title="Profile">
                <Icon icon="iconamoon:profile-fill" width="36" height="36"></Icon>
                <p v-if="menu_toggled"> User </p>
            </RouterLink>
            <RouterLink to="/settings" class="Item" title="Settings">
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
        width: 3vw;
        background-color: var(--wygf-bg-blue);
        box-shadow: 0 4px 6px 2px var(--color-background-soft);
    }
    nav {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        width: 100%;
    }
    .Menu:hover {
        align-items: flex-start;
        padding-right: 5px;
		width: 8vw;
		opacity: 95%
    }
    .Item {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        gap: 1vw;
        width: 100%;
        font-size: 0.75em;
    }
    .Item:hover {
        color: var(--color-text);
		cursor: pointer;
        background: none;
    }
    .router-link-active {
        color: var(--wygf-yellow);
    }
    .GH-Link {
        padding: 5px;
        margin-top: auto;
        justify-self: flex-end;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1vw;
        border-top: 1px solid var(--color-border);
        width: 100%;
    }
    .GH-Link:hover {
        color: var(--color-text);
    }
</style>

