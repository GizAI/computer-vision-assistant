#!/usr/bin/env python3
"""
Base Tool class for Autobot.
Defines the interface for all tools.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

# Set up logging
logger = logging.getLogger(__name__)

class Tool(ABC):
    """Abstract base class for all tools."""
    
    def __init__(self, name: str, description: str):
        """
        Initialize the tool.
        
        Args:
            name (str): Tool name
            description (str): Tool description
        """
        self.name = name
        self.description = description
        self.status = "idle"
        self.last_result = None
        
        logger.info(f"Initialized tool: {name}")
    
    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with the given parameters.
        
        Args:
            params (Dict[str, Any]): Tool parameters
            
        Returns:
            Dict[str, Any]: Tool execution result
        """
        pass
    
    def get_status(self) -> str:
        """
        Get the current status of the tool.
        
        Returns:
            str: Tool status
        """
        return self.status
    
    def get_last_result(self) -> Optional[Dict[str, Any]]:
        """
        Get the result of the last execution.
        
        Returns:
            Optional[Dict[str, Any]]: Last execution result
        """
        return self.last_result
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get tool metadata.
        
        Returns:
            Dict[str, Any]: Tool metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status
        }
    
    def _set_status(self, status: str) -> None:
        """
        Set the tool status.
        
        Args:
            status (str): New status
        """
        self.status = status
        logger.debug(f"Tool {self.name} status: {status}")
    
    def _set_result(self, result: Dict[str, Any]) -> None:
        """
        Set the last execution result.
        
        Args:
            result (Dict[str, Any]): Execution result
        """
        self.last_result = result
