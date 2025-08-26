<script lang="js">
import { defineComponent, ref } from 'vue';
import { usePreferenceStore } from '@/modules/stores/preferencesStore';
import { useUserStore } from '@/modules/stores/userStore';

export default defineComponent({
	name:'header_component',
	setup() {
		const user_store = useUserStore();
		const pref_store = usePreferenceStore();
		const is_toggled = ref((pref_store.theme == 'light-theme') ? true : false)

		return {user_store, pref_store, is_toggled}
	}
})

</script>
<template>
   <header>
       <h1> Pronghorn Census Software / {{ $route.name }}</h1>
	   <div id="User-Quick-Actions-Holder" v-if="user_store.logged_in">
			<label class="switch" for="theme-toggle" title="Toggle Theme">
					<input id="theme-toggle" type="checkbox" @change="pref_store.toggleTheme()" v-model="is_toggled"> 
					<div class="slider round">
					</div>
			</label>  
			<Icon icon="material-symbols-light:light-mode" width="24" height="24 " v-if="pref_store.theme == 'light-theme'"></Icon>
			<Icon icon="material-symbols:dark-mode-outline" width="24" height="24 " v-else></Icon>
			<p> {{ user_store.user?.username }} </p>
			</div>
   </header>
</template>

<style scoped>
header {
    display: flex;
    justify-content: flex-start;
    align-items: center;
    position: fixed;
    width: 100%;
    height: 4.5vh;
    top: 0;
    left: 0;
    margin-right: auto;
    color: var(--color-heading);
    background-color: var(--wygf-bg-blue);
    border-bottom: 1px solid var(--color-border);
    box-shadow: 0 4px 6px 2px var(--color-background-soft);
    h1 {
            font-size: 1.25em;
            margin-left: 1%;
        }
	#User-Quick-Actions-Holder {
		margin-left: auto;
		margin-right: 1%;
		display: flex;
		align-items: center;
		gap: 5px;
		overflow: visible;
		details {		
			cursor: pointer;	
			width: 6vw;
			background-color: var(--wygf-bg-blue);
		}
	}
	}
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
</style>