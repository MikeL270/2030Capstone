<script lang="ts">
import { defineComponent, ref } from 'vue';
import { usePreferenceStore } from '@/modules/stores/preferencesStore';
import { useUserStore } from '@/modules/stores/userStore';
import { preProcessFile } from 'typescript';

export default defineComponent({
	name:'header_component',
    setup() {
        const isDev = import.meta.env.DEV;
		const user_store = useUserStore();
		const pref_store = usePreferenceStore();
		const is_toggled = ref((pref_store.theme == 'light-theme') ? true : false)

		return {user_store, pref_store, is_toggled, isDev}
    },
    methods: {
        async logout() {
            await this.user_store.deuathenticate();
            this.$router.push('/authenticate')
        }
    }
})

</script>
<template>
    <header>
        <h1> Pronghorn Census Software / {{ $route.name }}</h1>
        <p v-if="isDev" style="color: red; margin-left: 0.5%; "> Development Mode  </p>
	    <div id="User-Quick-Actions-Holder" v-if="user_store.logged_in">
			<label class="switch" for="theme-toggle" title="Toggle Theme">
					<input id="theme-toggle" type="checkbox" @change="pref_store.toggleTheme()" v-model="is_toggled"> 
					<div class="slider round">
					</div>
			</label>  
			<Icon icon="material-symbols-light:light-mode" width="24" height="24 " v-if="pref_store.theme == 'light-theme'"></Icon>
			<Icon icon="material-symbols:dark-mode-outline" width="24" height="24 " v-else></Icon>
			<p> {{ user_store.user?.username }} </p>
            <button id="logout" @click="logout()"><Icon icon="mdi:logout"></Icon></button>
        </div>
    </header>
</template>

<style scoped>

	p {
		margin: 1%;
	}
	.switch {
        position: relative;
        display: inline-block;
        width: 2.5vw;
		align-self: center;
        height: 15px;
		margin: 2%;
    }
    .switch input {
        display: none;
    }
	.slider {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: #ccc;
        -webkit-transition: 0.4s;
        transition: 0.4s;
}
    .slider:before {
        position: absolute;
        content: "";
        height: 8px;
        width: 8px;
        left: 0.25vw;
        bottom: 4px;
        background-color: rgb(73, 73, 73);
        -webkit-transition: 0.4s;
        transition: 0.4s;
    }

    input:focus + .slider {
        box-shadow: 0 0 1px #101010;
    }
    input:checked + .slider:before {
        -webkit-transform: translateX(1.19vw);
        -ms-transform: translateX(1.19vw);
        transform: translateX(1.19vw);
    }
    .slider.round {
        border-radius: 34px;
    }
    .slider.round:before {
        border-radius: 50%;
    }
#logout {
    background: none;
    border: none;
    color: var(--color-text)
}
</style>