#!/usr/bin/env python3
"""
Task Execution Engine for Autobot.
Executes individual tasks defined in the plan.
"""

import os
import logging
import importlib
import time
from typing import Dict, Any, List, Optional, Type

from autobot.tools.base import Tool
from autobot.core.llm import LLMInterface

# Set up logging
logger = logging.getLogger(__name__)

class TaskExecutionEngine:
    """Engine for executing tasks."""
    
    def __init__(self, project, memory_manager, llm_interface: Optional[LLMInterface] = None):
        """
        Initialize the task execution engine.
        
        Args:
            project: Project instance
            memory_manager: Memory manager instance
            llm_interface (LLMInterface, optional): LLM interface. Defaults to None.
        """
        self.project = project
        self.memory_manager = memory_manager
        self.llm_interface = llm_interface or LLMInterface()
        
        # Initialize tools
        self.tools = {}
        self._init_tools()
        
        logger.info(f"Task Execution Engine initialized for project: {project.name}")
    
    def _init_tools(self) -> None:
        """Initialize available tools."""
        # CLI Tool
        try:
            from autobot.tools.cli import CLITool
            self.tools["cli"] = CLITool(working_dir=self.project.path)
            logger.info("CLI Tool initialized")
        except ImportError as e:
            logger.error(f"Failed to initialize CLI Tool: {str(e)}")
        
        # Python Executor Tool
        try:
            from autobot.tools.python import PythonExecutorTool
            self.tools["python"] = PythonExecutorTool(working_dir=self.project.path)
            logger.info("Python Executor Tool initialized")
        except ImportError as e:
            logger.error(f"Failed to initialize Python Executor Tool: {str(e)}")
        
        # Computer Vision Tool
        try:
            from autobot.tools.cv_assistant import ComputerVisionTool
            self.tools["computer_vision"] = ComputerVisionTool()
            logger.info("Computer Vision Tool initialized")
        except ImportError as e:
            logger.error(f"Failed to initialize Computer Vision Tool: {str(e)}")
        
        # File Tool
        try:
            from autobot.tools.file import FileTool
            self.tools["file"] = FileTool(working_dir=self.project.path)
            logger.info("File Tool initialized")
        except ImportError as e:
            logger.error(f"Failed to initialize File Tool: {str(e)}")
        
        # Web Search Tool
        try:
            from autobot.tools.web_search import WebSearchTool
            self.tools["web_search"] = WebSearchTool()
            logger.info("Web Search Tool initialized")
        except ImportError as e:
            logger.error(f"Failed to initialize Web Search Tool: {str(e)}")
    
    def execute_task(self, task: str) -> Dict[str, Any]:
        """
        Execute a task.
        
        Args:
            task (str): Task description
            
        Returns:
            Dict[str, Any]: Execution result
        """
        logger.info(f"Executing task: {task}")
        
        # Determine the best tool for the task
        tool_name, params = self._determine_tool(task)
        
        if not tool_name or tool_name not in self.tools:
            result = {
                "status": "error",
                "error": f"No suitable tool found for task: {task}",
                "task": task
            }
            logger.error(f"No suitable tool found for task: {task}")
            return result
        
        # Get the tool
        tool = self.tools[tool_name]
        
        # Execute the tool
        try:
            start_time = time.time()
            result = tool.execute(params)
            end_time = time.time()
            
            # Add execution metadata
            result["task"] = task
            result["tool"] = tool_name
            result["execution_time"] = end_time - start_time
            
            # Log execution
            self.memory_manager.add_execution_log(
                tool=tool_name,
                params=params,
                status=result.get("status", "unknown"),
                output=result,
                task_id=task
            )
            
            logger.info(f"Task executed: {task} (status: {result.get('status', 'unknown')})")
            
            return result
            
        except Exception as e:
            result = {
                "status": "error",
                "error": str(e),
                "task": task,
                "tool": tool_name
            }
            
            # Log execution
            self.memory_manager.add_execution_log(
                tool=tool_name,
                params=params,
                status="error",
                output={"error": str(e)},
                task_id=task
            )
            
            logger.error(f"Error executing task: {task} - {str(e)}")
            
            return result
    
    def _determine_tool(self, task: str) -> tuple[Optional[str], Dict[str, Any]]:
        """
        Determine the best tool for a task.
        
        Args:
            task (str): Task description
            
        Returns:
            tuple[Optional[str], Dict[str, Any]]: Tool name and parameters
        """
        # Construct prompt for tool selection
        tools_description = "\n".join([
            f"- {name}: {tool.description}" for name, tool in self.tools.items()
        ])
        
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI assistant that helps determine the best tool to use for a given task. "
                    "You will be given a task description and a list of available tools. "
                    "Your job is to select the most appropriate tool and specify the parameters to use with it. "
                    "Respond in JSON format with the following structure:\n"
                    "{\n"
                    "  \"tool\": \"tool_name\",\n"
                    "  \"params\": {\n"
                    "    \"param1\": \"value1\",\n"
                    "    \"param2\": \"value2\"\n"
                    "  },\n"
                    "  \"reasoning\": \"Brief explanation of why this tool was chosen\"\n"
                    "}\n\n"
                    f"Available tools:\n{tools_description}"
                )
            },
            {
                "role": "user",
                "content": f"Task: {task}"
            }
        ]
        
        # Generate tool selection
        response = self.llm_interface.generate(messages)
        content = response["choices"][0]["message"]["content"]
        
        # Extract JSON
        selection = self.llm_interface.extract_json(content)
        
        if not selection or "tool" not in selection:
            logger.warning(f"Failed to determine tool for task: {task}")
            return None, {}
        
        tool_name = selection.get("tool")
        params = selection.get("params", {})
        
        logger.info(f"Selected tool for task '{task}': {tool_name}")
        
        return tool_name, params
