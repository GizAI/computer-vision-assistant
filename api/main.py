#!/usr/bin/env python3
"""
FastAPI backend for Autobot.
Provides REST endpoints and WebSocket for user interaction.
"""

import os
import logging
import json
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, BackgroundTasks, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Set up logging
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Autobot API", description="API for Autobot autonomous agent")

# Create API router for /api prefix
api_router = APIRouter(prefix="/api")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Global orchestrator instance (set by start_api function)
orchestrator = None

# Pydantic models for API
class Message(BaseModel):
    content: str
    sender: str = "user"

class Project(BaseModel):
    name: str
    goal: str

class TaskRequest(BaseModel):
    task: str

# Root route
@app.get("/")
async def root():
    return {"message": "Autobot API is running"}

# API routes with /api prefix
@api_router.get("/status")
async def get_status():
    if not orchestrator:
        # Return a default status when orchestrator is not initialized
        return {
            "state": "initializing",
            "current_task": None,
            "project": "default_project",
            "goal": "Assist the user with their tasks",
            "message": "Server is starting. Please wait a moment for the orchestrator to initialize."
        }

    return orchestrator.get_status()

@api_router.post("/messages")
async def send_message(message: Message, background_tasks: BackgroundTasks):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    # Send message to orchestrator
    message_id = orchestrator.send_message(message.content, message.sender)

    # Broadcast message to WebSocket clients
    background_tasks.add_task(
        manager.broadcast,
        json.dumps({
            "type": "message",
            "id": message_id,
            "content": message.content,
            "sender": message.sender
        })
    )

    return {"id": message_id, "status": "sent"}

@api_router.get("/messages")
async def get_messages(limit: int = 10, offset: int = 0):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    return orchestrator.memory_manager.get_messages(limit, offset)

@api_router.get("/work-logs")
async def get_work_logs(limit: int = 50):
    """Get the work logs from the task AI."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    return orchestrator.get_work_logs(limit)

@api_router.get("/plan")
async def get_plan():
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    plan = orchestrator.planning_module.get_current_plan()

    return {"plan": plan}

@api_router.post("/tasks")
async def execute_task(task_request: TaskRequest, background_tasks: BackgroundTasks):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    # Send task command to orchestrator
    message_id = orchestrator.send_message(f"/task {task_request.task}", "user")

    # Broadcast message to WebSocket clients
    background_tasks.add_task(
        manager.broadcast,
        json.dumps({
            "type": "task",
            "id": message_id,
            "task": task_request.task
        })
    )

    return {"id": message_id, "status": "executing"}

@api_router.post("/reflect")
async def reflect(background_tasks: BackgroundTasks):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    # Send reflect command to orchestrator
    message_id = orchestrator.send_message("/reflect", "user")

    # Broadcast message to WebSocket clients
    background_tasks.add_task(
        manager.broadcast,
        json.dumps({
            "type": "reflect",
            "id": message_id
        })
    )

    return {"id": message_id, "status": "reflecting"}

@api_router.get("/projects")
async def list_projects():
    # Import from relative path
    from core.project import ProjectManager
    project_manager = ProjectManager()

    return project_manager.list_projects()

@api_router.get("/projects/{project_id}")
async def get_project(project_id: str):
    """Get a specific project by ID."""
    # Import from relative path
    from core.project import ProjectManager
    project_manager = ProjectManager()

    # Load the project
    project = project_manager.load_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    return project.to_dict()

@api_router.post("/projects")
async def create_project(project: Project, background_tasks: BackgroundTasks):
    # Import from relative path
    from core.project import ProjectManager
    project_manager = ProjectManager()

    new_project = project_manager.create_project(project.name, project.goal)

    # Broadcast project creation to WebSocket clients
    background_tasks.add_task(
        manager.broadcast,
        json.dumps({
            "type": "project_created",
            "name": project.name,
            "goal": project.goal
        })
    )

    return new_project.to_dict()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()

            # Parse message
            try:
                message_data = json.loads(data)

                if "type" in message_data:
                    if message_data["type"] == "message" and "content" in message_data:
                        # Send message to orchestrator
                        if orchestrator:
                            message_id = orchestrator.send_message(
                                message_data["content"],
                                message_data.get("sender", "user")
                            )

                            # Broadcast message to all clients
                            await manager.broadcast(
                                json.dumps({
                                    "type": "message",
                                    "id": message_id,
                                    "content": message_data["content"],
                                    "sender": message_data.get("sender", "user")
                                })
                            )

                    elif message_data["type"] == "status_request":
                        # Send status to client
                        if orchestrator:
                            await manager.send_personal_message(
                                json.dumps({
                                    "type": "status",
                                    "status": orchestrator.get_status()
                                }),
                                websocket
                            )

                    elif message_data["type"] == "work_logs_request":
                        # Send work logs to client
                        if orchestrator:
                            limit = message_data.get("limit", 50)
                            await manager.send_personal_message(
                                json.dumps({
                                    "type": "work_logs",
                                    "logs": orchestrator.get_work_logs(limit)
                                }),
                                websocket
                            )

            except json.JSONDecodeError:
                # If not JSON, treat as plain message
                if orchestrator:
                    message_id = orchestrator.send_message(data, "user")

                    # Broadcast message to all clients
                    await manager.broadcast(
                        json.dumps({
                            "type": "message",
                            "id": message_id,
                            "content": data,
                            "sender": "user"
                        })
                    )

    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Import and include route modules
from api.routes.project_name_generator import router as project_name_router
from api.routes.files import router as files_router

# Include routers
api_router.include_router(project_name_router)
api_router.include_router(files_router)

# Include the API router
app.include_router(api_router)

# Mount static files for frontend
@app.on_event("startup")
async def startup_event():
    # Check if UI directory exists
    ui_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui", "dist")
    if os.path.exists(ui_dir):
        app.mount("/", StaticFiles(directory=ui_dir, html=True), name="ui")
        logger.info(f"Mounted UI from {ui_dir}")

def start_api(port: int = 8000, debug: bool = False, orchestrator_instance = None):
    """
    Start the FastAPI server.

    Args:
        port (int, optional): Port to run on. Defaults to 8000.
        debug (bool, optional): Whether to run in debug mode. Defaults to False.
        orchestrator_instance (optional): Orchestrator instance. Defaults to None.
    """
    global orchestrator
    orchestrator = orchestrator_instance

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="debug" if debug else "info")

if __name__ == "__main__":
    start_api(debug=True)
