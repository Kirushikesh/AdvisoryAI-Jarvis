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

| Agent | Module | Role | Description |
| :--- | :--- | :--- | :--- |
| **Atlas** | `atlas.py` | RAG Specialist | Analyzes client docs, emails, and transcripts. Always ground insights in retrieved context. |
| **Emma** | `emma.py` | Paraplanner | Converts raw data into client-facing docs (emails, reports) with traceable reasoning. |
| **Colin** | `colin.py` | Compliance | Reviews outputs against UK FCA regulations. Returns binary Pass/Fail with reasoning. |

## 🛠️ Tools Registry

Agents have access to specialized tools in `src/jarvis/tools/`:
- **Market News:** `get_market_news` retrieves real-time financial updates.
- **Scheduler:** `add_cron_job`, `remove_cron_job`, etc., for periodic background work.
- **Monitor:** `find_files_updated_after` for tracking workspace modifications.

## 📜 Agent Working Conventions

1.  **Workspace Isolation:** Always perform file operations within the `workspace/` directory. Use the `WORKSPACE_DIR` constant defined in `deepagent.py`.
2.  **Safety First:** Colin must be consulted (or the Colin sub-agent used) before finalizing any client-facing recommendation.
3.  **NAR_MODE:** Follow the "Tool Call Style" defined in `deepagent.py`: do not narrate routine calls, but keep narration brief for complex multi-step work.
4.  **Prompts:** When modifying Jarvis's behavior, edit the `.md` files in `workspace/` rather than hardcoding prompts in Python files.
