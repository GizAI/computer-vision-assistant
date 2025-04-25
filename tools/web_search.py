#!/usr/bin/env python3
"""
Web Search Tool for Autobot.
Performs web searches and fetches web content.
"""

import os
import logging
import json
import requests
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, quote_plus
from bs4 import BeautifulSoup

from autobot.tools.base import Tool

# Set up logging
logger = logging.getLogger(__name__)

class WebSearchTool(Tool):
    """Tool for web search and content fetching."""
    
    def __init__(self, api_key: str = None, search_engine_id: str = None):
        """
        Initialize the web search tool.
        
        Args:
            api_key (str, optional): Google Custom Search API key. Defaults to None.
            search_engine_id (str, optional): Google Custom Search Engine ID. Defaults to None.
        """
        super().__init__(
            name="web_search",
            description="Performs web searches and fetches web content"
        )
        
        # Google Custom Search API credentials
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.search_engine_id = search_engine_id or os.getenv("GOOGLE_CSE_ID")
        
        # Check if credentials are available
        self.google_search_available = bool(self.api_key and self.search_engine_id)
        
        if not self.google_search_available:
            logger.warning("Google Custom Search API credentials not found. Using fallback search method.")
        
        logger.info(f"Web Search Tool initialized")
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a web search or fetch operation.
        
        Args:
            params (Dict[str, Any]): Operation parameters
                - operation (str): Operation to perform (search, fetch)
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
            if operation == "search":
                result = self._search(params)
            elif operation == "fetch":
                result = self._fetch_url(params)
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
    
    def _search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform a web search.
        
        Args:
            params (Dict[str, Any]): Search parameters
                - query (str): Search query
                - num_results (int, optional): Number of results to return. Defaults to 5.
            
        Returns:
            Dict[str, Any]: Search result
        """
        query = params.get("query")
        num_results = params.get("num_results", 5)
        
        if not query:
            return {
                "status": "error",
                "error": "No query provided"
            }
        
        # Use Google Custom Search API if available
        if self.google_search_available:
            return self._google_search(query, num_results)
        
        # Fallback to a basic search
        return self._fallback_search(query, num_results)
    
    def _google_search(self, query: str, num_results: int) -> Dict[str, Any]:
        """
        Perform a search using Google Custom Search API.
        
        Args:
            query (str): Search query
            num_results (int): Number of results to return
            
        Returns:
            Dict[str, Any]: Search result
        """
        url = "https://www.googleapis.com/customsearch/v1"
        
        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": min(num_results, 10)  # API limit is 10 results per request
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if "items" not in data:
                return {
                    "status": "success",
                    "message": "No results found",
                    "query": query,
                    "results": []
                }
            
            results = []
            
            for item in data["items"]:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "Google Custom Search API"
                })
            
            return {
                "status": "success",
                "query": query,
                "results": results,
                "result_count": len(results)
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Google Custom Search API request failed: {str(e)}")
            # Fall back to basic search
            return self._fallback_search(query, num_results)
    
    def _fallback_search(self, query: str, num_results: int) -> Dict[str, Any]:
        """
        Perform a basic search using a public search API.
        
        Args:
            query (str): Search query
            num_results (int): Number of results to return
            
        Returns:
            Dict[str, Any]: Search result
        """
        # Use DuckDuckGo API (no API key required)
        url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            results = []
            
            # Extract results from DuckDuckGo response
            if "Results" in data:
                for item in data["Results"][:num_results]:
                    results.append({
                        "title": item.get("Text", ""),
                        "link": item.get("FirstURL", ""),
                        "snippet": "",
                        "source": "DuckDuckGo"
                    })
            
            # Add abstract if available
            if "AbstractText" in data and data["AbstractText"]:
                results.insert(0, {
                    "title": data.get("Heading", ""),
                    "link": data.get("AbstractURL", ""),
                    "snippet": data["AbstractText"],
                    "source": "DuckDuckGo Abstract"
                })
            
            # Add related topics if needed to reach num_results
            if len(results) < num_results and "RelatedTopics" in data:
                for item in data["RelatedTopics"]:
                    if len(results) >= num_results:
                        break
                    
                    if "Text" in item and "FirstURL" in item:
                        results.append({
                            "title": item.get("Text", ""),
                            "link": item.get("FirstURL", ""),
                            "snippet": "",
                            "source": "DuckDuckGo Related"
                        })
            
            return {
                "status": "success",
                "query": query,
                "results": results,
                "result_count": len(results)
            }
            
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            logger.error(f"Fallback search failed: {str(e)}")
            
            # Return a minimal result
            return {
                "status": "error",
                "error": f"Search failed: {str(e)}",
                "query": query,
                "results": []
            }
    
    def _fetch_url(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch content from a URL.
        
        Args:
            params (Dict[str, Any]): Fetch parameters
                - url (str): URL to fetch
                - extract_text (bool, optional): Whether to extract text content. Defaults to True.
                - include_html (bool, optional): Whether to include HTML content. Defaults to False.
            
        Returns:
            Dict[str, Any]: Fetch result
        """
        url = params.get("url")
        extract_text = params.get("extract_text", True)
        include_html = params.get("include_html", False)
        
        if not url:
            return {
                "status": "error",
                "error": "No URL provided"
            }
        
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return {
                "status": "error",
                "error": f"Invalid URL: {url}"
            }
        
        try:
            # Set a user agent to avoid being blocked
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            result = {
                "status": "success",
                "url": url,
                "title": "",
                "content_type": response.headers.get("Content-Type", "")
            }
            
            # Check if content is HTML
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" in content_type:
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Extract title
                title_tag = soup.find("title")
                result["title"] = title_tag.text if title_tag else ""
                
                # Extract text content if requested
                if extract_text:
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.extract()
                    
                    # Get text
                    text = soup.get_text(separator="\n", strip=True)
                    
                    # Clean up text (remove excessive newlines)
                    lines = [line.strip() for line in text.splitlines() if line.strip()]
                    text = "\n".join(lines)
                    
                    result["text_content"] = text
                
                # Include HTML if requested
                if include_html:
                    result["html_content"] = response.text
                
            else:
                # For non-HTML content, just include the raw text
                result["text_content"] = response.text
            
            return result
            
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "error": f"Failed to fetch URL: {str(e)}",
                "url": url
            }
