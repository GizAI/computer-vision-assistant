#!/usr/bin/env python3
"""
API route for generating project names.
"""

import logging
from fastapi import APIRouter
from pydantic import BaseModel

from core.llm import LLMInterface

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic model for request
class ProjectNameRequest(BaseModel):
    message: str
@router.post("/generate-project-name")
async def generate_project_name(request: ProjectNameRequest):
    """
    Generate a project name with emoji based on a message.
    
    Args:
        request (ProjectNameRequest): Request with message
        
    Returns:
        dict: Generated project name with emoji
    """
    try:
        llm_interface = LLMInterface()
        prompt = f"""
        Generate a short, catchy project name (2-4 words) starting with ONE relevant emoji.
        Message: {request.message}
        Project name:
        """
        
        response = llm_interface.generate([
            {"role": "system", "content": "Generate project names starting with one emoji."},
            {"role": "user", "content": prompt}
        ])
        
        project_name = response["choices"][0]["message"]["content"].strip()
        logger.info(f"Generated project name: {project_name}")
        return {"name": project_name}
        
    except Exception as e:
        logger.error(f"Error generating project name: {str(e)}")
        return {"name": "🚀 New Project"}
