#!/usr/bin/env python3
"""
Core Orchestrator for Autobot.
The central "brain" running the main autonomous loop.
Supports dual AI functionality - one for user interaction and one for background tasks.
"""

import os
import time
import logging
import queue
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple

from autobot.core.llm import LLMInterface
from autobot.core.memory import MemoryManager
from autobot.core.planning import PlanningModule
from autobot.core.execution import TaskExecutionEngine
from autobot.core.reflection import ReflectionModule

# Set up logging
logger = logging.getLogger(__name__)

class AgentState(Enum):
    """Enum for agent states."""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    WAITING_FOR_USER = "waiting_for_user"
    SHUTDOWN = "shutdown"

class Orchestrator:
    """Core orchestrator for Autobot with dual AI functionality."""

    def __init__(self, project):
        """
        Initialize the orchestrator.

        Args:
            project: Project instance
        """
        self.project = project

        # Initialize LLM interfaces - one for user interaction, one for background tasks
        self.user_llm_interface = LLMInterface()
        self.task_llm_interface = LLMInterface()

        # Initialize components
        self.memory_manager = MemoryManager(project, self.task_llm_interface)
        self.planning_module = PlanningModule(project, self.task_llm_interface)
        self.execution_engine = TaskExecutionEngine(project, self.memory_manager, self.task_llm_interface)
        self.reflection_module = ReflectionModule(project, self.memory_manager, self.task_llm_interface)

        # Initialize state
        self.state = AgentState.IDLE
        self.current_task = None
        self.last_result = None
        self.running = False

        # Initialize message queues
        self.user_message_queue = queue.Queue()  # For user interaction AI
        self.task_message_queue = queue.Queue()  # For background task AI

        # Initialize work logs for the task AI
        self.work_logs = []

        logger.info(f"Orchestrator initialized for project: {project.name}")

    def run(self):
        """Run the main agent loop."""
        self.running = True

        logger.info("Starting agent loop")

        # Create initial plan if needed
        if not os.path.exists(self.project.plan_path) or os.path.getsize(self.project.plan_path) == 0:
            self.state = AgentState.PLANNING
            logger.info("Creating initial plan")
            self.planning_module.create_initial_plan()

        # Main agent loop
        while self.running:
            try:
                # Check for user messages
                self._check_user_messages()

                # Execute state-specific logic
                if self.state == AgentState.IDLE:
                    self._handle_idle_state()
                elif self.state == AgentState.PLANNING:
                    self._handle_planning_state()
                elif self.state == AgentState.EXECUTING:
                    self._handle_executing_state()
                elif self.state == AgentState.REFLECTING:
                    self._handle_reflecting_state()
                elif self.state == AgentState.WAITING_FOR_USER:
                    # Just wait for user input
                    time.sleep(1)
                elif self.state == AgentState.SHUTDOWN:
                    self.running = False

                # Small sleep to prevent CPU hogging
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error in agent loop: {str(e)}")
                self.state = AgentState.IDLE
                time.sleep(5)  # Wait a bit before retrying

    def shutdown(self):
        """Shutdown the agent."""
        logger.info("Shutting down agent")
        self.running = False
        self.state = AgentState.SHUTDOWN

    def send_message(self, message: str, sender: str = "user", message_type: str = "user_chat") -> int:
        """
        Send a message to the agent.

        Args:
            message (str): Message content
            sender (str, optional): Message sender. Defaults to "user".
            message_type (str, optional): Type of message - "user_chat" or "task_log". Defaults to "user_chat".

        Returns:
            int: Message ID
        """
        # Add message to memory
        message_id = self.memory_manager.add_message(sender, message)

        # Add to appropriate queue for processing
        if message_type == "user_chat":
            if sender == "user":
                self.user_message_queue.put({"id": message_id, "content": message})

                # If waiting for user, switch to idle to process the message
                if self.state == AgentState.WAITING_FOR_USER:
                    self.state = AgentState.IDLE
        elif message_type == "task_log":
            # Add to task logs
            self.work_logs.append({
                "id": message_id,
                "content": message,
                "sender": sender,
                "timestamp": time.time()
            })

            # Also add to task message queue if needed
            self.task_message_queue.put({"id": message_id, "content": message})

        return message_id

    def send_task_log(self, message: str) -> int:
        """
        Send a task log message from the background AI.

        Args:
            message (str): Log message content

        Returns:
            int: Message ID
        """
        return self.send_message(message, "task_ai", "task_log")

    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the agent.

        Returns:
            Dict[str, Any]: Status information
        """
        return {
            "state": self.state.value,
            "current_task": self.current_task,
            "project": self.project.name,
            "goal": self.project.goal
        }

    def get_work_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get the work logs from the task AI.

        Args:
            limit (int, optional): Maximum number of logs to return. Defaults to 50.

        Returns:
            List[Dict[str, Any]]: Work logs
        """
        # Return the most recent logs up to the limit
        return self.work_logs[-limit:] if self.work_logs else []

    def _check_user_messages(self):
        """Check for and process user messages."""
        # Process user chat messages
        if not self.user_message_queue.empty():
            # Get the latest message
            message = self.user_message_queue.get()

            # Process the message
            logger.info(f"Processing user chat message: {message['content']}")

            # Check if it's a command
            if message["content"].startswith("/"):
                self._handle_command(message["content"])
            else:
                # Otherwise, generate a response with the user interaction AI
                if self.state == AgentState.WAITING_FOR_USER:
                    # Resume execution
                    self.state = AgentState.IDLE

                # Generate a response using the user interaction AI
                self._generate_user_response(message["content"])

        # Process task messages
        if not self.task_message_queue.empty():
            # Get the latest message
            message = self.task_message_queue.get()

            # Process the message with the task AI
            logger.info(f"Processing task message: {message['content']}")

            # No need to generate a response, just log that we processed it
            pass

    def _handle_command(self, command: str):
        """
        Handle a command from the user.

        Args:
            command (str): Command string
        """
        cmd = command.lower().strip()

        if cmd == "/stop" or cmd == "/pause":
            logger.info("Pausing agent - changing state to WAITING_FOR_USER")
            self.state = AgentState.WAITING_FOR_USER
            self.send_message("Agent paused. Click Resume to continue.", "autobot")
            self.send_task_log("Agent paused by user. Waiting for resume command.")

        elif cmd == "/resume":
            logger.info("Resuming agent - changing state to IDLE")
            self.state = AgentState.IDLE
            self.send_message("Agent resumed. Continuing execution.", "autobot")
            self.send_task_log("Agent resumed by user. Continuing execution.")

        elif cmd == "/status":
            status = self.get_status()
            self.send_message(f"Current status: {status}", "autobot")

        elif cmd == "/plan":
            plan = self.planning_module.get_current_plan()
            self.send_message(f"Current plan:\n\n{plan}", "autobot")

        elif cmd.startswith("/task "):
            # Extract task text
            task = command[6:].strip()
            self.current_task = task
            self.state = AgentState.EXECUTING
            logger.info(f"Executing task: {task}")
            self.send_message(f"Executing task: {task}", "autobot")

        elif cmd == "/reflect":
            self.state = AgentState.REFLECTING
            logger.info("Reflecting on progress")
            self.send_message("Reflecting on progress...", "autobot")

        elif cmd == "/help":
            help_text = (
                "Available commands:\n"
                "/status - Get current agent status\n"
                "/plan - View current plan\n"
                "/task <task> - Execute a specific task\n"
                "/reflect - Reflect on progress\n"
                "/stop or /pause - Pause the agent\n"
                "/resume - Resume the agent\n"
                "/help - Show this help message"
            )
            self.send_message(help_text, "autobot")

        else:
            self.send_message(f"Unknown command: {command}. Type /help for available commands.", "autobot")

    def _generate_user_response(self, user_message: str):
        """
        Generate a response to a user message using the user interaction AI.

        Args:
            user_message (str): User message
        """
        # Construct prompt
        messages = self.memory_manager.construct_prompt(
            system_prompt=(
                "You are Autobot's user interaction AI. You are designed to help users by providing friendly and helpful responses. "
                f"You are currently working on the project '{self.project.name}' with the goal: '{self.project.goal}'. "
                "Your job is to communicate with the user while the background task AI handles the actual work. "
                "Provide a helpful response to the user's message."
            ),
            user_message=user_message,
            include_plan=True,
            include_recent_chat=True,
            include_search=True
        )

        # Generate response using the user interaction AI
        response = self.user_llm_interface.generate(messages)
        content = response["choices"][0]["message"]["content"]

        # Send response to the user chat
        self.send_message(content, "user_ai", "user_chat")

    def _generate_task_log(self, task_description: str):
        """
        Generate a task log entry using the task AI.

        Args:
            task_description (str): Description of the current task
        """
        # Construct prompt
        messages = self.memory_manager.construct_prompt(
            system_prompt=(
                "You are Autobot's task AI. You are designed to work on tasks and provide detailed logs of your work. "
                f"You are currently working on the project '{self.project.name}' with the goal: '{self.project.goal}'. "
                f"Your current state is: {self.state.value}. "
                f"You are working on the task: {task_description}. "
                "Provide a detailed log entry about what you're doing."
            ),
            user_message="Generate a log entry for the current task.",
            include_plan=True,
            include_recent_chat=False,
            include_search=True
        )

        # Generate log using the task AI
        response = self.task_llm_interface.generate(messages)
        content = response["choices"][0]["message"]["content"]

        # Send log to the task logs
        self.send_task_log(content)

    def _handle_idle_state(self):
        """Handle the idle state."""
        # Generate a task log
        self.send_task_log("Checking for the next task to execute...")

        # Check if there's a next task to execute
        next_task = self.planning_module.get_next_task()

        if next_task:
            # Move to executing state
            self.current_task = next_task
            self.state = AgentState.EXECUTING
            logger.info(f"Moving to executing state with task: {next_task}")

            # Generate a task log
            self.send_task_log(f"Found next task to execute: {next_task}")
            self._generate_task_log(next_task)
        else:
            # If no tasks, move to planning state to refine the plan
            self.state = AgentState.PLANNING
            logger.info("No tasks found, moving to planning state")

            # Generate a task log
            self.send_task_log("No tasks found in the current plan. Moving to planning state to create or refine the plan.")

    def _handle_planning_state(self):
        """Handle the planning state."""
        logger.info("Planning...")

        # Generate a task log
        self.send_task_log("Planning the next steps for the project...")

        # If we have a previous reflection, use it to refine the plan
        if self.last_result and "reflection" in self.last_result:
            self.send_task_log(f"Refining plan based on previous reflection: {self.last_result['reflection']}")
            self.planning_module.refine_plan(self.last_result["reflection"])
        else:
            # Otherwise, just create or update the plan
            current_plan = self.planning_module.get_current_plan()

            if not current_plan:
                self.send_task_log("Creating initial plan for the project...")
                self.planning_module.create_initial_plan()
            else:
                self.send_task_log("Reviewing and updating the current plan...")

        # Get the updated plan for logging
        updated_plan = self.planning_module.get_current_plan()
        if updated_plan:
            self.send_task_log(f"Updated plan:\n\n{updated_plan}")

        # Move to idle state to pick the next task
        self.state = AgentState.IDLE
        logger.info("Planning complete, moving to idle state")
        self.send_task_log("Planning complete. Moving to idle state to select the next task.")

    def _handle_executing_state(self):
        """Handle the executing state."""
        if not self.current_task:
            self.state = AgentState.IDLE
            logger.info("No current task to execute, moving to idle state")
            self.send_task_log("No current task to execute. Moving to idle state.")
            return

        logger.info(f"Executing task: {self.current_task}")
        self.send_task_log(f"Starting execution of task: {self.current_task}")

        # Generate detailed task log before execution
        self._generate_task_log(self.current_task)

        # Execute the task
        self.send_task_log(f"Executing task using appropriate tools...")
        result = self.execution_engine.execute_task(self.current_task)

        # Store the result
        self.last_result = result

        # Log the result
        status = result.get("status", "unknown")
        if status == "success":
            self.send_task_log(f"Task completed successfully: {self.current_task}\n\nResult: {result}")

            # Also send to user chat for awareness
            self.send_message(f"Task completed: {self.current_task}\n\nResult: {result}", "task_ai", "user_chat")

            # Mark task as complete in the plan
            self.planning_module.mark_task_complete(self.current_task)
        else:
            self.send_task_log(f"Task failed: {self.current_task}\n\nError: {result.get('error', 'Unknown error')}")

            # Also send to user chat for awareness
            self.send_message(f"Task failed: {self.current_task}\n\nError: {result.get('error', 'Unknown error')}", "task_ai", "user_chat")

            # Mark task as failed in the plan
            self.planning_module.mark_task_failed(self.current_task)

        # Move to reflecting state
        self.state = AgentState.REFLECTING
        logger.info(f"Task execution complete with status: {status}, moving to reflecting state")
        self.send_task_log(f"Task execution complete with status: {status}. Moving to reflection state to analyze results.")

    def _handle_reflecting_state(self):
        """Handle the reflecting state."""
        logger.info("Reflecting...")
        self.send_task_log("Reflecting on the completed task and overall progress...")

        if self.current_task and self.last_result:
            # Reflect on the task
            self.send_task_log(f"Analyzing results of task: {self.current_task}")
            reflection = self.reflection_module.reflect_on_task(self.current_task, self.last_result)

            # Store reflection in last_result
            self.last_result["reflection"] = reflection

            # Log the reflection
            self.send_task_log(f"Task reflection:\n\n{reflection}")

            # Periodically reflect on overall progress
            if hash(self.current_task) % 5 == 0:  # Every ~5 tasks
                self.send_task_log("Performing overall progress reflection...")
                plan = self.planning_module.get_current_plan()
                progress_reflection = self.reflection_module.reflect_on_progress(plan)

                # Log the progress reflection
                progress_assessment = progress_reflection.get('progress_assessment', 'No assessment available')
                self.send_task_log(f"Progress Reflection:\n\n{progress_assessment}")

                # Also send to user chat for awareness
                self.send_message(
                    f"Progress Reflection:\n\n{progress_assessment}",
                    "task_ai", "user_chat"
                )

        # Clear current task
        self.current_task = None

        # Move to planning state to update the plan based on reflection
        self.state = AgentState.PLANNING
        logger.info("Reflection complete, moving to planning state")
        self.send_task_log("Reflection complete. Moving to planning state to update the plan based on insights.")
