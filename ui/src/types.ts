// Common TypeScript interfaces for the application

export interface Status {
  state: 'idle' | 'planning' | 'executing' | 'reflecting' | 'waiting_for_user';
  current_task: string | null;
  project: string;  // Project name (for backward compatibility)
  project_id: string | null;  // Project ID
  goal: string;
}

export interface Message {
  id?: number;
  content: string;
  sender: string;
  timestamp?: string;
}

export interface Project {
  id: string;
  name: string;
  goal: string;
}

export interface WorkLog {
  id: number;
  content: string;
  timestamp: string;
}

export interface ApiResponse<T = any> {
  success: boolean;
  error?: string;
  data?: T;
}

export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}
