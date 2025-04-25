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

<script setup lang="ts">
import { onMounted, onBeforeUnmount } from "vue";
import { useAutobotStore } from "./stores/autobot";
import Sidebar from "./components/Sidebar.vue";

const autobotStore = useAutobotStore();

onMounted(() => {
  console.log("App mounted - initializing WebSocket and getting status");

  // Initialize WebSocket connection
  autobotStore.initWebSocket();

  // Get initial status
  autobotStore.getStatus();

  // Add event listener for page unload to properly close WebSocket
  window.addEventListener("beforeunload", handleBeforeUnload);
});

onBeforeUnmount(() => {
  console.log("App unmounting - cleaning up WebSocket");

  // Remove event listener
  window.removeEventListener("beforeunload", handleBeforeUnload);

  // Close WebSocket connection
  autobotStore.closeWebSocket();
});

// Handle page unload to properly close WebSocket
const handleBeforeUnload = () => {
  console.log("Page unloading - closing WebSocket");
  autobotStore.closeWebSocket();
};
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
