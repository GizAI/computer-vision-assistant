#!/usr/bin/env python3
"""
File Manager for Autobot.
Handles file I/O operations.
"""

import os
import json
import yaml
import logging
import shutil
from typing import Dict, Any, List, Optional, Union, BinaryIO

# Set up logging
logger = logging.getLogger(__name__)

class FileManager:
    """Manager for file operations."""
    
    @staticmethod
    def read_file(path: str, binary: bool = False) -> Union[str, bytes]:
        """
        Read a file.
        
        Args:
            path (str): Path to file
            binary (bool, optional): Whether to read in binary mode. Defaults to False.
            
        Returns:
            Union[str, bytes]: File content
        """
        try:
            mode = "rb" if binary else "r"
            encoding = None if binary else "utf-8"
            
            with open(path, mode, encoding=encoding) as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"Failed to read file {path}: {str(e)}")
            raise
    
    @staticmethod
    def write_file(path: str, content: Union[str, bytes], binary: bool = False) -> None:
        """
        Write to a file.
        
        Args:
            path (str): Path to file
            content (Union[str, bytes]): Content to write
            binary (bool, optional): Whether to write in binary mode. Defaults to False.
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            mode = "wb" if binary else "w"
            encoding = None if binary else "utf-8"
            
            with open(path, mode, encoding=encoding) as f:
                f.write(content)
                
        except Exception as e:
            logger.error(f"Failed to write file {path}: {str(e)}")
            raise
    
    @staticmethod
    def append_file(path: str, content: Union[str, bytes], binary: bool = False) -> None:
        """
        Append to a file.
        
        Args:
            path (str): Path to file
            content (Union[str, bytes]): Content to append
            binary (bool, optional): Whether to append in binary mode. Defaults to False.
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            mode = "ab" if binary else "a"
            encoding = None if binary else "utf-8"
            
            with open(path, mode, encoding=encoding) as f:
                f.write(content)
                
        except Exception as e:
            logger.error(f"Failed to append to file {path}: {str(e)}")
            raise
    
    @staticmethod
    def read_json(path: str) -> Dict[str, Any]:
        """
        Read a JSON file.
        
        Args:
            path (str): Path to file
            
        Returns:
            Dict[str, Any]: JSON content
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Failed to read JSON file {path}: {str(e)}")
            raise
    
    @staticmethod
    def write_json(path: str, content: Dict[str, Any], indent: int = 2) -> None:
        """
        Write to a JSON file.
        
        Args:
            path (str): Path to file
            content (Dict[str, Any]): Content to write
            indent (int, optional): JSON indentation. Defaults to 2.
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            with open(path, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=indent)
                
        except Exception as e:
            logger.error(f"Failed to write JSON file {path}: {str(e)}")
            raise
    
    @staticmethod
    def read_yaml(path: str) -> Dict[str, Any]:
        """
        Read a YAML file.
        
        Args:
            path (str): Path to file
            
        Returns:
            Dict[str, Any]: YAML content
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
                
        except Exception as e:
            logger.error(f"Failed to read YAML file {path}: {str(e)}")
            raise
    
    @staticmethod
    def write_yaml(path: str, content: Dict[str, Any]) -> None:
        """
        Write to a YAML file.
        
        Args:
            path (str): Path to file
            content (Dict[str, Any]): Content to write
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(content, f)
                
        except Exception as e:
            logger.error(f"Failed to write YAML file {path}: {str(e)}")
            raise
    
    @staticmethod
    def list_directory(path: str, recursive: bool = False, include_hidden: bool = False) -> List[Dict[str, Any]]:
        """
        List contents of a directory.
        
        Args:
            path (str): Path to directory
            recursive (bool, optional): Whether to list recursively. Defaults to False.
            include_hidden (bool, optional): Whether to include hidden files. Defaults to False.
            
        Returns:
            List[Dict[str, Any]]: List of items
        """
        try:
            if recursive:
                items = []
                
                for root, dirs, files in os.walk(path):
                    # Skip hidden directories if not include_hidden
                    if not include_hidden:
                        dirs[:] = [d for d in dirs if not d.startswith(".")]
                    
                    for file in files:
                        if include_hidden or not file.startswith("."):
                            rel_path = os.path.relpath(os.path.join(root, file), path)
                            items.append({
                                "name": file,
                                "path": rel_path,
                                "type": "file"
                            })
                    
                    for dir_name in dirs:
                        rel_path = os.path.relpath(os.path.join(root, dir_name), path)
                        items.append({
                            "name": dir_name,
                            "path": rel_path,
                            "type": "directory"
                        })
            else:
                items = []
                
                for item in os.listdir(path):
                    if include_hidden or not item.startswith("."):
                        item_path = os.path.join(path, item)
                        items.append({
                            "name": item,
                            "path": item,
                            "type": "directory" if os.path.isdir(item_path) else "file"
                        })
            
            return items
            
        except Exception as e:
            logger.error(f"Failed to list directory {path}: {str(e)}")
            raise
    
    @staticmethod
    def delete_file(path: str) -> None:
        """
        Delete a file.
        
        Args:
            path (str): Path to file
        """
        try:
            if os.path.exists(path):
                if os.path.isdir(path):
                    raise ValueError(f"Path is a directory: {path}")
                
                os.remove(path)
                
        except Exception as e:
            logger.error(f"Failed to delete file {path}: {str(e)}")
            raise
    
    @staticmethod
    def delete_directory(path: str, recursive: bool = False) -> None:
        """
        Delete a directory.
        
        Args:
            path (str): Path to directory
            recursive (bool, optional): Whether to delete recursively. Defaults to False.
        """
        try:
            if os.path.exists(path):
                if not os.path.isdir(path):
                    raise ValueError(f"Path is not a directory: {path}")
                
                if recursive:
                    shutil.rmtree(path)
                else:
                    os.rmdir(path)
                
        except Exception as e:
            logger.error(f"Failed to delete directory {path}: {str(e)}")
            raise
    
    @staticmethod
    def copy_file(source: str, destination: str) -> None:
        """
        Copy a file.
        
        Args:
            source (str): Source path
            destination (str): Destination path
        """
        try:
            # Create destination directory if it doesn't exist
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            shutil.copy2(source, destination)
            
        except Exception as e:
            logger.error(f"Failed to copy file from {source} to {destination}: {str(e)}")
            raise
    
    @staticmethod
    def move_file(source: str, destination: str) -> None:
        """
        Move a file.
        
        Args:
            source (str): Source path
            destination (str): Destination path
        """
        try:
            # Create destination directory if it doesn't exist
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            shutil.move(source, destination)
            
        except Exception as e:
            logger.error(f"Failed to move file from {source} to {destination}: {str(e)}")
            raise
    
    @staticmethod
    def file_exists(path: str) -> bool:
        """
        Check if a file exists.
        
        Args:
            path (str): Path to file
            
        Returns:
            bool: Whether the file exists
        """
        return os.path.exists(path) and os.path.isfile(path)
    
    @staticmethod
    def directory_exists(path: str) -> bool:
        """
        Check if a directory exists.
        
        Args:
            path (str): Path to directory
            
        Returns:
            bool: Whether the directory exists
        """
        return os.path.exists(path) and os.path.isdir(path)
    
    @staticmethod
    def make_directory(path: str) -> None:
        """
        Create a directory.
        
        Args:
            path (str): Path to directory
        """
        try:
            os.makedirs(path, exist_ok=True)
            
        except Exception as e:
            logger.error(f"Failed to create directory {path}: {str(e)}")
            raise
