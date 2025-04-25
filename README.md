# Autobot

Autobot is an autonomous AI agent designed to run on a user's desktop. It takes high-level goals from a user via a chat interface and works continuously to achieve them by planning, executing tasks, learning from outcomes, and adapting its strategy.

## Features

- **Autonomy:** Operates continuously with minimal human intervention after initial goal setting
- **Complex Task Handling:** Breaks down large, complex goals into manageable steps
- **Adaptive Planning:** Dynamically creates, updates, and manages hierarchical plans
- **Rich Tool Integration:** Seamlessly utilizes a wide range of tools:
  - CLI execution
  - Python code execution
  - Computer Vision for screen analysis and interaction
  - Web Search
  - File operations
- **Learning & Reflection:** Analyzes successes and failures to improve future performance
- **Sophisticated Context Management:** Maintains and utilizes relevant context
- **Privacy:** Ensures all sensitive data is stored and processed locally
- **User Interaction:** Provides a clear chat interface for task delegation, monitoring, and intervention

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/autobot.git
   cd autobot
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file with the following:
   ```
   OPENAI_API_KEY=your_openai_api_key
   LLM_MODEL=gpt-4.1-mini
   ```

## Usage

1. Start Autobot:
   ```
   python main.py --project "My Project" --goal "Build a simple web application"
   ```

2. Access the web interface:
   Open your browser and navigate to `http://localhost:8000`

3. Interact with Autobot through the chat interface

## Commands

- `/status` - Get current agent status
- `/plan` - View current plan
- `/task <task>` - Execute a specific task
- `/reflect` - Reflect on progress
- `/stop` or `/pause` - Pause the agent
- `/resume` - Resume the agent
- `/help` - Show help message

## Architecture

Autobot uses a modular, layered architecture:

- **Core Orchestrator:** The central "brain" running the main autonomous loop
- **Planning Module:** Creates and manages hierarchical task plans
- **Task Execution Engine:** Executes individual tasks defined in the plan
- **Tool Integration Layer:** Provides a standardized interface for tools
- **Memory & Context Manager:** Manages project-related information and constructs LLM prompts
- **Reflection & Learning Module:** Enables the agent to learn from its experience
- **LLM Interface:** Wrapper for interacting with the external LLM API
- **Persistence Layer:** Handles reading and writing data to the local disk
- **API & UI:** FastAPI backend and Vue 3 frontend for user interaction

## License

MIT
