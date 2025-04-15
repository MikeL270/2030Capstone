<script setup lang="ts">

import { ref } from 'vue'
import { Icon } from '@iconify/vue'

</script>

<template>

    <p>
        <Icon icon="tabler:copyright" /> 
        2025 {insert correct owner here} | All Rights Reserved
        <a href="https://github.com/benkoger/pronghorn-census/tree/main">
            <Icon icon="ri:github-fill" width="24" height="24" />
        </a>
    </p>

</template>

<style scoped>
    p {
        display: flex;
        justify-content: center;
        align-items: center;
    }
    a {
        display: flex;
        justify-content: center;
        align-items: center;
    }
</style>