#!/usr/bin/env python3
"""
API routes for file system access.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Pydantic models
class FileInfo(BaseModel):
    """Model for file information."""
    name: str
    path: str
    type: str  # "file" or "directory"
    size: Optional[int] = None
    modified: Optional[str] = None

class FileContent(BaseModel):
    """Model for file content."""
    path: str
    content: str

class FileSaveRequest(BaseModel):
    """Model for file save request."""
    path: str
    content: str

@router.get("/files")
async def list_files(path: str = ""):
    """
    List files in a directory.
    
    Args:
        path (str): Path to directory, relative to project workspace
        
    Returns:
        List[FileInfo]: List of files and directories
    """
    try:
        # Get the current project from the orchestrator
        from api.main import orchestrator
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")
            
        project = orchestrator.project
        
        # Construct the full path
        full_path = os.path.join(project.path, path) if path else project.path
        
        # Check if path exists
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail=f"Path not found: {path}")
            
        # List files and directories
        files = []
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            item_rel_path = os.path.join(path, item) if path else item
            
            # Get file stats
            stats = os.stat(item_path)
            
            files.append(FileInfo(
                name=item,
                path=item_rel_path,
                type="directory" if os.path.isdir(item_path) else "file",
                size=stats.st_size if not os.path.isdir(item_path) else None,
                modified=stats.st_mtime
            ))
            
        return files
        
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

@router.get("/files/content")
async def get_file_content(path: str):
    """
    Get file content.
    
    Args:
        path (str): Path to file, relative to project workspace
        
    Returns:
        FileContent: File content
    """
    try:
        # Get the current project from the orchestrator
        from api.main import orchestrator
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")
            
        project = orchestrator.project
        
        # Construct the full path
        full_path = os.path.join(project.path, path)
        
        # Check if file exists
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail=f"File not found: {path}")
            
        # Check if it's a directory
        if os.path.isdir(full_path):
            raise HTTPException(status_code=400, detail=f"Path is a directory: {path}")
            
        # Read file content
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        return FileContent(path=path, content=content)
        
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

@router.post("/files/save")
async def save_file(request: FileSaveRequest):
    """
    Save file content.
    
    Args:
        request (FileSaveRequest): File save request
        
    Returns:
        dict: Success message
    """
    try:
        # Get the current project from the orchestrator
        from api.main import orchestrator
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")
            
        project = orchestrator.project
        
        # Construct the full path
        full_path = os.path.join(project.path, request.path)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Write file content
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(request.content)
            
        return {"message": f"File saved: {request.path}"}
        
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
