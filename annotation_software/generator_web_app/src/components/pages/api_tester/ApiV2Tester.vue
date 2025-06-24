<script lang="ts">
import { createBatch } from '../../../modules/apiV1Methods';
import { defineComponent } from 'vue';
export default defineComponent({
    name: 'V1Tester',
    data() {
        return {
            apiResponse: null as string | null,
            params: {
                batch_size: '',
                desired_class: '',
                min_confidence: '',
            },
        };
    },
    methods: {
        async create_batch(params: Record<string, any>) {
            const responseData = await createBatch(params);
            this.apiResponse = JSON.stringify(responseData, null, 2);
        }
    },
});
</script>

<template>
    <h1> V2 API Tester </h1>
    <p> The V2 API is currently only a planned GraphQL API layer designed to enable fine grained
        management of the database layer to enable project administration tools that are outside of
        the current scope of the restful V1 API which focuses on being a minimum viable product. Since 
        there is currently only one developer for the webapp, API, and database a minimum skeleton of
        the project has been laid out with plans to revisit components as time allows. 
    </p>
</template>