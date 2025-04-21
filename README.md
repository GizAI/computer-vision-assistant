# Computer Vision Assistant

A tool that allows an AI assistant to control your computer by taking screenshots and performing mouse/keyboard actions.

> **Note**: This project is currently in experimental stage and has known limitations with icon recognition and performance. It works best with text-based UI elements.

## Features

- **Screenshot Capture**: Take screenshots of the entire screen or specific regions
- **OCR Text Recognition**: Extract text from screenshots with position information
- **Mouse Control**: Move the mouse and perform clicks at specific coordinates or on detected text
- **Keyboard Control**: Type text, press keys, and execute hotkey combinations
- **Interactive Mode**: Control your computer through an interactive command-line interface
- **Improved Coordinate Judgment**: Accurate coordinate validation and relative positioning
- **Timestamp Screenshots**: Automatically save screenshots with timestamps in a dedicated folder

## Installation

### Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

### Required Python Packages

```bash
pip install pyautogui pillow rich
```

### Optional OCR Support

For text recognition features, install Tesseract OCR:

1. Download and install Tesseract OCR:
   - Windows: [Tesseract OCR for Windows](https://github.com/UB-Mannheim/tesseract/wiki)
   - macOS: `brew install tesseract`
   - Linux: `sudo apt install tesseract-ocr`

2. Install the Python wrapper:
```bash
pip install pytesseract
```

3. If needed, configure the Tesseract path in `src/ocr.py`:
```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

## Usage

### Command Line Interface

The tool provides various commands for controlling your computer:

```bash
# Take a screenshot
python computer_vision_assistant.py screenshot --output screenshots/my_screenshot.png

# Take a screenshot of a specific region (left, top, width, height)
python computer_vision_assistant.py screenshot --region 100 100 400 300

# Analyze a screenshot with OCR
python computer_vision_assistant.py analyze --path screenshots/my_screenshot.png

# Find text on screen
python computer_vision_assistant.py find "search text"

# Click at specific coordinates
python computer_vision_assistant.py click-position 500 300

# Click on text visible on screen
python computer_vision_assistant.py click-text "Click me"

# Type text
python computer_vision_assistant.py type "Hello, world!"

# Press a key
python computer_vision_assistant.py press enter

# Press a hotkey combination
python computer_vision_assistant.py hotkey ctrl c

# Get current mouse position
python computer_vision_assistant.py mouse-position

# Move mouse to position
python computer_vision_assistant.py move-mouse 500 500

# Start interactive mode
python computer_vision_assistant.py interactive
```

### Interactive Mode

Interactive mode allows you to enter commands directly:

```bash
python computer_vision_assistant.py interactive
```

Available commands in interactive mode:
- `screenshot [output_path]` - Take a screenshot
- `analyze [path]` - Analyze a screenshot with OCR
- `find <text>` - Find text on screen
- `click-position <x> <y>` - Click at a specific position
- `click-text <text>` - Click on text visible on screen
- `type <text>` - Type text
- `press <key>` - Press a key
- `hotkey <key1> <key2> ...` - Press a hotkey combination
- `mouse-position` - Get current mouse position
- `move-mouse <x> <y>` - Move mouse to position
- `help` - Show help
- `exit` - Exit interactive mode

## Project Structure

```
computer_vision_assistant/
├── computer_vision_assistant.py  # Main entry point
├── screenshots/                  # Directory for storing screenshots
├── src/                          # Source code directory
│   ├── __init__.py               # Package initialization
│   ├── core.py                   # Core functionality
│   ├── screenshot.py             # Screenshot handling
│   ├── ocr.py                    # Text recognition
│   ├── input.py                  # Mouse and keyboard input
│   ├── cli.py                    # Command-line interface
│   └── utils.py                  # Utility functions
└── README.md                     # Documentation
```

## Advanced Usage

### Relative Coordinates

You can use percentage-based coordinates to make your automation more adaptable to different screen resolutions:

```python
from src.core import ComputerVisionAssistant

assistant = ComputerVisionAssistant()
x, y = assistant.get_relative_coordinates(50, 30)  # 50% of width, 30% of height
assistant.click_position(x, y)
```

### Custom Screenshot Directory

You can specify a custom directory for storing screenshots:

```python
from src.core import ComputerVisionAssistant

assistant = ComputerVisionAssistant(screenshot_dir="my_screenshots")
```

## Troubleshooting

### OCR Not Working

If text recognition features are not working:

1. Ensure Tesseract OCR is installed correctly
2. Check the Tesseract path in `src/ocr.py`
3. Verify that the `pytesseract` Python package is installed

### Mouse or Keyboard Actions Not Working

Some systems may have security restrictions that prevent programmatic control of mouse and keyboard:

- macOS: Grant accessibility permissions to your terminal application
- Windows: Run the script with administrator privileges if needed
- Linux: Ensure X11 permissions are correctly configured

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Known Limitations

- **Icon Recognition**: The tool relies on OCR for detecting UI elements, which works well for text but struggles with icons and graphical elements.
- **Performance**: Processing screenshots with OCR can be slow, especially on larger displays or with complex UIs.
- **Application Support**: The tool works best with text-heavy interfaces and may struggle with modern web applications that rely heavily on icons and dynamic elements.

## Future Improvements

- Add image recognition capabilities to detect icons and graphical UI elements
- Improve performance through optimized screenshot processing
- Implement UI element caching to reduce the need for repeated recognition
- Add application-specific modules for popular applications like Gmail, Office, etc.
- Explore the use of keyboard shortcuts as alternatives to mouse interactions
