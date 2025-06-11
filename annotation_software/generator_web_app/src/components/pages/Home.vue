<script lang="ts">
import Authenticate from '../Authenticate.vue'

export default {
    components: {
        Auth: Authenticate
    }
}

</script>
<template>
    <div class="Page-Container">        
        <div id="Auth">
            <div id="Auth-Title">
                <h2> Authentication Required </h2>
            </div>
            <Auth/>
        </div>
    </div>
</template>
    
<style scoped>
    .Page-Container {
        flex-direction: column;
    }
    #Auth-Title {
        display: flex;
        justify-content: center;
        align-items: center;
        background-color: var(--wygf-bg-blue);
        color: var(--wygf-yellow);
        width: 100%;
        height: 100%;
        border-radius: 4px 4px 0px 0px;
        padding: 1%;
        
    }
    #Auth {
        background-color: var(--color-background-mute);
        height: auto;
        width: 25vw;
        display: flex;
        flex-direction: column;
        justify-content: center;      
        align-items: center;   
        border-radius: 4px;
        box-shadow: 0 4px 6px 2px var(--color-background);
    }
    
</style>

