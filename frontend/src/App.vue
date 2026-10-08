<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();

onMounted(() => {
  if (authStore.isLoggedIn) {
    authStore.fetchUser();
  }
});
</script>

<style>
body {
  margin: 0;
  font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Microsoft YaHei", sans-serif;
  background: #f5f7fa;
}
#app {
  min-height: 100vh;
}
</style>
