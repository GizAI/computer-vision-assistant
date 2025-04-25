<template>
  <div class="h-screen w-full flex overflow-hidden bg-background">
    <!-- Sidebar -->
    <Sidebar />

    <!-- Main Content -->
    <main class="flex-1 overflow-hidden">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { onMounted } from "vue";
import { useAutobotStore } from "./stores/autobot";
import Sidebar from "./components/Sidebar.vue";

const autobotStore = useAutobotStore();

onMounted(() => {
  // Initialize WebSocket connection
  autobotStore.initWebSocket();

  // Get initial status
  autobotStore.getStatus();
});
</script>

<style>
html,
body,
#app {
  height: 100%;
  width: 100%;
  margin: 0;
  padding: 0;
  overflow: hidden;
}
</style>
