#!/usr/bin/env python3
"""
Utility functions for Computer Vision Assistant.
"""

import os
import json
import time
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

# Initialize console for rich output
console = Console()

def print_result(result, title="Result"):
    """
    Print a result dictionary in a formatted panel.
    
    Args:
        result (dict): Result dictionary
        title (str): Title for the panel
    """
    if isinstance(result, dict) and "status" in result:
        color = "green" if result["status"] == "success" else "red"
        console.print(Panel(
            Syntax(json.dumps(result, indent=2), "json", theme="monokai"),
            title=title,
            border_style=color
        ))
    else:
        console.print(result)

def print_table(data, title="Data", columns=None):
    """
    Print data in a formatted table.
    
    Args:
        data (list): List of dictionaries to display
        title (str): Title for the table
        columns (dict): Column definitions {name: style}
    """
    if not data:
        console.print(f"[yellow]No data to display for: {title}[/yellow]")
        return
    
    # Create table
    table = Table(title=title)
    
    # Add columns
    if columns:
        for name, style in columns.items():
            table.add_column(name, style=style)
    else:
        # Auto-generate columns from first item
        for key in data[0].keys():
            table.add_column(key, style="cyan")
    
    # Add rows
    for item in data:
        if columns:
            table.add_row(*[str(item.get(col, "")) for col in columns.keys()])
        else:
            table.add_row(*[str(item.get(key, "")) for key in data[0].keys()])
    
    console.print(table)

def print_welcome():
    """Print welcome message."""
    console.print(Panel(
        "[bold]Computer Vision Assistant[/bold]\n"
        "A tool that allows an AI assistant to control your computer by taking screenshots and performing mouse/keyboard actions.",
        title="Computer Vision Assistant",
        border_style="green"
    ))

def print_interactive_welcome():
    """Print welcome message for interactive mode."""
    console.print(Panel(
        "[bold]Computer Vision Assistant Interactive Mode[/bold]\n"
        "Type commands to control your computer. Type 'exit' to quit.",
        title="Interactive Mode",
        border_style="green"
    ))

def get_help_text():
    """Get help text for commands."""
    return """
Available commands:
  screenshot [output_path]       - Take a screenshot
  analyze [path]                 - Analyze a screenshot with OCR
  find <text>                    - Find text on screen
  click-position <x> <y>         - Click at a specific position
  click-text <text>              - Click on text visible on screen
  type <text>                    - Type text
  press <key>                    - Press a key
  hotkey <key1> <key2> ...       - Press a hotkey combination
  mouse-position                 - Get current mouse position
  move-mouse <x> <y>             - Move mouse to position
  help                           - Show this help
  exit                           - Exit interactive mode
"""
