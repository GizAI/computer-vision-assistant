<template>
  <div>
    <h1 class="text-2xl font-bold mb-6">Settings</h1>
    
    <div class="p-6 bg-card rounded-lg shadow-sm border mb-6">
      <h2 class="text-xl font-semibold mb-4">API Configuration</h2>
      
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium mb-1" for="api-key">OpenAI API Key</label>
          <input 
            v-model="settings.openaiApiKey" 
            id="api-key" 
            type="password" 
            class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="sk-..."
          />
          <p class="mt-1 text-sm text-muted-foreground">
            Your OpenAI API key is stored locally and never sent to any server except OpenAI.
          </p>
        </div>
        
        <div>
          <label class="block text-sm font-medium mb-1" for="model">LLM Model</label>
          <select 
            v-model="settings.model" 
            id="model" 
            class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="gpt-4.1-mini">GPT-4.1 Mini</option>
            <option value="gpt-4.1">GPT-4.1</option>
            <option value="gpt-4.1-turbo">GPT-4.1 Turbo</option>
            <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
          </select>
        </div>
      </div>
    </div>
    
    <div class="p-6 bg-card rounded-lg shadow-sm border mb-6">
      <h2 class="text-xl font-semibold mb-4">Tool Configuration</h2>
      
      <div class="space-y-4">
        <div class="flex items-center">
          <input 
            v-model="settings.enableCLI" 
            id="enable-cli" 
            type="checkbox" 
            class="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
          />
          <label for="enable-cli" class="ml-2 block text-sm">
            Enable CLI Tool
          </label>
        </div>
        
        <div class="flex items-center">
          <input 
            v-model="settings.enablePython" 
            id="enable-python" 
            type="checkbox" 
            class="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
          />
          <label for="enable-python" class="ml-2 block text-sm">
            Enable Python Executor Tool
          </label>
        </div>
        
        <div class="flex items-center">
          <input 
            v-model="settings.enablePlaywright" 
            id="enable-playwright" 
            type="checkbox" 
            class="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
          />
          <label for="enable-playwright" class="ml-2 block text-sm">
            Enable Playwright Tool
          </label>
        </div>
        
        <div class="flex items-center">
          <input 
            v-model="settings.enableCV" 
            id="enable-cv" 
            type="checkbox" 
            class="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
          />
          <label for="enable-cv" class="ml-2 block text-sm">
            Enable Computer Vision Tool
          </label>
        </div>
        
        <div class="flex items-center">
          <input 
            v-model="settings.enableAugmentCode" 
            id="enable-augment-code" 
            type="checkbox" 
            class="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
          />
          <label for="enable-augment-code" class="ml-2 block text-sm">
            Enable Augment Code Tool
          </label>
        </div>
      </div>
    </div>
    
    <div class="p-6 bg-card rounded-lg shadow-sm border mb-6">
      <h2 class="text-xl font-semibold mb-4">UI Settings</h2>
      
      <div class="space-y-4">
        <div class="flex items-center">
          <input 
            v-model="settings.darkMode" 
            id="dark-mode" 
            type="checkbox" 
            class="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
            @change="toggleDarkMode"
          />
          <label for="dark-mode" class="ml-2 block text-sm">
            Dark Mode
          </label>
        </div>
      </div>
    </div>
    
    <div class="flex justify-end gap-2">
      <button 
        @click="resetSettings" 
        class="px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors"
      >
        Reset
      </button>
      <button 
        @click="saveSettings" 
        class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/80 transition-colors"
      >
        Save
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

// Default settings
const defaultSettings = {
  openaiApiKey: '',
  model: 'gpt-4.1-mini',
  enableCLI: true,
  enablePython: true,
  enablePlaywright: true,
  enableCV: true,
  enableAugmentCode: true,
  darkMode: false
};

const settings = ref({ ...defaultSettings });

// Load settings on mount
onMounted(() => {
  loadSettings();
});

// Load settings from localStorage
const loadSettings = () => {
  try {
    const savedSettings = localStorage.getItem('autobot-settings');
    if (savedSettings) {
      settings.value = { ...defaultSettings, ...JSON.parse(savedSettings) };
    }
    
    // Apply dark mode if enabled
    if (settings.value.darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  } catch (error) {
    console.error('Error loading settings:', error);
  }
};

// Save settings to localStorage
const saveSettings = () => {
  try {
    localStorage.setItem('autobot-settings', JSON.stringify(settings.value));
    alert('Settings saved successfully');
  } catch (error) {
    console.error('Error saving settings:', error);
    alert('Failed to save settings');
  }
};

// Reset settings to defaults
const resetSettings = () => {
  if (confirm('Are you sure you want to reset all settings to defaults?')) {
    settings.value = { ...defaultSettings };
    saveSettings();
  }
};

// Toggle dark mode
const toggleDarkMode = () => {
  if (settings.value.darkMode) {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
};
</script>
