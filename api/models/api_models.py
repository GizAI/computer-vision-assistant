#!/usr/bin/env python3
"""
Pydantic models for Autobot API.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class Message(BaseModel):
    """Model for a chat message."""
    content: str
    sender: str = "user"

class Project(BaseModel):
    """Model for a project."""
    name: str
    goal: str
    id: Optional[str] = None

class TaskRequest(BaseModel):
    """Model for a task execution request."""
    task: str

class StatusResponse(BaseModel):
    """Model for agent status response."""
    state: str
    current_task: Optional[str] = None
    project: str  # Project name (for backward compatibility)
    project_id: Optional[str] = None  # Project ID
    goal: str

class MessageResponse(BaseModel):
    """Model for a message response."""
    id: int
    status: str = "sent"

class PlanResponse(BaseModel):
    """Model for a plan response."""
    plan: str

class ProjectListResponse(BaseModel):
    """Model for a project list response."""
    projects: List[Dict[str, Any]]

class ProjectResponse(BaseModel):
    """Model for a project response."""
    id: str
    name: str
    path: str
    goal: str
    created_at: str
    updated_at: str
    status: str
