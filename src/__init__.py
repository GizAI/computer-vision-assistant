"""
Computer Vision Assistant - A tool that allows an AI assistant to control your computer
by taking screenshots and performing mouse/keyboard actions.
"""

from .core import ComputerVisionAssistant
from .screenshot import take_screenshot, generate_screenshot_filename, get_screenshot_list
from .ocr import analyze_screenshot, find_text_on_screen, is_tesseract_available
from .input import (
    click_position, click_text, type_text, 
    press_key, press_hotkey, move_mouse, get_mouse_position
)

__version__ = "1.0.0"
