#!/usr/bin/env python3
"""
Playwright Tool for Autobot.
Provides browser automation capabilities.
"""

import os
import json
import logging
import time
from typing import Dict, Any, List, Optional, Union

from autobot.tools.base import Tool

# Set up logging
logger = logging.getLogger(__name__)

class PlaywrightTool(Tool):
    """Tool for browser automation using Playwright."""
    
    def __init__(self, user_data_dir: Optional[str] = None, headless: bool = False):
        """
        Initialize the Playwright tool.
        
        Args:
            user_data_dir (str, optional): Path to user data directory. Defaults to None.
            headless (bool, optional): Whether to run in headless mode. Defaults to False.
        """
        super().__init__(
            name="playwright",
            description="Controls a browser using Playwright"
        )
        
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.browser = None
        self.page = None
        
        # Try to import playwright
        try:
            from playwright.sync_api import sync_playwright
            self.playwright = sync_playwright().__enter__()
            self.available = True
            logger.info("Playwright Tool initialized successfully")
        except ImportError:
            logger.error("Failed to import playwright. Please install it with: pip install playwright")
            logger.error("Then install browsers with: playwright install")
            self.available = False
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a Playwright command.
        
        Args:
            params (Dict[str, Any]): Command parameters
                - action (str): Action to perform (open, goto, click, type, screenshot, etc.)
                - Additional parameters specific to each action
            
        Returns:
            Dict[str, Any]: Execution result
        """
        self._set_status("running")
        
        if not self.available:
            result = {
                "status": "error",
                "error": "Playwright is not available"
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
            if action == "open":
                result = self._open_browser(params)
            elif action == "close":
                result = self._close_browser(params)
            elif action == "goto":
                result = self._goto(params)
            elif action == "click":
                result = self._click(params)
            elif action == "type":
                result = self._type(params)
            elif action == "screenshot":
                result = self._screenshot(params)
            elif action == "get_text":
                result = self._get_text(params)
            elif action == "get_html":
                result = self._get_html(params)
            elif action == "evaluate":
                result = self._evaluate(params)
            elif action == "wait_for_selector":
                result = self._wait_for_selector(params)
            elif action == "wait_for_navigation":
                result = self._wait_for_navigation(params)
            elif action == "fill_form":
                result = self._fill_form(params)
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
    
    def _open_browser(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Open a browser.
        
        Args:
            params (Dict[str, Any]): Parameters
                - browser_type (str, optional): Browser type (chromium, firefox, webkit). Defaults to "chromium".
                - headless (bool, optional): Whether to run in headless mode. Defaults to self.headless.
                - user_data_dir (str, optional): Path to user data directory. Defaults to self.user_data_dir.
            
        Returns:
            Dict[str, Any]: Result
        """
        browser_type = params.get("browser_type", "chromium")
        headless = params.get("headless", self.headless)
        user_data_dir = params.get("user_data_dir", self.user_data_dir)
        
        # Close existing browser if open
        if self.browser:
            try:
                self.browser.close()
            except:
                pass
            self.browser = None
            self.page = None
        
        # Launch browser
        browser_options = {
            "headless": headless
        }
        
        if user_data_dir:
            browser_options["user_data_dir"] = user_data_dir
        
        if browser_type == "chromium":
            self.browser = self.playwright.chromium.launch(**browser_options)
        elif browser_type == "firefox":
            self.browser = self.playwright.firefox.launch(**browser_options)
        elif browser_type == "webkit":
            self.browser = self.playwright.webkit.launch(**browser_options)
        else:
            return {
                "status": "error",
                "error": f"Unknown browser type: {browser_type}"
            }
        
        # Create a new page
        self.page = self.browser.new_page()
        
        return {
            "status": "success",
            "message": f"Opened {browser_type} browser",
            "browser_type": browser_type,
            "headless": headless
        }
    
    def _close_browser(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Close the browser.
        
        Args:
            params (Dict[str, Any]): Parameters
            
        Returns:
            Dict[str, Any]: Result
        """
        if not self.browser:
            return {
                "status": "error",
                "error": "No browser is open"
            }
        
        try:
            self.browser.close()
            self.browser = None
            self.page = None
            
            return {
                "status": "success",
                "message": "Closed browser"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to close browser: {str(e)}"
            }
    
    def _goto(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Navigate to a URL.
        
        Args:
            params (Dict[str, Any]): Parameters
                - url (str): URL to navigate to
                - wait_until (str, optional): When to consider navigation complete. Defaults to "load".
                - timeout (int, optional): Timeout in milliseconds. Defaults to 30000.
            
        Returns:
            Dict[str, Any]: Result
        """
        if not self.page:
            return self._handle_no_page()
        
        url = params.get("url")
        wait_until = params.get("wait_until", "load")
        timeout = params.get("timeout", 30000)
        
        if not url:
            return {
                "status": "error",
                "error": "No URL provided"
            }
        
        try:
            response = self.page.goto(url, wait_until=wait_until, timeout=timeout)
            
            return {
                "status": "success",
                "url": self.page.url,
                "title": self.page.title(),
                "status_code": response.status if response else None
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to navigate to {url}: {str(e)}"
            }
    
    def _click(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Click on an element.
        
        Args:
            params (Dict[str, Any]): Parameters
                - selector (str): Element selector
                - button (str, optional): Mouse button (left, middle, right). Defaults to "left".
                - position (Dict[str, int], optional): Click position (x, y). Defaults to None.
                - delay (int, optional): Delay between mousedown and mouseup in milliseconds. Defaults to 0.
                - timeout (int, optional): Timeout in milliseconds. Defaults to 30000.
            
        Returns:
            Dict[str, Any]: Result
        """
        if not self.page:
            return self._handle_no_page()
        
        selector = params.get("selector")
        button = params.get("button", "left")
        position = params.get("position")
        delay = params.get("delay", 0)
        timeout = params.get("timeout", 30000)
        
        if not selector:
            return {
                "status": "error",
                "error": "No selector provided"
            }
        
        try:
            click_options = {
                "button": button,
                "delay": delay,
                "timeout": timeout
            }
            
            if position:
                click_options["position"] = position
            
            self.page.click(selector, **click_options)
            
            return {
                "status": "success",
                "message": f"Clicked on {selector}",
                "selector": selector
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to click on {selector}: {str(e)}"
            }
    
    def _type(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Type text into an element.
        
        Args:
            params (Dict[str, Any]): Parameters
                - selector (str): Element selector
                - text (str): Text to type
                - delay (int, optional): Delay between keystrokes in milliseconds. Defaults to 0.
                - timeout (int, optional): Timeout in milliseconds. Defaults to 30000.
            
        Returns:
            Dict[str, Any]: Result
        """
        if not self.page:
            return self._handle_no_page()
        
        selector = params.get("selector")
        text = params.get("text")
        delay = params.get("delay", 0)
        timeout = params.get("timeout", 30000)
        
        if not selector:
            return {
                "status": "error",
                "error": "No selector provided"
            }
        
        if text is None:
            return {
                "status": "error",
                "error": "No text provided"
            }
        
        try:
            self.page.fill(selector, "", timeout=timeout)
            self.page.type(selector, text, delay=delay, timeout=timeout)
            
            return {
                "status": "success",
                "message": f"Typed text into {selector}",
                "selector": selector,
                "text": text
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to type text into {selector}: {str(e)}"
            }
    
    def _screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Take a screenshot.
        
        Args:
            params (Dict[str, Any]): Parameters
                - path (str, optional): Path to save screenshot. Defaults to None.
                - selector (str, optional): Element selector to screenshot. Defaults to None.
                - full_page (bool, optional): Whether to take a full page screenshot. Defaults to False.
            
        Returns:
            Dict[str, Any]: Result
        """
        if not self.page:
            return self._handle_no_page()
        
        path = params.get("path")
        selector = params.get("selector")
        full_page = params.get("full_page", False)
        
        try:
            screenshot_options = {
                "full_page": full_page
            }
            
            if path:
                screenshot_options["path"] = path
            
            if selector:
                # Take element screenshot
                element = self.page.query_selector(selector)
                if not element:
                    return {
                        "status": "error",
                        "error": f"Element not found: {selector}"
                    }
                
                screenshot = element.screenshot(**screenshot_options)
            else:
                # Take page screenshot
                screenshot = self.page.screenshot(**screenshot_options)
            
            result = {
                "status": "success",
                "message": "Screenshot taken"
            }
            
            if path:
                result["path"] = path
            else:
                import base64
                result["data"] = base64.b64encode(screenshot).decode("ascii")
                result["encoding"] = "base64"
            
            return result
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to take screenshot: {str(e)}"
            }
    
    def _get_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get text content of an element.
        
        Args:
            params (Dict[str, Any]): Parameters
                - selector (str): Element selector
                - timeout (int, optional): Timeout in milliseconds. Defaults to 30000.
            
        Returns:
            Dict[str, Any]: Result
        """
        if not self.page:
            return self._handle_no_page()
        
        selector = params.get("selector")
        timeout = params.get("timeout", 30000)
        
        if not selector:
            return {
                "status": "error",
                "error": "No selector provided"
            }
        
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
            text = self.page.text_content(selector)
            
            return {
                "status": "success",
                "selector": selector,
                "text": text
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to get text from {selector}: {str(e)}"
            }
    
    def _get_html(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get HTML content of an element or page.
        
        Args:
            params (Dict[str, Any]): Parameters
                - selector (str, optional): Element selector. Defaults to None (whole page).
                - timeout (int, optional): Timeout in milliseconds. Defaults to 30000.
            
        Returns:
            Dict[str, Any]: Result
        """
        if not self.page:
            return self._handle_no_page()
        
        selector = params.get("selector")
        timeout = params.get("timeout", 30000)
        
        try:
            if selector:
                self.page.wait_for_selector(selector, timeout=timeout)
                html = self.page.inner_html(selector)
            else:
                html = self.page.content()
            
            return {
                "status": "success",
                "selector": selector,
                "html": html
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to get HTML: {str(e)}"
            }
    
    def _evaluate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate JavaScript code.
        
        Args:
            params (Dict[str, Any]): Parameters
                - expression (str): JavaScript expression to evaluate
                - arg (Any, optional): Argument to pass to the expression. Defaults to None.
            
        Returns:
            Dict[str, Any]: Result
        """
        if not self.page:
            return self._handle_no_page()
        
        expression = params.get("expression")
        arg = params.get("arg")
        
        if not expression:
            return {
                "status": "error",
                "error": "No expression provided"
            }
        
        try:
            if arg is not None:
                result = self.page.evaluate(expression, arg)
            else:
                result = self.page.evaluate(expression)
            
            return {
                "status": "success",
                "expression": expression,
                "result": result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to evaluate expression: {str(e)}"
            }
    
    def _wait_for_selector(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wait for an element to appear.
        
        Args:
            params (Dict[str, Any]): Parameters
                - selector (str): Element selector
                - state (str, optional): State to wait for (attached, detached, visible, hidden). Defaults to "visible".
                - timeout (int, optional): Timeout in milliseconds. Defaults to 30000.
            
        Returns:
            Dict[str, Any]: Result
        """
        if not self.page:
            return self._handle_no_page()
        
        selector = params.get("selector")
        state = params.get("state", "visible")
        timeout = params.get("timeout", 30000)
        
        if not selector:
            return {
                "status": "error",
                "error": "No selector provided"
            }
        
        try:
            element = self.page.wait_for_selector(selector, state=state, timeout=timeout)
            
            if element:
                return {
                    "status": "success",
                    "message": f"Element {selector} is {state}",
                    "selector": selector,
                    "state": state
                }
            else:
                return {
                    "status": "error",
                    "error": f"Element {selector} not found"
                }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to wait for selector {selector}: {str(e)}"
            }
    
    def _wait_for_navigation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wait for navigation to complete.
        
        Args:
            params (Dict[str, Any]): Parameters
                - url (str, optional): URL to wait for. Defaults to None.
                - wait_until (str, optional): When to consider navigation complete. Defaults to "load".
                - timeout (int, optional): Timeout in milliseconds. Defaults to 30000.
            
        Returns:
            Dict[str, Any]: Result
        """
        if not self.page:
            return self._handle_no_page()
        
        url = params.get("url")
        wait_until = params.get("wait_until", "load")
        timeout = params.get("timeout", 30000)
        
        try:
            with self.page.expect_navigation(url=url, wait_until=wait_until, timeout=timeout) as navigation_info:
                # This will wait for navigation to complete
                pass
            
            response = navigation_info.value
            
            return {
                "status": "success",
                "message": "Navigation complete",
                "url": self.page.url,
                "title": self.page.title(),
                "status_code": response.status if response else None
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to wait for navigation: {str(e)}"
            }
    
    def _fill_form(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fill a form with multiple fields.
        
        Args:
            params (Dict[str, Any]): Parameters
                - form_data (Dict[str, str]): Form data (selector -> value)
                - submit_selector (str, optional): Selector for submit button. Defaults to None.
                - timeout (int, optional): Timeout in milliseconds. Defaults to 30000.
            
        Returns:
            Dict[str, Any]: Result
        """
        if not self.page:
            return self._handle_no_page()
        
        form_data = params.get("form_data")
        submit_selector = params.get("submit_selector")
        timeout = params.get("timeout", 30000)
        
        if not form_data:
            return {
                "status": "error",
                "error": "No form data provided"
            }
        
        try:
            # Fill each field
            for selector, value in form_data.items():
                self.page.fill(selector, value, timeout=timeout)
            
            # Submit form if requested
            if submit_selector:
                self.page.click(submit_selector, timeout=timeout)
            
            return {
                "status": "success",
                "message": "Form filled",
                "form_data": form_data,
                "submitted": bool(submit_selector)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to fill form: {str(e)}"
            }
    
    def _handle_no_page(self) -> Dict[str, Any]:
        """
        Handle the case when no page is open.
        
        Returns:
            Dict[str, Any]: Error result
        """
        # Try to open a browser if none is open
        if not self.browser:
            try:
                return self._open_browser({})
            except Exception as e:
                return {
                    "status": "error",
                    "error": f"No browser is open and failed to open one: {str(e)}"
                }
        
        # Try to open a new page
        try:
            self.page = self.browser.new_page()
            return {
                "status": "success",
                "message": "Opened new page"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"No page is open and failed to open one: {str(e)}"
            }
