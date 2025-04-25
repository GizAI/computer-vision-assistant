#!/usr/bin/env python3
"""
Vector Database Manager for Autobot.
Handles vector database operations.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Union, Tuple

import chromadb
from chromadb.config import Settings

# Set up logging
logger = logging.getLogger(__name__)

class VectorDBManager:
    """Manager for vector database operations."""
    
    def __init__(self, db_path: str, project_name: str):
        """
        Initialize the vector database manager.
        
        Args:
            db_path (str): Path to vector database
            project_name (str): Project name
        """
        self.db_path = db_path
        self.project_name = project_name
        
        # Create directory if it doesn't exist
        os.makedirs(db_path, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize collections
        self._init_collections()
        
        logger.info(f"Vector DB Manager initialized with database: {db_path}")
    
    def _init_collections(self) -> None:
        """Initialize collections."""
        # Create collections if they don't exist
        self.file_collection = self.client.get_or_create_collection(
            name="files",
            metadata={"project": self.project_name}
        )
        
        self.chat_collection = self.client.get_or_create_collection(
            name="chat",
            metadata={"project": self.project_name}
        )
        
        self.web_collection = self.client.get_or_create_collection(
            name="web",
            metadata={"project": self.project_name}
        )
        
        self.insight_collection = self.client.get_or_create_collection(
            name="insights",
            metadata={"project": self.project_name}
        )
    
    def add_embedding(self, 
                     collection_name: str, 
                     id: str, 
                     embedding: List[float], 
                     text: str, 
                     metadata: Dict[str, Any]) -> None:
        """
        Add an embedding to a collection.
        
        Args:
            collection_name (str): Collection name
            id (str): Embedding ID
            embedding (List[float]): Embedding vector
            text (str): Text content
            metadata (Dict[str, Any]): Metadata
        """
        collection = self._get_collection(collection_name)
        
        collection.add(
            ids=[id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[text]
        )
        
        logger.debug(f"Added embedding to collection {collection_name} with ID: {id}")
    
    def search(self, 
              collection_name: str, 
              query_embedding: List[float], 
              limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search a collection for similar embeddings.
        
        Args:
            collection_name (str): Collection name
            query_embedding (List[float]): Query embedding
            limit (int, optional): Maximum number of results. Defaults to 5.
            
        Returns:
            List[Dict[str, Any]]: Search results
        """
        collection = self._get_collection(collection_name)
        
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
                "collection": collection_name
            })
        
        return formatted_results
    
    def delete_embedding(self, collection_name: str, id: str) -> None:
        """
        Delete an embedding from a collection.
        
        Args:
            collection_name (str): Collection name
            id (str): Embedding ID
        """
        collection = self._get_collection(collection_name)
        
        collection.delete(ids=[id])
        
        logger.debug(f"Deleted embedding from collection {collection_name} with ID: {id}")
    
    def update_embedding(self, 
                        collection_name: str, 
                        id: str, 
                        embedding: List[float], 
                        text: str, 
                        metadata: Dict[str, Any]) -> None:
        """
        Update an embedding in a collection.
        
        Args:
            collection_name (str): Collection name
            id (str): Embedding ID
            embedding (List[float]): Embedding vector
            text (str): Text content
            metadata (Dict[str, Any]): Metadata
        """
        collection = self._get_collection(collection_name)
        
        collection.update(
            ids=[id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[text]
        )
        
        logger.debug(f"Updated embedding in collection {collection_name} with ID: {id}")
    
    def get_embedding(self, collection_name: str, id: str) -> Optional[Dict[str, Any]]:
        """
        Get an embedding from a collection.
        
        Args:
            collection_name (str): Collection name
            id (str): Embedding ID
            
        Returns:
            Optional[Dict[str, Any]]: Embedding data
        """
        collection = self._get_collection(collection_name)
        
        result = collection.get(ids=[id])
        
        if not result["ids"]:
            return None
        
        return {
            "id": result["ids"][0],
            "text": result["documents"][0],
            "metadata": result["metadatas"][0],
            "collection": collection_name
        }
    
    def _get_collection(self, collection_name: str):
        """
        Get a collection by name.
        
        Args:
            collection_name (str): Collection name
            
        Returns:
            Collection: ChromaDB collection
        """
        if collection_name == "files":
            return self.file_collection
        elif collection_name == "chat":
            return self.chat_collection
        elif collection_name == "web":
            return self.web_collection
        elif collection_name == "insights":
            return self.insight_collection
        else:
            raise ValueError(f"Unknown collection: {collection_name}")
