#!/usr/bin/env python3
"""
SQLite Manager for Autobot.
Handles SQLite database operations.
"""

import os
import json
import sqlite3
import logging
from typing import Dict, Any, List, Optional, Union, Tuple

# Set up logging
logger = logging.getLogger(__name__)

class SQLiteManager:
    """Manager for SQLite database operations."""
    
    def __init__(self, db_path: str):
        """
        Initialize the SQLite manager.
        
        Args:
            db_path (str): Path to SQLite database
        """
        self.db_path = db_path
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_db()
        
        logger.info(f"SQLite Manager initialized with database: {db_path}")
    
    def _init_db(self) -> None:
        """Initialize the database with required tables."""
        conn = self._get_connection()
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
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection.
        
        Returns:
            sqlite3.Connection: Database connection
        """
        return sqlite3.connect(self.db_path)
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute a query and return results.
        
        Args:
            query (str): SQL query
            params (tuple, optional): Query parameters. Defaults to ().
            
        Returns:
            List[Dict[str, Any]]: Query results
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(query, params)
        
        results = []
        for row in cursor.fetchall():
            results.append(dict(row))
        
        conn.close()
        
        return results
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        Execute an update query and return the number of affected rows.
        
        Args:
            query (str): SQL query
            params (tuple, optional): Query parameters. Defaults to ().
            
        Returns:
            int: Number of affected rows
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(query, params)
        
        affected_rows = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return affected_rows
    
    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """
        Execute an insert query and return the last inserted row ID.
        
        Args:
            query (str): SQL query
            params (tuple, optional): Query parameters. Defaults to ().
            
        Returns:
            int: Last inserted row ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(query, params)
        
        last_row_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return last_row_id
    
    def add_message(self, sender: str, content: str, timestamp: str, metadata: Dict[str, Any] = None) -> int:
        """
        Add a message to the database.
        
        Args:
            sender (str): Message sender
            content (str): Message content
            timestamp (str): Message timestamp
            metadata (Dict[str, Any], optional): Message metadata. Defaults to None.
            
        Returns:
            int: Message ID
        """
        metadata_json = json.dumps(metadata or {})
        
        query = "INSERT INTO messages (timestamp, sender, content, metadata) VALUES (?, ?, ?, ?)"
        params = (timestamp, sender, content, metadata_json)
        
        return self.execute_insert(query, params)
    
    def get_messages(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get messages from the database.
        
        Args:
            limit (int, optional): Maximum number of messages. Defaults to 10.
            offset (int, optional): Offset for pagination. Defaults to 0.
            
        Returns:
            List[Dict[str, Any]]: Messages
        """
        query = "SELECT * FROM messages ORDER BY id DESC LIMIT ? OFFSET ?"
        params = (limit, offset)
        
        messages = self.execute_query(query, params)
        
        # Parse metadata JSON
        for message in messages:
            try:
                message["metadata"] = json.loads(message["metadata"])
            except (json.JSONDecodeError, TypeError):
                message["metadata"] = {}
        
        # Reverse to get chronological order
        return list(reversed(messages))
    
    def add_execution_log(self, 
                         tool: str, 
                         params: Dict[str, Any], 
                         status: str, 
                         timestamp: str,
                         output: Any = None, 
                         task_id: str = None, 
                         metadata: Dict[str, Any] = None) -> int:
        """
        Add an execution log to the database.
        
        Args:
            tool (str): Tool used
            params (Dict[str, Any]): Tool parameters
            status (str): Execution status
            timestamp (str): Execution timestamp
            output (Any, optional): Execution output. Defaults to None.
            task_id (str, optional): Task ID. Defaults to None.
            metadata (Dict[str, Any], optional): Execution metadata. Defaults to None.
            
        Returns:
            int: Log ID
        """
        params_json = json.dumps(params)
        output_json = json.dumps(output) if output is not None else None
        metadata_json = json.dumps(metadata or {})
        
        query = "INSERT INTO execution_logs (timestamp, task_id, tool, params, status, output, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)"
        query_params = (timestamp, task_id, tool, params_json, status, output_json, metadata_json)
        
        return self.execute_insert(query, query_params)
    
    def get_execution_logs(self, limit: int = 10, offset: int = 0, task_id: str = None) -> List[Dict[str, Any]]:
        """
        Get execution logs from the database.
        
        Args:
            limit (int, optional): Maximum number of logs. Defaults to 10.
            offset (int, optional): Offset for pagination. Defaults to 0.
            task_id (str, optional): Filter by task ID. Defaults to None.
            
        Returns:
            List[Dict[str, Any]]: Execution logs
        """
        if task_id:
            query = "SELECT * FROM execution_logs WHERE task_id = ? ORDER BY id DESC LIMIT ? OFFSET ?"
            params = (task_id, limit, offset)
        else:
            query = "SELECT * FROM execution_logs ORDER BY id DESC LIMIT ? OFFSET ?"
            params = (limit, offset)
        
        logs = self.execute_query(query, params)
        
        # Parse JSON fields
        for log in logs:
            try:
                log["params"] = json.loads(log["params"])
            except (json.JSONDecodeError, TypeError):
                log["params"] = {}
            
            try:
                log["output"] = json.loads(log["output"])
            except (json.JSONDecodeError, TypeError):
                log["output"] = None
            
            try:
                log["metadata"] = json.loads(log["metadata"])
            except (json.JSONDecodeError, TypeError):
                log["metadata"] = {}
        
        return logs
    
    def add_insight(self, 
                   content: str, 
                   timestamp: str,
                   task_id: str = None, 
                   metadata: Dict[str, Any] = None) -> int:
        """
        Add an insight to the database.
        
        Args:
            content (str): Insight content
            timestamp (str): Insight timestamp
            task_id (str, optional): Task ID. Defaults to None.
            metadata (Dict[str, Any], optional): Insight metadata. Defaults to None.
            
        Returns:
            int: Insight ID
        """
        metadata_json = json.dumps(metadata or {})
        
        query = "INSERT INTO insights (timestamp, task_id, content, metadata) VALUES (?, ?, ?, ?)"
        params = (timestamp, task_id, content, metadata_json)
        
        return self.execute_insert(query, params)
    
    def get_insights(self, limit: int = 10, offset: int = 0, task_id: str = None) -> List[Dict[str, Any]]:
        """
        Get insights from the database.
        
        Args:
            limit (int, optional): Maximum number of insights. Defaults to 10.
            offset (int, optional): Offset for pagination. Defaults to 0.
            task_id (str, optional): Filter by task ID. Defaults to None.
            
        Returns:
            List[Dict[str, Any]]: Insights
        """
        if task_id:
            query = "SELECT * FROM insights WHERE task_id = ? ORDER BY id DESC LIMIT ? OFFSET ?"
            params = (task_id, limit, offset)
        else:
            query = "SELECT * FROM insights ORDER BY id DESC LIMIT ? OFFSET ?"
            params = (limit, offset)
        
        insights = self.execute_query(query, params)
        
        # Parse metadata JSON
        for insight in insights:
            try:
                insight["metadata"] = json.loads(insight["metadata"])
            except (json.JSONDecodeError, TypeError):
                insight["metadata"] = {}
        
        return insights
