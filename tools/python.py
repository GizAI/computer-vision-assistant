#!/usr/bin/env python3
"""
Python Executor Tool for Autobot.
Executes Python code snippets or scripts.
"""

import os
import sys
import logging
import tempfile
import traceback
from io import StringIO
from typing import Dict, Any, List, Optional

from autobot.tools.base import Tool

# Set up logging
logger = logging.getLogger(__name__)

class PythonExecutorTool(Tool):
    """Tool for executing Python code."""
    
    def __init__(self, working_dir: str = None):
        """
        Initialize the Python executor tool.
        
        Args:
            working_dir (str, optional): Working directory for scripts. Defaults to None.
        """
        super().__init__(
            name="python",
            description="Executes Python code snippets or scripts"
        )
        
        self.working_dir = working_dir
        
        logger.info(f"Python Executor Tool initialized")
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Python code.
        
        Args:
            params (Dict[str, Any]): Execution parameters
                - code (str): Python code to execute
                - save_to_file (bool, optional): Whether to save code to a file. Defaults to False.
                - filename (str, optional): Filename to save code to. Required if save_to_file is True.
                - working_dir (str, optional): Working directory. Defaults to self.working_dir.
                - timeout (int, optional): Timeout in seconds. Defaults to 30.
                - use_subprocess (bool, optional): Whether to use subprocess. Defaults to False.
            
        Returns:
            Dict[str, Any]: Execution result
                - status (str): "success" or "error"
                - output (str): Standard output
                - error (str): Error message (if status is "error")
                - filename (str): Filename (if save_to_file is True)
        """
        self._set_status("running")
        
        # Extract parameters
        code = params.get("code")
        save_to_file = params.get("save_to_file", False)
        filename = params.get("filename")
        working_dir = params.get("working_dir", self.working_dir)
        timeout = params.get("timeout", 30)
        use_subprocess = params.get("use_subprocess", False)
        
        if not code:
            result = {
                "status": "error",
                "error": "No code provided"
            }
            self._set_result(result)
            self._set_status("idle")
            return result
        
        # If saving to file
        if save_to_file:
            if not filename:
                result = {
                    "status": "error",
                    "error": "No filename provided for saving code"
                }
                self._set_result(result)
                self._set_status("idle")
                return result
            
            if not working_dir:
                result = {
                    "status": "error",
                    "error": "No working directory provided for saving code"
                }
                self._set_result(result)
                self._set_status("idle")
                return result
            
            file_path = os.path.join(working_dir, filename)
            
            try:
                with open(file_path, "w") as f:
                    f.write(code)
                
                logger.info(f"Saved Python code to {file_path}")
                
                result = {
                    "status": "success",
                    "message": f"Code saved to {filename}",
                    "filename": filename,
                    "path": file_path
                }
                
                # If only saving, not executing
                if not use_subprocess:
                    self._set_result(result)
                    self._set_status("idle")
                    return result
                
            except Exception as e:
                result = {
                    "status": "error",
                    "error": f"Failed to save code to file: {str(e)}"
                }
                self._set_result(result)
                self._set_status("idle")
                return result
        
        # Execute code
        if use_subprocess:
            # Use CLI tool to execute Python script
            from autobot.tools.cli import CLITool
            
            cli_tool = CLITool(working_dir=working_dir)
            
            if save_to_file:
                # Execute saved file
                result = cli_tool.execute({
                    "command": f"python {filename}",
                    "timeout": timeout,
                    "working_dir": working_dir
                })
            else:
                # Save to temporary file and execute
                with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as temp_file:
                    temp_file.write(code)
                    temp_path = temp_file.name
                
                try:
                    result = cli_tool.execute({
                        "command": f"python {temp_path}",
                        "timeout": timeout,
                        "working_dir": working_dir
                    })
                finally:
                    # Clean up temporary file
                    try:
                        os.remove(temp_path)
                    except:
                        pass
            
            self._set_result(result)
            self._set_status("idle")
            return result
            
        else:
            # Execute in current process
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            old_cwd = os.getcwd()
            
            redirected_output = StringIO()
            redirected_error = StringIO()
            
            sys.stdout = redirected_output
            sys.stderr = redirected_error
            
            if working_dir:
                os.chdir(working_dir)
            
            try:
                # Execute code
                exec(code, {})
                
                output = redirected_output.getvalue()
                error = redirected_error.getvalue()
                
                result = {
                    "status": "success",
                    "output": output
                }
                
                if error:
                    result["stderr"] = error
                
                if save_to_file:
                    result["filename"] = filename
                    result["path"] = file_path
                
                self._set_result(result)
                self._set_status("idle")
                return result
                
            except Exception as e:
                error = redirected_error.getvalue()
                if not error:
                    error = traceback.format_exc()
                
                result = {
                    "status": "error",
                    "error": str(e),
                    "traceback": error
                }
                
                if save_to_file:
                    result["filename"] = filename
                    result["path"] = file_path
                
                self._set_result(result)
                self._set_status("idle")
                return result
                
            finally:
                # Restore stdout, stderr, and cwd
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                
                if working_dir:
                    os.chdir(old_cwd)
    
    def execute_file(self, file_path: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute a Python file.
        
        Args:
            file_path (str): Path to Python file
            timeout (int, optional): Timeout in seconds. Defaults to 30.
            
        Returns:
            Dict[str, Any]: Execution result
        """
        if not os.path.exists(file_path):
            result = {
                "status": "error",
                "error": f"File not found: {file_path}"
            }
            return result
        
        # Use CLI tool to execute Python script
        from autobot.tools.cli import CLITool
        
        cli_tool = CLITool(working_dir=os.path.dirname(file_path))
        
        return cli_tool.execute({
            "command": f"python {os.path.basename(file_path)}",
            "timeout": timeout
        })
