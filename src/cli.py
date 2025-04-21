#!/usr/bin/env python3
"""
Command-line interface for Computer Vision Assistant.
"""

import os
import sys
import json
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from .core import ComputerVisionAssistant
from .screenshot import take_screenshot, get_screenshot_list
from .ocr import analyze_screenshot, find_text_on_screen
from .input import (
    click_position, click_text, type_text, 
    press_key, press_hotkey, move_mouse, get_mouse_position
)
from .utils import (
    print_result, print_table, print_welcome, 
    print_interactive_welcome, get_help_text
)

# Initialize console for rich output
console = Console()

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Computer Vision Assistant")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Screenshot command
    screenshot_parser = subparsers.add_parser("screenshot", help="Take a screenshot")
    screenshot_parser.add_argument("--output", "-o", help="Output file path")
    screenshot_parser.add_argument("--region", "-r", nargs=4, type=int, 
                                  help="Region to capture (left top width height)")

    # List screenshots command
    subparsers.add_parser("list-screenshots", help="List all screenshots")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a screenshot")
    analyze_parser.add_argument("--path", "-p", help="Path to screenshot file")

    # Find text command
    find_parser = subparsers.add_parser("find", help="Find text on screen")
    find_parser.add_argument("text", help="Text to find")

    # Click position command
    click_pos_parser = subparsers.add_parser("click-position", help="Click at a specific position")
    click_pos_parser.add_argument("x", type=int, help="X coordinate")
    click_pos_parser.add_argument("y", type=int, help="Y coordinate")
    click_pos_parser.add_argument("--button", "-b", default="left", 
                                 choices=["left", "middle", "right"], help="Mouse button")
    click_pos_parser.add_argument("--clicks", "-c", type=int, default=1, help="Number of clicks")

    # Click text command
    click_text_parser = subparsers.add_parser("click-text", help="Click on text visible on screen")
    click_text_parser.add_argument("text", help="Text to click on")

    # Type text command
    type_parser = subparsers.add_parser("type", help="Type text")
    type_parser.add_argument("text", help="Text to type")
    type_parser.add_argument("--interval", "-i", type=float, help="Interval between keystrokes", default=0.1)

    # Press key command
    key_parser = subparsers.add_parser("press", help="Press a key")
    key_parser.add_argument("key", help="Key to press")

    # Press hotkey command
    hotkey_parser = subparsers.add_parser("hotkey", help="Press a hotkey combination")
    hotkey_parser.add_argument("keys", nargs="+", help="Keys to press as a hotkey")

    # Get mouse position command
    subparsers.add_parser("mouse-position", help="Get current mouse position")

    # Move mouse command
    move_parser = subparsers.add_parser("move-mouse", help="Move mouse to position")
    move_parser.add_argument("x", type=int, help="X coordinate")
    move_parser.add_argument("y", type=int, help="Y coordinate")
    move_parser.add_argument("--duration", "-d", type=float, default=0.5, help="Duration of movement")

    # Interactive mode command
    subparsers.add_parser("interactive", help="Start interactive mode")

    return parser.parse_args()

def handle_interactive_mode(assistant):
    """Handle interactive mode."""
    print_interactive_welcome()

    while True:
        command = console.input("[bold green]> [/bold green]")

        if command.lower() in ('exit', 'quit'):
            break
            
        if command.lower() in ('help', '?'):
            console.print(get_help_text())
            continue

        try:
            # Parse the command
            parts = command.split()
            if not parts:
                continue

            cmd = parts[0]
            args = parts[1:]

            # Execute the appropriate command
            if cmd == "screenshot":
                output = args[0] if args else None
                result = take_screenshot(assistant, output_path=output)

            elif cmd == "list-screenshots":
                result = get_screenshot_list(assistant)
                if result["status"] == "success":
                    console.print(f"[bold green]Found {result['count']} screenshots[/bold green]")
                    for screenshot in result["screenshots"]:
                        console.print(f"  {screenshot}")
                    continue

            elif cmd == "analyze":
                path = args[0] if args else None
                result = analyze_screenshot(assistant, path)
                if result["status"] == "success":
                    console.print(f"[bold green]Extracted {len(result['words'])} words[/bold green]")
                    console.print(Panel(
                        result["full_text"][:1000] + ("..." if len(result["full_text"]) > 1000 else ""),
                        title="Extracted Text (First 1000 chars)",
                        border_style="green"
                    ))
                    continue

            elif cmd == "find":
                if not args:
                    result = {"status": "error", "message": "Text to find is required"}
                else:
                    result = find_text_on_screen(assistant, args[0])
                    if result["status"] == "success":
                        console.print(f"[bold green]Found {result['matches_count']} matches for '{args[0]}'[/bold green]")
                        if result["matches_count"] > 0:
                            columns = {
                                "text": "cyan", 
                                "x": "green", 
                                "y": "green", 
                                "width": "blue", 
                                "height": "blue"
                            }
                            print_table(result["matches"], f"Matches for '{args[0]}'", columns)
                        continue

            elif cmd == "click-position":
                if len(args) < 2:
                    result = {"status": "error", "message": "X and Y coordinates are required"}
                else:
                    button = args[2] if len(args) > 2 else "left"
                    clicks = int(args[3]) if len(args) > 3 else 1
                    result = click_position(assistant, int(args[0]), int(args[1]), button, clicks)

            elif cmd == "click-text":
                if not args:
                    result = {"status": "error", "message": "Text to click is required"}
                else:
                    result = click_text(assistant, args[0])

            elif cmd == "type":
                if not args:
                    result = {"status": "error", "message": "Text to type is required"}
                else:
                    result = type_text(" ".join(args))

            elif cmd == "press":
                if not args:
                    result = {"status": "error", "message": "Key to press is required"}
                else:
                    result = press_key(args[0])

            elif cmd == "hotkey":
                if not args:
                    result = {"status": "error", "message": "Keys for hotkey are required"}
                else:
                    result = press_hotkey(*args)

            elif cmd == "mouse-position":
                result = get_mouse_position()

            elif cmd == "move-mouse":
                if len(args) < 2:
                    result = {"status": "error", "message": "X and Y coordinates are required"}
                else:
                    duration = float(args[2]) if len(args) > 2 else 0.5
                    result = move_mouse(assistant, int(args[0]), int(args[1]), duration)

            else:
                result = {"status": "error", "message": f"Unknown command: {cmd}"}

            # Display the result
            print_result(result, f"{cmd.capitalize()} Result")

        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")

def main():
    """Main entry point for the CLI."""
    args = parse_arguments()
    
    # Create assistant
    assistant = ComputerVisionAssistant()

    if args.command == "screenshot":
        region = args.region if args.region else None
        result = take_screenshot(assistant, region, args.output)
        print_result(result, "Screenshot Result")

    elif args.command == "list-screenshots":
        result = get_screenshot_list(assistant)
        if result["status"] == "success":
            console.print(f"[bold green]Found {result['count']} screenshots[/bold green]")
            for screenshot in result["screenshots"]:
                console.print(f"  {screenshot}")
        else:
            print_result(result, "List Screenshots Result")

    elif args.command == "analyze":
        result = analyze_screenshot(assistant, args.path)
        if result["status"] == "success":
            console.print(Panel(
                result["full_text"],
                title="Extracted Text",
                border_style="green"
            ))

            # Display words with positions in a table
            columns = {
                "text": "cyan", 
                "x": "green", 
                "y": "green", 
                "width": "blue", 
                "height": "blue", 
                "conf": "magenta"
            }
            print_table(result["words"][:20], "Words with Positions", columns)

            if len(result["words"]) > 20:
                console.print(f"[yellow]Showing 20 of {len(result['words'])} words[/yellow]")
        else:
            print_result(result, "Analysis Result")

    elif args.command == "find":
        result = find_text_on_screen(assistant, args.text)
        if result["status"] == "success":
            console.print(f"[bold green]Found {result['matches_count']} matches for '{args.text}'[/bold green]")

            if result["matches_count"] > 0:
                columns = {
                    "text": "cyan", 
                    "x": "green", 
                    "y": "green", 
                    "width": "blue", 
                    "height": "blue"
                }
                print_table(result["matches"], f"Matches for '{args.text}'", columns)
        else:
            print_result(result, "Find Text Result")

    elif args.command == "click-position":
        result = click_position(assistant, args.x, args.y, args.button, args.clicks)
        print_result(result, "Click Position Result")

    elif args.command == "click-text":
        result = click_text(assistant, args.text)
        print_result(result, "Click Text Result")

    elif args.command == "type":
        result = type_text(args.text, args.interval)
        print_result(result, "Type Text Result")

    elif args.command == "press":
        result = press_key(args.key)
        print_result(result, "Press Key Result")

    elif args.command == "hotkey":
        result = press_hotkey(*args.keys)
        print_result(result, "Press Hotkey Result")

    elif args.command == "mouse-position":
        result = get_mouse_position()
        print_result(result, "Mouse Position")

    elif args.command == "move-mouse":
        result = move_mouse(assistant, args.x, args.y, args.duration)
        print_result(result, "Move Mouse Result")

    elif args.command == "interactive":
        handle_interactive_mode(assistant)

    else:
        parse_arguments().__parser__.print_help()
