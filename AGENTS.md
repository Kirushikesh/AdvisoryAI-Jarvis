# AGENTS.md - CLI Agent Guide for Jarvis

This document serves as a guide for AI agents (CLI agents, coding assistants, assistants) working on the **Jarvis** project. It outlines the project architecture, roles, and operational conventions.

## 🚀 Project Overview

**Jarvis** is a Deep Agent designed for Independent Financial Advisors (IFAs). It acts as a proactive assistant that can research market news, analyze client data, generate professional documents, and ensure regulatory compliance.

## 🏗️ Core Architecture

The system is built as a **Deep Agent** using the `deepagents` framework, which orchestrates various specialist sub-agents.

- **Main Entry Point:** `src/jarvis/deepagent.py` - Defines the Jarvis agent, its tools, and its sub-agents.
- **Backend:** Uses a `FilesystemBackend` for managing workspace persistence.
- **Prompt Source:** Prompts are dynamically loaded from the `workspace/` directory.

## 📂 Folder Structure

```text
.
├── workspace/                # Agent operating environment & persistence
│   ├── AGENTS.md             # Instructions FOR JARVIS (not for code assistants)
│   ├── SOUL.md               # Jarvis's identity & personality
│   ├── IDENTITY.md           # Role definition
│   ├── USER.md               # Context about the advisor
│   ├── TOOLS.md              # Documentation for Jarvis's tools
│   ├── HEARTBEAT.md          # Proactive task checklist
│   ├── MEMORY.md             # Long-term client/advisor insights
│   └── memory/               # Daily logs and state files
├── src/jarvis/               # Application Source Code
│   ├── sub_agents/           # Specialist sub-agent definitions
│   │   ├── atlas.py          # RAG Specialist
│   │   ├── emma.py           # Paraplanner (Document Generator)
│   │   ├── colin.py          # Compliance Guardrail
│   │   └── __init__.py       # Exports sub-agent graphs
│   ├── tools/                # Custom tool implementations
│   │   ├── news.py           # Market news retrieval
│   │   ├── scheduler.py      # Cron/periodic task management
│   │   ├── file_monitor.py   # Workspace change tracking
│   │   └── user_interaction.py # Advisor feedback tools
│   ├── utils/                # Utility classes (Vector store, etc.)
│   ├── config.py             # Environment configuration
│   ├── api.py                # FastAPI endpoint
│   └── deepagent.py          # Core agent assembly
├── frontend/                 # React frontend (Vite/Tailwind)
├── raw_datasets/            # Source data for RAG ingestion
├── scripts/                  # Helper scripts (ingestion, setup)
└── pyproject.toml            # Dependencies (uv)
```

## 🤖 Sub-Agent Registry

| Agent | Role | Focus |
| :--- | :--- | :--- |
| **Atlas** | RAG Specialist | Analyzes client docs, emails, and transcripts. Grounded in ChromaDB and Workspace data. |
| **Emma** | Paraplanner | Generates professional client documents with traceable reasoning. |
| **Colin** | Compliance | Binary Pass/Fail reviews against UK FCA regulations using live web search. |

## 🛠️ Key Capabilities & Tools

1. **Reactive Urgency Check (10-Day Sweep):** Jarvis can scan the last 10 days of emails and meeting notes across the entire client book.
2. **Proactive Heartbeat:** A background pulse (`jarvis_heartbeat.py`) that monitors workspace changes and alerts the advisor via the dashboard.
3. **Custom Tools:**
    - `get_market_news`: Real-time UK financial updates.
    - `find_files_updated_after`: Targeted detection of new workspace documents.
    - `add_cron_job`: Dynamic scheduling for recurring advisory tasks.

## 📂 Project Navigation

- `src/jarvis/`: Core logic and agent definitions.
- `workspace/`: Jarvis's operational brain and client datasets.
- `frontend/`: React-based advisor dashboard.
- `sample/`: Standardized data for testing and demonstrations.

## 📜 Agent Working Conventions

1.  **Workspace Isolation:** Always perform file operations within the `workspace/` directory. Use the `WORKSPACE_DIR` constant defined in `deepagent.py`.
2.  **Safety First:** Colin must be consulted (or the Colin sub-agent used) before finalizing any client-facing recommendation.
3.  **NAR_MODE:** Follow the "Tool Call Style" defined in `deepagent.py`: do not narrate routine calls, but keep narration brief for complex multi-step work.
4.  **Prompts:** When modifying Jarvis's behavior, edit the `.md` files in `workspace/` rather than hardcoding prompts in Python files.
