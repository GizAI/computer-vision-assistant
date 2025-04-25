#!/usr/bin/env python3
"""
File Tool for Autobot.
Handles file operations.
"""

import os
import shutil
import logging
import json
import csv
import yaml
from typing import Dict, Any, List, Optional, Union, BinaryIO

from autobot.tools.base import Tool

# Set up logging
logger = logging.getLogger(__name__)

class FileTool(Tool):
    """Tool for file operations."""
    
    def __init__(self, working_dir: str = None):
        """
        Initialize the file tool.
        
        Args:
            working_dir (str, optional): Working directory for file operations. Defaults to None.
        """
        super().__init__(
            name="file",
            description="Handles file operations (read, write, list, etc.)"
        )
        
        self.working_dir = working_dir
        
        logger.info(f"File Tool initialized")
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a file operation.
        
        Args:
            params (Dict[str, Any]): Operation parameters
                - operation (str): Operation to perform (read, write, append, list, delete, copy, move, exists)
                - Additional parameters specific to each operation
            
        Returns:
            Dict[str, Any]: Operation result
        """
        self._set_status("running")
        
        # Extract operation
        operation = params.get("operation")
        
        if not operation:
            result = {
                "status": "error",
                "error": "No operation provided"
            }
            self._set_result(result)
            self._set_status("idle")
            return result
        
        try:
            # Dispatch to appropriate method
            if operation == "read":
                result = self._read_file(params)
            elif operation == "write":
                result = self._write_file(params)
            elif operation == "append":
                result = self._append_file(params)
            elif operation == "list":
                result = self._list_directory(params)
            elif operation == "delete":
                result = self._delete_file(params)
            elif operation == "copy":
                result = self._copy_file(params)
            elif operation == "move":
                result = self._move_file(params)
            elif operation == "exists":
                result = self._file_exists(params)
            elif operation == "mkdir":
                result = self._make_directory(params)
            else:
                result = {
                    "status": "error",
                    "error": f"Unknown operation: {operation}"
                }
            
            self._set_result(result)
            self._set_status("idle")
            return result
            
        except Exception as e:
            result = {
                "status": "error",
                "error": str(e),
                "operation": operation
            }
            self._set_result(result)
            self._set_status("idle")
            return result
    
    def _resolve_path(self, path: str) -> str:
        """
        Resolve a path relative to the working directory.
        
        Args:
            path (str): Path to resolve
            
        Returns:
            str: Resolved path
        """
        if os.path.isabs(path):
            return path
        
        if self.working_dir:
            return os.path.join(self.working_dir, path)
        
        return path
    
    def _read_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Read a file.
        
        Args:
            params (Dict[str, Any]): Read parameters
                - path (str): Path to file
                - binary (bool, optional): Whether to read in binary mode. Defaults to False.
                - format (str, optional): Format to parse (json, csv, yaml). Defaults to None.
            
        Returns:
            Dict[str, Any]: Read result
        """
        path = params.get("path")
        binary = params.get("binary", False)
        format_type = params.get("format")
        
        if not path:
            return {
                "status": "error",
                "error": "No path provided"
            }
        
        resolved_path = self._resolve_path(path)
        
        if not os.path.exists(resolved_path):
            return {
                "status": "error",
                "error": f"File not found: {path}"
            }
        
        try:
            mode = "rb" if binary else "r"
            encoding = None if binary else "utf-8"
            
            with open(resolved_path, mode, encoding=encoding) as f:
                if binary:
                    content = f.read()
                    # Convert bytes to base64 for JSON serialization
                    import base64
                    content = base64.b64encode(content).decode("ascii")
                    return {
                        "status": "success",
                        "content": content,
                        "encoding": "base64",
                        "path": path
                    }
                
                if format_type == "json":
                    content = json.load(f)
                elif format_type == "csv":
                    reader = csv.DictReader(f)
                    content = list(reader)
                elif format_type == "yaml":
                    content = yaml.safe_load(f)
                else:
                    content = f.read()
                
                return {
                    "status": "success",
                    "content": content,
                    "path": path
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to read file: {str(e)}",
                "path": path
            }
    
    def _write_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Write to a file.
        
        Args:
            params (Dict[str, Any]): Write parameters
                - path (str): Path to file
                - content (Union[str, bytes, Dict, List]): Content to write
                - binary (bool, optional): Whether to write in binary mode. Defaults to False.
                - format (str, optional): Format to write (json, csv, yaml). Defaults to None.
                - overwrite (bool, optional): Whether to overwrite existing file. Defaults to True.
            
        Returns:
            Dict[str, Any]: Write result
        """
        path = params.get("path")
        content = params.get("content")
        binary = params.get("binary", False)
        format_type = params.get("format")
        overwrite = params.get("overwrite", True)
        
        if not path:
            return {
                "status": "error",
                "error": "No path provided"
            }
        
        if content is None:
            return {
                "status": "error",
                "error": "No content provided"
            }
        
        resolved_path = self._resolve_path(path)
        
        if os.path.exists(resolved_path) and not overwrite:
            return {
                "status": "error",
                "error": f"File already exists: {path}"
            }
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(resolved_path), exist_ok=True)
            
            mode = "wb" if binary else "w"
            encoding = None if binary else "utf-8"
            
            with open(resolved_path, mode, encoding=encoding) as f:
                if binary:
                    # If content is base64 encoded
                    if isinstance(content, str):
                        import base64
                        content = base64.b64decode(content)
                    f.write(content)
                elif format_type == "json":
                    json.dump(content, f, indent=2)
                elif format_type == "csv":
                    if not isinstance(content, list) or not content:
                        return {
                            "status": "error",
                            "error": "CSV content must be a non-empty list of dictionaries",
                            "path": path
                        }
                    
                    writer = csv.DictWriter(f, fieldnames=content[0].keys())
                    writer.writeheader()
                    writer.writerows(content)
                elif format_type == "yaml":
                    yaml.dump(content, f)
                else:
                    f.write(content)
            
            return {
                "status": "success",
                "message": f"File written successfully: {path}",
                "path": path
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to write file: {str(e)}",
                "path": path
            }
    
    def _append_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Append to a file.
        
        Args:
            params (Dict[str, Any]): Append parameters
                - path (str): Path to file
                - content (str): Content to append
                - binary (bool, optional): Whether to append in binary mode. Defaults to False.
            
        Returns:
            Dict[str, Any]: Append result
        """
        path = params.get("path")
        content = params.get("content")
        binary = params.get("binary", False)
        
        if not path:
            return {
                "status": "error",
                "error": "No path provided"
            }
        
        if content is None:
            return {
                "status": "error",
                "error": "No content provided"
            }
        
        resolved_path = self._resolve_path(path)
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(resolved_path), exist_ok=True)
            
            mode = "ab" if binary else "a"
            encoding = None if binary else "utf-8"
            
            with open(resolved_path, mode, encoding=encoding) as f:
                if binary and isinstance(content, str):
                    # If content is base64 encoded
                    import base64
                    content = base64.b64decode(content)
                
                f.write(content)
            
            return {
                "status": "success",
                "message": f"Content appended successfully: {path}",
                "path": path
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to append to file: {str(e)}",
                "path": path
            }
    
    def _list_directory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        List contents of a directory.
        
        Args:
            params (Dict[str, Any]): List parameters
                - path (str, optional): Path to directory. Defaults to working_dir.
                - recursive (bool, optional): Whether to list recursively. Defaults to False.
                - include_hidden (bool, optional): Whether to include hidden files. Defaults to False.
                - full_paths (bool, optional): Whether to return full paths. Defaults to False.
            
        Returns:
            Dict[str, Any]: List result
        """
        path = params.get("path", self.working_dir)
        recursive = params.get("recursive", False)
        include_hidden = params.get("include_hidden", False)
        full_paths = params.get("full_paths", False)
        
        if not path:
            return {
                "status": "error",
                "error": "No path provided"
            }
        
        resolved_path = self._resolve_path(path)
        
        if not os.path.exists(resolved_path):
            return {
                "status": "error",
                "error": f"Directory not found: {path}"
            }
        
        if not os.path.isdir(resolved_path):
            return {
                "status": "error",
                "error": f"Not a directory: {path}"
            }
        
        try:
            if recursive:
                items = []
                
                for root, dirs, files in os.walk(resolved_path):
                    # Skip hidden directories if not include_hidden
                    if not include_hidden:
                        dirs[:] = [d for d in dirs if not d.startswith(".")]
                    
                    for file in files:
                        if include_hidden or not file.startswith("."):
                            rel_path = os.path.relpath(os.path.join(root, file), resolved_path)
                            items.append({
                                "name": file,
                                "path": os.path.join(path, rel_path) if full_paths else rel_path,
                                "type": "file"
                            })
                    
                    for dir_name in dirs:
                        rel_path = os.path.relpath(os.path.join(root, dir_name), resolved_path)
                        items.append({
                            "name": dir_name,
                            "path": os.path.join(path, rel_path) if full_paths else rel_path,
                            "type": "directory"
                        })
            else:
                items = []
                
                for item in os.listdir(resolved_path):
                    if include_hidden or not item.startswith("."):
                        item_path = os.path.join(resolved_path, item)
                        items.append({
                            "name": item,
                            "path": os.path.join(path, item) if full_paths else item,
                            "type": "directory" if os.path.isdir(item_path) else "file"
                        })
            
            return {
                "status": "success",
                "items": items,
                "count": len(items),
                "path": path
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to list directory: {str(e)}",
                "path": path
            }
    
    def _delete_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delete a file or directory.
        
        Args:
            params (Dict[str, Any]): Delete parameters
                - path (str): Path to file or directory
                - recursive (bool, optional): Whether to delete directory recursively. Defaults to False.
            
        Returns:
            Dict[str, Any]: Delete result
        """
        path = params.get("path")
        recursive = params.get("recursive", False)
        
        if not path:
            return {
                "status": "error",
                "error": "No path provided"
            }
        
        resolved_path = self._resolve_path(path)
        
        if not os.path.exists(resolved_path):
            return {
                "status": "error",
                "error": f"File or directory not found: {path}"
            }
        
        try:
            if os.path.isdir(resolved_path):
                if recursive:
                    shutil.rmtree(resolved_path)
                else:
                    os.rmdir(resolved_path)
            else:
                os.remove(resolved_path)
            
            return {
                "status": "success",
                "message": f"Deleted successfully: {path}",
                "path": path
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to delete: {str(e)}",
                "path": path
            }
    
    def _copy_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Copy a file or directory.
        
        Args:
            params (Dict[str, Any]): Copy parameters
                - source (str): Source path
                - destination (str): Destination path
                - overwrite (bool, optional): Whether to overwrite existing destination. Defaults to False.
            
        Returns:
            Dict[str, Any]: Copy result
        """
        source = params.get("source")
        destination = params.get("destination")
        overwrite = params.get("overwrite", False)
        
        if not source or not destination:
            return {
                "status": "error",
                "error": "Source and destination paths are required"
            }
        
        resolved_source = self._resolve_path(source)
        resolved_destination = self._resolve_path(destination)
        
        if not os.path.exists(resolved_source):
            return {
                "status": "error",
                "error": f"Source not found: {source}"
            }
        
        if os.path.exists(resolved_destination) and not overwrite:
            return {
                "status": "error",
                "error": f"Destination already exists: {destination}"
            }
        
        try:
            # Create destination directory if it doesn't exist
            os.makedirs(os.path.dirname(resolved_destination), exist_ok=True)
            
            if os.path.isdir(resolved_source):
                if os.path.exists(resolved_destination):
                    shutil.rmtree(resolved_destination)
                shutil.copytree(resolved_source, resolved_destination)
            else:
                shutil.copy2(resolved_source, resolved_destination)
            
            return {
                "status": "success",
                "message": f"Copied {source} to {destination}",
                "source": source,
                "destination": destination
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to copy: {str(e)}",
                "source": source,
                "destination": destination
            }
    
    def _move_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Move a file or directory.
        
        Args:
            params (Dict[str, Any]): Move parameters
                - source (str): Source path
                - destination (str): Destination path
                - overwrite (bool, optional): Whether to overwrite existing destination. Defaults to False.
            
        Returns:
            Dict[str, Any]: Move result
        """
        source = params.get("source")
        destination = params.get("destination")
        overwrite = params.get("overwrite", False)
        
        if not source or not destination:
            return {
                "status": "error",
                "error": "Source and destination paths are required"
            }
        
        resolved_source = self._resolve_path(source)
        resolved_destination = self._resolve_path(destination)
        
        if not os.path.exists(resolved_source):
            return {
                "status": "error",
                "error": f"Source not found: {source}"
            }
        
        if os.path.exists(resolved_destination) and not overwrite:
            return {
                "status": "error",
                "error": f"Destination already exists: {destination}"
            }
        
        try:
            # Create destination directory if it doesn't exist
            os.makedirs(os.path.dirname(resolved_destination), exist_ok=True)
            
            if os.path.exists(resolved_destination) and overwrite:
                if os.path.isdir(resolved_destination):
                    shutil.rmtree(resolved_destination)
                else:
                    os.remove(resolved_destination)
            
            shutil.move(resolved_source, resolved_destination)
            
            return {
                "status": "success",
                "message": f"Moved {source} to {destination}",
                "source": source,
                "destination": destination
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to move: {str(e)}",
                "source": source,
                "destination": destination
            }
    
    def _file_exists(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if a file or directory exists.
        
        Args:
            params (Dict[str, Any]): Exists parameters
                - path (str): Path to check
            
        Returns:
            Dict[str, Any]: Exists result
        """
        path = params.get("path")
        
        if not path:
            return {
                "status": "error",
                "error": "No path provided"
            }
        
        resolved_path = self._resolve_path(path)
        
        exists = os.path.exists(resolved_path)
        is_file = os.path.isfile(resolved_path) if exists else False
        is_dir = os.path.isdir(resolved_path) if exists else False
        
        return {
            "status": "success",
            "exists": exists,
            "is_file": is_file,
            "is_directory": is_dir,
            "path": path
        }
    
    def _make_directory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a directory.
        
        Args:
            params (Dict[str, Any]): Mkdir parameters
                - path (str): Path to create
                - parents (bool, optional): Whether to create parent directories. Defaults to True.
            
        Returns:
            Dict[str, Any]: Mkdir result
        """
        path = params.get("path")
        parents = params.get("parents", True)
        
        if not path:
            return {
                "status": "error",
                "error": "No path provided"
            }
        
        resolved_path = self._resolve_path(path)
        
        if os.path.exists(resolved_path):
            if os.path.isdir(resolved_path):
                return {
                    "status": "success",
                    "message": f"Directory already exists: {path}",
                    "path": path
                }
            else:
                return {
                    "status": "error",
                    "error": f"Path exists but is not a directory: {path}",
                    "path": path
                }
        
        try:
            if parents:
                os.makedirs(resolved_path)
            else:
                os.mkdir(resolved_path)
            
            return {
                "status": "success",
                "message": f"Directory created: {path}",
                "path": path
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to create directory: {str(e)}",
                "path": path
            }
