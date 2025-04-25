<template>
  <div class="h-full flex flex-col">
    <!-- Header with toggle - Consistent with Plan section -->
    <div
      @click="toggleExplorer"
      class="flex items-center justify-between py-2 px-3 rounded-md hover:bg-muted cursor-pointer transition-colors"
    >
      <div class="flex items-center gap-2">
        <Folder size="16" />
        <span class="text-sm font-medium">Workspace</span>
      </div>
      <ChevronDown
        size="16"
        :class="{ 'transform rotate-180 transition-transform': showExplorer }"
        class="transition-transform"
      />
    </div>

    <!-- File Explorer Content -->
    <div
      v-if="showExplorer"
      class="flex-grow overflow-auto transition-all duration-300"
    >
      <div v-if="loading" class="flex justify-center items-center p-4">
        <div
          class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"
        ></div>
      </div>

      <div v-else-if="error" class="p-4 text-sm text-destructive">
        {{ error }}
      </div>

      <div
        v-else-if="files.length === 0"
        class="p-4 text-sm text-muted-foreground text-center"
      >
        No files found in workspace
      </div>

      <div v-else class="p-2">
        <div class="text-xs text-muted-foreground mb-2">
          Current path: {{ currentPath || "/" }}
        </div>

        <!-- Navigation buttons -->
        <div class="flex gap-2 mb-2">
          <button
            @click="navigateUp"
            class="px-2 py-1 text-xs bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors"
            :disabled="!currentPath"
          >
            Up
          </button>
          <button
            @click="refreshFiles"
            class="px-2 py-1 text-xs bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors"
          >
            Refresh
          </button>
        </div>

        <!-- File list -->
        <div class="space-y-1">
          <div
            v-for="file in files"
            :key="file.path"
            @click="handleFileClick(file)"
            class="flex items-center gap-2 p-2 rounded-md hover:bg-muted cursor-pointer text-sm"
          >
            <!-- Folder icon -->
            <svg
              v-if="file.type === 'directory'"
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              class="text-yellow-500"
            >
              <path
                d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"
              ></path>
            </svg>

            <!-- File icon -->
            <svg
              v-else
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              class="text-blue-500"
            >
              <path
                d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"
              ></path>
              <polyline points="14 2 14 8 20 8"></polyline>
            </svg>

            <span>{{ file.name }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- File Viewer Modal -->
    <div
      v-if="showFileViewer"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="closeFileViewer"
    >
      <div
        class="bg-card p-4 rounded-lg shadow-lg w-full max-w-3xl max-h-[80vh] flex flex-col"
      >
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-medium">{{ selectedFile.name }}</h3>
          <div class="flex gap-2">
            <button
              v-if="!editingFile"
              @click="startEditFile"
              class="px-3 py-1 text-sm bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors"
            >
              Edit
            </button>
            <button
              @click="closeFileViewer"
              class="px-3 py-1 text-sm bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/80 transition-colors"
            >
              Close
            </button>
          </div>
        </div>

        <div
          v-if="fileLoading"
          class="flex-grow flex justify-center items-center"
        >
          <div
            class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"
          ></div>
        </div>

        <div v-else-if="fileError" class="flex-grow p-4 text-destructive">
          {{ fileError }}
        </div>

        <div v-else class="flex-grow flex flex-col">
          <div v-if="!editingFile" class="flex-grow overflow-auto">
            <pre
              class="text-sm p-4 bg-muted rounded-md overflow-x-auto whitespace-pre-wrap"
              >{{ fileContent }}</pre
            >
          </div>

          <div v-else class="flex-grow flex flex-col">
            <textarea
              v-model="editedFileContent"
              class="flex-grow p-4 text-sm font-mono border rounded-md focus:outline-none focus:ring-1 focus:ring-primary"
            ></textarea>

            <div class="flex justify-end gap-2 mt-4">
              <button
                @click="cancelEditFile"
                class="px-3 py-1 text-sm bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors"
              >
                Cancel
              </button>
              <button
                @click="saveFile"
                class="px-3 py-1 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/80 transition-colors"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";
import { ChevronDown, Folder } from "lucide-vue-next";

// File explorer state
const showExplorer = ref(false);
const files = ref([]);
const currentPath = ref("");
const loading = ref(false);
const error = ref(null);

// File viewer state
const showFileViewer = ref(false);
const selectedFile = ref(null);
const fileContent = ref("");
const editedFileContent = ref("");
const editingFile = ref(false);
const fileLoading = ref(false);
const fileError = ref(null);

// Toggle file explorer
const toggleExplorer = () => {
  showExplorer.value = !showExplorer.value;

  // Load files if opening and no files loaded yet
  if (showExplorer.value && files.value.length === 0) {
    loadFiles();
  }
};

// Load files from the current path
const loadFiles = async () => {
  loading.value = true;
  error.value = null;

  try {
    const response = await axios.get(
      `/api/files?path=${encodeURIComponent(currentPath.value)}`
    );
    files.value = response.data;
  } catch (err) {
    console.error("Error loading files:", err);
    error.value = "Failed to load files. Please try again.";
  } finally {
    loading.value = false;
  }
};

// Refresh files
const refreshFiles = () => {
  loadFiles();
};

// Navigate up one directory
const navigateUp = () => {
  if (!currentPath.value) return;

  const parts = currentPath.value.split("/");
  parts.pop();
  currentPath.value = parts.join("/");
  loadFiles();
};

// Handle file click
const handleFileClick = (file) => {
  if (file.type === "directory") {
    // Navigate into directory
    currentPath.value = currentPath.value
      ? `${currentPath.value}/${file.name}`
      : file.name;
    loadFiles();
  } else {
    // Open file viewer
    selectedFile.value = file;
    openFileViewer();
  }
};

// Open file viewer
const openFileViewer = async () => {
  showFileViewer.value = true;
  fileLoading.value = true;
  fileError.value = null;

  try {
    const filePath = currentPath.value
      ? `${currentPath.value}/${selectedFile.value.name}`
      : selectedFile.value.name;

    const response = await axios.get(
      `/api/files/content?path=${encodeURIComponent(filePath)}`
    );
    fileContent.value = response.data.content;
  } catch (err) {
    console.error("Error loading file content:", err);
    fileError.value = "Failed to load file content. Please try again.";
  } finally {
    fileLoading.value = false;
  }
};

// Close file viewer
const closeFileViewer = () => {
  showFileViewer.value = false;
  selectedFile.value = null;
  fileContent.value = "";
  editedFileContent.value = "";
  editingFile.value = false;
  fileError.value = null;
};

// Start editing file
const startEditFile = () => {
  editedFileContent.value = fileContent.value;
  editingFile.value = true;
};

// Cancel editing file
const cancelEditFile = () => {
  editingFile.value = false;
  editedFileContent.value = "";
};

// Save file
const saveFile = async () => {
  fileLoading.value = true;
  fileError.value = null;

  try {
    const filePath = currentPath.value
      ? `${currentPath.value}/${selectedFile.value.name}`
      : selectedFile.value.name;

    await axios.post("/api/files/save", {
      path: filePath,
      content: editedFileContent.value,
    });

    fileContent.value = editedFileContent.value;
    editingFile.value = false;
  } catch (err) {
    console.error("Error saving file:", err);
    fileError.value = "Failed to save file. Please try again.";
  } finally {
    fileLoading.value = false;
  }
};

// Load files on mount
onMounted(() => {
  if (showExplorer.value) {
    loadFiles();
  }
});
</script>
