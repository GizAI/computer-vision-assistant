## Autobot: System Design Document

**1. Overview**

Autobot is an autonomous AI agent designed to run on a user's desktop. It takes high-level goals from a user via a chat interface and works continuously (24/7) to achieve them by planning, executing tasks using various local tools, learning from outcomes, and adapting its strategy. All data, except for LLM API interactions, remains local to ensure privacy. The system utilizes a web-based UI (FastAPI + Vue 3 + shadcn-vue) for interaction and monitoring.

**2. Goals**

* **Autonomy:** Operate continuously with minimal human intervention after initial goal setting.
* **Complex Task Handling:** Break down large, complex goals (e.g., SaaS development, research) into manageable steps.
* **Adaptive Planning:** Dynamically create, update, and manage hierarchical plans based on progress, user input, and reflection.
* **Rich Tool Integration:** Seamlessly utilize a wide range of tools: CLI, Python execution, Browser Automation (Playwright), Computer Vision, VS Code Extensions (Augment Code), Web Search, File I/O, etc.
* **Learning & Reflection:** Analyze successes and failures to improve future performance.
* **Sophisticated Context Management:** Maintain and utilize relevant context from project files, conversations, and past actions for effective LLM interaction.
* **Privacy:** Ensure all sensitive data (code, plans, conversations, intermediate results) is stored and processed locally.
* **User Interaction:** Provide a clear chat interface for task delegation, monitoring, and intervention.
* **Extensibility:** Allow easy addition of new tools, planning strategies, or memory systems.

**3. High-Level Architecture**

We'll use a modular, layered architecture:

```mermaid
graph TD
    UI[User Interface (Vue 3 / shadcn-vue)] -->|HTTP/WebSocket| API_GW[API Gateway (FastAPI)];

    subgraph Autobot Core Engine (Local Desktop Process)
        API_GW -->|User Input/Commands| Core_Orchestrator[Core Orchestrator];
        Core_Orchestrator -->|Goal/Task| Planning_Module[Planning Module];
        Core_Orchestrator -->|Task to Execute| Task_Execution_Engine[Task Execution Engine];
        Core_Orchestrator -->|Analyze Result| Reflection_Module[Reflection & Learning Module];
        Core_Orchestrator -->|Query/Store Context| Memory_Context_Manager[Memory & Context Manager];
        Core_Orchestrator -->|Manage Projects| Project_Manager[Project Manager];

        Planning_Module -->|Read/Write Plan| Persistence_Layer[Persistence Layer];
        Task_Execution_Engine -->|Invoke Tool| Tool_Integration_Layer[Tool Integration Layer];
        Task_Execution_Engine -->|Log Output/Status| Memory_Context_Manager;
        Reflection_Module -->|Read History/Results| Memory_Context_Manager;
        Reflection_Module -->|Update Strategy/Plan| Planning_Module;
        Reflection_Module -->|Store Insights| Memory_Context_Manager;

        Memory_Context_Manager -->|Store/Retrieve Data| Persistence_Layer;
        Memory_Context_Manager -->|Generate Embeddings| LLM_Interface[LLM Interface];
        Memory_Context_Manager -->|Construct Prompt| LLM_Interface;

        Project_Manager -->|Manage Files/DBs| Persistence_Layer;

        Tool_Integration_Layer -->|Interact With| Tools[External Tools (CLI, Python, Playwright, CV, Augment Code, Web, Files)];
        Core_Orchestrator -->|Generate/Reason| LLM_Interface;
        Planning_Module -->|Generate/Refine Plan| LLM_Interface;
        LLM_Interface -->|API Call| External_LLM[External LLM API (e.g., OpenAI)];

        subgraph Persistence Layer (Local Filesystem / DBs)
            Persistence_Layer -->|Stores| Project_Files[Project Files];
            Persistence_Layer -->|Stores| Plan_MD[Plan Files (Markdown)];
            Persistence_Layer -->|Stores| Chat_DB[Chat History DB (SQLite)];
            Persistence_Layer -->|Stores| Vector_DB[Vector Database (e.g., ChromaDB, LanceDB)];
            Persistence_Layer -->|Stores| Config_Files[Configuration Files];
            Persistence_Layer -->|Stores| Logs[Execution Logs];
        end

    end

    style Core_Orchestrator fill:#f9f,stroke:#333,stroke-width:2px
```

**4. Core Components**

* **4.1. User Interface (UI)**
    * **Technology:** Vue 3 frontend with shadcn-vue components.
    * **Functionality:** Displays chat history, current plan status, agent activity log. Allows users to submit initial prompts, provide mid-task feedback/instructions, and view results. Communicates with the backend via HTTP REST API and WebSockets for real-time updates.
    * **Backend (API Gateway):** FastAPI application.
        * Provides REST endpoints for managing projects, sending messages, retrieving status, viewing plans.
        * Uses WebSockets to push real-time updates (new messages, status changes, plan updates) to the UI.
        * Acts as the primary interface to the `Core Orchestrator`.

* **4.2. Core Orchestrator (Agent Loop)**
    * **Functionality:** The central "brain" running the main autonomous loop.
        * Manages the agent's state (e.g., `IDLE`, `PLANNING`, `EXECUTING`, `REFLECTING`, `WAITING_FOR_TOOL`).
        * Receives goals/instructions from the API Gateway.
        * Coordinates interactions between other modules: Planning, Execution, Memory, Reflection.
        * Handles user interruptions, integrating new instructions into the current process.
        * Decides when to plan, execute, reflect, or query the LLM for high-level reasoning.
        * Runs continuously (potentially in a background thread/process).
    * **Workflow:**
        1.  **Perceive:** Check for user input, current task status, tool feedback.
        2.  **Orient:** Assess current state, goal priority, available resources/context (via Memory Manager).
        3.  **Decide:** Choose next action: Refine plan (call Planning Module), execute next task (call Execution Engine), reflect on results (call Reflection Module), query LLM for guidance, or wait.
        4.  **Act:** Trigger the chosen module/action.
        5.  **Update:** Process results, update state, log actions (via Memory Manager).
        6.  Loop.

* **4.3. Project Manager**
    * **Functionality:** Handles the lifecycle of projects.
        * Creates new project directories upon initial user prompt. Structure: `/projects/{project_name}/`.
        * Initializes project-specific resources: `plan.md`, `chat_history.sqlite`, vector DB collection, log files, potential `.env` or config files.
        * Loads and unloads project contexts when the user switches projects.

* **4.4. Planning Module**
    * **Functionality:** Responsible for creating and managing task plans.
        * Takes a high-level goal or sub-goal as input.
        * Uses LLM assistance to break down goals into hierarchical steps (tree structure).
        * Persists the plan in a human-readable format (`plan.md`) within the project directory.
        * Plan Format (`plan.md`): Use Markdown task lists. Nested lists represent the hierarchy. Status markers (`[ ]`, `[x]`, `[!]` - ToDo, Done, Failed) track progress. Add metadata like estimated time or dependencies if needed.
        * Updates the plan based on task completion, reflection insights, or new user directives. This might involve adding detail to steps, marking steps done/failed, or restructuring parts of the plan.

* **4.5. Task Execution Engine**
    * **Functionality:** Executes individual tasks defined in the plan.
        * Receives a specific task description (e.g., "Run `npm install`", "Write Python function to parse API response", "Summarize URL `https://example.com`", "Ask Augment Code to refactor `main.py`").
        * Determines the best tool for the task (can use LLM reasoning).
        * Invokes the appropriate tool via the `Tool Integration Layer`.
        * Monitors execution, captures output (stdout, stderr), status codes, and potential artifacts (files created/modified).
        * Handles timeouts and basic error conditions.
        * Reports results back to the `Core Orchestrator`.

* **4.6. Tool Integration Layer**
    * **Functionality:** Provides a standardized interface for the `Task Execution Engine` to interact with various tools.
    * **Design:** Abstract base class (`Tool`) defining methods like `execute(params)`, `get_status()`, `description`.
    * **Concrete Implementations:**
        * `CLITool`: Executes shell commands (OS-specific handling needed, potentially using LLM to generate correct commands).
        * `PythonExecutorTool`: Executes Python code snippets or scripts (uses a sandboxed environment if possible, or directly runs `python <script>`). Needs access to project virtual environments.
        * `PlaywrightTool`: Controls a browser instance. Crucially, needs configuration to use the user's existing browser profiles (`user_data_dir`) to leverage existing logins and cookies.
        * `ComputerVisionTool`: Interfaces with `computer_vision_assistant.py` (assumed to provide functions for screen analysis, UI element interaction).
        * `AugmentCodeTool`: Interacts with the VS Code extension. **Challenge:** Requires a stable interface. Possibilities:
            1.  Official API or CLI provided by Augment Code (Ideal).
            2.  VS Code task execution or command palette automation.
            3.  (Fallback) UI automation via `ComputerVisionTool` (less reliable).
            * Needs robust status tracking (idle, running, waiting for input, complete, error). The Orchestrator needs to manage interactions, potentially providing input when Augment Code waits.
        * `WebSearchTool`: Uses a search engine API (e.g., Google Search, Bing Search) or library.
        * `FileReaderTool` / `FileWriterTool`: Reads/writes files within the project directory (or elsewhere, with caution).
    * **Extensibility:** New tools can be added by implementing the `Tool` interface.

* **4.7. Memory & Context Manager**
    * **Functionality:** The central repository for all project-related information and the engine for constructing LLM prompts.
    * **Components:**
        * **Data Storage (via Persistence Layer):**
            * `Project Files`: Raw files managed by Project Manager.
            * `Chat History`: Stored in a project-specific SQLite database (`chat_history.sqlite`) with tables for messages (timestamp, sender, content).
            * `Plan State`: Mirrored from `plan.md` or directly managed if needed.
            * `Execution Logs`: Details of tool executions (task, tool used, params, timestamp, status, output). Stored in files or DB.
            * `Learned Insights`: Store reflections, failure analyses, successful strategies in a structured format (DB table or dedicated files).
            * `Vector Store`: Local vector database (e.g., ChromaDB, LanceDB) storing embeddings.
        * **Embedding Engine:**
            * Uses the configured OpenAI embedding model API.
            * Strategically embeds:
                * File content (chunked) on creation/modification.
                * Conversation turns (user and Autobot messages).
                * Summaries of web pages or long documents.
                * Tool outputs (especially text-based ones).
                * Learned insights.
            * Embeddings include rich metadata (source path/URL, timestamp, data type, project ID, task ID).
        * **Context Retrieval Engine:**
            * Implements the hybrid search strategy:
                1.  Fetch recent conversation history (e.g., last N turns).
                2.  Generate search queries based on the current task, goal, and recent chat.
                3.  Perform BM25 keyword search (on chat history, logs, potentially file names/content) for literal matches.
                4.  Perform HNSW (or similar ANN) vector search on the Vector DB for semantic matches.
                5.  Combine and rank results from BM25 and HNSW.
                6.  Retrieve top K relevant context pieces (chat messages, file chunks, web summaries, insights).
            * Retrieves current relevant plan sections.
            * Retrieves tool status information (e.g., Augment Code state).
        * **Prompt Constructor:**
            * Assembles the final prompt for the LLM, incorporating:
                * System prompt (defining Autobot's role, capabilities, current goal).
                * Retrieved context (recent chat + hybrid search results, sorted chronologically or by relevance).
                * Current plan context / task details.
                * Specific instructions for the LLM (e.g., "plan the next steps", "write python code for...", "analyze this failure").
            * Manages context window limits by prioritizing the most relevant information.

* **4.8. Reflection & Learning Module**
    * **Functionality:** Enables the agent to learn from its experience.
        * Triggered after significant task completion, failure, or periodically.
        * Retrieves context about the task, its execution, the plan, and related past experiences from the Memory Manager.
        * Uses the LLM to perform self-critique: "Why did this task succeed/fail?", "Was this the most efficient tool/method?", "What assumptions were wrong?", "How can I improve this process next time?".
        * Stores these generated insights (linked to the task/goal) in the Memory Manager (including embeddings) for future retrieval.
        * Optionally, suggests immediate plan modifications to the Planning Module based on reflections.

* **4.9. LLM Interface**
    * **Functionality:** Abstract wrapper for interacting with the external LLM API (initially OpenAI).
    * Handles API key management securely (e.g., via environment variables or a config file).
    * Receives prompts constructed by the Memory Manager or other components.
    * Manages API calls, including error handling, retries with backoff.
    * Parses LLM responses, extracting structured information (code, commands, plan updates, JSON, text analysis) as needed.
    * Pluggable design to potentially support different LLM providers or local models in the future.

* **4.10. Persistence Layer**
    * **Functionality:** Handles the actual reading and writing of data to the local disk.
    * Manages file I/O for project files, Markdown plans, logs.
    * Interacts with the SQLite database for chat history, potentially logs/insights.
    * Interacts with the chosen Vector Database library for storing and querying embeddings.
    * Loads/saves application configuration.

**5. Technology Stack Summary**

* **Backend:** Python, FastAPI
* **Frontend:** Vue 3, shadcn-vue, TypeScript/JavaScript
* **Real-time Communication:** WebSockets
* **Database:** SQLite (for structured relational data like chat)
* **Vector Database:** ChromaDB, LanceDB, FAISS (local persistent options)
* **LLM:** OpenAI API (initially, designed for pluggability)
* **Browser Automation:** Playwright
* **Packaging:** PyInstaller, Electron (if bundling FastAPI/Vue into a single desktop app) or run backend separately.

**6. Data Management & Privacy**

* **Local First:** All project data, plans, chat history, vector embeddings, logs, and intermediate results are stored exclusively on the user's local machine within the project directories.
* **LLM Interaction:** Only the constructed prompts and the LLM's responses are sent to/received from the external LLM API. No local files or full databases are uploaded.
* **Configuration:** API keys and sensitive configurations should be stored securely (e.g., environment variables, secure local storage).

**7. Key Considerations & Future Enhancements**

* **Augment Code Interaction:** The reliability heavily depends on the available interface for Augment Code. This needs investigation early on.
* **Error Handling & Resilience:** Implement robust error handling at all levels (tool execution, API calls, file I/O). The agent needs to recover from transient failures.
* **Resource Management:** Monitor CPU, memory, and disk usage, especially during intensive tasks like embedding or long-running processes.
* **Security:** Executing arbitrary code (Python, CLI) and controlling browsers has security implications. Consider sandboxing or permissions if possible, although the requirement grants full PC access. Warn the user.
* **Scalability:** While desktop-focused, the modular design allows for potentially scaling parts later (e.g., a more robust database, distributed task execution if ever needed).
* **Multi-Agent Collaboration:** Future architecture could support multiple Autobot instances or specialized agents working together.
* **Local LLMs:** Design the LLM Interface to potentially accommodate local LLMs (running via llama.cpp, Ollama, etc.) for enhanced privacy or offline capability.
* **Cost Management:** Track LLM API usage per project/task.