import { defineStore } from "pinia";
import axios, { AxiosError } from "axios";
import type { Status, Message, Project, ApiResponse, WebSocketMessage } from "../types";

export const useAutobotStore = defineStore("autobot", {
  state: () => ({
    status: {
      state: "idle" as Status["state"],
      current_task: null as string | null,
      project: "",
      project_id: null as string | null,
      goal: "",
    },
    messages: [] as Message[],
    workLogs: [] as any[],
    projects: [] as Project[],
    plan: "",
    websocket: null as WebSocket | null,
    websocketConnected: false,
    error: null as string | null,
    loading: false,
  }),

  getters: {
    isIdle: (state): boolean => state.status.state === "idle",
    isPlanning: (state): boolean => state.status.state === "planning",
    isExecuting: (state): boolean => state.status.state === "executing",
    isReflecting: (state): boolean => state.status.state === "reflecting",
    isWaitingForUser: (state): boolean => state.status.state === "waiting_for_user",
    currentProject: (state): string => state.status.project,
    currentGoal: (state): string => state.status.goal,
    currentTask: (state): string | null => state.status.current_task,
  },

  actions: {
    // Helper method to handle API requests
    async apiRequest<T>(
      method: 'get' | 'post',
      url: string,
      data?: any
    ): Promise<T> {
      try {
        this.loading = true;
        const response = method === 'get'
          ? await axios.get<T>(url)
          : await axios.post<T>(url, data);
        this.error = null;
        return response.data;
      } catch (error) {
        const err = error as AxiosError;
        this.error = err.message || `Failed to ${method} ${url}`;
        console.error(`Error ${method}ing ${url}:`, error);
        throw error;
      } finally {
        this.loading = false;
      }
    },

    // API methods
    async getStatus(): Promise<void> {
      const status = await this.apiRequest<Status>('get', '/api/status');
      this.status = {
        ...status,
        current_task: status.current_task || null
      };
    },

    async getMessages(limit = 20, offset = 0): Promise<void> {
      this.messages = await this.apiRequest<Message[]>(
        'get',
        `/api/messages?limit=${limit}&offset=${offset}`
      );
    },

    async getWorkLogs(limit = 50): Promise<void> {
      this.workLogs = await this.apiRequest<any[]>(
        'get',
        `/api/work-logs?limit=${limit}`
      );
    },

    async sendMessage(content: string, sender = "user"): Promise<any> {
      return this.apiRequest<any>(
        'post',
        '/api/messages',
        { content, sender }
      );
    },

    async getPlan(): Promise<void> {
      const response = await this.apiRequest<{ plan: string }>('get', '/api/plan');
      this.plan = response.plan;
    },

    async executeTask(task: string): Promise<any> {
      return this.apiRequest<any>('post', '/api/tasks', { task });
    },

    async reflect(): Promise<any> {
      return this.apiRequest<any>('post', '/api/reflect');
    },

    async getProjects(): Promise<void> {
      this.projects = await this.apiRequest<Project[]>('get', '/api/projects');
    },

    async createProject(name: string, goal: string): Promise<any> {
      const response = await this.apiRequest<any>(
        'post',
        '/api/projects',
        { name, goal }
      );
      await this.getProjects();
      return response;
    },

    async loadProject(projectId: string): Promise<any> {
      try {
        this.loading = true;
        console.log(`Loading project with ID: ${projectId}`);

        // First get the project details
        const response = await axios.get(`/api/projects/${encodeURIComponent(projectId)}`);
        const projectData = response.data;

        console.log("Project data loaded:", projectData);

        if (!projectData || !projectData.id) {
          throw new Error(`Invalid project data received for ID: ${projectId}`);
        }

        // Select the project on the server side
        await axios.post(`/api/projects/${encodeURIComponent(projectId)}/select`);

        // Clear existing data first to prevent UI flicker
        this.messages = [];
        this.workLogs = [];
        this.plan = "";

        // Update status with project data
        this.status = {
          ...this.status,
          project: projectData.name || "",
          project_id: projectData.id,
          goal: projectData.goal || "",
        };

        // Get project data in parallel
        await Promise.all([
          this.getMessages(),
          this.getWorkLogs(),
          this.getPlan()
        ]);

        this.error = null;
        return projectData;
      } catch (error) {
        const err = error as AxiosError;
        this.error = err.message || "Failed to load project";
        console.error("Error loading project:", error);

        // Reset state on error
        this.clearCurrentProject();

        throw error;
      } finally {
        this.loading = false;
      }
    },

    clearCurrentProject(): void {
      // Reset project-specific data
      this.status = {
        ...this.status,
        project: "",
        project_id: null,
        goal: "",
        current_task: null,
      };
      this.messages = [];
      this.workLogs = [];
      this.plan = "";
      console.log("Cleared current project state");
    },

    initWebSocket(): void {
      // Close existing connection if any
      this.closeWebSocket();

      // Create new WebSocket connection
      try {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        console.log(`Connecting to WebSocket at ${wsUrl}`);

        this.websocket = new WebSocket(wsUrl);

        this.websocket.onopen = () => {
          console.log("WebSocket connected successfully");
          this.websocketConnected = true;
          this.error = null;

          // Request initial data
          this.sendWebSocketRequest("status_request");
          this.sendWebSocketRequest("work_logs_request", { limit: 50 });
        };

        this.websocket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data) as WebSocketMessage;
            console.log(`Received WebSocket message of type: ${data.type}`);

            switch (data.type) {
              case "message":
                this.messages.push({
                  id: data.id,
                  content: data.content,
                  sender: data.sender,
                  timestamp: new Date().toISOString(),
                });
                break;
              case "status":
                console.log("Received status update:", data.status);
                this.status = data.status;
                break;
              case "project_created":
                console.log("Project created:", data);
                this.getProjects();
                break;
              case "work_logs":
                this.workLogs = data.logs;
                break;
              case "goal_updated":
                console.log("Goal updated:", data.goal);
                this.status.goal = data.goal;
                break;
              case "plan_updated":
                console.log("Plan updated");
                this.plan = data.plan;
                break;
              case "project_updated":
                if (data.project) {
                  console.log("Project updated:", data.project);
                  this.status.project = data.project.name;
                  this.status.project_id = data.project.id;
                  this.status.goal = data.project.goal;

                  // Refresh related data
                  this.getMessages();
                  this.getWorkLogs();
                  this.getPlan();
                }
                break;
              case "project_selected":
                console.log("Project selected:", data);
                // Update status with selected project data
                if (data.id) {
                  this.status.project_id = data.id;
                  this.status.project = data.name || "";
                  this.status.goal = data.goal || "";

                  // Refresh related data
                  this.getMessages();
                  this.getWorkLogs();
                  this.getPlan();
                }
                break;
            }
          } catch (error) {
            console.error("Error processing WebSocket message:", error);
          }
        };

        this.websocket.onclose = (event) => {
          console.log(`WebSocket disconnected with code: ${event.code}, reason: ${event.reason}`);
          this.websocketConnected = false;

          // Only attempt to reconnect if it wasn't a normal closure
          if (event.code !== 1000) {
            console.log("Attempting to reconnect in 5 seconds...");
            // Attempt to reconnect after a delay
            setTimeout(() => this.initWebSocket(), 5000);
          }
        };

        this.websocket.onerror = (error) => {
          console.error("WebSocket error:", error);
          this.error = "WebSocket connection error";
        };
      } catch (error) {
        console.error("Error initializing WebSocket:", error);
        this.error = "Failed to initialize WebSocket connection";

        // Try to reconnect after a delay
        setTimeout(() => this.initWebSocket(), 5000);
      }
    },

    closeWebSocket(): void {
      if (this.websocket) {
        try {
          // Only close if the connection is open or connecting
          if (this.websocket.readyState === WebSocket.OPEN ||
              this.websocket.readyState === WebSocket.CONNECTING) {
            console.log("Closing existing WebSocket connection");
            this.websocket.close(1000, "Normal closure");
          }
        } catch (error) {
          console.error("Error closing WebSocket:", error);
        } finally {
          this.websocket = null;
          this.websocketConnected = false;
        }
      }
    },

    sendWebSocketRequest(type: string, data: Record<string, any> = {}): void {
      this.sendWebSocketData({ type, ...data });
    },

    sendWebSocketData(data: Record<string, any>): void {
      if (!this.websocket) {
        console.error("WebSocket not initialized");
        // Try to initialize WebSocket if it doesn't exist
        this.initWebSocket();
        return;
      }

      if (this.websocket.readyState === WebSocket.CONNECTING) {
        // If still connecting, wait and retry
        console.log("WebSocket still connecting, waiting to send data");
        setTimeout(() => this.sendWebSocketData(data), 500);
        return;
      }

      if (this.websocket.readyState !== WebSocket.OPEN) {
        console.error(`WebSocket not open (state: ${this.websocket.readyState})`);
        // Try to reinitialize WebSocket if it's closed or closing
        if (this.websocket.readyState === WebSocket.CLOSED ||
            this.websocket.readyState === WebSocket.CLOSING) {
          console.log("Reinitializing WebSocket connection");
          this.initWebSocket();
        }
        return;
      }

      try {
        const jsonData = JSON.stringify(data);
        this.websocket.send(jsonData);
        console.log(`Sent WebSocket data: ${jsonData.substring(0, 100)}${jsonData.length > 100 ? '...' : ''}`);
      } catch (error) {
        console.error("Error sending WebSocket data:", error);
      }
    },

    sendWebSocketMessage(content: string, sender = "user"): void {
      this.sendWebSocketData({
        type: "message",
        content,
        sender,
      });
    },

    async pauseAgent(): Promise<ApiResponse<null>> {
      console.log("Pausing agent");
      try {
        await this.sendMessage("/pause");
        // Update local state immediately for better UX
        this.status.state = "waiting_for_user";
        return { success: true };
      } catch (error) {
        const err = error as Error;
        console.error("Error pausing agent:", error);
        return { success: false, error: err.message };
      }
    },

    async resumeAgent(): Promise<ApiResponse<null>> {
      console.log("Resuming agent");
      try {
        await this.sendMessage("/resume");
        // Update local state immediately for better UX
        this.status.state = "idle";
        return { success: true };
      } catch (error) {
        const err = error as Error;
        console.error("Error resuming agent:", error);
        return { success: false, error: err.message };
      }
    },

    async updateGoal(goal: string): Promise<ApiResponse<null>> {
      console.log("Updating goal:", goal);
      try {
        const response = await this.apiRequest<ApiResponse<null>>(
          'post',
          '/api/goal',
          { goal }
        );
        // Update local state immediately for better UX
        this.status.goal = goal;
        return response;
      } catch (error) {
        const err = error as Error;
        console.error("Error updating goal:", error);
        return { success: false, error: err.message };
      }
    },

    async updatePlan(plan: string): Promise<ApiResponse<null>> {
      console.log("Updating plan:", plan);
      try {
        const response = await this.apiRequest<ApiResponse<null>>(
          'post',
          '/api/plan',
          { plan }
        );
        // Update local state immediately for better UX
        this.plan = plan;
        return response;
      } catch (error) {
        const err = error as Error;
        console.error("Error updating plan:", error);
        return { success: false, error: err.message };
      }
    },
  },
});
