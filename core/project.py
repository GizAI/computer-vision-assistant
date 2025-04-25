#!/usr/bin/env python3
"""
Project Manager for Autobot.
Handles the lifecycle of projects, including creation, loading, and management.
"""

import os
import json
import logging
import shutil
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

# Set up logging
logger = logging.getLogger(__name__)

class Project:
    """Class representing an Autobot project."""

    def __init__(self, name: str, path: str, goal: str = None, project_id: str = None):
        """
        Initialize a project.

        Args:
            name (str): Project name
            path (str): Path to project directory
            goal (str, optional): Project goal. Defaults to None.
            project_id (str, optional): Project ID. Defaults to None (will generate a new UUID).
        """
        self.name = name
        self.path = path
        self.goal = goal
        self.id = project_id or str(uuid.uuid4())
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
            "id": self.id,
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
            "id": self.id,
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

    def load_project(self, project_id: str) -> Optional[Project]:
        """
        Load an existing project by ID or name.

        Args:
            project_id (str): Project ID or name

        Returns:
            Optional[Project]: Loaded project or None if not found
        """
        # First try to find by ID in all project configs
        for item in os.listdir(self.projects_dir):
            project_path = os.path.join(self.projects_dir, item)

            if os.path.isdir(project_path):
                config_path = os.path.join(project_path, "config.json")

                if os.path.exists(config_path):
                    try:
                        with open(config_path, "r", encoding="utf-8") as f:
                            config = json.load(f)

                        # Check if this is the project we're looking for by ID
                        if config.get("id") == project_id:
                            # Create project instance
                            project = Project(
                                name=config.get("name", item),
                                path=project_path,
                                goal=config.get("goal", ""),
                                project_id=config.get("id")
                            )

                            # Set additional properties from config
                            project.created_at = config.get("created_at", project.created_at)
                            project.updated_at = config.get("updated_at", project.updated_at)
                            project.status = config.get("status", project.status)

                            logger.info(f"Loaded project by ID: {project_id} from {project_path}")
                            return project
                    except json.JSONDecodeError:
                        pass

        # If not found by ID, try by name (for backward compatibility)
        # Sanitize project name for filesystem
        safe_name = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in project_id)

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
                    name=config.get("name", project_id),
                    path=project_path,
                    goal=config.get("goal", ""),
                    project_id=config.get("id")
                )

                # Set additional properties from config
                project.created_at = config.get("created_at", project.created_at)
                project.updated_at = config.get("updated_at", project.updated_at)
                project.status = config.get("status", project.status)

                logger.info(f"Loaded project by name: {project_id} from {project_path}")

                return project

            except json.JSONDecodeError:
                logger.error(f"Failed to load config from {config_path}")

        # If no config or failed to load, create a basic project instance
        project = Project(name=project_id, path=project_path)
        logger.info(f"Loaded project with basic info: {project_id} from {project_path}")

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

                        # Generate an ID if one doesn't exist
                        project_id = config.get("id")
                        if not project_id:
                            project_id = str(uuid.uuid4())
                            # Save the ID back to the config
                            config["id"] = project_id
                            with open(config_path, "w", encoding="utf-8") as f:
                                json.dump(config, f, indent=2)

                        projects.append({
                            "id": project_id,
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

                # If no config or failed to load, add basic info with a new ID
                project_id = str(uuid.uuid4())

                # Create a basic config with the ID
                config = {
                    "id": project_id,
                    "name": item,
                    "goal": "",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "status": "active"
                }

                # Save the config
                try:
                    with open(config_path, "w", encoding="utf-8") as f:
                        json.dump(config, f, indent=2)
                except Exception as e:
                    logger.error(f"Failed to save config for {item}: {e}")

                projects.append({
                    "id": project_id,
                    "name": item,
                    "path": project_path,
                    "goal": "",
                    "created_at": config["created_at"],
                    "updated_at": config["updated_at"],
                    "status": "active"
                })

        return projects

    def rename_project(self, project_id: str, new_name: str) -> Project:
        """
        Rename an existing project.

        Args:
            project_id (str): The ID or name of the project to rename.
            new_name (str): The desired new name for the project.

        Returns:
            Project: The updated project object.

        Raises:
            FileNotFoundError: If the project with project_id does not exist.
            ValueError: If a project with new_name already exists or names are invalid.
        """
        # Sanitize new name
        safe_new_name = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in new_name)

        if not safe_new_name:
            raise ValueError("Project name cannot be empty after sanitization.")

        # First try to find project by ID
        project_found = False
        old_project_path = None
        old_name = None
        project_config = None

        for item in os.listdir(self.projects_dir):
            item_path = os.path.join(self.projects_dir, item)

            if os.path.isdir(item_path):
                config_path = os.path.join(item_path, "config.json")

                if os.path.exists(config_path):
                    try:
                        with open(config_path, "r", encoding="utf-8") as f:
                            config = json.load(f)

                        # Check if this is the project we're looking for by ID
                        if config.get("id") == project_id:
                            old_project_path = item_path
                            old_name = config.get("name", item)
                            project_config = config
                            project_found = True
                            break
                    except json.JSONDecodeError:
                        pass

        # If not found by ID, try by name (for backward compatibility)
        if not project_found:
            # Sanitize project name for filesystem
            safe_old_name = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in project_id)
            old_project_path = os.path.join(self.projects_dir, safe_old_name)
            old_name = project_id

            # Check if project directory exists
            if not os.path.exists(old_project_path) or not os.path.isdir(old_project_path):
                logger.error(f"Project directory to rename not found: {old_project_path}")
                raise FileNotFoundError(f"Project '{project_id}' not found.")

            # Try to load config
            config_path = os.path.join(old_project_path, "config.json")
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        project_config = json.load(f)
                except json.JSONDecodeError:
                    project_config = None

        # Check if old name and new name are the same
        if old_name == new_name:
            raise ValueError("New project name cannot be the same as the old name.")

        # Determine new path
        new_project_path = os.path.join(self.projects_dir, safe_new_name)

        # Check if new project name already exists
        if os.path.exists(new_project_path):
            logger.error(f"Project directory with the new name already exists: {new_project_path}")
            raise ValueError(f"A project named '{new_name}' already exists.")

        try:
            # Rename the directory
            os.rename(old_project_path, new_project_path)
            logger.info(f"Renamed project directory from {old_project_path} to {new_project_path}")

            # Update the config file inside the renamed directory
            config_path = os.path.join(new_project_path, "config.json")
            project = None

            if project_config:
                try:
                    # Update project name in config
                    project_config["name"] = new_name
                    project_config["updated_at"] = datetime.now().isoformat()

                    # Ensure we have an ID
                    if "id" not in project_config:
                        project_config["id"] = str(uuid.uuid4())

                    with open(config_path, "w", encoding="utf-8") as f:
                        json.dump(project_config, f, indent=2)

                    # Create project instance with updated info
                    project = Project(
                        name=new_name,
                        path=new_project_path,
                        goal=project_config.get("goal", ""),
                        project_id=project_config.get("id")
                    )
                    project.created_at = project_config.get("created_at", project.created_at)
                    project.updated_at = project_config.get("updated_at", project.updated_at)
                    project.status = project_config.get("status", project.status)

                    logger.info(f"Updated config file for renamed project: {config_path}")

                except (json.JSONDecodeError, IOError) as e:
                    logger.error(f"Error updating config file {config_path} after rename: {e}")
                    # Continue even if config update fails, but log the error

            # If config update failed or no config existed, return a basic project object
            if not project:
                 project = Project(name=new_name, path=new_project_path)
                 project.save_config() # Attempt to save a basic config

            return project

        except OSError as e:
            logger.error(f"Error renaming project directory {old_project_path} to {new_project_path}: {e}")
            # Attempt to revert rename if possible, though this might fail too
            if not os.path.exists(old_project_path) and os.path.exists(new_project_path):
                 try:
                     os.rename(new_project_path, old_project_path)
                     logger.warning(f"Attempted to revert rename for {old_name}")
                 except OSError as revert_e:
                     logger.error(f"Failed to revert rename: {revert_e}")
            raise ValueError(f"Failed to rename project: {e}")


    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project by ID or name.

        Args:
            project_id (str): Project ID or name

        Returns:
            bool: True if deleted, False otherwise
        """
        # First try to find by ID
        for item in os.listdir(self.projects_dir):
            project_path = os.path.join(self.projects_dir, item)

            if os.path.isdir(project_path):
                config_path = os.path.join(project_path, "config.json")

                if os.path.exists(config_path):
                    try:
                        with open(config_path, "r", encoding="utf-8") as f:
                            config = json.load(f)

                        # Check if this is the project we're looking for by ID
                        if config.get("id") == project_id:
                            # Delete project directory
                            shutil.rmtree(project_path)
                            logger.info(f"Deleted project by ID: {project_id} at {project_path}")
                            return True
                    except json.JSONDecodeError:
                        pass

        # If not found by ID, try by name (for backward compatibility)
        # Sanitize project name for filesystem
        safe_name = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in project_id)

        # Check if project directory exists
        project_path = os.path.join(self.projects_dir, safe_name)

        if not os.path.exists(project_path):
            logger.warning(f"Project directory does not exist: {project_path}")
            return False

        # Delete project directory
        shutil.rmtree(project_path)

        logger.info(f"Deleted project by name: {project_id} at {project_path}")

        return True
