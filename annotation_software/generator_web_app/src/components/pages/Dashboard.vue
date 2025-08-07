<script lang="ts">
import { defineComponent } from 'vue';
import { useUserStore } from '@/modules/stores/userStore';

export default defineComponent({
    name: 'Dashboard',
    setup() {
        const user_store = (useUserStore());
        return { user_store }
    }
})
</script>
<template>
</template>
<style scoped>

</style>

