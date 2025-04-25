<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Projects</h1>
      <button 
        @click="showCreateModal = true" 
        class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/80 transition-colors"
      >
        Create Project
      </button>
    </div>
    
    <div v-if="loading" class="flex justify-center my-8">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
    </div>
    
    <div v-else-if="projects.length === 0" class="text-center my-12">
      <p class="text-xl text-muted-foreground">No projects found</p>
      <p class="mt-2 text-muted-foreground">Create a new project to get started</p>
    </div>
    
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div 
        v-for="project in projects" 
        :key="project.name" 
        class="p-6 bg-card rounded-lg shadow-sm border hover:shadow-md transition-shadow"
      >
        <h2 class="text-xl font-semibold mb-2">{{ project.name }}</h2>
        <p class="text-muted-foreground mb-4 line-clamp-2">{{ project.goal }}</p>
        
        <div class="flex justify-between items-center">
          <span class="text-sm text-muted-foreground">
            {{ formatDate(project.created_at) }}
          </span>
          <router-link 
            :to="`/projects/${project.name}`" 
            class="px-3 py-1 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors"
          >
            Open
          </router-link>
        </div>
      </div>
    </div>
    
    <!-- Create Project Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-background rounded-lg p-6 w-full max-w-md">
        <h2 class="text-xl font-semibold mb-4">Create New Project</h2>
        
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-1" for="project-name">Project Name</label>
            <input 
              v-model="newProject.name" 
              id="project-name" 
              type="text" 
              class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="My Project"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium mb-1" for="project-goal">Project Goal</label>
            <textarea 
              v-model="newProject.goal" 
              id="project-goal" 
              rows="4" 
              class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Describe what you want to achieve with this project"
            ></textarea>
          </div>
        </div>
        
        <div class="flex justify-end gap-2 mt-6">
          <button 
            @click="showCreateModal = false" 
            class="px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors"
          >
            Cancel
          </button>
          <button 
            @click="createProject" 
            class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/80 transition-colors"
            :disabled="!newProject.name || !newProject.goal || creatingProject"
          >
            {{ creatingProject ? 'Creating...' : 'Create' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useAutobotStore } from '../stores/autobot';
import { useRouter } from 'vue-router';

const autobotStore = useAutobotStore();
const router = useRouter();

const showCreateModal = ref(false);
const newProject = ref({
  name: '',
  goal: ''
});
const creatingProject = ref(false);

const projects = computed(() => autobotStore.projects);
const loading = computed(() => autobotStore.loading);

// Fetch projects on mount
onMounted(async () => {
  await autobotStore.getProjects();
});

// Create a new project
const createProject = async () => {
  if (!newProject.value.name || !newProject.value.goal) return;
  
  try {
    creatingProject.value = true;
    const result = await autobotStore.createProject(newProject.value.name, newProject.value.goal);
    showCreateModal.value = false;
    newProject.value = { name: '', goal: '' };
    
    // Navigate to the new project
    router.push(`/projects/${result.name}`);
  } catch (error) {
    console.error('Error creating project:', error);
  } finally {
    creatingProject.value = false;
  }
};

// Format date
const formatDate = (dateString) => {
  if (!dateString) return '';
  
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString();
  } catch (error) {
    return dateString;
  }
};
</script>
