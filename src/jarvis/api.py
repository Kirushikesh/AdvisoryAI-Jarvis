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

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Import Jarvis modules AFTER loading .env
from jarvis.deepagent import create_jarvis_agent
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


# ============================================================================
# Notification Storage (in-memory for simplicity)
# ============================================================================

_notifications: List[dict] = []
MAX_NOTIFICATIONS = 50


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
    
    # Start heartbeat scheduler in background thread
    def start_heartbeat():
        print(f"💓 Heartbeat scheduler started ({HEARTBEAT_INTERVAL_MINUTES} min interval)")
        # Run initial heartbeat after a short delay
        import time
        time.sleep(5)  # Wait for API to be fully ready
        heartbeat_job()
        # Then run the scheduler loop
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
        
        # Invoke the agent
        if request.agent == "jarvis":
            result = agent.invoke(
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
            result = agent.invoke(
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
