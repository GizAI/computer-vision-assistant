<template>
  <div class="h-full w-full flex flex-col">
    <!-- Dual Panel UI: Chat and Work Logs -->
    <div class="flex flex-col md:flex-row flex-grow overflow-hidden">
      <!-- Left Panel: User Chat Interface -->
      <div class="w-full md:w-1/2 flex flex-col h-full border-r">
        <div class="p-3 bg-card border-b">
          <h2 class="text-lg font-semibold">
            {{ status.project || "New Chat" }}
          </h2>
        </div>

        <div
          ref="chatContainer"
          class="flex-grow overflow-y-auto p-4 bg-background"
        >
          <div
            v-if="messages.length === 0"
            class="flex items-center justify-center h-full text-muted-foreground"
          >
            No messages yet
          </div>
          <div v-else class="space-y-4">
            <div
              v-for="message in messages"
              :key="message.id"
              class="flex gap-3"
              :class="{ 'justify-end': message.sender === 'user' }"
            >
              <div
                v-if="message.sender !== 'user'"
                class="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-bold"
              >
                A
              </div>
              <div
                class="max-w-[80%] p-3 rounded-lg"
                :class="
                  message.sender === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-secondary text-secondary-foreground'
                "
              >
                <div
                  class="whitespace-pre-wrap overflow-x-hidden"
                  v-html="formatMessage(message.content)"
                ></div>
              </div>
              <div
                v-if="message.sender === 'user'"
                class="w-8 h-8 rounded-full bg-muted flex items-center justify-center text-muted-foreground font-bold"
              >
                U
              </div>
            </div>
          </div>
        </div>

        <div class="p-4 border-t bg-card">
          <div class="flex gap-2">
            <input
              v-model="newMessage"
              @keydown.enter="sendMessage"
              type="text"
              placeholder="Type a message..."
              class="flex-1 px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <button
              @click="sendMessage"
              class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/80 transition-colors"
            >
              Send
            </button>
          </div>
        </div>
      </div>

      <!-- Right Panel: AI Work Logs and Workspace -->
      <div class="w-full md:w-1/2 flex flex-col h-full">
        <!-- Modern Header with Status and Controls -->
        <div class="p-3 bg-card border-b">
          <!-- Editable Goal with Status and Controls on the right -->
          <div class="flex justify-between items-center mb-3">
            <!-- Editable Goal - Bold and modern design -->
            <div
              v-if="!editingGoal"
              @click="startEditGoal"
              class="cursor-pointer group flex-grow"
            >
              <div class="font-bold text-base">
                {{ status.goal || "What do you want to accomplish?" }}
                <span
                  class="ml-1 opacity-0 group-hover:opacity-100 transition-opacity text-xs text-primary"
                  >✏️</span
                >
              </div>
            </div>
            <div v-else class="flex-grow">
              <input
                v-model="editedGoal"
                class="w-full px-3 py-2 text-base font-bold border-0 border-b focus:outline-none focus:border-primary transition-colors bg-transparent"
                placeholder="What do you want to accomplish?"
                @keydown.enter="saveGoal"
                @blur="saveGoal"
                ref="goalInput"
                autofocus
              />
            </div>

            <!-- Status Indicator and Control Buttons -->
            <div class="flex items-center gap-2 ml-4">
              <!-- Status Indicator - Moved next to button -->
              <div class="flex items-center">
                <div
                  class="w-2 h-2 rounded-full mr-2"
                  :class="{
                    'bg-green-500': status.state === 'executing',
                    'bg-yellow-500': status.state === 'waiting_for_user',
                    'bg-blue-500': status.state === 'planning',
                    'bg-purple-500': status.state === 'reflecting',
                    'bg-gray-400': status.state === 'idle',
                  }"
                ></div>
                <span class="text-sm font-medium">{{
                  capitalizeFirstLetter(status.state)
                }}</span>
              </div>

              <!-- Control Buttons -->
              <button
                v-if="status.state === 'waiting_for_user'"
                @click="resumeAgent"
                class="px-3 py-1 bg-primary text-primary-foreground rounded-md hover:bg-primary/80 transition-colors text-sm"
                :disabled="resumingAgent"
              >
                {{ resumingAgent ? "Resuming..." : "Resume" }}
              </button>
              <button
                v-else
                @click="pauseAgent"
                class="px-3 py-1 bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/80 transition-colors text-sm"
                :disabled="pausingAgent"
              >
                {{ pausingAgent ? "Pausing..." : "Pause" }}
              </button>
            </div>
          </div>
          <!-- Collapsible Plan - Modern toggle design with task name -->
          <div
            @click="togglePlan"
            class="flex items-center justify-between py-2 px-3 rounded-md hover:bg-muted cursor-pointer transition-colors"
          >
            <div class="flex items-center gap-2">
              <ClipboardList size="16" />
              <span class="text-sm font-medium">{{
                status.current_task || "Plan"
              }}</span>
            </div>
            <ChevronDown
              size="16"
              :class="{ 'transform rotate-180 transition-transform': showPlan }"
              class="transition-transform"
            />
          </div>

          <!-- Plan Content - Expanded view -->
          <div
            v-if="showPlan"
            class="mt-2 overflow-hidden transition-all duration-300"
          >
            <div v-if="!editingPlan" class="relative">
              <div
                class="bg-muted p-3 rounded text-sm max-h-60 overflow-y-auto whitespace-pre-wrap"
              >
                {{
                  plan ||
                  "No plan available yet. The AI will create one based on your goal."
                }}
              </div>
              <button
                @click="startEditPlan"
                class="absolute top-2 right-2 p-1 rounded-md bg-background/80 hover:bg-background text-muted-foreground hover:text-foreground transition-colors"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path
                    d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"
                  ></path>
                  <path
                    d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"
                  ></path>
                </svg>
              </button>
            </div>
            <div v-else class="mt-1">
              <textarea
                v-model="editedPlan"
                class="w-full p-3 text-sm border rounded-md focus:outline-none focus:ring-1 focus:ring-primary h-60 font-mono"
                ref="planTextarea"
                @blur="savePlan"
              ></textarea>
              <div class="flex justify-end mt-2">
                <button
                  @click="savePlan"
                  class="px-3 py-1 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/80 transition-colors"
                >
                  Save
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Work Logs -->
        <div
          ref="workLogsContainer"
          class="flex-grow overflow-y-auto p-4 bg-background"
        >
          <div
            v-if="workLogs.length === 0"
            class="flex items-center justify-center h-full text-muted-foreground"
          >
            No work logs yet
          </div>
          <div v-else class="space-y-4">
            <div
              v-for="log in workLogs"
              :key="log.id"
              class="p-3 rounded-lg bg-muted"
            >
              <div class="text-xs text-muted-foreground mb-1">
                {{ formatTimestamp(log.timestamp) }}
              </div>
              <div
                class="whitespace-pre-wrap overflow-x-hidden"
                v-html="formatMessage(log.content)"
              ></div>
            </div>
          </div>
        </div>

        <!-- File Explorer Component with consistent styling -->
        <div class="border-t p-3">
          <FileExplorer />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from "vue";
import { useAutobotStore } from "../stores/autobot";
import { marked } from "marked";
import FileExplorer from "../components/FileExplorer.vue";
import axios from "axios";
import { ChevronDown, ClipboardList } from "lucide-vue-next";
import { useRoute, useRouter } from "vue-router";

const autobotStore = useAutobotStore();
const route = useRoute();
const router = useRouter();
const newMessage = ref("");
const chatContainer = ref(null);
const workLogsContainer = ref(null);
const goalInput = ref(null);
const planTextarea = ref(null);

// Editable goal state
const editingGoal = ref(false);
const editedGoal = ref("");

// Collapsible and editable plan state
const showPlan = ref(false);
const editingPlan = ref(false);
const editedPlan = ref("");
const plan = ref("");

// Project creation state
const creatingProject = ref(false);

const status = computed(() => autobotStore.status);
const messages = computed(() => autobotStore.messages);
const workLogs = computed(() => autobotStore.workLogs);

// Scroll to bottom of chat container
const scrollToBottom = async (container) => {
  await nextTick();
  if (container && container.value) {
    container.value.scrollTop = container.value.scrollHeight;
  }
};

// Fetch initial data
onMounted(async () => {
  // Check if we have a project ID in the route
  const projectId = route.params.id;

  if (projectId) {
    // Load the specific project
    try {
      await autobotStore.loadProject(decodeURIComponent(projectId as string));
    } catch (error) {
      console.error("Error loading project from route:", error);
      // If project loading fails, redirect to home
      router.push("/");
    }
  } else {
    // Just get the status if no project is specified
    await autobotStore.getStatus();
    await autobotStore.getMessages();
    await autobotStore.getWorkLogs();

    // Get the current plan
    try {
      await autobotStore.getPlan();
      plan.value = autobotStore.plan;
    } catch (error) {
      console.error("Error fetching plan:", error);
    }
  }

  // Scroll to bottom of chat and work logs initially
  scrollToBottom(chatContainer);
  scrollToBottom(workLogsContainer);
});

// Watch for new messages and scroll to bottom
watch(
  () => messages.value.length,
  () => {
    scrollToBottom(chatContainer);
  }
);

// Watch for new work logs and scroll to bottom
watch(
  () => workLogs.value.length,
  () => {
    scrollToBottom(workLogsContainer);
  }
);

// Watch for status changes
watch(
  () => autobotStore.status,
  (newStatus) => {
    console.log("Status updated:", newStatus);
  }
);

// Watch for plan changes
watch(
  () => autobotStore.plan,
  (newPlan) => {
    if (newPlan && !editingPlan.value) {
      plan.value = newPlan;
    }
  }
);

// Watch for route changes to handle navigation between projects
watch(
  () => route.params.id,
  async (newProjectId) => {
    if (newProjectId) {
      // Load the specific project when route changes
      try {
        await autobotStore.loadProject(
          decodeURIComponent(newProjectId as string)
        );
      } catch (error) {
        console.error("Error loading project from route change:", error);
        router.push("/");
      }
    } else {
      // Clear project when navigating to home
      autobotStore.clearCurrentProject();
    }
  }
);

// Generate a project name with emoji using AI
const generateProjectName = async (message) => {
  const response = await axios.post("/api/generate-project-name", {
    message: message,
  });

  return response.data.name;
};

// Create a new project based on the first message
const createNewProject = async (message) => {
  if (creatingProject.value) return;

  creatingProject.value = true;
  try {
    // Generate a project name based on the message content
    const projectName = await generateProjectName(message);

    // Create the project with the message as the initial goal
    const newProject = await autobotStore.createProject(projectName, message);

    // Update the URL to the project-specific URL
    router.push(`/project/${encodeURIComponent(projectName)}`);

    // Send the message to the new project
    await autobotStore.sendMessage(message);

    console.log(`Created and loaded new project: ${projectName}`);
  } catch (error) {
    console.error("Error creating project:", error);
  } finally {
    creatingProject.value = false;
  }
};

// Send a message
const sendMessage = async () => {
  if (!newMessage.value.trim()) return;

  const messageContent = newMessage.value;
  newMessage.value = ""; // Clear input immediately for better UX

  try {
    // If no project is selected, create a new one first
    if (!status.value.project) {
      // Create a new project with the message as the goal
      // This will also send the message
      await createNewProject(messageContent);
    } else {
      // Otherwise, just send the message to the existing project
      await autobotStore.sendMessage(messageContent);
    }

    // Scroll to bottom after sending
    scrollToBottom(chatContainer);
  } catch (error) {
    console.error("Error sending message:", error);
  }
};

// Execute a command
const executeCommand = async (command) => {
  try {
    await autobotStore.sendMessage(command);
  } catch (error) {
    console.error("Error executing command:", error);
  }
};

// State for pause/resume buttons
const pausingAgent = ref(false);
const resumingAgent = ref(false);

// Pause the agent
const pauseAgent = async () => {
  if (pausingAgent.value) return;

  pausingAgent.value = true;
  try {
    await autobotStore.pauseAgent();
  } catch (error) {
    console.error("Error pausing agent:", error);
  } finally {
    pausingAgent.value = false;
  }
};

// Resume the agent
const resumeAgent = async () => {
  if (resumingAgent.value) return;

  resumingAgent.value = true;
  try {
    await autobotStore.resumeAgent();
  } catch (error) {
    console.error("Error resuming agent:", error);
  } finally {
    resumingAgent.value = false;
  }
};

// This function is no longer needed as we're using WebSockets for real-time updates

// Goal editing functions
const startEditGoal = () => {
  editedGoal.value = status.value.goal || "";
  editingGoal.value = true;
  nextTick(() => {
    if (goalInput.value) {
      goalInput.value.focus();
    }
  });
};

const saveGoal = async () => {
  try {
    if (editedGoal.value.trim() !== "") {
      // Send a command to update the goal
      await executeCommand(`/goal ${editedGoal.value}`);
    }
    editingGoal.value = false;
  } catch (error) {
    console.error("Error saving goal:", error);
  }
};

// Plan functions
const togglePlan = async () => {
  showPlan.value = !showPlan.value;

  // If opening the plan and we don't have it yet, fetch it
  if (showPlan.value && !plan.value) {
    try {
      await autobotStore.getPlan();
      plan.value = autobotStore.plan;
    } catch (error) {
      console.error("Error fetching plan:", error);
    }
  }
};

const startEditPlan = () => {
  editedPlan.value = plan.value || "";
  editingPlan.value = true;
  nextTick(() => {
    if (planTextarea.value) {
      planTextarea.value.focus();
    }
  });
};

const savePlan = async () => {
  try {
    if (editedPlan.value.trim() !== "") {
      // Send a command to update the plan
      // This is a placeholder - you'll need to implement the actual API endpoint
      await executeCommand(`/update_plan ${editedPlan.value}`);
      plan.value = editedPlan.value;
    }
    editingPlan.value = false;
  } catch (error) {
    console.error("Error saving plan:", error);
  }
};

// Format message with markdown
const formatMessage = (content) => {
  return marked(content);
};

// Format timestamp
const formatTimestamp = (timestamp) => {
  if (!timestamp) return "";

  // If it's a number (Unix timestamp), convert to Date
  const date =
    typeof timestamp === "number"
      ? new Date(timestamp * 1000)
      : new Date(timestamp);

  return date.toLocaleString();
};

// Utility function to capitalize first letter
const capitalizeFirstLetter = (string) => {
  if (!string) return "";
  return string.charAt(0).toUpperCase() + string.slice(1);
};
</script>
