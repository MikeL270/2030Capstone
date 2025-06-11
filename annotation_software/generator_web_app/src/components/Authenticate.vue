<script lang="ts">
import { authSession } from '../modules/apiV1Methods';
import { defineComponent } from 'vue'; 

export default defineComponent({
    name: 'Authenticate',
    data() {
        return {
           success: false,
           input_text: '',
        };
    },
    methods: {
        async establish_auth(external_id: string) {
            const responseData = await authSession(external_id)
            if(responseData["message"] === "success") {
                this.success = true;
            }
        },
    }
}); 
</script>

<template>
    <div id="auth-window">
        <label for="auth_input"> Enter your secret token: </label>
        <input type="password" id="auth_input" v-model="input_text" autocomplete="off" >
        <button @click="establish_auth(input_text)"> Authenticate </button>
        <p v-if="success">
            Successful Authentication
        </p>

    </div>
</template>
<style scoped>
    #auth-window {
        margin-top: auto;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        width: 100%;
        padding: 2.5%;
        gap: 10px;
    }
    #auth-window input {
        border-radius: 4px;
    }
    #auth-window button {
        background-color: var(--wygf-bg-blue);
        border: none;
        color: var(--color-text);
        font-weight: bold;
        border-radius: 4px;
        width: 100%;
        height: 5vh;
    }
    #auth-window button:hover {
        background-color: var(--wygf-yellow);
        color: var(--wygf-bg-blue)
    }
</style>