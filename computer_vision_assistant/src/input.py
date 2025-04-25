#!/usr/bin/env python3
"""
Input (mouse and keyboard) functionality for Computer Vision Assistant.
"""


import pyautogui
from rich.console import Console

# Initialize console for rich output
console = Console()

def click_position(assistant, x, y, button='left', clicks=1, interval=0.0):
    """
    Click at the specified position.

    Args:
        assistant: ComputerVisionAssistant instance
        x (int): X coordinate
        y (int): Y coordinate
        button (str): Mouse button ('left', 'middle', 'right')
        clicks (int): Number of clicks
        interval (float): Interval between clicks

    Returns:
        dict: Result of the click operation
    """
    try:
        # Validate coordinates
        x, y = assistant.validate_coordinates(x, y)

        # Move mouse to position and click
        pyautogui.moveTo(x, y, duration=0.5)
        pyautogui.click(x=x, y=y, button=button, clicks=clicks, interval=interval)

        return {
            "status": "success",
            "message": f"Clicked at position ({x}, {y}) with {button} button, {clicks} times"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def click_text(assistant, text_to_click):
    """
    Find and click on text visible on the screen.

    Args:
        assistant: ComputerVisionAssistant instance
        text_to_click (str): Text to click on

    Returns:
        dict: Result of the click operation
    """
    if not assistant.tesseract_available:
        return {
            "status": "error",
            "message": "Tesseract OCR is not available. Install Tesseract OCR to use this feature."
        }

    try:
        # Find the text on screen
        from src.ocr import find_text_on_screen
        result = find_text_on_screen(assistant, text_to_click)

        if result["status"] != "success":
            return result

        if result["matches_count"] == 0:
            return {"status": "error", "message": f"Text '{text_to_click}' not found on screen"}

        # Click on the first match (center of the text)
        match = result["matches"][0]
        x = match["x"] + match["width"] // 2
        y = match["y"] + match["height"] // 2

        return click_position(assistant, x, y)
    except Exception as e:
        return {"status": "error", "message": str(e)}

def type_text(text, interval=0.1):
    """
    Type the specified text with the keyboard.

    Args:
        text (str): Text to type
        interval (float): Interval between keystrokes

    Returns:
        dict: Result of the typing operation
    """
    try:
        pyautogui.typewrite(text, interval=interval)
        return {
            "status": "success",
            "message": f"Typed text: '{text}'"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def press_key(key):
    """
    Press a specific key.

    Args:
        key (str): Key to press

    Returns:
        dict: Result of the key press operation
    """
    try:
        pyautogui.press(key)
        return {
            "status": "success",
            "message": f"Pressed key: {key}"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def press_hotkey(*keys):
    """
    Press a hotkey combination.

    Args:
        *keys: Keys to press as a hotkey

    Returns:
        dict: Result of the hotkey operation
    """
    try:
        pyautogui.hotkey(*keys)
        return {
            "status": "success",
            "message": f"Pressed hotkey: {'+'.join(keys)}"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def move_mouse(assistant, x, y, duration=0.5):
    """
    Move the mouse to the specified position.

    Args:
        assistant: ComputerVisionAssistant instance
        x (int): X coordinate
        y (int): Y coordinate
        duration (float): Duration of the movement

    Returns:
        dict: Result of the mouse movement operation
    """
    try:
        # Validate coordinates
        x, y = assistant.validate_coordinates(x, y)

        # Move mouse to position
        pyautogui.moveTo(x, y, duration=duration)

        return {
            "status": "success",
            "message": f"Moved mouse to position ({x}, {y})"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_mouse_position():
    """
    Get the current mouse position.

    Returns:
        dict: Current mouse position
    """
    try:
        x, y = pyautogui.position()
        return {
            "status": "success",
            "x": x,
            "y": y
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
