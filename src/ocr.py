#!/usr/bin/env python3
"""
OCR (Optical Character Recognition) functionality for Computer Vision Assistant.
"""


from PIL import Image
from rich.console import Console

# Initialize console for rich output
console = Console()

# Try to import pytesseract, but don't fail if it's not available
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

# Configure pytesseract path if needed (Windows users might need this)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def is_tesseract_available():
    """Check if Tesseract OCR is available."""
    return TESSERACT_AVAILABLE

def analyze_screenshot(assistant, screenshot_path=None):
    """
    Analyze the screenshot using OCR to extract text.

    Args:
        assistant: ComputerVisionAssistant instance
        screenshot_path (str): Optional path to screenshot file

    Returns:
        dict: Result of the OCR analysis
    """
    if not TESSERACT_AVAILABLE:
        return {
            "status": "error",
            "message": "Tesseract OCR is not available. Install Tesseract OCR to use this feature."
        }

    try:
        # Use the provided screenshot or the last one taken
        if screenshot_path:
            img = Image.open(screenshot_path)
        elif assistant.last_screenshot:
            img = assistant.last_screenshot
        else:
            return {"status": "error", "message": "No screenshot available for analysis"}

        # Extract text using OCR
        text = pytesseract.image_to_string(img)

        # Extract text with position information
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

        # Create a list of words with their positions
        words_with_positions = []
        for i in range(len(data['text'])):
            if data['text'][i].strip():
                words_with_positions.append({
                    'text': data['text'][i],
                    'x': data['left'][i],
                    'y': data['top'][i],
                    'width': data['width'][i],
                    'height': data['height'][i],
                    'conf': data['conf'][i]
                })

        return {
            "status": "success",
            "full_text": text,
            "words": words_with_positions
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def find_text_on_screen(assistant, text_to_find, take_new_screenshot=True):
    """
    Find the position of specific text on the screen.

    Args:
        assistant: ComputerVisionAssistant instance
        text_to_find (str): Text to search for
        take_new_screenshot (bool): Whether to take a new screenshot

    Returns:
        dict: Result with matches
    """
    if not TESSERACT_AVAILABLE:
        return {
            "status": "error",
            "message": "Tesseract OCR is not available. Install Tesseract OCR to use this feature."
        }

    try:
        # Take a fresh screenshot if requested
        if take_new_screenshot:
            from src.screenshot import take_screenshot
            take_screenshot(assistant)

        # Analyze the screenshot
        result = analyze_screenshot(assistant)

        if result["status"] != "success":
            return result

        # Search for the text in the words list
        matches = []
        for word in result["words"]:
            if text_to_find.lower() in word["text"].lower():
                matches.append(word)

        return {
            "status": "success",
            "matches_count": len(matches),
            "matches": matches
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
