# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## 🎯 Project Overview

**Jarvis** is a sophisticated Deep Agent system designed for Independent Financial Advisors (IFAs). Built on the LangChain Deep Agents framework, it provides autonomous monitoring, risk identification, and professional document generation for financial advisory practices.

### Core Technologies

- **Framework**: LangChain Deep Agents (v0.3.12+)
- **Backend**: FastAPI with WebSocket support
- **Frontend**: React + Vite + Tailwind CSS
- **Vector Store**: ChromaDB for semantic search
- **LLM**: OpenAI GPT-4.1 (chat), GPT-4o-mini (heartbeat/cron)
- **Communication**: Telegram Bot API, WebSocket voice pipeline
- **Scheduling**: APScheduler for background tasks
- **MCP Integration**: Calendar and Market Feed servers

### Architecture Pattern: "Board of Specialists"

Jarvis operates as an orchestrator that delegates specialized tasks to three expert sub-agents:

| Agent | Role | Implementation | Key Tools |
|-------|------|----------------|-----------|
| **Jarvis** | Orchestrator | `src/jarvis/deepagent.py` | File operations, scheduling, MCP tools |
| **Atlas** | RAG Specialist | `src/jarvis/sub_agents/atlas.py` | `retrieve_context` (ChromaDB search) |
| **Emma** | Paraplanner | `src/jarvis/sub_agents/emma.py` | Document generation (delegates to Atlas) |
| **Colin** | Compliance | `src/jarvis/sub_agents/colin.py` | `search_uk_compliance` (Tavily FCA search) |

## 🏗️ Key Architectural Concepts

### 1. Dynamic System Prompt

Unlike traditional chatbots with static prompts, Jarvis builds its personality and context dynamically at runtime by reading workspace files:

```python
# In deepagent.py
def build_system_prompt(mode: str = "chat") -> str:
    agents_md = read_file("AGENTS.md")      # Operational instructions
    soul_md = read_file("SOUL.md")          # Personality and values
    identity_md = read_file("IDENTITY.md")  # Professional identity
    user_md = read_file("USER.md")          # Advisor context
    tools_md = read_file("TOOLS.md")        # Tool documentation
    heartbeat_md = read_file("HEARTBEAT.md") # Proactive task checklist
```

**Important**: When modifying Jarvis's behavior, edit the `.md` files in `workspace/` rather than hardcoding prompts in Python.

### 2. Workspace-Centric Design

All operations happen within the `workspace/` directory:

```
workspace/
├── AGENTS.md          # Instructions for Jarvis (not for code assistants)
├── SOUL.md            # Jarvis's personality
├── IDENTITY.md        # Role definition
├── USER.md            # Advisor context
├── TOOLS.md           # Tool documentation
├── HEARTBEAT.md       # Proactive task checklist
├── MEMORY.md          # Long-term insights
├── datasets/          # Client data (CRM, emails, transcripts)
│   ├── client_name/
│   │   ├── crm.json
│   │   ├── email_archive/*.txt
│   │   └── meeting_transcripts/*.txt
└── memory/            # Daily logs (YYYY-MM-DD.md)
```

**Convention**: Use `WORKSPACE_DIR` constant from `config.py` for all file operations.

### 3. MCP Server Integration

Jarvis connects to Model Context Protocol (MCP) servers for specialized capabilities:

**Calendar MCP** (`src/jarvis/tools/calendar_server.py`):
- Manages advisor calendar events
- Sends and archives client emails
- Tools are pre-loaded at API startup via `init_calendar_tools()`

**Market Feed MCP** (`src/jarvis/tools/market_feed_server.py`):
- Fetches macroeconomic indicators
- Searches financial news (Tavily)
- Retrieves asset performance data
- Tools are pre-loaded via `init_market_feed_tools()`

**Implementation Pattern**:
```python
# Tools are cached globally to avoid repeated subprocess spawns
_calendar_tools: list = []

async def init_calendar_tools():
    """Warm-up at FastAPI startup"""
    global _calendar_tools
    if not _calendar_tools:
        client = MultiServerMCPClient({...})
        _calendar_tools = await client.get_tools()
```

### 4. Proactive Heartbeat System

Jarvis runs continuously in the background (`src/jarvis/jarvis_heartbeat.py`):

- **Interval**: Every 30 minutes (configurable via `HEARTBEAT_INTERVAL_MINUTES`)
- **Model**: GPT-4o-mini (cost-efficient for monitoring)
- **Actions**: Can directly raise notifications or draft emails without explicit prompting

**Heartbeat Flow**:
1. Read `SOUL.md`, `USER.md`, `MEMORY.md`, `HEARTBEAT.md`
2. Use `find_files_updated_after` to detect new files (last 30 min)
3. If urgent: Read context, consult Atlas, verify with Colin
4. Take action: `send_important_notification` or `send_draft_email`
5. Reply `HEARTBEAT_OK` if nothing needs attention

**Special Tokens**:
- `HEARTBEAT_OK`: Nothing needs attention
- `NO_REPLY`: Used in chat when Jarvis has nothing to add

### 5. Sub-Agent Communication

Sub-agents are integrated as `CompiledSubAgent` instances:

```python
atlas_subagent = CompiledSubAgent(
    name="atlas",
    description="RAG specialist for analyzing client data...",
    runnable=atlas_agent  # The LangGraph compiled agent
)

agent = create_deep_agent(
    model="openai:gpt-4.1",
    tools=[...],
    subagents=[atlas_subagent, emma_subagent, colin_subagent],
    backend=FilesystemBackend(root_dir=str(WORKSPACE_DIR)),
    checkpointer=MemorySaver(),
)
```

**Delegation Pattern**: Jarvis can invoke sub-agents by name in its reasoning, and the framework handles routing.

### 6. Voice Pipeline (Sandwich Architecture)

WebSocket endpoint at `/ws/voice` implements a streaming voice interaction pipeline:

```
Audio Input → STT → Agent Processing → TTS → Audio Output
```

**Implementation**: `src/jarvis/tools/voice_pipeline.py`
- Uses OpenAI's built-in STT and TTS models
- Streams responses in real-time
- Supports interruption and context switching

## 🛠️ Development Workflow

### Initial Setup

```bash
# Install dependencies
uv sync

# Ingest client documents into ChromaDB
python scripts/ingest_documents.py

# Start backend (includes heartbeat scheduler)
uv run uvicorn jarvis.api:app --reload --port 8000

# Start frontend (separate terminal)
cd frontend && npm install && npm run dev
```

### Testing Sub-Agents Individually

Each sub-agent can be tested standalone:

```bash
# Test Atlas (RAG)
uv run python src/jarvis/sub_agents/atlas.py

# Test Emma (Paraplanner)
uv run python src/jarvis/sub_agents/emma.py

# Test Colin (Compliance)
uv run python src/jarvis/sub_agents/colin.py
```

### Running Telegram Bot

```bash
# Set TELEGRAM_BOT_TOKEN in .env
uv run python src/jarvis/telegram_bot.py

# Chat with agents via Telegram
@jarvis Who are my top 3 clients by AUM?
@atlas What did Alan say about risk tolerance?
@emma Draft an email to Gareth about his policy
@colin Is it compliant to guarantee 5% returns?
```

### Adding New Tools

1. **Create tool function** in `src/jarvis/tools/`:
```python
from langchain_core.tools import tool

@tool
def my_new_tool(param: str) -> str:
    """Tool description for the LLM."""
    # Implementation
    return result
```

2. **Register in deepagent.py**:
```python
from jarvis.tools.my_tool import my_new_tool

tools = [
    find_files_updated_after,
    my_new_tool,  # Add here
    *calendar_tools,
    *market_feed_tools,
]
```

3. **Document in workspace/TOOLS.md** so Jarvis knows when to use it.

### Adding New Sub-Agents

1. **Create agent file** in `src/jarvis/sub_agents/`:
```python
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

llm = init_chat_model("gpt-4.1")

my_agent = create_agent(
    model=llm,
    tools=[...],
    system_prompt="You are...",
    middleware=[TodoListMiddleware(), ModelRetryMiddleware(...)],
)
```

2. **Register in deepagent.py**:
```python
from jarvis.sub_agents.my_agent import my_agent

my_subagent = CompiledSubAgent(
    name="my_agent",
    description="What this agent does...",
    runnable=my_agent
)

agent = create_deep_agent(
    subagents=[atlas_subagent, emma_subagent, colin_subagent, my_subagent],
    ...
)
```

## 📋 Development Conventions

### File Organization

- **Sub-agents**: `src/jarvis/sub_agents/` - Each agent in its own file
- **Tools**: `src/jarvis/tools/` - Reusable tool functions
- **Utils**: `src/jarvis/utils/` - Helper classes (vector store, etc.)
- **Workspace**: `workspace/` - Jarvis's operating environment (prompts, data, memory)
- **Raw Data**: `raw_datasets/` - Source documents for ingestion
- **Scripts**: `scripts/` - Utility scripts (ingestion, setup)

### Naming Conventions

- **Client folders**: `lowercase_with_underscores` (e.g., `david_chen`)
- **Email files**: `YYYY-MM-DD_descriptive_name.txt`
- **Meeting transcripts**: `YYYY-MM-DD_meeting_topic.txt`
- **Memory files**: `YYYY-MM-DD.md` (daily logs)

### Code Style

- **Type hints**: Use throughout for clarity
- **Docstrings**: Required for all tools and public functions
- **Error handling**: Wrap external API calls in try-except blocks
- **Async/await**: Use for I/O operations (file reads, API calls)
- **Tool descriptions**: Must be clear and specific for LLM understanding

### Testing Approach

- **Unit tests**: Test individual tools in isolation
- **Integration tests**: Test sub-agent interactions
- **End-to-end tests**: Test full Jarvis workflows
- **Demo scenarios**: Use `sample/` directory for standardized test cases

## 🔧 Key Implementation Details

### Agent Invocation Pattern

```python
# For Jarvis (main orchestrator)
result = await agent.ainvoke(
    {"messages": [("user", request.message)]},
    config={"configurable": {"thread_id": thread_id}}
)

# For sub-agents (atlas, emma, colin)
result = await atlas_agent.ainvoke(
    {"messages": [("user", query)]},
    config={"configurable": {"thread_id": thread_id}}
)
```

### Notification System

Notifications are stored in-memory and exposed via `/api/notifications`:

```python
def add_notification(notification_type: str, title: str, message: str):
    notification = {
        "id": str(uuid.uuid4()),
        "type": notification_type,  # info, warning, action, success
        "title": title,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "read": False
    }
    _notifications.insert(0, notification)
```

### Email Draft Workflow

1. Jarvis/Emma drafts email → stored in `_email_suggestions`
2. Advisor reviews in UI → can edit body
3. Approve → Calendar MCP sends and archives
4. Reject → removed from pending list

### Middleware Stack

All agents use consistent middleware:

```python
middleware=[
    TodoListMiddleware(),           # Task tracking
    ModelRetryMiddleware(           # Automatic retries
        max_retries=3,
        backoff_factor=2.0,
        initial_delay=1.0,
    ),
]
```

## 🚨 Critical Safety Rules

1. **Never modify client data** without explicit advisor approval
2. **Always use Colin** before sending client-facing recommendations
3. **Cite sources** in all Emma-generated documents
4. **Respect workspace isolation** - all operations within `workspace/`
5. **Handle sensitive data** - never log client information
6. **Validate file uploads** - only `.txt` files allowed via API

## 📊 Data Flow Patterns

### Urgency Sweep (Reactive)
```
User Query → Jarvis → glob/find files (last 10 days) 
→ Atlas (analyze each) → Jarvis (synthesize) → User
```

### Heartbeat (Proactive)
```
Scheduler → Jarvis (read HEARTBEAT.md) → find_files_updated_after 
→ Atlas (analyze new files) → Colin (verify) 
→ send_important_notification OR send_draft_email
```

### Document Generation
```
User Request → Jarvis → Emma (draft) → Atlas (gather context) 
→ Emma (finalize) → Colin (compliance check) → User
```

## 🔌 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/chat` | POST | Send message to any agent |
| `/api/clients` | GET | List all clients from workspace |
| `/api/upload` | POST | Upload client documents |
| `/api/notifications` | GET/POST | Manage advisor notifications |
| `/api/email-suggestions` | GET | Get pending email drafts |
| `/api/email-suggestions/{id}/approve` | POST | Approve and send email |
| `/api/scheduled-tasks` | GET | List all cron jobs |
| `/ws/voice` | WebSocket | Real-time voice interaction |

## 🎨 Frontend Structure

```
frontend/src/
├── pages/
│   ├── DashboardPage.jsx    # Overview with notifications
│   ├── ChatPage.jsx         # Multi-agent chat interface
│   ├── ClientsPage.jsx      # Client list and file upload
│   └── MeetingsPage.jsx     # Calendar with Atlas insights
├── components/
│   ├── NotificationPanel.jsx
│   ├── EmailSuggestions.jsx
│   ├── ScheduledTasks.jsx
│   └── Sidebar.jsx
└── hooks/
    └── useAudioRecorder.js  # Voice recording logic
```

## 🧪 Testing Scenarios

### Demo 1: Reactive Urgency Sweep
Ask Jarvis: *"Show me anything in the last 10 days that looks urgent across my book?"*
- Jarvis scans `datasets/**/email_archive/*.txt` and `datasets/**/meeting_transcripts/*.txt`
- Filters files by date (last 10 days from today)
- Uses Atlas to analyze each file for urgency
- Returns synthesized report

### Demo 2: Proactive Heartbeat
1. Upload `sample/2026-02-01_ill_situation.txt` to Gareth Cheeseman's email archive
2. Wait for next heartbeat (max 30 min)
3. Jarvis detects new file, reads context, consults Atlas
4. Raises notification or drafts email automatically

### Demo 3: Multi-Agent Telegram Chat
```
@jarvis Who are my top 3 clients by AUM?
@atlas What did Alan say about risk tolerance?
@emma Draft an email to Gareth about his policy
@colin Is it compliant to guarantee 5% returns?
```

## 🔄 Common Development Tasks

### Adding a New Client

1. Create folder: `workspace/datasets/client_name/`
2. Add `crm.json` with client details
3. Create subfolders: `email_archive/`, `meeting_transcripts/`
4. Run ingestion: `python scripts/ingest_documents.py`

### Modifying Jarvis's Behavior

1. Edit relevant workspace file:
   - `SOUL.md` - Personality changes
   - `IDENTITY.md` - Role adjustments
   - `HEARTBEAT.md` - Proactive task updates
2. Restart API (prompt rebuilds on startup)

### Debugging Agent Responses

1. Check agent-specific system prompts in `src/jarvis/sub_agents/`
2. Test sub-agent standalone using `__main__` block
3. Review tool descriptions - LLM relies on these for tool selection
4. Check middleware logs for retry attempts

### Adding Scheduled Tasks

```python
from jarvis.tools.scheduler import add_cron_job

add_cron_job(
    name="weekly_portfolio_review",
    cron_expression="0 9 * * MON",  # Every Monday at 9 AM
    task_description="Review all client portfolios for rebalancing opportunities",
    model="openai:gpt-4o-mini"
)
```

## 📦 Dependencies

Key packages (see `pyproject.toml` for full list):

- `deepagents>=0.3.12` - Core agent framework
- `langchain>=1.2.9` - LLM orchestration
- `langchain-openai>=1.1.7` - OpenAI integration
- `langchain-mcp-adapters>=0.1.0` - MCP server support
- `chromadb>=1.4.1` - Vector database
- `fastapi>=0.115.0` - Web framework
- `python-telegram-bot>=22.6` - Telegram integration
- `apscheduler>=3.11.2` - Background scheduling
- `tavily>=1.1.0` - Web search for compliance

## 🚀 Deployment

### Backend (Railway)
- Deployed via `Procfile`: `web: uvicorn jarvis.api:app --host 0.0.0.0 --port $PORT`
- Environment variables required: `OPENAI_API_KEY`, `TAVILY_API_KEY`, `TELEGRAM_BOT_TOKEN`

### Frontend (Vercel)
- Build command: `npm run build`
- Output directory: `dist`
- Environment variable: `VITE_API_URL` (points to Railway backend)

## 🎓 Learning Resources

- Some docs to external packages used in this project are in the `external_package_docs` folder


