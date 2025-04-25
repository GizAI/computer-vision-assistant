import { defineStore } from "pinia";
import axios, { AxiosError } from "axios";
import type { Status, Message, Project, ApiResponse, WebSocketMessage } from "../types";

export const useAutobotStore = defineStore("autobot", {
  state: () => ({
    status: {
      state: "idle" as Status["state"],
      current_task: null as string | null,
      project: "",
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
        const response = await axios.get(`/api/projects/${encodeURIComponent(projectId)}`);

        // Update status with project data
        this.status = {
          ...this.status,
          project: projectId,
          goal: response.data.goal || "",
        };

        // Get project data in parallel
        await Promise.all([
          this.getMessages(),
          this.getWorkLogs(),
          this.getPlan()
        ]);

        this.error = null;
        return response.data;
      } catch (error) {
        const err = error as AxiosError;
        this.error = err.message || "Failed to load project";
        console.error("Error loading project:", error);
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

        // Request initial data
        this.sendWebSocketRequest("status_request");
        this.sendWebSocketRequest("work_logs_request", { limit: 50 });
      };

      this.websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WebSocketMessage;

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
              this.status = data.status;
              break;
            case "project_created":
              this.getProjects();
              break;
            case "work_logs":
              this.workLogs = data.logs;
              break;
            case "goal_updated":
              this.status.goal = data.goal;
              break;
            case "plan_updated":
              this.plan = data.plan;
              break;
            case "project_updated":
              if (data.project) {
                this.status.project = data.project.name;
                this.status.goal = data.project.goal;

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

      this.websocket.onclose = () => {
        console.log("WebSocket disconnected");
        this.websocketConnected = false;

        // Attempt to reconnect after a delay
        setTimeout(() => this.initWebSocket(), 5000);
      };

      this.websocket.onerror = (error) => {
        console.error("WebSocket error:", error);
        this.error = "WebSocket connection error";
      };
    },

    sendWebSocketRequest(type: string, data: Record<string, any> = {}): void {
      this.sendWebSocketData({ type, ...data });
    },

    sendWebSocketData(data: Record<string, any>): void {
      if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
        console.error("WebSocket not connected");
        return;
      }
      this.websocket.send(JSON.stringify(data));
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
  },
});
