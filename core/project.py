#!/usr/bin/env python3
"""
Project Manager for Autobot.
Handles the lifecycle of projects, including creation, loading, and management.
"""

import os
import json
import logging
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional

# Set up logging
logger = logging.getLogger(__name__)

class Project:
    """Class representing an Autobot project."""

    def __init__(self, name: str, path: str, goal: str = None):
        """
        Initialize a project.

        Args:
            name (str): Project name
            path (str): Path to project directory
            goal (str, optional): Project goal. Defaults to None.
        """
        self.name = name
        self.path = path
        self.goal = goal
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.status = "active"

        # Paths to project resources
        self.plan_path = os.path.join(path, "plan.md")
        self.chat_db_path = os.path.join(path, "chat_history.sqlite")
        self.vector_db_path = os.path.join(path, "vector_db")
        self.logs_path = os.path.join(path, "logs")
        self.config_path = os.path.join(path, "config.json")

        # Load config if exists
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load project configuration from file."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Failed to load config from {self.config_path}")
                return {}
        return {}

    def save_config(self) -> None:
        """Save project configuration to file."""
        config = {
            "name": self.name,
            "goal": self.goal,
            "created_at": self.created_at,
            "updated_at": datetime.now().isoformat(),
            "status": self.status,
            # Add any other project-specific configuration
        }

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary."""
        return {
            "name": self.name,
            "path": self.path,
            "goal": self.goal,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status,
        }

class ProjectManager:
    """Manager for Autobot projects."""

    def __init__(self, projects_dir: str = "projects"):
        """
        Initialize the project manager.

        Args:
            projects_dir (str, optional): Directory to store projects. Defaults to "projects".
        """
        self.projects_dir = projects_dir

        # Create projects directory if it doesn't exist
        os.makedirs(self.projects_dir, exist_ok=True)

        logger.info(f"Project Manager initialized with projects directory: {self.projects_dir}")

    def create_project(self, name: str, goal: str) -> Project:
        """
        Create a new project.

        Args:
            name (str): Project name
            goal (str): Project goal

        Returns:
            Project: Created project
        """
        # Sanitize project name for filesystem
        safe_name = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in name)

        # Create project directory
        project_path = os.path.join(self.projects_dir, safe_name)

        if os.path.exists(project_path):
            logger.warning(f"Project directory already exists: {project_path}")
            return self.load_project(name)

        os.makedirs(project_path, exist_ok=True)

        # Create project subdirectories
        os.makedirs(os.path.join(project_path, "logs"), exist_ok=True)
        os.makedirs(os.path.join(project_path, "vector_db"), exist_ok=True)

        # Create initial plan file
        with open(os.path.join(project_path, "plan.md"), "w", encoding="utf-8") as f:
            f.write(f"# Project Plan: {name}\n\n")
            f.write(f"## Goal\n{goal}\n\n")
            f.write("## Tasks\n\n")
            f.write("- [ ] Initial planning\n")

        # Create project instance
        project = Project(name, project_path, goal)

        # Save project configuration
        project.save_config()

        logger.info(f"Created new project: {name} at {project_path}")

        return project

    def load_project(self, name: str) -> Optional[Project]:
        """
        Load an existing project.

        Args:
            name (str): Project name

        Returns:
            Optional[Project]: Loaded project or None if not found
        """
        # Sanitize project name for filesystem
        safe_name = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in name)

        # Check if project directory exists
        project_path = os.path.join(self.projects_dir, safe_name)

        if not os.path.exists(project_path):
            logger.warning(f"Project directory does not exist: {project_path}")
            return None

        # Load project configuration
        config_path = os.path.join(project_path, "config.json")

        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)

                # Create project instance
                project = Project(
                    name=config.get("name", name),
                    path=project_path,
                    goal=config.get("goal", "")
                )

                # Set additional properties from config
                project.created_at = config.get("created_at", project.created_at)
                project.updated_at = config.get("updated_at", project.updated_at)
                project.status = config.get("status", project.status)

                logger.info(f"Loaded project: {name} from {project_path}")

                return project

            except json.JSONDecodeError:
                logger.error(f"Failed to load config from {config_path}")

        # If no config or failed to load, create a basic project instance
        project = Project(name, project_path)
        logger.info(f"Loaded project with basic info: {name} from {project_path}")

        return project

    def list_projects(self) -> List[Dict[str, Any]]:
        """
        List all projects.

        Returns:
            List[Dict[str, Any]]: List of project dictionaries
        """
        projects = []

        for item in os.listdir(self.projects_dir):
            project_path = os.path.join(self.projects_dir, item)

            if os.path.isdir(project_path):
                # Try to load project configuration
                config_path = os.path.join(project_path, "config.json")

                if os.path.exists(config_path):
                    try:
                        with open(config_path, "r", encoding="utf-8") as f:
                            config = json.load(f)

                        projects.append({
                            "name": config.get("name", item),
                            "path": project_path,
                            "goal": config.get("goal", ""),
                            "created_at": config.get("created_at", ""),
                            "updated_at": config.get("updated_at", ""),
                            "status": config.get("status", "active")
                        })
                        continue
                    except json.JSONDecodeError:
                        pass

                # If no config or failed to load, add basic info
                projects.append({
                    "name": item,
                    "path": project_path,
                    "goal": "",
                    "created_at": "",
                    "updated_at": "",
                    "status": "active"
                })

        return projects

    def delete_project(self, name: str) -> bool:
        """
        Delete a project.

        Args:
            name (str): Project name

        Returns:
            bool: True if deleted, False otherwise
        """
        # Sanitize project name for filesystem
        safe_name = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in name)

        # Check if project directory exists
        project_path = os.path.join(self.projects_dir, safe_name)

        if not os.path.exists(project_path):
            logger.warning(f"Project directory does not exist: {project_path}")
            return False

        # Delete project directory
        shutil.rmtree(project_path)

        logger.info(f"Deleted project: {name} at {project_path}")

        return True
