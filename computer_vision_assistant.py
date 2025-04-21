#!/usr/bin/env python3
"""
Computer Vision Assistant - A tool that allows an AI assistant to control your computer
by taking screenshots and performing mouse/keyboard actions.
"""

# Main entry point for the Computer Vision Assistant
from src.utils import print_welcome
from src.cli import main

if __name__ == "__main__":
    print_welcome()
    main()
