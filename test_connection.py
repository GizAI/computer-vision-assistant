#!/usr/bin/env python3
"""
Test script to verify the connection between the FastAPI server and frontend.
"""

import os
import sys
import requests
import time
import subprocess
import webbrowser
from pathlib import Path

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_server_status(url="http://localhost:8000"):
    """Check if the FastAPI server is running."""
    try:
        response = requests.get(f"{url}/api/status")
        if response.status_code == 200:
            print(f"✅ FastAPI server is running at {url}")
            return True
        else:
            print(f"❌ FastAPI server returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to FastAPI server at {url}")
        return False

def check_frontend_build():
    """Check if the frontend build exists."""
    ui_dist_path = Path("ui/dist")
    if ui_dist_path.exists() and ui_dist_path.is_dir():
        index_html = ui_dist_path / "index.html"
        if index_html.exists():
            print("✅ Frontend build exists")
            return True

    print("❌ Frontend build not found")
    return False

def main():
    """Main function to test the connection."""
    print("Testing connection between FastAPI server and frontend...")

    # Check if server is already running
    server_running = check_server_status()

    if not server_running:
        print("\nStarting FastAPI server...")
        server_process = subprocess.Popen(
            [sys.executable, "main.py", "--debug"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Wait for server to start
        for _ in range(10):
            time.sleep(1)
            if check_server_status():
                server_running = True
                break

    if not server_running:
        print("❌ Failed to start FastAPI server")
        return

    # Check frontend build
    frontend_built = check_frontend_build()

    if not frontend_built:
        print("\nBuilding frontend...")
        os.chdir("ui")
        subprocess.run(["npm", "install"], check=True)
        subprocess.run(["npm", "run", "build"], check=True)
        os.chdir("..")

        frontend_built = check_frontend_build()

    if not frontend_built:
        print("❌ Failed to build frontend")
        return

    # Open browser to test the connection
    print("\nOpening browser to test the connection...")
    webbrowser.open("http://localhost:8000")

    print("\nTest complete. Check the browser to verify the connection.")
    print("Press Ctrl+C to exit.")

    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting...")
        if 'server_process' in locals():
            server_process.terminate()

if __name__ == "__main__":
    main()
