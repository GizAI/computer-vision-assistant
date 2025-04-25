# VS Code Configuration for Autobot

This directory contains VS Code configuration files for building, running, and debugging the Autobot application.

## Available Configurations

### Debug Configurations (F5 or Run > Start Debugging)

1. **Python: Autobot Server** - Runs the full Python backend server with uvicorn and the orchestrator
2. **Python: FastAPI Only** - Runs only the FastAPI server with uvicorn
3. **Frontend: Vite Dev Server** - Runs only the frontend development server
4. **Debug All** - Runs the backend server first, then the frontend development server
5. **Server + Frontend** - Runs both the full backend server and frontend development server in parallel
6. **FastAPI + Frontend** - Runs both the FastAPI-only server and frontend development server in parallel

### Tasks (Terminal > Run Task)

1. **build-frontend** - Builds the frontend for production (includes npm install)
2. **start-server** - Starts the full Python backend server with orchestrator
3. **start-fastapi-only** - Starts only the FastAPI server with uvicorn
4. **start-dev-frontend** - Starts the frontend development server (includes npm install)
5. **build-and-run-all** - Builds the frontend and then runs the full server (production mode)
6. **dev-mode-all** - Runs both the full server and frontend in development mode
7. **fastapi-dev-mode** - Runs the FastAPI-only server and frontend in development mode

## How to Use

### For Full Development (with Orchestrator)

1. Press `F5` and select "Server + Frontend" to run both the backend and frontend in development mode with debugging enabled
2. Or run the task "dev-mode-all" from the Command Palette (Ctrl+Shift+P > Tasks: Run Task > dev-mode-all)

### For FastAPI-Only Development (without Orchestrator)

1. Press `F5` and select "FastAPI + Frontend" to run the FastAPI server and frontend in development mode
2. Or run the task "fastapi-dev-mode" from the Command Palette (Ctrl+Shift+P > Tasks: Run Task > fastapi-dev-mode)

### For Production Build and Test

1. Run the task "build-and-run-all" from the Command Palette (Ctrl+Shift+P > Tasks: Run Task > build-and-run-all)
2. This will build the frontend and then start the server with the built frontend

## Debugging

- When running in debug mode, you can set breakpoints in both Python and JavaScript/Vue files
- For Python, breakpoints will work as expected
- For frontend code, you'll need to use the browser's developer tools for detailed debugging

## Integration Between FastAPI and Frontend

- The frontend makes API calls to the FastAPI server at `/api/*` endpoints
- WebSocket communication is established at the `/ws` endpoint
- When running in development mode, Vite's proxy configuration forwards these requests to the FastAPI server
- When running in production mode, the FastAPI server serves the built frontend directly

## Requirements

- VS Code extensions:
  - Python extension
  - JavaScript Debugger extension
  - Volar (for Vue files)
  - ESLint
  - Prettier
- Python dependencies (install with `pip install -r requirements.txt`)
- Node.js and npm (for frontend development)
