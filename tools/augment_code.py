#!/usr/bin/env python3
"""
Augment Code Tool for Autobot.
Interfaces with the Augment Code VS Code extension.
"""

import os
import json
import logging
import time
import subprocess
from typing import Dict, Any, List, Optional

from autobot.tools.base import Tool

# Set up logging
logger = logging.getLogger(__name__)

class AugmentCodeTool(Tool):
    """Tool for interfacing with Augment Code VS Code extension."""
    
    def __init__(self, vscode_path: Optional[str] = None):
        """
        Initialize the Augment Code tool.
        
        Args:
            vscode_path (str, optional): Path to VS Code executable. Defaults to None.
        """
        super().__init__(
            name="augment_code",
            description="Interfaces with the Augment Code VS Code extension"
        )
        
        # Find VS Code executable
        self.vscode_path = vscode_path or self._find_vscode()
        
        # Check if VS Code is available
        self.vscode_available = bool(self.vscode_path)
        
        # Check if Augment Code extension is installed
        self.augment_code_available = self._check_augment_code()
        
        if self.vscode_available and self.augment_code_available:
            logger.info("Augment Code Tool initialized successfully")
        else:
            if not self.vscode_available:
                logger.error("VS Code not found. Please provide the path to VS Code executable.")
            if not self.augment_code_available:
                logger.error("Augment Code extension not found. Please install it in VS Code.")
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an Augment Code command.
        
        Args:
            params (Dict[str, Any]): Command parameters
                - action (str): Action to perform (open_file, ask_question, etc.)
                - Additional parameters specific to each action
            
        Returns:
            Dict[str, Any]: Execution result
        """
        self._set_status("running")
        
        if not self.vscode_available:
            result = {
                "status": "error",
                "error": "VS Code is not available"
            }
            self._set_result(result)
            self._set_status("idle")
            return result
        
        if not self.augment_code_available:
            result = {
                "status": "error",
                "error": "Augment Code extension is not available"
            }
            self._set_result(result)
            self._set_status("idle")
            return result
        
        # Extract action
        action = params.get("action")
        
        if not action:
            result = {
                "status": "error",
                "error": "No action provided"
            }
            self._set_result(result)
            self._set_status("idle")
            return result
        
        try:
            # Dispatch to appropriate method
            if action == "open_file":
                result = self._open_file(params)
            elif action == "ask_question":
                result = self._ask_question(params)
            elif action == "execute_command":
                result = self._execute_command(params)
            elif action == "get_status":
                result = self._get_augment_status(params)
            else:
                result = {
                    "status": "error",
                    "error": f"Unknown action: {action}"
                }
            
            self._set_result(result)
            self._set_status("idle")
            return result
            
        except Exception as e:
            result = {
                "status": "error",
                "error": str(e),
                "action": action
            }
            self._set_result(result)
            self._set_status("idle")
            return result
    
    def _find_vscode(self) -> Optional[str]:
        """
        Find the VS Code executable.
        
        Returns:
            Optional[str]: Path to VS Code executable
        """
        # Common paths for VS Code
        common_paths = []
        
        # Windows
        if os.name == "nt":
            common_paths.extend([
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
                os.path.expandvars(r"%ProgramFiles%\Microsoft VS Code\Code.exe"),
                os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft VS Code\Code.exe")
            ])
        # macOS
        elif os.name == "posix" and os.uname().sysname == "Darwin":
            common_paths.extend([
                "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code",
                os.path.expanduser("~/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code")
            ])
        # Linux
        elif os.name == "posix":
            common_paths.extend([
                "/usr/bin/code",
                "/usr/local/bin/code",
                os.path.expanduser("~/.local/bin/code")
            ])
        
        # Check if VS Code is in PATH
        try:
            if os.name == "nt":
                result = subprocess.run(["where", "code"], capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip().split("\n")[0]
            else:
                result = subprocess.run(["which", "code"], capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip()
        except:
            pass
        
        # Check common paths
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _check_augment_code(self) -> bool:
        """
        Check if Augment Code extension is installed.
        
        Returns:
            bool: Whether Augment Code is available
        """
        if not self.vscode_available:
            return False
        
        try:
            # List installed extensions
            result = subprocess.run(
                [self.vscode_path, "--list-extensions"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                extensions = result.stdout.strip().split("\n")
                
                # Check for Augment Code extension
                # Note: This is a placeholder, replace with actual extension ID
                augment_code_id = "augmentcode.augmentcode"
                
                return augment_code_id in extensions
            
            return False
        except:
            return False
    
    def _open_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Open a file in VS Code.
        
        Args:
            params (Dict[str, Any]): Parameters
                - file_path (str): Path to file
                - line (int, optional): Line number to navigate to. Defaults to None.
                - column (int, optional): Column number to navigate to. Defaults to None.
            
        Returns:
            Dict[str, Any]: Result
        """
        file_path = params.get("file_path")
        line = params.get("line")
        column = params.get("column")
        
        if not file_path:
            return {
                "status": "error",
                "error": "No file path provided"
            }
        
        # Construct command
        command = [self.vscode_path, file_path]
        
        # Add line and column if provided
        if line is not None:
            if column is not None:
                command.append(f"--goto={file_path}:{line}:{column}")
            else:
                command.append(f"--goto={file_path}:{line}")
        
        try:
            # Execute command
            subprocess.Popen(command)
            
            return {
                "status": "success",
                "message": f"Opened file: {file_path}",
                "file_path": file_path,
                "line": line,
                "column": column
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to open file: {str(e)}"
            }
    
    def _ask_question(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ask a question to Augment Code.
        
        Args:
            params (Dict[str, Any]): Parameters
                - question (str): Question to ask
                - file_path (str, optional): Path to file for context. Defaults to None.
                - wait_for_response (bool, optional): Whether to wait for response. Defaults to False.
                - timeout (int, optional): Timeout in seconds. Defaults to 60.
            
        Returns:
            Dict[str, Any]: Result
        """
        question = params.get("question")
        file_path = params.get("file_path")
        wait_for_response = params.get("wait_for_response", False)
        timeout = params.get("timeout", 60)
        
        if not question:
            return {
                "status": "error",
                "error": "No question provided"
            }
        
        # Since there's no direct API to Augment Code, we'll use a workaround
        # This is a placeholder implementation that simulates asking a question
        
        # First, open the file if provided
        if file_path:
            self._open_file({"file_path": file_path})
            time.sleep(1)  # Wait for file to open
        
        # Execute the "Ask Augment" command
        # Note: This is a placeholder, replace with actual command ID
        command_result = self._execute_command({
            "command": "augmentcode.askAugment",
            "args": [question]
        })
        
        if command_result.get("status") != "success":
            return command_result
        
        # If not waiting for response, return immediately
        if not wait_for_response:
            return {
                "status": "success",
                "message": "Question sent to Augment Code",
                "question": question,
                "file_path": file_path
            }
        
        # Wait for response
        # Note: This is a placeholder, replace with actual implementation
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self._get_augment_status({})
            
            if status.get("status") == "success" and status.get("augment_status") == "idle":
                # Augment has finished processing
                return {
                    "status": "success",
                    "message": "Augment Code has processed the question",
                    "question": question,
                    "file_path": file_path,
                    "response": "Response not available through API"  # Placeholder
                }
            
            time.sleep(1)
        
        return {
            "status": "error",
            "error": f"Timed out waiting for Augment Code response after {timeout} seconds",
            "question": question,
            "file_path": file_path
        }
    
    def _execute_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a VS Code command.
        
        Args:
            params (Dict[str, Any]): Parameters
                - command (str): Command ID
                - args (List[Any], optional): Command arguments. Defaults to None.
            
        Returns:
            Dict[str, Any]: Result
        """
        command = params.get("command")
        args = params.get("args", [])
        
        if not command:
            return {
                "status": "error",
                "error": "No command provided"
            }
        
        try:
            # Construct command
            vscode_command = [self.vscode_path, "--command", command]
            
            # Add arguments if provided
            if args:
                # Convert args to JSON string
                args_json = json.dumps(args)
                vscode_command.extend(["--args", args_json])
            
            # Execute command
            subprocess.Popen(vscode_command)
            
            return {
                "status": "success",
                "message": f"Executed command: {command}",
                "command": command,
                "args": args
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to execute command: {str(e)}"
            }
    
    def _get_augment_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get Augment Code status.
        
        Args:
            params (Dict[str, Any]): Parameters
            
        Returns:
            Dict[str, Any]: Result
        """
        # Note: This is a placeholder, replace with actual implementation
        # In a real implementation, this would query the Augment Code extension status
        
        return {
            "status": "success",
            "augment_status": "idle",  # Placeholder, could be "idle", "processing", "waiting_for_input"
            "message": "Augment Code status retrieved"
        }
