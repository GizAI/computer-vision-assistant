import { defineStore } from "pinia";
import axios from "axios";

export const useAutobotStore = defineStore("autobot", {
  state: () => ({
    status: {
      state: "idle",
      current_task: null,
      project: "",
      goal: "",
    },
    messages: [],
    workLogs: [],
    projects: [],
    plan: "",
    websocket: null,
    websocketConnected: false,
    error: null,
    loading: false,
  }),

  getters: {
    isIdle: (state) => state.status.state === "idle",
    isPlanning: (state) => state.status.state === "planning",
    isExecuting: (state) => state.status.state === "executing",
    isReflecting: (state) => state.status.state === "reflecting",
    isWaitingForUser: (state) => state.status.state === "waiting_for_user",
    currentProject: (state) => state.status.project,
    currentGoal: (state) => state.status.goal,
    currentTask: (state) => state.status.current_task,
  },

  actions: {
    async getStatus() {
      try {
        this.loading = true;
        const response = await axios.get("/api/status");
        this.status = response.data;
        this.error = null;
      } catch (error) {
        this.error = error.message || "Failed to get status";
        console.error("Error getting status:", error);
      } finally {
        this.loading = false;
      }
    },

    async getMessages(limit = 20, offset = 0) {
      try {
        this.loading = true;
        const response = await axios.get(
          `/api/messages?limit=${limit}&offset=${offset}`
        );
        this.messages = response.data;
        this.error = null;
      } catch (error) {
        this.error = error.message || "Failed to get messages";
        console.error("Error getting messages:", error);
      } finally {
        this.loading = false;
      }
    },

    async getWorkLogs(limit = 50) {
      try {
        this.loading = true;
        const response = await axios.get(`/api/work-logs?limit=${limit}`);
        this.workLogs = response.data;
        this.error = null;
      } catch (error) {
        this.error = error.message || "Failed to get work logs";
        console.error("Error getting work logs:", error);
      } finally {
        this.loading = false;
      }
    },

    async sendMessage(content, sender = "user") {
      try {
        this.loading = true;
        const response = await axios.post("/api/messages", { content, sender });
        this.error = null;
        return response.data;
      } catch (error) {
        this.error = error.message || "Failed to send message";
        console.error("Error sending message:", error);
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async getPlan() {
      try {
        this.loading = true;
        const response = await axios.get("/api/plan");
        this.plan = response.data.plan;
        this.error = null;
      } catch (error) {
        this.error = error.message || "Failed to get plan";
        console.error("Error getting plan:", error);
      } finally {
        this.loading = false;
      }
    },

    async executeTask(task) {
      try {
        this.loading = true;
        const response = await axios.post("/api/tasks", { task });
        this.error = null;
        return response.data;
      } catch (error) {
        this.error = error.message || "Failed to execute task";
        console.error("Error executing task:", error);
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async reflect() {
      try {
        this.loading = true;
        const response = await axios.post("/api/reflect");
        this.error = null;
        return response.data;
      } catch (error) {
        this.error = error.message || "Failed to reflect";
        console.error("Error reflecting:", error);
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async getProjects() {
      try {
        this.loading = true;
        const response = await axios.get("/api/projects");
        this.projects = response.data;
        this.error = null;
      } catch (error) {
        this.error = error.message || "Failed to get projects";
        console.error("Error getting projects:", error);
      } finally {
        this.loading = false;
      }
    },

    async createProject(name, goal) {
      try {
        this.loading = true;
        const response = await axios.post("/api/projects", { name, goal });
        this.error = null;
        await this.getProjects();
        return response.data;
      } catch (error) {
        this.error = error.message || "Failed to create project";
        console.error("Error creating project:", error);
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async loadProject(projectId) {
      try {
        this.loading = true;
        const response = await axios.get(
          `/api/projects/${encodeURIComponent(projectId)}`
        );

        // Update status with project data
        this.status = {
          ...this.status,
          project: projectId, // Store the project ID
          goal: response.data.goal || "",
        };

        // Get messages for this project
        await this.getMessages();

        // Get work logs for this project
        await this.getWorkLogs();

        // Get plan for this project
        await this.getPlan();

        this.error = null;
        return response.data;
      } catch (error) {
        this.error = error.message || "Failed to load project";
        console.error("Error loading project:", error);
        throw error;
      } finally {
        this.loading = false;
      }
    },

    // Clear the current project state without creating a new project
    clearCurrentProject() {
      // Keep the current state but clear project-specific data
      this.status = {
        ...this.status,
        project: "",
        goal: "",
        current_task: null,
      };

      // Clear messages, work logs, and plan
      this.messages = [];
      this.workLogs = [];
      this.plan = "";

      console.log("Cleared current project state");
    },

    initWebSocket() {
      // Close existing connection if any
      if (this.websocket) {
        this.websocket.close();
      }

      // Create new WebSocket connection
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsUrl = `${protocol}//${window.location.host}/ws`;

      this.websocket = new WebSocket(wsUrl);

      this.websocket.onopen = () => {
        console.log("WebSocket connected");
        this.websocketConnected = true;

        // Request initial status
        this.websocket.send(JSON.stringify({ type: "status_request" }));

        // Request initial work logs
        this.websocket.send(
          JSON.stringify({ type: "work_logs_request", limit: 50 })
        );
      };

      this.websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === "message") {
            // Add message to list
            const message = {
              id: data.id,
              content: data.content,
              sender: data.sender,
              timestamp: new Date().toISOString(),
            };

            this.messages.push(message);
          } else if (data.type === "status") {
            // Update status
            this.status = data.status;
          } else if (data.type === "project_created") {
            // Refresh projects list
            this.getProjects();
          } else if (data.type === "work_logs") {
            // Update work logs
            this.workLogs = data.logs;
          } else if (data.type === "goal_updated") {
            // Update goal
            this.status.goal = data.goal;
          } else if (data.type === "plan_updated") {
            // Update plan
            this.plan = data.plan;
          } else if (data.type === "project_updated") {
            // Update project data
            if (data.project) {
              this.status.project = data.project.name;
              this.status.goal = data.project.goal;

              // Refresh related data
              this.getMessages();
              this.getWorkLogs();
              this.getPlan();
            }
          }
        } catch (error) {
          console.error("Error processing WebSocket message:", error);
        }
      };

      this.websocket.onclose = () => {
        console.log("WebSocket disconnected");
        this.websocketConnected = false;

        // Attempt to reconnect after a delay
        setTimeout(() => {
          this.initWebSocket();
        }, 5000);
      };

      this.websocket.onerror = (error) => {
        console.error("WebSocket error:", error);
        this.error = "WebSocket connection error";
      };
    },

    sendWebSocketMessage(content, sender = "user") {
      if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
        console.error("WebSocket not connected");
        return;
      }

      this.websocket.send(
        JSON.stringify({
          type: "message",
          content,
          sender,
        })
      );
    },

    // Pause the agent
    async pauseAgent() {
      console.log("Pausing agent");
      try {
        // Send the pause command
        await this.sendMessage("/pause");

        // Update local state immediately for better UX
        this.status.state = "waiting_for_user";

        return { success: true };
      } catch (error) {
        console.error("Error pausing agent:", error);
        return { success: false, error: error.message };
      }
    },

    // Resume the agent
    async resumeAgent() {
      console.log("Resuming agent");
      try {
        // Send the resume command
        await this.sendMessage("/resume");

        // Update local state immediately for better UX
        this.status.state = "idle";

        return { success: true };
      } catch (error) {
        console.error("Error resuming agent:", error);
        return { success: false, error: error.message };
      }
    },
  },
});
