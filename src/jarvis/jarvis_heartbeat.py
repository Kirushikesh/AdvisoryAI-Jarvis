import time
import threading
import schedule

from jarvis.deepagent import create_jarvis_agent, build_system_prompt
from jarvis.config import (
    HEARTBEAT_INTERVAL_MINUTES,
    HEARTBEAT_PROMPT,
    HEARTBEAT_OK_TOKEN,
    NO_REPLY_TOKEN
)
from jarvis.tools.heartbeat_tools import send_important_notification, send_draft_email
import uuid


def heartbeat_job():
    """
    Scheduled heartbeat job that invokes Jarvis with the heartbeat prompt.
    Runs every HEARTBEAT_INTERVAL_MINUTES.
    """
    print("\n[Scheduler]: Triggering Heartbeat...")
    
    try:
        # Create agent with auto-built system prompt and oss model for heartbeat
        # Provide heartbeat-specific tools so the LLM can push notifications
        # and draft emails on its own.
        agent = create_jarvis_agent(
            model="openai:gpt-5-nano",
            extra_tools=[send_important_notification, send_draft_email],
        )
        
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
            # Agent handles actions via tools (notification / draft email)
            print(f"[Scheduler]: Heartbeat completed with tool actions")
            pass
            
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
