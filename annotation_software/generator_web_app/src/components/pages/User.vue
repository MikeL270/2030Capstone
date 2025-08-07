<script lang="ts">
import { defineComponent } from "vue";
import { useUserStore } from "@/modules/stores/userStore";

export default defineComponent({
  name: "Profile",
  setup() {
    const user_store = useUserStore();
    if (!user_store.projects) user_store.get_user_projects();
    return { user_store };
  },
});
</script>
<template>
  <div class="Page-Container">
    <div id="Page-Title">
      <h1>{{ user_store.get_username }}'s Profile</h1>
    </div>
    <div id="User-Roles" class="Box">
      <h2>{{ user_store.get_username }}'s Roles</h2>
      <hr />
      <ul v-for="role in user_store.get_roles">
        <li>{{ role.name }}</li>
      </ul>
    </div>
    <div id="User-Projects" class="Box">
      <h2>{{ user_store.get_username }}'s Projects</h2>
      <hr />
      <ul v-for="project in user_store.projects">
        <li>{{ project.name }}</li>
      </ul>
    </div>
  </div>
</template>
<style scoped>
#Page-Title {
  display: flex;
  justify-content: center;
  margin-bottom: auto;
  width: 100%;
  background-color: var(--color-background-mute);
  position: absolute;
  box-shadow: 0 4px 6px 2px var(--color-background);
  top: 0;
}
.Page-Container {
  display: grid;
  grid-template-columns: auto auto;
  gap: 5%;
  padding: 5%;
  position: relative;
}
.Box {
  display: flex;
  flex-direction: column;
  background-color: var(--color-background-mute);
  padding: 2%;
  border-radius: 4px 4px 4px 4px;
  box-shadow: 0 8px 12px 4px var(--color-background);
}
</style>
