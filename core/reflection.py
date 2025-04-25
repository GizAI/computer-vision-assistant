#!/usr/bin/env python3
"""
Reflection & Learning Module for Autobot.
Enables the agent to learn from its experience.
"""

import logging
import json
import sqlite3
from typing import Dict, Any, List, Optional

from autobot.core.llm import LLMInterface

# Set up logging
logger = logging.getLogger(__name__)

class ReflectionModule:
    """Module for reflection and learning."""

    def __init__(self, project, memory_manager, llm_interface: Optional[LLMInterface] = None):
        """
        Initialize the reflection module.

        Args:
            project: Project instance
            memory_manager: Memory manager instance
            llm_interface (LLMInterface, optional): LLM interface. Defaults to None.
        """
        self.project = project
        self.memory_manager = memory_manager
        self.llm_interface = llm_interface or LLMInterface()

        logger.info(f"Reflection Module initialized for project: {project.name}")

    def reflect_on_task(self, task: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reflect on a task execution.

        Args:
            task (str): Task description
            result (Dict[str, Any]): Task execution result

        Returns:
            Dict[str, Any]: Reflection result
        """
        logger.info(f"Reflecting on task: {task}")

        # Construct prompt for reflection
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI assistant that reflects on task execution to learn and improve. "
                    "You will be given a task description and its execution result. "
                    "Your job is to analyze what went well, what went wrong, and what could be improved. "
                    "Respond in JSON format with the following structure:\n"
                    "{\n"
                    "  \"success\": true/false,\n"
                    "  \"analysis\": \"Detailed analysis of the task execution\",\n"
                    "  \"lessons_learned\": [\"Lesson 1\", \"Lesson 2\", ...],\n"
                    "  \"improvement_suggestions\": [\"Suggestion 1\", \"Suggestion 2\", ...]\n"
                    "}"
                )
            },
            {
                "role": "user",
                "content": f"Task: {task}\n\nResult: {result}"
            }
        ]

        # Generate reflection
        response = self.llm_interface.generate(messages)
        content = response["choices"][0]["message"]["content"]

        # Extract JSON
        reflection = self.llm_interface.extract_json(content)

        if not reflection:
            logger.warning(f"Failed to generate reflection for task: {task}")
            reflection = {
                "success": result.get("status") == "success",
                "analysis": "Failed to generate reflection",
                "lessons_learned": [],
                "improvement_suggestions": []
            }

        # Store reflection as insight
        insight_content = (
            f"Task: {task}\n\n"
            f"Analysis: {reflection.get('analysis', '')}\n\n"
            f"Lessons Learned:\n" + "\n".join([f"- {lesson}" for lesson in reflection.get('lessons_learned', [])]) + "\n\n"
            f"Improvement Suggestions:\n" + "\n".join([f"- {suggestion}" for suggestion in reflection.get('improvement_suggestions', [])])
        )

        self.memory_manager.add_insight(
            content=insight_content,
            task_id=task,
            metadata={
                "task": task,
                "success": reflection.get("success", False),
                "result_status": result.get("status")
            }
        )

        logger.info(f"Reflection generated for task: {task}")

        return reflection

    def reflect_on_progress(self, plan: str) -> Dict[str, Any]:
        """
        Reflect on overall progress.

        Args:
            plan (str): Current plan content

        Returns:
            Dict[str, Any]: Reflection result
        """
        logger.info("Reflecting on overall progress")

        # Get recent insights
        conn = sqlite3.connect(self.project.chat_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM insights ORDER BY id DESC LIMIT 5"
        )

        insights = []
        for row in cursor.fetchall():
            insight = dict(row)
            try:
                insight["metadata"] = json.loads(insight["metadata"])
            except json.JSONDecodeError:
                insight["metadata"] = {}
            insights.append(insight)

        conn.close()

        # Construct prompt for reflection
        insights_text = "\n\n".join([insight["content"] for insight in insights])

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI assistant that reflects on project progress to learn and improve. "
                    "You will be given the current project plan and recent insights. "
                    "Your job is to analyze overall progress, identify patterns, and suggest improvements. "
                    "Respond in JSON format with the following structure:\n"
                    "{\n"
                    "  \"progress_assessment\": \"Assessment of overall progress\",\n"
                    "  \"patterns_identified\": [\"Pattern 1\", \"Pattern 2\", ...],\n"
                    "  \"strengths\": [\"Strength 1\", \"Strength 2\", ...],\n"
                    "  \"challenges\": [\"Challenge 1\", \"Challenge 2\", ...],\n"
                    "  \"strategy_adjustments\": [\"Adjustment 1\", \"Adjustment 2\", ...]\n"
                    "}"
                )
            },
            {
                "role": "user",
                "content": f"Current Plan:\n\n{plan}\n\nRecent Insights:\n\n{insights_text}"
            }
        ]

        # Generate reflection
        response = self.llm_interface.generate(messages)
        content = response["choices"][0]["message"]["content"]

        # Extract JSON
        reflection = self.llm_interface.extract_json(content)

        if not reflection:
            logger.warning("Failed to generate progress reflection")
            reflection = {
                "progress_assessment": "Failed to generate reflection",
                "patterns_identified": [],
                "strengths": [],
                "challenges": [],
                "strategy_adjustments": []
            }

        # Store reflection as insight
        insight_content = (
            f"Progress Assessment: {reflection.get('progress_assessment', '')}\n\n"
            f"Patterns Identified:\n" + "\n".join([f"- {pattern}" for pattern in reflection.get('patterns_identified', [])]) + "\n\n"
            f"Strengths:\n" + "\n".join([f"- {strength}" for strength in reflection.get('strengths', [])]) + "\n\n"
            f"Challenges:\n" + "\n".join([f"- {challenge}" for challenge in reflection.get('challenges', [])]) + "\n\n"
            f"Strategy Adjustments:\n" + "\n".join([f"- {adjustment}" for adjustment in reflection.get('strategy_adjustments', [])])
        )

        self.memory_manager.add_insight(
            content=insight_content,
            task_id="progress_reflection",
            metadata={
                "type": "progress_reflection"
            }
        )

        logger.info("Progress reflection generated")

        return reflection
