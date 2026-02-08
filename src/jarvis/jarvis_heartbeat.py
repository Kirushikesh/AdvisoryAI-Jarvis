import time
import threading
import schedule
import requests

from jarvis.deepagent import create_jarvis_agent, build_system_prompt
from jarvis.config import (
    HEARTBEAT_INTERVAL_MINUTES,
    HEARTBEAT_PROMPT,
    HEARTBEAT_OK_TOKEN,
    NO_REPLY_TOKEN
)
import uuid

# API endpoint for notifications
API_BASE_URL = "http://localhost:8000"


def send_notification(title: str, message: str, notification_type: str = "action"):
    """Send a notification to the API for the frontend dashboard."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/notifications",
            json={
                "type": notification_type,
                "title": title,
                "message": message
            },
            timeout=5
        )
        if response.ok:
            print(f"[Scheduler]: Notification sent to dashboard")
        else:
            print(f"[Scheduler]: Failed to send notification: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"[Scheduler]: Could not reach API: {e}")


def heartbeat_job():
    """
    Scheduled heartbeat job that invokes Jarvis with the heartbeat prompt.
    Runs every HEARTBEAT_INTERVAL_MINUTES.
    """
    print("\n[Scheduler]: Triggering Heartbeat...")
    
    try:
        # Create agent with auto-built system prompt
        agent = create_jarvis_agent()
        
        # Send the heartbeat prompt
        result = agent.invoke(
            {"messages": [{"role": "user", "content": HEARTBEAT_PROMPT}]},
            config={"configurable": {"thread_id": f"heartbeat_{uuid.uuid4()}"}}
        )
        response = result["messages"][-1].content
        
        # Handle response based on tokens
        if HEARTBEAT_OK_TOKEN in response:
            print("[Scheduler]: Heartbeat OK - No action needed")
        elif NO_REPLY_TOKEN in response:
            print("[Scheduler]: No reply - Nothing to report")
        else:
            # Jarvis has something important to report - send to dashboard
            print(f"\n[Jarvis (Heartbeat)]: {response}")
            send_notification(
                title="🚨 Jarvis Alert",
                message=response,
                notification_type="action"
            )
            
    except Exception as e:
        print(f"\n[Scheduler]: Error in heartbeat: {e}")


def run_scheduler():
    """
    Background scheduler that triggers heartbeats every HEARTBEAT_INTERVAL_MINUTES.
    """
    schedule.every(HEARTBEAT_INTERVAL_MINUTES).minutes.do(heartbeat_job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)


def main():
    """
    Main entry point for Jarvis Heartbeat.
    Runs the heartbeat scheduler autonomously - no user input needed.
    """
    print("=" * 60)
    print("  JARVIS HEARTBEAT - Autonomous Monitoring")
    print("=" * 60)
    print()
    
    # Trigger an immediate heartbeat on startup
    print("Running initial heartbeat...")
    heartbeat_job()
    print()
    
    # Run the scheduler (blocking)
    print(f"✓ Scheduler started ({HEARTBEAT_INTERVAL_MINUTES} min interval)")
    print("Press Ctrl+C to stop.")
    print("-" * 60)
    
    try:
        run_scheduler()
    except KeyboardInterrupt:
        print("\n\nHeartbeat stopped. Goodbye!")


if __name__ == "__main__":
    main()
