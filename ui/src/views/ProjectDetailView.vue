<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">{{ projectName }}</h1>
      <div class="flex gap-2">
        <button 
          @click="goBack" 
          class="px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors"
        >
          Back
        </button>
        <button 
          @click="loadProject" 
          class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/80 transition-colors"
        >
          Load Project
        </button>
      </div>
    </div>
    
    <div v-if="loading" class="flex justify-center my-8">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
    </div>
    
    <div v-else-if="!project" class="text-center my-12">
      <p class="text-xl text-muted-foreground">Project not found</p>
    </div>
    
    <div v-else>
      <!-- Project Details -->
      <div class="p-6 bg-card rounded-lg shadow-sm border mb-6">
        <h2 class="text-xl font-semibold mb-4">Project Details</h2>
        
        <div class="space-y-4">
          <div>
            <h3 class="text-sm font-medium text-muted-foreground">Goal</h3>
            <p class="mt-1">{{ project.goal }}</p>
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <h3 class="text-sm font-medium text-muted-foreground">Created</h3>
              <p class="mt-1">{{ formatDate(project.created_at) }}</p>
            </div>
            <div>
              <h3 class="text-sm font-medium text-muted-foreground">Last Updated</h3>
              <p class="mt-1">{{ formatDate(project.updated_at) }}</p>
            </div>
            <div>
              <h3 class="text-sm font-medium text-muted-foreground">Status</h3>
              <p class="mt-1">{{ capitalizeFirstLetter(project.status) }}</p>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Project Plan -->
      <div class="p-6 bg-card rounded-lg shadow-sm border mb-6">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-xl font-semibold">Project Plan</h2>
          <button 
            @click="refreshPlan" 
            class="px-3 py-1 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors"
          >
            Refresh
          </button>
        </div>
        
        <div v-if="loadingPlan" class="flex justify-center my-8">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
        
        <div v-else-if="!plan" class="text-center my-8">
          <p class="text-muted-foreground">No plan available</p>
        </div>
        
        <div v-else class="prose prose-sm max-w-none" v-html="formatMarkdown(plan)"></div>
      </div>
      
      <!-- Execute Task -->
      <div class="p-6 bg-card rounded-lg shadow-sm border">
        <h2 class="text-xl font-semibold mb-4">Execute Task</h2>
        
        <div class="flex gap-2">
          <input 
            v-model="taskInput" 
            type="text" 
            placeholder="Enter task description..." 
            class="flex-1 px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <button 
            @click="executeTask" 
            class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/80 transition-colors"
            :disabled="!taskInput || executingTask"
          >
            {{ executingTask ? 'Executing...' : 'Execute' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAutobotStore } from '../stores/autobot';
import { marked } from 'marked';

const route = useRoute();
const router = useRouter();
const autobotStore = useAutobotStore();

const projectName = computed(() => route.params.name);
const project = ref(null);
const plan = ref('');
const loading = ref(false);
const loadingPlan = ref(false);
const taskInput = ref('');
const executingTask = ref(false);

// Fetch project details and plan on mount
onMounted(async () => {
  await loadProjectDetails();
  await loadProjectPlan();
});

// Load project details
const loadProjectDetails = async () => {
  loading.value = true;
  try {
    await autobotStore.getProjects();
    project.value = autobotStore.projects.find(p => p.name === projectName.value);
  } catch (error) {
    console.error('Error loading project details:', error);
  } finally {
    loading.value = false;
  }
};

// Load project plan
const loadProjectPlan = async () => {
  loadingPlan.value = true;
  try {
    await autobotStore.getPlan();
    plan.value = autobotStore.plan;
  } catch (error) {
    console.error('Error loading project plan:', error);
  } finally {
    loadingPlan.value = false;
  }
};

// Refresh plan
const refreshPlan = async () => {
  await loadProjectPlan();
};

// Execute a task
const executeTask = async () => {
  if (!taskInput.value) return;
  
  executingTask.value = true;
  try {
    await autobotStore.executeTask(taskInput.value);
    taskInput.value = '';
    
    // Navigate to home to see task execution
    router.push('/');
  } catch (error) {
    console.error('Error executing task:', error);
  } finally {
    executingTask.value = false;
  }
};

// Load project into Autobot
const loadProject = async () => {
  try {
    await autobotStore.sendMessage(`/project ${projectName.value}`);
    router.push('/');
  } catch (error) {
    console.error('Error loading project:', error);
  }
};

// Go back to projects list
const goBack = () => {
  router.push('/projects');
};

// Format markdown
const formatMarkdown = (markdown) => {
  return marked(markdown);
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

// Utility function to capitalize first letter
const capitalizeFirstLetter = (string) => {
  if (!string) return '';
  return string.charAt(0).toUpperCase() + string.slice(1);
};
</script>
