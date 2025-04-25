#!/usr/bin/env python3
"""
LLM Interface for Autobot.
Provides a standardized interface for interacting with LLM APIs.
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional, Union
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

class LLMInterface:
    """Interface for interacting with LLM APIs."""

    def __init__(self, model: str = None, api_key: str = None):
        """
        Initialize the LLM interface.

        Args:
            model (str, optional): LLM model to use. Defaults to env var or "gpt-4.1-mini".
            api_key (str, optional): API key for the LLM provider. Defaults to env var.
        """
        self.model = model or os.getenv("LLM_MODEL", "gpt-4.1-mini")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("No API key provided. Set OPENAI_API_KEY environment variable or pass api_key parameter.")

        # Set up API endpoints
        self.chat_endpoint = "https://api.openai.com/v1/chat/completions"
        self.embedding_endpoint = "https://api.openai.com/v1/embeddings"
        self.embedding_model = "text-embedding-3-small"

        # Set up headers
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        logger.info(f"LLM Interface initialized with model: {self.model}")

    def generate(self,
                 messages: List[Dict[str, str]],
                 temperature: float = 0.7,
                 max_tokens: int = 1000,
                 stop: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate a response from the LLM.

        Args:
            messages (List[Dict[str, str]]): List of message dictionaries with 'role' and 'content'
            temperature (float, optional): Sampling temperature. Defaults to 0.7.
            max_tokens (int, optional): Maximum tokens to generate. Defaults to 1000.
            stop (List[str], optional): List of stop sequences. Defaults to None.

        Returns:
            Dict[str, Any]: Response from the LLM
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if stop:
            payload["stop"] = stop

        # Log the request (excluding API key for security)
        logger.info(f"LLM Request to {self.model}: {json.dumps({k: v for k, v in payload.items() if k != 'api_key'})}")

        # Implement retry logic with exponential backoff
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.chat_endpoint,
                    headers=self.headers,
                    json=payload,
                    timeout=60
                )

                response.raise_for_status()
                result = response.json()

                # Log the response (truncated for brevity)
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                logger.info(f"LLM Response from {self.model} (truncated): {content[:200]}...")

                return result

            except requests.exceptions.RequestException as e:
                logger.warning(f"LLM API request failed (attempt {attempt+1}/{max_retries}): {str(e)}")

                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"LLM API request failed after {max_retries} attempts")
                    raise

    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector for a text.

        Args:
            text (str): Text to embed

        Returns:
            List[float]: Embedding vector
        """
        payload = {
            "model": self.embedding_model,
            "input": text
        }

        # Log the embedding request
        logger.info(f"Embedding Request to {self.embedding_model}: text length={len(text)}")

        # Implement retry logic with exponential backoff
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.embedding_endpoint,
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )

                response.raise_for_status()
                result = response.json()

                # Extract the embedding vector
                embedding = result.get("data", [{}])[0].get("embedding", [])

                # Log the embedding response
                logger.info(f"Embedding Response from {self.embedding_model}: vector length={len(embedding)}")

                return embedding

            except requests.exceptions.RequestException as e:
                logger.warning(f"Embedding API request failed (attempt {attempt+1}/{max_retries}): {str(e)}")

                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Embedding API request failed after {max_retries} attempts")
                    raise

    def extract_json(self, content: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response content.

        Args:
            content (str): LLM response content

        Returns:
            Dict[str, Any]: Extracted JSON
        """
        try:
            # Try to find JSON within the content (between triple backticks)
            import re
            json_match = re.search(r"```json\n(.*?)\n```", content, re.DOTALL)

            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)

            # If no JSON found between backticks, try to parse the entire content
            return json.loads(content)

        except json.JSONDecodeError:
            logger.warning(f"Failed to extract JSON from content: {content[:100]}...")
            return {}
