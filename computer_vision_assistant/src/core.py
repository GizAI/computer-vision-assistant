#!/usr/bin/env python3
"""
Core functionality for Computer Vision Assistant.
"""

import os
import pyautogui
from rich.console import Console

# Initialize console for rich output
console = Console()

class ComputerVisionAssistant:
    """Main class for Computer Vision Assistant functionality."""

    def __init__(self, screenshot_dir="screenshots"):
        """
        Initialize the Computer Vision Assistant.

        Args:
            screenshot_dir (str): Directory to store screenshots
        """
        # Store the last screenshot for analysis
        self.last_screenshot = None
        self.last_screenshot_path = None

        # Get screen dimensions
        self.screen_width, self.screen_height = pyautogui.size()
        console.print(f"[bold green]Screen resolution: {self.screen_width}x{self.screen_height}[/bold green]")

        # Set up screenshot directory
        self.screenshot_dir = screenshot_dir
        os.makedirs(self.screenshot_dir, exist_ok=True)

        # Check if OCR is available
        try:
            import pytesseract
            self.tesseract_available = True
        except ImportError:
            self.tesseract_available = False

        if not self.tesseract_available:
            console.print("[yellow]Warning: Tesseract OCR is not available. Text recognition features will not work.[/yellow]")
            console.print("[yellow]Install Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki[/yellow]")

    def get_screen_dimensions(self):
        """Get the current screen dimensions."""
        return {
            "width": self.screen_width,
            "height": self.screen_height
        }

    def validate_coordinates(self, x, y):
        """
        Validate that coordinates are within screen bounds.

        Args:
            x (int): X coordinate
            y (int): Y coordinate

        Returns:
            tuple: Valid (x, y) coordinates
        """
        valid_x = max(0, min(int(x), self.screen_width - 1))
        valid_y = max(0, min(int(y), self.screen_height - 1))

        # Warn if coordinates were adjusted
        if valid_x != x or valid_y != y:
            console.print(f"[yellow]Warning: Coordinates ({x}, {y}) adjusted to ({valid_x}, {valid_y}) to fit screen[/yellow]")

        return valid_x, valid_y

    def get_relative_coordinates(self, x_percent, y_percent):
        """
        Convert percentage-based coordinates to absolute screen coordinates.

        Args:
            x_percent (float): X coordinate as percentage of screen width (0-100)
            y_percent (float): Y coordinate as percentage of screen height (0-100)

        Returns:
            tuple: (x, y) coordinates in pixels
        """
        x = int((x_percent / 100) * self.screen_width)
        y = int((y_percent / 100) * self.screen_height)
        return self.validate_coordinates(x, y)
