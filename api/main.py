#!/usr/bin/env python3
"""
FastAPI backend for Autobot.
Provides REST endpoints and WebSocket for user interaction.
"""

import os
import logging
import json
import asyncio
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Set up logging
logger = logging.getLogger(__name__)

# Define lifespan context manager
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Mount UI static files
    ui_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui", "dist")
    if os.path.exists(ui_dir):
        app.mount("/", StaticFiles(directory=ui_dir, html=True), name="ui")
        logger.info(f"Mounted UI from {ui_dir}")
    yield
    # Shutdown: Nothing to clean up

# Create FastAPI app with lifespan
app = FastAPI(
    title="Autobot API",
    description="API for Autobot autonomous agent",
    lifespan=lifespan
)

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
        self._lock = asyncio.Lock()  # Add a lock for thread safety

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
            logger.info(f"WebSocket connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Active connections: {len(self.active_connections)}")
        except ValueError:
            # Connection might have been removed already
            logger.warning("Attempted to disconnect a WebSocket that was not in active_connections")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {str(e)}")
            # Remove the connection if it's broken
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        disconnected_websockets = []

        # Make a copy of active_connections to avoid modification during iteration
        async with self._lock:
            connections = self.active_connections.copy()

        for connection in connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {str(e)}")
                disconnected_websockets.append(connection)

        # Clean up disconnected websockets
        for websocket in disconnected_websockets:
            self.disconnect(websocket)

manager = ConnectionManager()

# Global orchestrator instance (set by start_api function or set_orchestrator function)
orchestrator = None

def set_orchestrator(orchestrator_instance):
    """
    Set the global orchestrator instance.

    Args:
        orchestrator_instance: The orchestrator instance to use.
    """
    global orchestrator
    orchestrator = orchestrator_instance

# Pydantic models for API
class Message(BaseModel):
    content: str
    sender: str = "user"

class Project(BaseModel):
    name: str
    goal: str
    id: str = None

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

    if not orchestrator.memory_manager:
        # Return empty list when no project is selected
        return []

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

    if not orchestrator.planning_module:
        # Return empty plan when no project is selected
        return {"plan": ""}

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

# Goal update endpoint
class GoalUpdateRequest(BaseModel):
    goal: str

@api_router.post("/goal")
async def update_goal(goal_request: GoalUpdateRequest, background_tasks: BackgroundTasks):
    """Update the current project's goal."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    if not orchestrator.current_project:
        raise HTTPException(status_code=400, detail="No project is currently selected")

    # Update the goal in the project
    orchestrator.update_goal(goal_request.goal)

    # Broadcast goal update to WebSocket clients
    background_tasks.add_task(
        manager.broadcast,
        json.dumps({
            "type": "goal_updated",
            "goal": goal_request.goal
        })
    )

    return {"status": "success", "message": "Goal updated"}

# Plan update endpoint
class PlanUpdateRequest(BaseModel):
    plan: str

@api_router.post("/plan")
async def update_plan(plan_request: PlanUpdateRequest, background_tasks: BackgroundTasks):
    """Update the current project's plan."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    if not orchestrator.planning_module:
        raise HTTPException(status_code=400, detail="Planning module not initialized")

    # Update the plan
    orchestrator.planning_module.update_plan(plan_request.plan)

    # Broadcast plan update to WebSocket clients
    background_tasks.add_task(
        manager.broadcast,
        json.dumps({
            "type": "plan_updated",
            "plan": plan_request.plan
        })
    )

    return {"status": "success", "message": "Plan updated"}

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

@api_router.post("/projects/{project_id}/select")
async def select_project(project_id: str, background_tasks: BackgroundTasks):
    """Select a project as the current project for the orchestrator."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    # Import from relative path
    from core.project import ProjectManager
    project_manager = ProjectManager()

    # Load the project
    project = project_manager.load_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    # Set the project in the orchestrator
    orchestrator.set_project(project)

    # Broadcast project selection to WebSocket clients
    background_tasks.add_task(
        manager.broadcast,
        json.dumps({
            "type": "project_selected",
            "id": project.id,
            "name": project.name,
            "goal": project.goal
        })
    )

    return {"status": "success", "message": f"Project '{project.name}' selected", "id": project.id}

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
            "id": new_project.id,
            "name": project.name,
            "goal": project.goal
        })
    )

    return new_project.to_dict()

class ProjectUpdateRequest(BaseModel):
    name: str

@api_router.put("/projects/{project_id}")
async def rename_project(project_id: str, update_request: ProjectUpdateRequest, background_tasks: BackgroundTasks):
    """Rename a project."""
    from core.project import ProjectManager
    project_manager = ProjectManager()

    try:
        # First try to get the project to get its original name
        project = project_manager.load_project(project_id)
        old_name = project.name if project else project_id

        # Rename the project
        updated_project = project_manager.rename_project(project_id, update_request.name)

        # Broadcast project update
        background_tasks.add_task(
            manager.broadcast,
            json.dumps({
                "type": "project_renamed",
                "id": updated_project.id,
                "old_name": old_name,
                "new_name": update_request.name
            })
        )

        return updated_project.to_dict()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")
    except ValueError as e: # Handle potential naming conflicts or invalid names
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error renaming project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during project rename")


@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str, background_tasks: BackgroundTasks):
    """Delete a project."""
    from core.project import ProjectManager
    project_manager = ProjectManager()

    try:
        # First try to get the project to get its name
        project = project_manager.load_project(project_id)
        project_name = project.name if project else project_id

        # Delete the project
        project_manager.delete_project(project_id)

        # Broadcast project deletion
        background_tasks.add_task(
            manager.broadcast,
            json.dumps({
                "type": "project_deleted",
                "id": project_id,
                "name": project_name
            })
        )

        return {"message": f"Project '{project_name}' deleted successfully"}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during project deletion")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_id = id(websocket)  # Generate a unique ID for this connection
    logger.info(f"New WebSocket connection request from client {client_id}")

    try:
        await manager.connect(websocket)
        logger.info(f"WebSocket client {client_id} connected successfully")

        # Send initial status to the client
        if orchestrator:
            try:
                await manager.send_personal_message(
                    json.dumps({
                        "type": "status",
                        "status": orchestrator.get_status()
                    }),
                    websocket
                )
            except Exception as e:
                logger.error(f"Error sending initial status to client {client_id}: {str(e)}")

        # Main message loop
        while True:
            try:
                data = await websocket.receive_text()
                logger.debug(f"Received message from client {client_id}: {data[:100]}...")

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
                logger.info(f"WebSocket client {client_id} disconnected")
                break
            except Exception as e:
                logger.error(f"Error processing message from client {client_id}: {str(e)}")
                # If we get an error processing a message, we should still continue the loop
                # unless it's a disconnect error
                if "disconnected" in str(e).lower() or "connection closed" in str(e).lower():
                    logger.info(f"WebSocket client {client_id} connection lost")
                    break
    except Exception as e:
        logger.error(f"Error in WebSocket connection for client {client_id}: {str(e)}")
    finally:
        # Always ensure we disconnect the websocket
        manager.disconnect(websocket)
        logger.info(f"WebSocket client {client_id} cleanup complete")

# Import and include route modules
from api.routes.project_name_generator import router as project_name_router
from api.routes.files import router as files_router

# Include routers
api_router.include_router(project_name_router)
api_router.include_router(files_router)

# Include the API router
app.include_router(api_router)

# Note: UI mounting is now handled in the lifespan context manager

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
