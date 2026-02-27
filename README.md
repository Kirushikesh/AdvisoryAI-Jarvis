# Jarvis - The Proactive AI Agent for Financial Advisors

Jarvis is a sophisticated AI assistant designed specifically for Independent Financial Advisors (IFAs). Built on a "Board of Specialists" architecture, Jarvis autonomously monitors client data, identifies risks, and drafts professional communications.

---

## 🚀 Hackathon Journey: Prelims to Finals

This final submission significantly elevates the preliminary architecture to directly address the **Final Round Evaluation Criteria**:

* **"MCP Integration Backbone" (Technical Ambition):** Replaced static Python tools with true Model Context Protocol (MCP) servers. Jarvis now natively integrates with a **Calendar MCP** (for scheduling and email management) and a **Market Feed MCP** (for live macroeconomic data and news).
* **Action Execution - "Adviser approves, not produces" (30% Adviser Would Use It):** Shifted the UI paradigm from passive notifications to active staging. When Jarvis's heartbeat detects an issue, the `Emma` and `Colin` sub-agents proactively draft a compliance-checked response. The advisor simply clicks **"Approve & Send"** or **"Edit"** in the dashboard, ensuring complete regulatory control.
* **Pre-Meeting Insights:** Integrated a **"Get Insights with Atlas"** feature directly into the Calendar UI. Before a meeting, Atlas automatically queries ChromaDB to map the client's past discussions, risk tolerance, and open action items into a pre-meeting brief.
* **Multi-Channel & Voice (25% Technical Ambition):** Pushed the boundaries of the tech stack by implementing Telegram integration with agent-routing (`@jarvis`, `@emma`, `@colin`) and a WebSocket-based **Voice Pipeline (Sandwich Architecture)** featuring real-time STT and TTS.

---

## 🎥 Demo Recordings
**[View Demo Videos and Slide Deck on Google Drive](https://drive.google.com/drive/u/0/folders/1AIWCfXR0D3X2tHkzCKVuaYE480TbVNAc)**

---

## 🌐 Live Deployment

| Component | URL |
|-----------|-----|
| **Frontend** | [advisory-ai-jarvis.vercel.app](https://advisory-ai-jarvis.vercel.app/) |
| **Backend API** | [Railway API Docs](https://advisoryai-jarvis-production-bcea.up.railway.app/docs) |

> **Login Credentials:** Username: `abimanyu` | Password: `admin`

---

## 🏗️ Core Architecture

- **Jarvis Orchestrator**: The central brain that manages delegation and identity synthesis.
- **Atlas (RAG Specialist)**: Deep-dives into client files, emails, and transcripts.
- **Emma (Paraplanner)**: Drafts suitability reports and advisor correspondence.
- **Colin (Compliance)**: Ensures all outputs meet UK FCA regulations.

### Model Usage
| Context | Model |
|---------|-------|
| Direct Chat (Jarvis) | `openai:gpt-5.1-chat-latest` |
| Heartbeat & Cron Jobs | `openai:gpt-4o-mini` |
| Voice Agents (TTS & STT)| Built-in OpenAI models |

---

## ⚙️ Core Features & Capabilities

### 1. LangChain Deep Agents
Jarvis is built using [LangChain Deep Agents](https://github.com/langchain-ai/deepagents), a framework for creating sophisticated AI agents with tool use, planning, and sub-agent delegation. This provides Jarvis with:
- **Autonomous reasoning** with multi-step planning.
- **Tool orchestration** with built-in filesystem, web, and custom tools.
- **Sub-agent delegation** for specialized tasks.

### 2. Multi-Channel Communication (Telegram & Voice)
- **Telegram Integration**: Advisors can communicate with Jarvis or any of the sub-agents directly from Telegram, making the assistant accessible on the go.
- **Voice Agents**: Jarvis and its sub-agents feature built-in voice capabilities. Text-to-Speech (TTS) and Speech-to-Text (STT) are seamlessly integrated using OpenAI models, enabling natural Voice-to-Voice interactions via a "Sandwich Architecture".

### 3. Dynamic System Prompt
Instead of a static prompt, Jarvis builds its personality and context dynamically at runtime by reading workspace files:
- `SOUL.md` - Core personality and values.
- `IDENTITY.md` - Professional identity as a financial advisor assistant.
- `USER.md` - Information about the advisor Jarvis serves.
- `HEARTBEAT.md` - Instructions for autonomous background checks.

### 4. Sub-Agents (Board of Specialists)
Jarvis delegates specialized tasks to three expert sub-agents:

| Agent | Role | When Used |
|-------|------|-----------|
| **Atlas** | RAG Specialist | Searches client documents, emails, and transcripts |
| **Emma** | Paraplanner | Drafts professional client communications |
| **Colin** | Compliance | Validates outputs against UK FCA regulations |

### 5. MCP Server Integrations (Calendar & News)
Jarvis natively connects to standardized Model Context Protocol (MCP) servers:
- **Calendar MCP**: Directly integrates calendar capabilities. The UI features a dedicated **Calendar Page**, where advisors can click **"Get Insights with Atlas"** on any meeting to automatically have Atlas query relevant client files and prepare insights.
- **Market News MCP**: Equips the orchestrator with specialized tools to fetch macroeconomic indicators, financial news, and asset performance via Tavily and other sources.

### 6. Email Drafts & Advisor Approval Workflow
Jarvis and Emma autonomously draft responses to incoming client emails. 
- These drafts are populated directly in the **UI's Email Drafts** section.
- The advisor can review, edit, approve, or reject these drafts before they are sent, ensuring complete compliance and control over client correspondence.

### 7. Proactive Background Heartbeat
Jarvis runs continuously in the background using APScheduler. 
- During a heartbeat, Jarvis monitors live market news and client files.
- **Direct Actions:** If urgent info is found, Jarvis can directly use its tools to **Raise a Notification** to the advisor via the UI/Telegram, or generate an **Email Draft** to proactively handle the situation without explicit prompting.

### 8. Memory & Vector Store (ChromaDB)
Client documents (emails, transcripts, policies) are embedded and stored in ChromaDB for semantic search. This enables:
- **Context-aware retrieval** - Find relevant documents based on meaning, not just keywords
- **Cross-client analysis** - Search across all clients for similar situations

### 9. Custom Tools
Jarvis has access to both default and custom tools:

**Default Deep Agent Tools:**
- Filesystem operations (read, write, list, glob)
- Web browsing and search
- Planning and task management

**Custom Financial & System Tools:**
| Tool | Purpose |
|------|---------|
| `get_macro_indicators` | Fetches macroeconomic indicators via Market News MCP |
| `search_financial_news`| Searches for recent UK Financial/Regulatory news via Market News MCP |
| `get_asset_performance`| Checks performance snapshots for assets via Market News MCP |
| `raise_notification` | Sends an urgent alert directly to the dashboard from the heartbeat |
| `draft_email` | Drafts a client email for advisor review |
| `retrieve_context` | Vector search in ChromaDB (Atlas) |
| `search_uk_compliance` | FCA regulatory search (Colin) |

---

## 🚀 Quick Start: Testing the Demos

### Login to Dashboard
- **Username**: `abimanyu`
- **Password**: `admin`

### Demo 1: The Reactive "Urgency Sweep"
*Test Jarvis's ability to scan his entire "book" for urgent matters.*
1. **Launch the Dashboard**: Run `cd frontend && npm run dev`.
2. **Open the Chat**: Navigate to the "Chat" page.
3. **Ask the Query**: *"Show me anything in the last 10 days that looks urgent across my book (emails and meeting notes)?"*
4. **Behind the Scenes**: Jarvis will scan `datasets/**` for files modified between Jan 28 and Feb 08, 2026, and use **Atlas** to identify risks.

### Demo 2: The Proactive Heartbeat (Gareth Cheeseman)
*Test how Jarvis identifies new incoming data and alerts you autonomously.*
1. **Prepare the Data**: Locate the sample email in `sample/2026-02-01_ill_situation.txt`.
2. **Upload**: Go to the "Clients" page in the dashboard -> Select **Gareth Cheeseman** -> Upload the sample file as an "Email Archive" document.
3. **The Result**: Within 30 minutes (or on the next heartbeat), a notification or email draft will appear in the Dashboard: *"🚨 Jarvis Alert: Gareth Cheeseman has emailed regarding income protection policies due to illness..."*

### Demo 3: Multi-Agent Telegram Chat
*Test how advisors can talk to any of the sub-agents on the go.*
1. **Setup Token**: Ensure `TELEGRAM_BOT_TOKEN` is set in your `.env` file.
2. **Start the Bot**: Open a terminal and run `uv run python src/jarvis/telegram_bot.py`.
3. **Chat on Telegram**: Go to telegram and find your bot.
4. **Invoke Agents**: Prefix your messages with the agent's name to route the query:
   - `@jarvis Who are my top 3 clients by AUM?`
   - `@emma Draft a quick email to Gareth letting him know we are looking into his policy.`
   - `@atlas What did Alan say in our last meeting about his risk tolerance?`

---

## 🛠️ Local Development

### 1. Ingest Base Data
```bash
python scripts/ingest_documents.py

```

### 2. Run Backend (API + Heartbeat + WebSocket)

```bash
uv run uvicorn jarvis.api:app --reload --port 8000

```
> **Note**: The heartbeat scheduler now runs as a background thread within the API. Websockets are enabled and expose the STT/TTS sandwich layers.

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

### 1. The "Live Whisperer" (Real-Time Meeting Assistant)

The ultimate execution of the "Proactive Hunch Engine." Jarvis will serve as a background listener during Zoom/GMeet client calls. By processing streaming audio transcripts in real-time, Jarvis will push hidden, compliance-checked prompts to the advisor's dashboard mid-conversation (e.g., *"Client mentioned retiring early. Their current trajectory won't meet the £55k target. Suggest modeling a salary sacrifice."*).

### 2. Compliance-Audited Client Group Chats

Embed Jarvis in WhatsApp or Slack group chats between the advisor and client families. To maintain strict FCA compliance, `Colin` will audit every response generated by Jarvis. The advisor will use an "Approve & Forward" workflow, ensuring clients get rapid, accurate answers while keeping the advisor fully in the loop.

### 3. Performance Benchmarking

Evaluate Jarvis quality using human judges (advisor ratings on response quality), LLM-as-judge scoring for consistency, and task completion metrics.

---

*"I'm not just a chatbot; I'm a teammate who never sleeps."* — **Jarvis**