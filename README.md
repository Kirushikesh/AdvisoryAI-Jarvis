# Jarvis - The Proactive AI Agent for Financial Advisors

Jarvis is a sophisticated AI assistant designed specifically for Independent Financial Advisors (IFAs). Built on a "Board of Specialists" architecture, Jarvis autonomously monitors client data, identifies risks, and drafts professional communications.

---

## 🎥 Demo Recordings
**[View Demo Videos and Slide Deck on Google Drive](https://drive.google.com/drive/u/0/folders/1AIWCfXR0D3X2tHkzCKVuaYE480TbVNAc)**

---

## 🌐 Live Deployment

| Component | URL |
|-----------|-----|
| **Frontend** | [Vercel Dashboard](https://advisory-ai-jarvis.vercel.app) |
| **Backend API** | [Railway API Docs](https://advisoryai-jarvis-production-bcea.up.railway.app/docs) |

---

## 🏗️ Core Architecture

- **Jarvis Orchestrator**: The central brain that manages delegation and identity synthesis.
- **Atlas (RAG Specialist)**: Deep-dives into client files, emails, and transcripts.
- **Emma (Paraplanner)**: Drafts suitability reports and advisor correspondence.
- **Colin (Compliance)**: Ensures all outputs meet UK FCA regulations.

### Model Usage
| Context | Model |
|---------|-------|
| Direct Chat (Jarvis) | `openai:gpt-4.1` |
| Heartbeat & Cron Jobs | `openai:gpt-oss-120b` |

---

## ⚙️ Core Features & Capabilities

### 1. LangChain Deep Agents
Jarvis is built using [LangChain Deep Agents](https://github.com/langchain-ai/deepagents), a framework for creating sophisticated AI agents with tool use, planning, and sub-agent delegation. This provides Jarvis with:
- **Autonomous reasoning** with multi-step planning
- **Tool orchestration** with built-in filesystem, web, and custom tools
- **Sub-agent delegation** for specialized tasks

### 2. Dynamic System Prompt
Instead of a static prompt, Jarvis builds its personality and context dynamically at runtime by reading workspace files:
- `SOUL.md` - Core personality and values
- `IDENTITY.md` - Professional identity as a financial advisor assistant
- `USER.md` - Information about the advisor Jarvis serves
- `HEARTBEAT.md` - Instructions for autonomous background checks

This allows the advisor to customize Jarvis's behavior by simply editing markdown files.

### 3. Sub-Agents (Board of Specialists)
Jarvis delegates specialized tasks to three expert sub-agents:

| Agent | Role | When Used |
|-------|------|-----------|
| **Atlas** | RAG Specialist | Searches client documents, emails, and transcripts |
| **Emma** | Paraplanner | Drafts professional client communications |
| **Colin** | Compliance | Validates outputs against UK FCA regulations |

Each sub-agent has its own system prompt, tools, and communication style.

### 4. Skills
Skills are modular, file-based instruction sets that extend Jarvis's capabilities without modifying code. Located in `./skills/`, each skill contains:
- `SKILL.md` - Instructions and workflows
- Supporting scripts and templates

Jarvis automatically loads and uses relevant skills based on the task context.

### 5. Cron Jobs (Scheduled Tasks)
Jarvis can schedule its own future tasks using APScheduler. This enables:
- **Periodic reviews** - e.g., "Review client portfolios every Monday at 9am"
- **Deadline reminders** - e.g., "Remind me about Sarah's annual review in 3 days"
- **Autonomous monitoring** - Self-scheduled tasks that run without human intervention

The dashboard displays all scheduled tasks and allows manual cancellation.

### 6. Memory Files
Jarvis maintains persistent memory through workspace files:
- `memory/daily_log.md` - Record of daily interactions and outcomes
- `memory/client_notes.md` - Important client-specific observations

This allows Jarvis to recall past conversations and build context over time.

### 7. Silent Reply Tokens
To save tokens and avoid unnecessary chatter, Jarvis uses special tokens:
- `NO_REPLY` - When there's nothing meaningful to say (e.g., simple greetings)
- `HEARTBEAT_OK` - When a background check finds nothing urgent

The API filters these tokens so they never reach the user interface.

### 8. ChromaDB Vector Store
Client documents (emails, transcripts, policies) are embedded and stored in ChromaDB for semantic search. This enables:
- **Context-aware retrieval** - Find relevant documents based on meaning, not just keywords
- **Cross-client analysis** - Search across all clients for similar situations
- **Efficient long-term memory** - Store large document collections without token limits

### 9. Tools
Jarvis has access to both default and custom tools:

**Default Tools (from Deep Agents):**
- Filesystem operations (read, write, list, glob)
- Web browsing and search
- Planning and task management

**Custom Tools:**
| Tool | Purpose |
|------|---------|
| `get_market_news` | Fetches live UK financial news via Tavily |
| `find_files_updated_after` | Detects recently modified workspace files |
| `add_cron_job` | Schedules future tasks |
| `remove_cron_job` | Cancels scheduled tasks |
| `list_cron_jobs` | Shows all scheduled tasks |
| `retrieve_context` | Vector search in ChromaDB (Atlas) |
| `search_uk_compliance` | FCA regulatory search (Colin) |

---

## 🚀 Quick Start: Testing the Demos

### Demo 1: The Reactive "Urgency Sweep"
*Test Jarvis's ability to scan his entire "book" for urgent matters.*

1. **Launch the Dashboard**: Run `cd frontend && npm run dev`.
2. **Open the Chat**: Navigate to the "Chat" page.
3. **Ask the Query**:
   > *"Show me anything in the last 10 days that looks urgent across my book (emails and meeting notes)?"*
4. **Behind the Scenes**: Jarvis will scan `datasets/**` for files modified between Jan 28 and Feb 08, 2026, and use **Atlas** to identify risks.

### Demo 2: The Proactive Heartbeat (Gareth Cheeseman)
*Test how Jarvis identifies new incoming data and alerts you autonomously.*

1. **Prepare the Data**: Locate the sample email in `sample/2026-02-01_ill_situation.txt`.
2. **Upload**: 
   - Go to the "Clients" page in the dashboard.
   - Select **Gareth Cheeseman**.
   - Upload the sample file as an "Email Archive" document.
3. **The Result**: Within 30 minutes (or on the next heartbeat), a notification will appear in the Dashboard: 
   > *"🚨 Jarvis Alert: Gareth Cheeseman has emailed regarding income protection policies due to illness..."*

---

## 🛠️ Local Development

### 1. Ingest Base Data
```bash
python scripts/ingest_documents.py
```

### 2. Run Backend (API + Heartbeat)
```bash
uv run uvicorn jarvis.api:app --reload --port 8000
```
> **Note**: The heartbeat scheduler now runs as a background thread within the API.

### 3. Run Frontend
```bash
cd frontend && npm run dev
```

---

## 📂 Project Structure
- `src/jarvis/`: Core Agent and Sub-agent logic.
- `workspace/`: Operating environment, prompts, and client datasets.
- `frontend/`: Advisor dashboard (React + Vite).
- `sample/`: Standardized text data for system validation.
- `skills/`: Modular skill definitions.

---

## 🔮 Future Directions

### 1. Multi-Channel Communication
Integrate Jarvis with WhatsApp, Telegram, and Slack gateways so advisors can interact from their preferred messaging platform - not just the web dashboard.

### 2. Direct Email & Calendar Integration
Connect Jarvis directly to Gmail, Outlook, and calendar APIs via MCP (Model Context Protocol) servers. This would enable:
- Automatic email ingestion without manual uploads
- Meeting scheduling and follow-up reminders
- Real-time client communication monitoring

### 3. Group Chat with Clients
Embed Jarvis in group chats between advisor and client families. The advisor could invoke Jarvis with `@jarvis` to:
- Answer client questions with compliance-checked responses
- Pull relevant policy details mid-conversation
- Draft follow-up actions in real-time

### 4. Performance Benchmarking
Evaluate Jarvis quality using:
- **Human judges** - Advisor ratings on response quality
- **LLM-as-judge** - Automated scoring for consistency and compliance
- **Task completion metrics** - Success rate on standard scenarios

### 5. Extensible Skills Library
Build a library of shareable skills:
- Annual review workflows
- Product recommendation templates
- Regulatory update handlers
- Client onboarding wizards

---

*"I'm not just a chatbot; I'm a teammate who never sleeps."* — **Jarvis**
