<template>
  <div
    class="h-screen flex flex-col bg-card border-r transition-all duration-300"
    :class="{ 'w-64': !collapsed, 'w-16': collapsed }"
  >
    <!-- Header with logo and toggle -->
    <div class="p-4 border-b flex items-center justify-between">
      <div class="flex items-center gap-2" v-if="!collapsed">
        <div
          class="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-bold"
        >
          A
        </div>
        <h1 class="text-xl font-bold">Autobot</h1>
      </div>
      <div
        v-else
        class="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-bold mx-auto"
      >
        A
      </div>
      <button
        @click="toggleSidebar"
        class="p-1 rounded-md hover:bg-muted transition-colors"
        :class="{ 'ml-auto': collapsed }"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <line x1="3" y1="12" x2="21" y2="12" />
          <line x1="3" y1="6" x2="21" y2="6" />
          <line x1="3" y1="18" x2="21" y2="18" />
        </svg>
      </button>
    </div>

    <!-- Projects List -->
    <div class="flex-grow overflow-y-auto">
      <div class="p-2 flex items-center justify-between">
        <div
          v-if="!collapsed"
          class="text-sm font-semibold text-muted-foreground"
        >
          PROJECTS
        </div>
        <!-- New Project Button -->
        <button
          @click="createEmptyProject"
          class="p-2 rounded-md bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors flex items-center justify-center"
          :title="collapsed ? 'New Project' : ''"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          <span v-if="!collapsed" class="ml-2">New</span>
        </button>
      </div>

      <div class="space-y-1 px-2 mt-2">
        <button
          v-for="project in projects"
          :key="project.name"
          @click="loadProject(project)"
          class="w-full text-left p-2 rounded-md hover:bg-muted transition-colors flex items-center gap-2"
          :class="{
            'bg-muted': currentProject === project.name,
            'justify-center': collapsed,
          }"
        >
          <div
            class="w-6 h-6 rounded-full bg-secondary flex items-center justify-center text-secondary-foreground font-medium text-xs"
            v-if="collapsed"
          >
            {{ getProjectIcon(project.name) }}
          </div>
          <span v-if="!collapsed" class="truncate">{{ project.name }}</span>
        </button>
      </div>
    </div>

    <!-- Footer with Settings -->
    <div class="p-2 border-t">
      <button
        @click="showSettingsModal = true"
        class="w-full p-2 rounded-md hover:bg-muted transition-colors flex items-center gap-2"
        :class="{ 'justify-center': collapsed }"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path
            d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"
          />
          <circle cx="12" cy="12" r="3" />
        </svg>
        <span v-if="!collapsed">Settings</span>
      </button>
    </div>

    <!-- Settings Modal -->
    <div
      v-if="showSettingsModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showSettingsModal = false"
    >
      <div class="bg-card p-6 rounded-lg shadow-lg w-full max-w-md">
        <h2 class="text-xl font-bold mb-4">Settings</h2>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-1">API Key</label>
            <input
              v-model="settings.apiKey"
              type="password"
              class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Enter your API key"
            />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">Model</label>
            <select
              v-model="settings.model"
              class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="gpt-4">GPT-4</option>
              <option value="gpt-4-mini">GPT-4 Mini</option>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
            </select>
          </div>
          <div class="flex items-center">
            <input
              id="auto-refresh"
              v-model="settings.autoRefresh"
              type="checkbox"
              class="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
            />
            <label for="auto-refresh" class="ml-2 block text-sm">
              Auto-refresh work logs
            </label>
          </div>
        </div>
        <div class="flex justify-end gap-2 mt-6">
          <button
            @click="showSettingsModal = false"
            class="px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors"
          >
            Cancel
          </button>
          <button
            @click="saveSettings"
            class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/80 transition-colors"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useAutobotStore } from "../stores/autobot";
import { useRouter } from "vue-router";
import type { Project } from "../types";

const autobotStore = useAutobotStore();
const router = useRouter();
const collapsed = ref(false);
const showSettingsModal = ref(false);
const creatingProject = ref(false);

const settings = ref({
  apiKey: "",
  model: "gpt-4",
  autoRefresh: true,
});

const projects = computed(() => autobotStore.projects);
const currentProject = computed(() => autobotStore.status.project);

// Fetch projects on mount
onMounted(async () => {
  await autobotStore.getProjects();
});

// Watch for project changes from WebSocket
watch(
  () => autobotStore.projects,
  (newProjects) => {
    console.log("Projects updated:", newProjects);
  }
);

// Toggle sidebar collapse
const toggleSidebar = () => {
  collapsed.value = !collapsed.value;
};

// Load a project directly
const loadProject = async (project: Project) => {
  try {
    // Navigate to the project-specific URL
    router.push(`/project/${encodeURIComponent(project.name)}`);
  } catch (error) {
    console.error("Error loading project:", error);
  }
};

// Clear the current project state without creating a new project
const createEmptyProject = () => {
  // Clear the current project state in the store
  autobotStore.clearCurrentProject();

  // Navigate to home if not already there
  if (router.currentRoute.value.path !== "/") {
    router.push("/");
  }
};

// Extract emoji from project name
const getProjectIcon = (name) => {
  const firstChar = name.substring(0, 2);
  return firstChar;
};

// Save settings
const saveSettings = () => {
  // Here you would typically save settings to the server
  // For now, we'll just close the modal
  showSettingsModal.value = false;
};
</script>
