#!/usr/bin/env python3
"""
Autobot: An autonomous AI agent designed to run on a user's desktop.
It takes high-level goals from a user via a chat interface and works continuously
to achieve them by planning, executing tasks, learning from outcomes, and adapting its strategy.
"""

import os
import sys
import argparse
from rich.console import Console
from fastapi import FastAPI

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.main import app as api_app, start_api
from core.orchestrator import Orchestrator, AgentState

# Initialize console for rich output
console = Console()

# Default port and debug settings
DEFAULT_PORT = 8000
DEBUG_MODE = True

# Global orchestrator instance
orchestrator = None


def print_welcome():
    """Print welcome message."""
    from rich.panel import Panel

    console.print(Panel(
        "[bold]Autobot[/bold]\n"
        "An autonomous AI agent designed to run on your desktop.\n"
        "It takes high-level goals and works continuously to achieve them.",
        title="Autobot",
        border_style="green"
    ))

def init_app():
    """Initialize the FastAPI app with orchestrator.

    Returns:
        FastAPI: The initialized FastAPI application
    """
    global orchestrator

    # Initialize orchestrator
    orchestrator = Orchestrator()

    # Set the initial state to waiting_for_user (paused)
    orchestrator.state = AgentState.WAITING_FOR_USER

    # Set the orchestrator in the API app
    from api.main import set_orchestrator
    set_orchestrator(orchestrator)

    return api_app

# Create app instance for uvicorn
app = init_app()

def main():
    """Main entry point for Autobot."""
    print_welcome()

    # Parse command line arguments for port and debug mode only
    parser = argparse.ArgumentParser(description="Autobot - Autonomous AI Agent")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port for the API server")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    # Start the orchestrator without a project
    orchestrator = Orchestrator()

    # Import AgentState from core.orchestrator
    from core.orchestrator import AgentState

    # Set the initial state to waiting_for_user (paused)
    orchestrator.state = AgentState.WAITING_FOR_USER

    # Start the API server in a separate thread
    import threading
    api_thread = threading.Thread(target=start_api, args=(args.port, args.debug, orchestrator))
    api_thread.daemon = True
    api_thread.start()

    # Start the orchestrator
    try:
        console.print("[bold green]Starting Orchestrator and API server in paused state...[/bold green]")
        console.print("[bold yellow]The AI will wait for user input before starting any tasks.[/bold yellow]")
        orchestrator.run()
    except KeyboardInterrupt:
        console.print("[bold yellow]Shutting down Autobot...[/bold yellow]")
        orchestrator.shutdown()

if __name__ == "__main__":
    main()
