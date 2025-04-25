#!/usr/bin/env python3
"""
CLI Tool for Autobot.
Executes shell commands.
"""

import os
import subprocess
import logging
import platform
import shlex
from typing import Dict, Any, List, Optional

from autobot.tools.base import Tool

# Set up logging
logger = logging.getLogger(__name__)

class CLITool(Tool):
    """Tool for executing shell commands."""
    
    def __init__(self, working_dir: str = None):
        """
        Initialize the CLI tool.
        
        Args:
            working_dir (str, optional): Working directory for commands. Defaults to None.
        """
        super().__init__(
            name="cli",
            description="Executes shell commands on the local system"
        )
        
        self.working_dir = working_dir
        self.os_type = platform.system()
        
        logger.info(f"CLI Tool initialized (OS: {self.os_type})")
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a shell command.
        
        Args:
            params (Dict[str, Any]): Command parameters
                - command (str): Command to execute
                - timeout (int, optional): Timeout in seconds. Defaults to 60.
                - working_dir (str, optional): Working directory. Defaults to self.working_dir.
                - capture_output (bool, optional): Whether to capture output. Defaults to True.
            
        Returns:
            Dict[str, Any]: Execution result
                - status (str): "success" or "error"
                - stdout (str): Standard output (if capture_output is True)
                - stderr (str): Standard error (if capture_output is True)
                - exit_code (int): Exit code
                - command (str): Executed command
                - error (str): Error message (if status is "error")
        """
        self._set_status("running")
        
        # Extract parameters
        command = params.get("command")
        timeout = params.get("timeout", 60)
        working_dir = params.get("working_dir", self.working_dir)
        capture_output = params.get("capture_output", True)
        
        if not command:
            result = {
                "status": "error",
                "error": "No command provided",
                "command": command
            }
            self._set_result(result)
            self._set_status("idle")
            return result
        
        logger.info(f"Executing command: {command}")
        
        try:
            # Prepare command based on OS
            if self.os_type == "Windows":
                # For Windows, use shell=True to support built-in commands
                shell = True
                # No need to split the command on Windows with shell=True
                cmd = command
            else:
                # For Unix-like systems, split the command
                shell = False
                cmd = shlex.split(command)
            
            # Execute command
            process = subprocess.run(
                cmd,
                shell=shell,
                cwd=working_dir,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
            
            # Prepare result
            result = {
                "status": "success" if process.returncode == 0 else "error",
                "exit_code": process.returncode,
                "command": command
            }
            
            if capture_output:
                result["stdout"] = process.stdout
                result["stderr"] = process.stderr
            
            if process.returncode != 0:
                result["error"] = f"Command failed with exit code {process.returncode}"
                if capture_output:
                    result["error"] += f": {process.stderr}"
            
            self._set_result(result)
            self._set_status("idle")
            return result
            
        except subprocess.TimeoutExpired:
            result = {
                "status": "error",
                "error": f"Command timed out after {timeout} seconds",
                "command": command
            }
            self._set_result(result)
            self._set_status("idle")
            return result
            
        except Exception as e:
            result = {
                "status": "error",
                "error": str(e),
                "command": command
            }
            self._set_result(result)
            self._set_status("idle")
            return result
    
    def execute_script(self, script: str, script_name: str = "script", timeout: int = 60, working_dir: str = None) -> Dict[str, Any]:
        """
        Execute a multi-line script by saving it to a temporary file and running it.
        
        Args:
            script (str): Script content
            script_name (str, optional): Base name for the script file. Defaults to "script".
            timeout (int, optional): Timeout in seconds. Defaults to 60.
            working_dir (str, optional): Working directory. Defaults to self.working_dir.
            
        Returns:
            Dict[str, Any]: Execution result
        """
        self._set_status("running")
        
        working_dir = working_dir or self.working_dir
        
        if not working_dir:
            result = {
                "status": "error",
                "error": "No working directory provided for script execution"
            }
            self._set_result(result)
            self._set_status("idle")
            return result
        
        # Determine file extension based on OS
        if self.os_type == "Windows":
            script_file = f"{script_name}.bat"
            script = script.replace("\n", "\r\n")  # Ensure Windows line endings
        else:
            script_file = f"{script_name}.sh"
            script = "#!/bin/bash\n" + script
        
        script_path = os.path.join(working_dir, script_file)
        
        try:
            # Write script to file
            with open(script_path, "w") as f:
                f.write(script)
            
            # Make script executable on Unix-like systems
            if self.os_type != "Windows":
                os.chmod(script_path, 0o755)
            
            # Execute script
            command = script_path if self.os_type == "Windows" else f"./{script_file}"
            
            return self.execute({
                "command": command,
                "timeout": timeout,
                "working_dir": working_dir
            })
            
        except Exception as e:
            result = {
                "status": "error",
                "error": str(e),
                "script": script
            }
            self._set_result(result)
            self._set_status("idle")
            return result
        finally:
            # Clean up script file
            try:
                if os.path.exists(script_path):
                    os.remove(script_path)
            except Exception as e:
                logger.warning(f"Failed to remove script file {script_path}: {str(e)}")
    
    def list_directory(self, directory: str = None) -> Dict[str, Any]:
        """
        List contents of a directory.
        
        Args:
            directory (str, optional): Directory to list. Defaults to working_dir.
            
        Returns:
            Dict[str, Any]: Directory listing result
        """
        directory = directory or self.working_dir
        
        if not directory:
            result = {
                "status": "error",
                "error": "No directory provided"
            }
            return result
        
        if self.os_type == "Windows":
            command = f"dir /b {directory}"
        else:
            command = f"ls -la {directory}"
        
        return self.execute({"command": command})
