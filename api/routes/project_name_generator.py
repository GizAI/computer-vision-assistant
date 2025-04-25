#!/usr/bin/env python3
"""
API route for generating project names.
"""

import logging
import random
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Import LLM interface
from core.llm import LLMInterface

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Pydantic model for request
class ProjectNameRequest(BaseModel):
    message: str

# List of emojis for fallback
EMOJIS = ["🚀", "✨", "🔮", "🛠️", "🧩", "🧠", "🤖", "📊", "🔍", "💡", 
          "🎯", "🎮", "📱", "💻", "🌐", "📈", "🔧", "⚙️", "🔌", "🧪"]

@router.post("/generate-project-name")
async def generate_project_name(request: ProjectNameRequest):
    """
    Generate a project name based on a message.
    
    Args:
        request (ProjectNameRequest): Request with message
        
    Returns:
        dict: Generated project name
    """
    try:
        # Initialize LLM interface
        llm_interface = LLMInterface()
        
        # Create prompt
        prompt = f"""
        Generate a short, catchy project name based on the following message. 
        The name should start with an appropriate emoji and be 2-4 words long.
        
        Message: {request.message}
        
        Project name:
        """
        
        # Generate project name
        response = llm_interface.generate([
            {"role": "system", "content": "You are a helpful assistant that generates creative project names."},
            {"role": "user", "content": prompt}
        ])
        
        # Extract project name
        project_name = response["choices"][0]["message"]["content"].strip()
        
        # Ensure it starts with an emoji
        if not any(c in project_name[:2] for c in EMOJIS):
            # Add a random emoji if none is present
            emoji = random.choice(EMOJIS)
            project_name = f"{emoji} {project_name}"
        
        logger.info(f"Generated project name: {project_name}")
        
        return {"name": project_name}
        
    except Exception as e:
        logger.error(f"Error generating project name: {str(e)}")
        
        # Fallback to a simple name with random emoji
        emoji = random.choice(EMOJIS)
        fallback_name = f"{emoji} Project {random.randint(1000, 9999)}"
        
        return {"name": fallback_name}
