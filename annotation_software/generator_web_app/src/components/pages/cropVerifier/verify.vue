<script lang="ts">
import { defineComponent } from 'vue';
import { useCropVerifierStore } from '@/modules/stores/cropVerifierStore';

export default defineComponent({
    name: 'crop-verifier',
    setup() {
        const cvs = useCropVerifierStore();

        return { cvs }
    },
    methods: {

    },
})

</script>
<template>
   <div id="cropContianer">

   </div>
</template>
<style scoped>

</style>