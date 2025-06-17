<script lang="ts">
import { defineComponent, ref, computed } from 'vue'; 
import { useUserStore } from '@/modules/userManagement';
import { useRouter, useRoute } from 'vue-router';

export default defineComponent({
    name: 'Authenticate',
    setup() {
        const user_store = (useUserStore());
        const router = useRouter();
        const route = useRoute();

        const redirection_path = route.query.redirect as string; 

        return { user_store, router, route, redirection_path }
    },
    data() {
        return {
            show_message: false,
            message: '',
            id_input: '',
        };
    },
    methods: {
        async establish_auth(external_id: string) {
            await this.user_store.authenticate(external_id)
            if (this.user_store.logged_in) {
                this.create_message(`Welcome, ${this.user_store.user?.userName}`)
                if (this.redirection_path) {
                    this.router.push(this.redirection_path);
                }
                else {
                    this.router.push('/');
                }
            } else {
                this.create_message('Authentication Failed!')
            }
        },
        // TODO: Move this to its own component mounted in app.vue to persist 
        create_message(message: string) {
            this.show_message = true;
            this.message = message;
        }
    },
    watch: {
        show_message(newValue) {
            if (newValue) setTimeout(() => {
                this.show_message = false;
            }, 3000)
        }
    },
    mounted() {
        this.create_message("You must be logged in to view this resource!");
    },
}); 
</script>

<template>
    <div class="Page-Container">
        <transition name="fade">
            <div v-if="show_message" id="Popup-Message">
                <Icon icon="material-symbols:info" width="16" height="16" />
                <p> {{ message }} </p>
            </div>
        </transition>
        <div id="auth-wrapper">
            <div id="wrapper-title">
                <h2> Authentication Required </h2>
                
            </div>
            <form id="auth-input">
                <label for="token_input"> Enter your access token: </label>
                <input type="password" id="token_input" v-model="id_input" autocomplete="off" >
            </form>
             <button @click="establish_auth(id_input)"> Authenticate </button>
        </div>
    </div>
</template>
<style scoped>
.Page-Container {
        flex-direction: column;
        
    }
    #wrapper-title {
        display: flex;
        justify-content: center;
        align-items: center;
        background-color: var(--wygf-bg-blue);
        color: var(--wygf-yellow);
        width: 100%;
        height: 100%;
        max-height: 10vh;
        border-radius: 4px 4px 0px 0px;
        padding: 1%;
        font-size: 1em;
    }
    #auth-wrapper {
        background-color: var(--color-background-mute);
        height: 50vh;
        min-width: 25vw;
        display: flex;
        flex-direction: column;
        justify-content: center;      
        align-items: center;   
        border-radius: 4px;
        box-shadow: 0 8px 12px 4px var(--color-background);
    }
    #auth-input {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        height: 100%;
        width: 100%;
        padding: 2.5%;
        gap: 10px
    }
    #auth-input label {
        font-size: 1em;
    }
    #auth-input input {
        border-radius: 4px;
        width: 90%;
    }
    #auth-wrapper button {
        background-color: var(--wygf-bg-blue);
        border: none;
        color: var(--color-text);
        font-weight: bold;
        border-radius: 0 0 4px 4px;
        width: 100%;
        height: 15vh;
        margin-top: auto;
    }
    #auth-wrapper button:hover {
        background-color: var(--wygf-yellow);
        color: var(--wygf-bg-blue)
    }
    #Popup-Message {
        display: flex;
        justify-content: center;
        align-items: center;
        background-color: var(--wygf-bg-blue);
        color: var(--wygf-yellow);
        padding: 1%;
        position: absolute;
        top: 0;
        margin-top: 6vh;
        border-radius: 4px;
        height: 5vh;
        min-width: 35vw;
    }
    #Popup-Message svg {
        margin-right: 1%;
    }
    .fade-enter-active,
    .fade-leave-active {
        transition: opacity 0.5s ease;
    }

    .fade-enter-from,
    .fade-leave-to {
    opacity: 0;
    }
</style>