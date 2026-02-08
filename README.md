# Jarvis - The Proactive AI Agent for Financial Advisors

Jarvis is a sophisticated AI assistant designed specifically for Independent Financial Advisors (IFAs). Built on a "Board of Specialists" architecture, Jarvis autonomously monitors client data, identifies risks, and drafts professional communications.

---

## 🏗️ Core Architecture

- **Jarvis Orchestrator**: The central brain that manages delegation and identity synthesis.
- **Atlas (RAG Specialist)**: Deep-dives into client files, emails, and transcripts.
- **Emma (Paraplanner)**: Drafts suitability reports and advisor correspondence.
- **Colin (Compliance)**: Ensures all outputs meet UK FCA regulations.

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
3. **Trigger the Pulse**:
   - Ensure the heartbeat is running: `python -m jarvis.jarvis_heartbeat`.
   - (Optional) Force a heartbeat by typing `/heartbeat` in the chat.
4. **The Result**: Within seconds, a notification will appear in the Dashboard: 
   > *"🚨 Jarvis Alert: Gareth Cheeseman has emailed regarding income protection policies due to illness..."*

---

## 🛠️ Usage & Commands

### 1. Ingest Base Data
```bash
python scripts/ingest_documents.py
```

### 2. Run Backend & Heartbeat
```bash
# Terminal 1: API
uv run uvicorn jarvis.api:app --reload --port 8000

# Terminal 2: Background Heartbeat
python -m jarvis.jarvis_heartbeat
```

### 3. Run Frontend
```bash
cd frontend && npm run dev
```

---

## 📂 Project Structure
- `src/jarvis/`: Core Agent and Sub-agent logic.
- `workspace/`: Operating environment, prompts, and client datasets.
- `frontend/`: Advisor dashboard.
- `sample/`: Standardized text data for system validation.

---

*“I’m not just a chatbot; I’m a teammate who never sleeps.”* — **Jarvis**
