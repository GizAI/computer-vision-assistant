#!/usr/bin/env python3
"""
Planning Module for Autobot.
Creates and manages hierarchical task plans.
"""

import os
import re
import logging
from typing import Dict, List, Any, Optional, Tuple

from core.llm import LLMInterface

# Set up logging
logger = logging.getLogger(__name__)

class PlanningModule:
    """Module for creating and managing task plans."""

    def __init__(self, project, llm_interface: Optional[LLMInterface] = None):
        """
        Initialize the planning module.

        Args:
            project: Project instance
            llm_interface (LLMInterface, optional): LLM interface. Defaults to None.
        """
        self.project = project
        self.llm_interface = llm_interface or LLMInterface()

        logger.info(f"Planning Module initialized for project: {project.name}")

    def create_initial_plan(self) -> str:
        """
        Create an initial plan for the project.

        Returns:
            str: Generated plan content
        """
        # Check if plan already exists
        if os.path.exists(self.project.plan_path):
            with open(self.project.plan_path, "r", encoding="utf-8") as f:
                existing_plan = f.read()
                if len(existing_plan.strip()) > 0:
                    logger.info(f"Plan already exists for project: {self.project.name}")
                    return existing_plan

        # Construct prompt for plan generation
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert project planner for an autonomous AI agent. "
                    "Your task is to create a detailed, hierarchical plan for achieving a goal. "
                    "The plan should be in Markdown format with nested task lists. "
                    "Each task should be actionable and specific. "
                    "Use the following format:\n\n"
                    "# Project Plan: [Project Name]\n\n"
                    "## Goal\n[Goal description]\n\n"
                    "## Tasks\n\n"
                    "- [ ] High-level task 1\n"
                    "  - [ ] Subtask 1.1\n"
                    "    - [ ] Sub-subtask 1.1.1\n"
                    "  - [ ] Subtask 1.2\n"
                    "- [ ] High-level task 2\n"
                    "  - [ ] Subtask 2.1\n"
                    "  - [ ] Subtask 2.2\n\n"
                    "Make sure tasks are specific, actionable, and cover all necessary steps to achieve the goal."
                )
            },
            {
                "role": "user",
                "content": f"Create a detailed plan for the following project:\n\nProject Name: {self.project.name}\n\nGoal: {self.project.goal}"
            }
        ]

        # Generate plan
        response = self.llm_interface.generate(messages)
        plan_content = response["choices"][0]["message"]["content"]

        # Save plan to file
        with open(self.project.plan_path, "w", encoding="utf-8") as f:
            f.write(plan_content)

        logger.info(f"Created initial plan for project: {self.project.name}")

        return plan_content

    def get_current_plan(self) -> str:
        """
        Get the current plan content.

        Returns:
            str: Current plan content
        """
        try:
            with open(self.project.plan_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read plan file: {str(e)}")
            return ""

    def update_plan(self, updated_plan: str) -> bool:
        """
        Update the plan with new content.

        Args:
            updated_plan (str): Updated plan content

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(self.project.plan_path, "w", encoding="utf-8") as f:
                f.write(updated_plan)

            logger.info(f"Updated plan for project: {self.project.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to update plan file: {str(e)}")
            return False

    def mark_task_complete(self, task_text: str) -> bool:
        """
        Mark a task as complete in the plan.

        Args:
            task_text (str): Text of the task to mark complete

        Returns:
            bool: True if successful, False otherwise
        """
        current_plan = self.get_current_plan()

        # Escape special characters in task_text for regex
        escaped_task_text = re.escape(task_text)

        # Replace "- [ ]" with "- [x]" for the specific task
        updated_plan = re.sub(
            f"- \\[ \\]\\s*{escaped_task_text}",
            f"- [x] {task_text}",
            current_plan
        )

        if updated_plan == current_plan:
            logger.warning(f"Task not found in plan: {task_text}")
            return False

        return self.update_plan(updated_plan)

    def mark_task_failed(self, task_text: str) -> bool:
        """
        Mark a task as failed in the plan.

        Args:
            task_text (str): Text of the task to mark failed

        Returns:
            bool: True if successful, False otherwise
        """
        current_plan = self.get_current_plan()

        # Escape special characters in task_text for regex
        escaped_task_text = re.escape(task_text)

        # Replace "- [ ]" with "- [!]" for the specific task
        updated_plan = re.sub(
            f"- \\[ \\]\\s*{escaped_task_text}",
            f"- [!] {task_text}",
            current_plan
        )

        if updated_plan == current_plan:
            logger.warning(f"Task not found in plan: {task_text}")
            return False

        return self.update_plan(updated_plan)

    def add_subtasks(self, parent_task: str, subtasks: List[str]) -> bool:
        """
        Add subtasks to a parent task in the plan.

        Args:
            parent_task (str): Text of the parent task
            subtasks (List[str]): List of subtask texts

        Returns:
            bool: True if successful, False otherwise
        """
        current_plan = self.get_current_plan()

        # Escape special characters in parent_task for regex
        escaped_parent_task = re.escape(parent_task)

        # Find the parent task line
        parent_match = re.search(f"(- \\[[ x!]\\]\\s*{escaped_parent_task})", current_plan)

        if not parent_match:
            logger.warning(f"Parent task not found in plan: {parent_task}")
            return False

        # Get the indentation level of the parent task
        parent_line = parent_match.group(1)
        parent_indent = len(parent_line) - len(parent_line.lstrip())

        # Create subtask lines with proper indentation
        subtask_lines = ""
        for subtask in subtasks:
            # Add 2 spaces more indentation than the parent
            subtask_lines += " " * (parent_indent + 2) + f"- [ ] {subtask}\n"

        # Insert subtasks after the parent task
        updated_plan = current_plan.replace(
            parent_line,
            f"{parent_line}\n{subtask_lines.rstrip()}"
        )

        return self.update_plan(updated_plan)

    def get_next_task(self) -> Optional[str]:
        """
        Get the next incomplete task from the plan.

        Returns:
            Optional[str]: Next task text or None if no tasks remain
        """
        current_plan = self.get_current_plan()

        # Find all incomplete tasks (marked with "- [ ]")
        incomplete_tasks = re.findall(r"- \[ \]\s*(.*?)$", current_plan, re.MULTILINE)

        if not incomplete_tasks:
            logger.info("No incomplete tasks found in plan")
            return None

        # Return the first incomplete task
        return incomplete_tasks[0]

    def refine_plan(self, reflection: str) -> str:
        """
        Refine the plan based on reflection.

        Args:
            reflection (str): Reflection content

        Returns:
            str: Refined plan content
        """
        current_plan = self.get_current_plan()

        # Construct prompt for plan refinement
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert project planner for an autonomous AI agent. "
                    "Your task is to refine an existing project plan based on reflection and progress. "
                    "The plan is in Markdown format with nested task lists. "
                    "Tasks are marked as follows:\n"
                    "- [ ] Incomplete task\n"
                    "- [x] Completed task\n"
                    "- [!] Failed task\n\n"
                    "Update the plan by:\n"
                    "1. Adding new tasks or subtasks where needed\n"
                    "2. Removing or modifying tasks that are no longer relevant\n"
                    "3. Restructuring tasks if a better approach is identified\n\n"
                    "Maintain the existing format and structure. Return the complete updated plan."
                )
            },
            {
                "role": "user",
                "content": f"Here is the current project plan:\n\n{current_plan}\n\nHere is a reflection on the progress and challenges:\n\n{reflection}\n\nPlease refine the plan based on this reflection."
            }
        ]

        # Generate refined plan
        response = self.llm_interface.generate(messages)
        refined_plan = response["choices"][0]["message"]["content"]

        # Save refined plan
        self.update_plan(refined_plan)

        logger.info(f"Refined plan for project: {self.project.name}")

        return refined_plan
