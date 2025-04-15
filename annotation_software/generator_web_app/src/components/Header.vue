<script setup lang="ts">
import { ref } from 'vue'
import { Icon } from '@iconify/vue'


</script>

<template>
  <div class="Title">
    <h1> Pronghorn Counter </h1>
  </div>
  <div class="Navigation">
    <a href="https://www.minecraft.net"> I am a router link</a>
  </div>

</template>

<style scoped>
  .Title {
    position: absolute;
    left: 0;
    padding: 0.5%;
  }
  .Navigation {
    position: absolute;
    right: 0;
    display: flex;
    flex-direction: column;
    padding: 0.5%;
  }
</style>