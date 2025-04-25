#!/usr/bin/env python3
"""
Memory & Context Manager for Autobot.
Manages project-related information and constructs LLM prompts.
"""

import os
import json
import sqlite3
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
import chromadb
from chromadb.config import Settings

from autobot.core.llm import LLMInterface

# Set up logging
logger = logging.getLogger(__name__)

class MemoryManager:
    """Manager for Autobot memory and context."""
    
    def __init__(self, project, llm_interface: Optional[LLMInterface] = None):
        """
        Initialize the memory manager.
        
        Args:
            project: Project instance
            llm_interface (LLMInterface, optional): LLM interface. Defaults to None.
        """
        self.project = project
        self.llm_interface = llm_interface or LLMInterface()
        
        # Initialize SQLite database for chat history
        self._init_chat_db()
        
        # Initialize vector database
        self._init_vector_db()
        
        logger.info(f"Memory Manager initialized for project: {project.name}")
    
    def _init_chat_db(self) -> None:
        """Initialize SQLite database for chat history."""
        conn = sqlite3.connect(self.project.chat_db_path)
        cursor = conn.cursor()
        
        # Create messages table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            sender TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT
        )
        ''')
        
        # Create execution_logs table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            task_id TEXT,
            tool TEXT NOT NULL,
            params TEXT,
            status TEXT NOT NULL,
            output TEXT,
            metadata TEXT
        )
        ''')
        
        # Create insights table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            task_id TEXT,
            content TEXT NOT NULL,
            metadata TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def _init_vector_db(self) -> None:
        """Initialize vector database."""
        self.chroma_client = chromadb.PersistentClient(
            path=self.project.vector_db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create collections if they don't exist
        self.file_collection = self.chroma_client.get_or_create_collection(
            name="files",
            metadata={"project": self.project.name}
        )
        
        self.chat_collection = self.chroma_client.get_or_create_collection(
            name="chat",
            metadata={"project": self.project.name}
        )
        
        self.web_collection = self.chroma_client.get_or_create_collection(
            name="web",
            metadata={"project": self.project.name}
        )
        
        self.insight_collection = self.chroma_client.get_or_create_collection(
            name="insights",
            metadata={"project": self.project.name}
        )
    
    def add_message(self, sender: str, content: str, metadata: Dict[str, Any] = None) -> int:
        """
        Add a message to the chat history.
        
        Args:
            sender (str): Message sender (user or autobot)
            content (str): Message content
            metadata (Dict[str, Any], optional): Additional metadata. Defaults to None.
            
        Returns:
            int: Message ID
        """
        conn = sqlite3.connect(self.project.chat_db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        metadata_json = json.dumps(metadata or {})
        
        cursor.execute(
            "INSERT INTO messages (timestamp, sender, content, metadata) VALUES (?, ?, ?, ?)",
            (timestamp, sender, content, metadata_json)
        )
        
        message_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        # Add to vector database
        self._add_to_vector_db(
            collection=self.chat_collection,
            text=content,
            metadata={
                "id": str(message_id),
                "timestamp": timestamp,
                "sender": sender,
                **(metadata or {})
            }
        )
        
        return message_id
    
    def get_messages(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get recent messages from chat history.
        
        Args:
            limit (int, optional): Maximum number of messages. Defaults to 10.
            offset (int, optional): Offset for pagination. Defaults to 0.
            
        Returns:
            List[Dict[str, Any]]: List of message dictionaries
        """
        conn = sqlite3.connect(self.project.chat_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM messages ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        
        messages = []
        for row in cursor.fetchall():
            message = dict(row)
            try:
                message["metadata"] = json.loads(message["metadata"])
            except json.JSONDecodeError:
                message["metadata"] = {}
            messages.append(message)
        
        conn.close()
        
        # Reverse to get chronological order
        return list(reversed(messages))
    
    def add_execution_log(self, 
                         tool: str, 
                         params: Dict[str, Any], 
                         status: str, 
                         output: Any = None, 
                         task_id: str = None, 
                         metadata: Dict[str, Any] = None) -> int:
        """
        Add an execution log entry.
        
        Args:
            tool (str): Tool used
            params (Dict[str, Any]): Tool parameters
            status (str): Execution status (success, error, etc.)
            output (Any, optional): Tool output. Defaults to None.
            task_id (str, optional): Associated task ID. Defaults to None.
            metadata (Dict[str, Any], optional): Additional metadata. Defaults to None.
            
        Returns:
            int: Log entry ID
        """
        conn = sqlite3.connect(self.project.chat_db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        params_json = json.dumps(params)
        output_json = json.dumps(output) if output is not None else None
        metadata_json = json.dumps(metadata or {})
        
        cursor.execute(
            "INSERT INTO execution_logs (timestamp, task_id, tool, params, status, output, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (timestamp, task_id, tool, params_json, status, output_json, metadata_json)
        )
        
        log_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return log_id
    
    def add_insight(self, content: str, task_id: str = None, metadata: Dict[str, Any] = None) -> int:
        """
        Add an insight from reflection.
        
        Args:
            content (str): Insight content
            task_id (str, optional): Associated task ID. Defaults to None.
            metadata (Dict[str, Any], optional): Additional metadata. Defaults to None.
            
        Returns:
            int: Insight ID
        """
        conn = sqlite3.connect(self.project.chat_db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        metadata_json = json.dumps(metadata or {})
        
        cursor.execute(
            "INSERT INTO insights (timestamp, task_id, content, metadata) VALUES (?, ?, ?, ?)",
            (timestamp, task_id, content, metadata_json)
        )
        
        insight_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        # Add to vector database
        self._add_to_vector_db(
            collection=self.insight_collection,
            text=content,
            metadata={
                "id": str(insight_id),
                "timestamp": timestamp,
                "task_id": task_id,
                **(metadata or {})
            }
        )
        
        return insight_id
    
    def _add_to_vector_db(self, collection, text: str, metadata: Dict[str, Any]) -> None:
        """
        Add text to vector database.
        
        Args:
            collection: ChromaDB collection
            text (str): Text to embed
            metadata (Dict[str, Any]): Metadata for the embedding
        """
        # Generate embedding
        embedding = self.llm_interface.get_embedding(text)
        
        # Add to collection
        collection.add(
            ids=[metadata.get("id", str(int(time.time() * 1000)))],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[text]
        )
    
    def add_file_to_memory(self, file_path: str, content: str = None) -> None:
        """
        Add a file to memory.
        
        Args:
            file_path (str): Path to the file
            content (str, optional): File content. If None, will read from file. Defaults to None.
        """
        # Get file content if not provided
        if content is None:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                logger.error(f"Failed to read file {file_path}: {str(e)}")
                return
        
        # Get relative path to project
        rel_path = os.path.relpath(file_path, self.project.path)
        
        # Add to vector database
        self._add_to_vector_db(
            collection=self.file_collection,
            text=content,
            metadata={
                "id": rel_path,
                "path": rel_path,
                "timestamp": datetime.now().isoformat(),
                "type": "file"
            }
        )
    
    def add_web_content(self, url: str, title: str, content: str) -> None:
        """
        Add web content to memory.
        
        Args:
            url (str): Web page URL
            title (str): Web page title
            content (str): Web page content
        """
        # Add to vector database
        self._add_to_vector_db(
            collection=self.web_collection,
            text=content,
            metadata={
                "id": url,
                "url": url,
                "title": title,
                "timestamp": datetime.now().isoformat(),
                "type": "web"
            }
        )
    
    def search_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search memory for relevant context.
        
        Args:
            query (str): Search query
            limit (int, optional): Maximum number of results. Defaults to 5.
            
        Returns:
            List[Dict[str, Any]]: List of search results
        """
        # Generate embedding for query
        query_embedding = self.llm_interface.get_embedding(query)
        
        # Search each collection
        file_results = self._search_collection(self.file_collection, query_embedding, limit)
        chat_results = self._search_collection(self.chat_collection, query_embedding, limit)
        web_results = self._search_collection(self.web_collection, query_embedding, limit)
        insight_results = self._search_collection(self.insight_collection, query_embedding, limit)
        
        # Combine and sort results by distance
        all_results = file_results + chat_results + web_results + insight_results
        all_results.sort(key=lambda x: x["distance"])
        
        # Return top results
        return all_results[:limit]
    
    def _search_collection(self, collection, query_embedding: List[float], limit: int) -> List[Dict[str, Any]]:
        """
        Search a collection for relevant context.
        
        Args:
            collection: ChromaDB collection
            query_embedding (List[float]): Query embedding
            limit (int): Maximum number of results
            
        Returns:
            List[Dict[str, Any]]: List of search results
        """
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=limit
        )
        
        formatted_results = []
        for i in range(len(results["ids"][0])):
            formatted_results.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if "distances" in results else 0,
                "collection": collection.name
            })
        
        return formatted_results
    
    def get_plan_content(self) -> str:
        """
        Get the current plan content.
        
        Returns:
            str: Plan content
        """
        try:
            with open(self.project.plan_path, "r") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read plan file: {str(e)}")
            return ""
    
    def construct_prompt(self, 
                        system_prompt: str, 
                        user_message: str, 
                        include_plan: bool = True,
                        include_recent_chat: bool = True,
                        include_search: bool = True,
                        search_query: str = None,
                        search_limit: int = 5) -> List[Dict[str, str]]:
        """
        Construct a prompt for the LLM.
        
        Args:
            system_prompt (str): System prompt
            user_message (str): User message
            include_plan (bool, optional): Include plan in context. Defaults to True.
            include_recent_chat (bool, optional): Include recent chat in context. Defaults to True.
            include_search (bool, optional): Include search results in context. Defaults to True.
            search_query (str, optional): Search query. If None, uses user_message. Defaults to None.
            search_limit (int, optional): Maximum number of search results. Defaults to 5.
            
        Returns:
            List[Dict[str, str]]: List of message dictionaries for LLM
        """
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add plan if requested
        if include_plan:
            plan_content = self.get_plan_content()
            if plan_content:
                messages.append({
                    "role": "system", 
                    "content": f"Current project plan:\n\n{plan_content}"
                })
        
        # Add recent chat if requested
        if include_recent_chat:
            recent_messages = self.get_messages(limit=5)
            for msg in recent_messages:
                messages.append({
                    "role": "user" if msg["sender"] == "user" else "assistant",
                    "content": msg["content"]
                })
        
        # Add search results if requested
        if include_search:
            query = search_query or user_message
            search_results = self.search_memory(query, limit=search_limit)
            
            if search_results:
                context_str = "Relevant context from memory:\n\n"
                
                for result in search_results:
                    source_type = result["collection"]
                    metadata = result["metadata"]
                    
                    if source_type == "files":
                        context_str += f"From file {metadata.get('path', 'unknown')}:\n{result['text']}\n\n"
                    elif source_type == "chat":
                        context_str += f"From chat ({metadata.get('sender', 'unknown')}):\n{result['text']}\n\n"
                    elif source_type == "web":
                        context_str += f"From web page {metadata.get('title', 'unknown')} ({metadata.get('url', 'unknown')}):\n{result['text']}\n\n"
                    elif source_type == "insights":
                        context_str += f"From previous insight:\n{result['text']}\n\n"
                
                messages.append({
                    "role": "system",
                    "content": context_str
                })
        
        # Add user message
        messages.append({"role": "user", "content": user_message})
        
        return messages
