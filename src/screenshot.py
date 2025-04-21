#!/usr/bin/env python3
"""
Screenshot functionality for Computer Vision Assistant.
"""

import os
import time
import pyautogui
from datetime import datetime
from PIL import Image
from rich.console import Console

# Initialize console for rich output
console = Console()

def generate_screenshot_filename(prefix="screenshot"):
    """
    Generate a filename for a screenshot with timestamp.
    
    Args:
        prefix (str): Prefix for the filename
        
    Returns:
        str: Filename with timestamp
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.png"

def take_screenshot(assistant, region=None, output_path=None):
    """
    Take a screenshot of the entire screen or a specific region.
    
    Args:
        assistant: ComputerVisionAssistant instance
        region (tuple): Optional (left, top, width, height) tuple
        output_path (str): Optional path to save the screenshot
        
    Returns:
        dict: Result of the screenshot operation
    """
    try:
        # Generate filename if not provided
        if not output_path:
            filename = generate_screenshot_filename()
            output_path = os.path.join(assistant.screenshot_dir, filename)
        
        # Take screenshot (of region if specified)
        if region:
            left, top, width, height = region
            # Validate region coordinates
            left, top = assistant.validate_coordinates(left, top)
            # Ensure width and height don't exceed screen boundaries
            width = min(width, assistant.screen_width - left)
            height = min(height, assistant.screen_height - top)
            screenshot = pyautogui.screenshot(region=(left, top, width, height))
        else:
            screenshot = pyautogui.screenshot()
        
        # Store screenshot
        assistant.last_screenshot = screenshot
        
        # Save screenshot
        screenshot.save(output_path)
        assistant.last_screenshot_path = output_path
        console.print(f"[green]Screenshot saved to {output_path}[/green]")
        
        return {
            "status": "success",
            "width": screenshot.width,
            "height": screenshot.height,
            "path": output_path,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_screenshot_list(assistant):
    """
    Get a list of all screenshots in the screenshot directory.
    
    Args:
        assistant: ComputerVisionAssistant instance
        
    Returns:
        list: List of screenshot filenames
    """
    try:
        if not os.path.exists(assistant.screenshot_dir):
            return {"status": "error", "message": f"Screenshot directory {assistant.screenshot_dir} does not exist"}
        
        screenshots = [f for f in os.listdir(assistant.screenshot_dir) if f.endswith('.png')]
        return {
            "status": "success",
            "count": len(screenshots),
            "screenshots": screenshots
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
