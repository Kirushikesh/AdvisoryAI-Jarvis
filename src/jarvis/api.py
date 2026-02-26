"""
FastAPI backend for Jarvis Financial Advisor system.
Provides endpoints for chat, file upload, and notifications.
"""

import os
import shutil
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager

# Load environment variables BEFORE importing Jarvis modules
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True)

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio

# Import Jarvis modules AFTER loading .env
from jarvis.deepagent import create_jarvis_agent, init_calendar_tools, init_market_feed_tools
from jarvis.config import WORKSPACE_DIR  # Use config.py for correct workspace path
from jarvis.sub_agents.atlas import atlas_agent
from jarvis.sub_agents.emma import emma_agent
from jarvis.sub_agents.colin import colin_agent
from jarvis.tools.scheduler import get_all_scheduled_jobs, add_cron_job, task_descriptions


# ============================================================================
# Models
# ============================================================================

class ChatRequest(BaseModel):
    message: str
    agent: str = "jarvis"  # jarvis, atlas, emma, colin
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    thread_id: str
    agent: str


class Notification(BaseModel):
    id: str
    type: str  # info, warning, action, success
    title: str
    message: str
    timestamp: str
    read: bool = False


class ClientInfo(BaseModel):
    name: str
    folder: str
    file_count: int


class EmailSuggestion(BaseModel):
    id: str
    client_name: str
    to: str
    subject: str
    body: str
    status: str = "pending"  # pending | approved | rejected
    created_at: str


class ApproveEmailRequest(BaseModel):
    edited_body: Optional[str] = None


# ============================================================================
# Notification Storage (in-memory for simplicity)
# ============================================================================

_notifications: List[dict] = []
MAX_NOTIFICATIONS = 50


# ============================================================================
# Email Suggestion Storage (in-memory)
# ============================================================================

_email_suggestions: dict = {}


def seed_email_suggestions():
    """Seed demo email suggestions that Jarvis has drafted and Emma has verified."""
    suggestions = [
        {
            "id": str(uuid.uuid4()),
            "client_name": "David Chen",
            "to": "David Chen <david.chen@globalbank.com>",
            "subject": "Remortgage Options – Summary Attached",
            "body": (
                "Hi David,\n\n"
                "As discussed, I've attached the remortgage comparison.\n\n"
                "Key trade-off is flexibility versus certainty:\n"
                "- 5-year fix: lower rate, more optionality\n"
                "- 10-year fix: higher rate, but aligns with retirement horizon\n\n"
                "This becomes more nuanced if we layer in the French property, so I suggest "
                "we park a final decision until after the March trip.\n\n"
                "Happy to talk it through.\n\n"
                "Best,\nAbimanyu"
            ),
            "status": "pending",
            "created_at": "2026-02-26T16:18:00",
        },
        {
            "id": str(uuid.uuid4()),
            "client_name": "Keith Lard",
            "to": "David Green <david.green@accountancy.co.uk>",
            "subject": "Company Pension Contribution – Keith Lard",
            "body": (
                "Hi David,\n\n"
                "As discussed, please proceed with the £180,000 employer pension contribution "
                "for Keith Lard's SIPP before the company liquidation process begins.\n\n"
                "This utilises carry-forward allowances and is the preferred extraction method.\n\n"
                "Let us know once processed.\n\n"
                "Kind regards,\nAbimanyu"
            ),
            "status": "pending",
            "created_at": "2026-02-26T16:05:00",
        },
        {
            "id": str(uuid.uuid4()),
            "client_name": "Lisa Rahman",
            "to": "Lisa Rahman <lisa.rahman@digitalmarketing.co.uk>",
            "subject": "Wills – Solicitor Introduction",
            "body": (
                "Hi Lisa,\n\n"
                "Following up as promised — I've re-sent the details for the solicitor to update "
                "your wills and include both children, with guardianship for Mark confirmed.\n\n"
                "No urgency panic, but it's one of those things that's much easier done calmly.\n\n"
                "Let me know if you'd like me to chase on your behalf.\n\n"
                "Best,\nAbimanyu"
            ),
            "status": "pending",
            "created_at": "2026-02-26T13:42:00",
        },
        {
            "id": str(uuid.uuid4()),
            "client_name": "Priya Patel",
            "to": "Anil Patel <anil.patel@datainsights.com>",
            "subject": "Pension Consolidation – Forms Re-sent",
            "body": (
                "Hi Anil,\n\n"
                "I've re-sent the pension consolidation paperwork for the Accenture and Deloitte schemes.\n\n"
                "As a reminder, current charges are costing roughly £800 per year more than necessary. "
                "Once completed, this becomes a set-and-forget improvement.\n\n"
                "Let me know if you want me to walk through the forms quickly — otherwise, "
                "please aim to return these this month.\n\n"
                "Best,\nAbimanyu"
            ),
            "status": "pending",
            "created_at": "2026-02-26T15:21:00",
        },
    ]
    for s in suggestions:
        _email_suggestions[s["id"]] = s
    print("[API] Email suggestions seeded successfully")


def add_notification(notification_type: str, title: str, message: str):
    """Add a notification to the store."""
    notification = {
        "id": str(uuid.uuid4()),
        "type": notification_type,
        "title": title,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "read": False
    }
    _notifications.insert(0, notification)
    # Keep only the most recent notifications
    if len(_notifications) > MAX_NOTIFICATIONS:
        _notifications.pop()
    return notification


def seed_demo_data():
    """Seed demo notifications and scheduled tasks on API startup."""
    # Seed demo notifications
    demo_notifications = [
        ("warning", "📋 Compliance Review Required", "Emma has drafted a suitability letter for Sarah Thompson. Colin flagged it for review - missing risk warning disclosures. Please review before sending."),
        ("info", "📈 Market Update: UK Gilts", "Bank of England held interest rates at 4.5%. This may impact Brian Potter's fixed income allocation. Consider reviewing his portfolio."),
        ("success", "✅ Annual Review Complete", "Completed annual review for Emma Thompson. Updated risk profile and investment strategy documented. Next review scheduled for February 2027."),
        ("action", "🔔 Policy Renewal Reminder", "Brian Potter's life insurance policy renews in 14 days. Atlas found a potentially better rate with Scottish Widows. Recommend scheduling a call."),
    ]
    
    for notif_type, title, message in demo_notifications:
        add_notification(notif_type, title, message)
    
    # Seed demo scheduled tasks
    from jarvis.tools.scheduler import seed_demo_jobs
    seed_demo_jobs()
    
    print("[API] Demo data seeded successfully")


# Seed demo data on module load
seed_demo_data()
seed_email_suggestions()


# ============================================================================
# Agent Management
# ============================================================================

# Store active agents per thread
_agents = {}
_chat_histories = {}

def get_or_create_agent(agent_type: str, thread_id: str):
    """Get or create an agent for the given thread."""
    key = f"{agent_type}:{thread_id}"

    if key not in _agents:
        if agent_type == "jarvis":
            _agents[key] = create_jarvis_agent()
        elif agent_type == "atlas":
            _agents[key] = atlas_agent
        elif agent_type == "emma":
            _agents[key] = emma_agent
        elif agent_type == "colin":
            _agents[key] = colin_agent
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

    return _agents[key]


# ============================================================================
# FastAPI App
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    import threading
    from jarvis.jarvis_heartbeat import run_scheduler, heartbeat_job
    from jarvis.config import HEARTBEAT_INTERVAL_MINUTES

    print("🚀 Jarvis API starting...")
    print(f"📁 Workspace: {WORKSPACE_DIR}")

    # Pre-warm calendar MCP tools so the cache is ready before any request
    print("📅 Loading Calendar MCP tools...")
    await init_calendar_tools()
    print("📅 Calendar MCP tools ready")

    # Pre-warm market feed MCP tools
    print("📈 Loading Market Feed MCP tools...")
    await init_market_feed_tools()
    print("📈 Market Feed MCP tools ready")

    # Start heartbeat scheduler in background thread
    def start_heartbeat():
        print(f"💓 Heartbeat scheduler started ({HEARTBEAT_INTERVAL_MINUTES} min interval)")
        import time
        time.sleep(300)  # Wait for API to be fully ready
        heartbeat_job()
        run_scheduler()

    heartbeat_thread = threading.Thread(target=start_heartbeat, daemon=True)
    heartbeat_thread.start()

    yield
    print("👋 Jarvis API shutting down...")


app = FastAPI(
    title="Jarvis Financial Advisor API",
    description="Backend API for the Jarvis AI financial advisor system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for frontend
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Add frontend URL from environment variable if present
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/")
async def root():
    return {"status": "online", "service": "Jarvis Financial Advisor API"}


from jarvis.tools.voice_pipeline import stt_stream, agent_stream, tts_stream

@app.websocket("/ws/voice")
async def websocket_voice_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time voice interaction using the Sandwich architecture.
    Client sends PCM audio (bytes). Server sends STT text, Agent text, and TTS PCM audio back.
    """
    await websocket.accept()
    session_id = str(uuid.uuid4())
    print(f"[WebSocket] Voice connection established: {session_id}")

    # 1. Producer: Read audio bytes from the client into an async generator
    async def websocket_audio_stream():
        try:
            while True:
                data = await websocket.receive_bytes()
                yield data
        except WebSocketDisconnect:
            print(f"[WebSocket] Client disconnected: {session_id}")
        except Exception as e:
            print(f"[WebSocket] Error reading audio: {e}")

    try:
        # Create the pipeline: Audio -> STT -> Agent -> TTS
        stt_gen = stt_stream(websocket_audio_stream())
        agent_gen = agent_stream(stt_gen, session_id)
        tts_gen = tts_stream(agent_gen)
        
        # 2. Consumer: Loop through final pipeline outputs and send to client
        async for event in tts_gen:
            if event.type == "stt_chunk" or event.type == "stt_output":
                # Send transcript update
                await websocket.send_json({"type": event.type, "text": event.transcript})
            elif event.type == "agent_chunk":
                # Send text response from agent
                await websocket.send_json({"type": event.type, "text": event.text})
            elif event.type == "tts_chunk":
                # Send synthesized audio payload
                await websocket.send_bytes(event.audio)
            elif event.type == "error":
                await websocket.send_json({"type": "error", "message": event.message})
                
    except Exception as e:
        print(f"[WebSocket Pipeline Error] {e}")
        try:
            await websocket.send_json({"type": "error", "message": "Voice pipeline encountered an error."})
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
        print(f"[WebSocket] Voice connection closed: {session_id}")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to an agent and get a response.
    """
    thread_id = request.thread_id or str(uuid.uuid4())
    
    try:
        agent = get_or_create_agent(request.agent, thread_id)
        
        # Prepare the input
        config = {"configurable": {"thread_id": thread_id}}
        
        # Invoke the agent (ainvoke is non-blocking — releases the event loop while the LLM responds)
        if request.agent == "jarvis":
            result = await agent.ainvoke(
                {"messages": [("user", request.message)]},
                config
            )
            # Extract the last AI message
            response_text = ""
            for msg in reversed(result.get("messages", [])):
                if hasattr(msg, "content") and msg.type == "ai":
                    response_text = msg.content
                    break
        else:
            # Sub-agents (atlas, emma, colin)
            result = await agent.ainvoke(
                {"messages": [("user", request.message)]},
                config
            )
            response_text = ""
            for msg in reversed(result.get("messages", [])):
                if hasattr(msg, "content") and msg.type == "ai":
                    response_text = msg.content
                    break
        
        # Handle NO_REPLY responses
        if response_text.strip() == "NO_REPLY":
            response_text = "I don't have anything to add at this moment."
        
        return ChatResponse(
            response=response_text,
            thread_id=thread_id,
            agent=request.agent
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/clients", response_model=List[ClientInfo])
async def list_clients():
    """
    List all available clients from the workspace/datasets folder.
    """
    datasets_dir = WORKSPACE_DIR / "datasets"
    clients = []
    
    if datasets_dir.exists():
        for client_folder in sorted(datasets_dir.iterdir()):
            if client_folder.is_dir() and not client_folder.name.startswith('.'):
                # Count files in the folder
                file_count = len([f for f in client_folder.iterdir() if f.is_file()])
                
                # Convert folder name to display name
                display_name = client_folder.name.replace('_', ' ').title()
                
                clients.append(ClientInfo(
                    name=display_name,
                    folder=client_folder.name,
                    file_count=file_count
                ))
    
    return clients


@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    client: str = Form(...),
    upload_type: str = Form(...)
):
    """
    Upload a markdown file to a client's folder.
    """
    # Validate file type
    if not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Only .txt files are allowed")
    
    # Convert client name to folder name
    client_folder = client.lower().replace(' ', '_')
    target_dir = WORKSPACE_DIR / "datasets" / client_folder
    
    # Create folder if it doesn't exist
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine subfolder based on upload type
    if upload_type == "transcript":
        subfolder = "meeting_transcripts"
    else:
        subfolder = "email_archive"
    
    # Create subfolder
    (target_dir / subfolder).mkdir(exist_ok=True)
    
    # Save file
    target_path = target_dir / subfolder / file.filename
    
    try:
        content = await file.read()
        target_path.write_bytes(content)
        
        return {
            "success": True,
            "message": f"File uploaded to {client_folder}/{subfolder}/",
            "path": str(target_path.relative_to(WORKSPACE_DIR))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


class CreateNotificationRequest(BaseModel):
    type: str = "action"  # info, warning, action, success
    title: str
    message: str


@app.post("/api/notifications", response_model=Notification)
async def create_notification(request: CreateNotificationRequest):
    """
    Create a new notification (used by heartbeat system).
    """
    notification = add_notification(
        notification_type=request.type,
        title=request.title,
        message=request.message
    )
    return Notification(**notification)


@app.get("/api/notifications", response_model=List[Notification])
async def get_notifications():
    """
    Get recent notifications from Jarvis.
    Combines stored heartbeat notifications with file activity notifications.
    """
    notifications = []
    
    # First, add any stored heartbeat notifications (these are the priority ones)
    for n in _notifications:
        notifications.append(Notification(**n))
    
    # Then check for recent file changes in workspace (if we need more)
    if len(notifications) < 5:
        datasets_dir = WORKSPACE_DIR / "datasets"
        
        if datasets_dir.exists():
            recent_files = []
            for client_folder in datasets_dir.iterdir():
                if client_folder.is_dir():
                    for file_path in client_folder.rglob("*.md"):
                        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        recent_files.append((file_path, mtime, client_folder.name))
            
            recent_files.sort(key=lambda x: x[1], reverse=True)
            
            for file_path, mtime, client in recent_files[:3]:
                client_display = client.replace('_', ' ').title()
                
                notifications.append(Notification(
                    id=str(uuid.uuid4()),
                    type="info",
                    title=f"Document Activity: {client_display}",
                    message=f"File '{file_path.name}' was recently updated.",
                    timestamp=mtime.isoformat(),
                    read=False
                ))
    
    # Add a standing "online" notification if no other notifications
    if len(notifications) == 0:
        notifications.append(Notification(
            id=str(uuid.uuid4()),
            type="success",
            title="Jarvis Online",
            message="I'm ready to help. Ask me anything or upload documents for analysis.",
            timestamp=datetime.now().isoformat(),
            read=True
        ))
    
    return notifications[:10]  # Limit to 10 notifications


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "workspace": str(WORKSPACE_DIR),
        "workspace_exists": WORKSPACE_DIR.exists()
    }


# ============================================================================
# Scheduled Tasks
# ============================================================================

class ScheduledTask(BaseModel):
    id: str
    name: str
    description: str
    cron: str
    next_run: Optional[str] = None
    trigger: str


@app.get("/api/scheduled-tasks", response_model=List[ScheduledTask])
async def get_scheduled_tasks():
    """
    Get all scheduled cron jobs for display in the dashboard.
    """
    jobs = get_all_scheduled_jobs()
    return [ScheduledTask(**job) for job in jobs]


# ============================================================================
# Email Suggestions
# ============================================================================

@app.get("/api/email-suggestions", response_model=List[EmailSuggestion])
async def get_email_suggestions():
    """
    Return all pending email suggestions drafted by Jarvis and verified by Emma.
    """
    pending = [
        EmailSuggestion(**s)
        for s in _email_suggestions.values()
        if s["status"] == "pending"
    ]
    # Sort by created_at descending
    pending.sort(key=lambda x: x.created_at, reverse=True)
    return pending


@app.post("/api/email-suggestions/{suggestion_id}/approve")
async def approve_email_suggestion(
    suggestion_id: str,
    request: ApproveEmailRequest = ApproveEmailRequest(),
):
    """
    Approve a Jarvis-suggested email and send it via the Calendar MCP (saves to email_archive).
    """
    if suggestion_id not in _email_suggestions:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    suggestion = _email_suggestions[suggestion_id]
    if suggestion["status"] != "pending":
        raise HTTPException(status_code=400, detail=f"Suggestion is already {suggestion['status']}")

    # Use edited body if provided, otherwise use original
    body = request.edited_body if request.edited_body else suggestion["body"]

    try:
        # Directly call the calendar_server send_email function
        # (imported module, not subprocess — MCP tools are loaded at startup)
        from jarvis.tools.calendar_server import send_email as calendar_send_email
        result = calendar_send_email(
            client_name=suggestion["client_name"],
            to=suggestion["to"],
            subject=suggestion["subject"],
            body=body,
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail="Calendar MCP send_email failed")

        # Mark as approved
        _email_suggestions[suggestion_id]["status"] = "approved"

        return {
            "success": True,
            "message": result.get("message", "Email sent and archived successfully."),
            "filename": result.get("filename"),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


@app.post("/api/email-suggestions/{suggestion_id}/reject")
async def reject_email_suggestion(suggestion_id: str):
    """
    Reject a Jarvis-suggested email (removes it from the pending list).
    """
    if suggestion_id not in _email_suggestions:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    suggestion = _email_suggestions[suggestion_id]
    if suggestion["status"] != "pending":
        raise HTTPException(status_code=400, detail=f"Suggestion is already {suggestion['status']}")

    _email_suggestions[suggestion_id]["status"] = "rejected"
    return {"success": True, "message": "Email suggestion rejected."}


# ============================================================================
# Meetings
# ============================================================================

class Meeting(BaseModel):
    id: str
    client_name: str
    client_email: str
    subject: str
    content: str
    date: str          # YYYY-MM-DD
    start_time: str    # HH:MM
    end_time: str      # HH:MM


def _get_demo_meetings() -> List[dict]:
    """Return hardcoded demo meetings for the current week."""
    return [
        {
            "id": "mtg-001",
            "client_name": "Gareth Cheeseman",
            "client_email": "gareth.cheeseman@constructionpm.com",
            "subject": "Property Purchase & Protection Review",
            "content": (
                "Follow-up from Gareth's salary increase confirmation (now £78k). "
                "He has redirected extra income into house savings as agreed.\n\n"
                "Agenda:\n"
                "• Review deposit progress — current savings £45k vs target £40k deposit\n"
                "• Discuss timeline for property purchase (target Jul 2026)\n"
                "• Urgent: Will update needed post-divorce — currently leaving estate to ex-spouse Claire\n"
                "• Income protection — still unprotected during peak financial responsibility years\n"
                "• Jack's ongoing therapy costs and custody arrangement impact on budget"
            ),
            "date": "2026-02-27",
            "start_time": "09:00",
            "end_time": "10:00",
        },
        {
            "id": "mtg-002",
            "client_name": "Brian Potter",
            "client_email": "brian.potter47@gmail.com",
            "subject": "Downsizing Options & Gifting Strategy for Sarah",
            "content": (
                "Follow-up from our earlier call about supporting daughter Sarah. "
                "Brian was emotional — this needs a sensitive approach.\n\n"
                "Agenda:\n"
                "• Walk through the £30k gift option for Sarah with transparency plan for Andrew\n"
                "• Review downsizing options — potential £150k equity release from Willow Close\n"
                "• Margaret's inherited ISA (£47k) — spousal transfer still pending\n"
                "• Excess cash position (£115k across savings/premium bonds) — discuss investment\n"
                "• Check in on Brian's wellbeing — bereavement support, loneliness concerns"
            ),
            "date": "2026-02-27",
            "start_time": "14:00",
            "end_time": "15:00",
        },
        {
            "id": "mtg-003",
            "client_name": "Hyacinth Bucket",
            "client_email": "hyacinth.bucket@talktalk.net",
            "subject": "Sheridan Financial Support & LPA Planning",
            "content": (
                "Follow-up from Hyacinth's urgent email about Sheridan needing financial assistance again. "
                "Historic £25k already unrepaid.\n\n"
                "Agenda:\n"
                "• Discuss boundaries for Sheridan support — unbounded goal is depleting savings\n"
                "• Critical: LPAs and will update for both Hyacinth (73) and Richard (75) — neither in place\n"
                "• Savings runway risk — depletion projected early 2030s without changes\n"
                "• Richard's private pension drawdown (£45k remaining) — withdrawal strategy\n"
                "• Car replacement goal — recommended budget £18k vs Hyacinth's £35k aspiration"
            ),
            "date": "2026-02-28",
            "start_time": "10:00",
            "end_time": "11:00",
        },
        {
            "id": "mtg-004",
            "client_name": "Robert Hughes",
            "client_email": "robert.hughes@rghlegal.com",
            "subject": "BTL Refinancing & Pre-Retirement Strategy",
            "content": (
                "Follow-up from the BTL rate update email. "
                "Guildford property rate expired Aug 2025 — refinancing overdue.\n\n"
                "Agenda:\n"
                "• Review latest refinancing rates for Guildford BTL (current mortgage £85k)\n"
                "• Recommendation: Sell Guildford BTL post-refinance — after-tax return weak vs alternatives\n"
                "• Partnership exit planning — £280k buyout over 4 years (£70k/year)\n"
                "• IHT exposure estimated ~£580k — LPAs, updated wills, gifting strategy needed\n"
                "• Tom's house deposit gift (£75k) — timing and tax implications\n"
                "• Charles Stanley managed portfolio fee drag — £2,720/year, worth reviewing"
            ),
            "date": "2026-03-02",
            "start_time": "11:00",
            "end_time": "12:00",
        },
        {
            "id": "mtg-005",
            "client_name": "Rodney & Cassandra Trotter",
            "client_email": "cass.trotter@citybank.co.uk",
            "subject": "House Purchase Deposit & Debt Clearance Plan",
            "content": (
                "Follow-up from Cassandra's email expressing frustration about housing delays. "
                "She wants to see 'real progress this year'.\n\n"
                "Agenda:\n"
                "• Deposit position — current savings £38k joint + ISAs vs £50k target\n"
                "• Director's loan (£12k overdrawn) — declare dividend to clear and avoid S455 tax\n"
                "• Personal loan at 9.8% interest — prioritise clearing £8k balance\n"
                "• Rodney's salary restructure — increase to £60k for mortgage strength\n"
                "• Income protection — Rodney self-employed with two dependants, currently unprotected\n"
                "• Relationship check-in — financial stress driving marital tension"
            ),
            "date": "2026-03-03",
            "start_time": "15:00",
            "end_time": "16:00",
        },
        {
            "id": "mtg-006",
            "client_name": "Basil Fawlty",
            "client_email": "basil@fawltytowers.co.uk",
            "subject": "Hotel Exit Strategy & Valuation Discussion",
            "content": (
                "Follow-up from Basil's email rejecting the £1.45m valuation as 'unrealistic'. "
                "He remains emotionally attached to the hotel. Sybil wants to proceed with a sale.\n\n"
                "Agenda:\n"
                "• Address Basil's valuation expectations — agent estimates £1.2m–£1.3m range\n"
                "• CGT planning — estimated gain £925k, BADR tax ~£92.5k\n"
                "• Lease-back option as compromise — potential income £48k/year\n"
                "• Retirement income modelling — £65k/year target from pensions + investments\n"
                "• Mediterranean relocation plans — budget £120k for overseas property\n"
                "• Manage Basil/Sybil dynamic — need aligned decision before proceeding"
            ),
            "date": "2026-03-04",
            "start_time": "09:30",
            "end_time": "10:30",
        },
    ]


@app.get("/api/meetings", response_model=List[Meeting])
async def get_meetings():
    """
    Get upcoming meetings for the advisor.
    """
    return [Meeting(**m) for m in _get_demo_meetings()]
