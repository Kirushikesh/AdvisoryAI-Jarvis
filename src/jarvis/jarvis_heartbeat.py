import time
import threading
import schedule

from jarvis.deepagent import create_jarvis_agent, build_system_prompt
from jarvis.config import (
    HEARTBEAT_INTERVAL_MINUTES,
    HEARTBEAT_PROMPT,
    HEARTBEAT_OK_TOKEN,
    NO_REPLY_TOKEN,
    NEED_USER_ATTENTION_TOKEN
)


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
        result = agent.invoke({"messages": [{"role": "user", "content": HEARTBEAT_PROMPT}]})
        response = result["messages"][-1].content
        
        # Handle response based on tokens
        if HEARTBEAT_OK_TOKEN in response:
            print("[Scheduler]: Heartbeat OK - No action needed")
        elif NEED_USER_ATTENTION_TOKEN in response:
            print(f"\n⚠️  [Jarvis ALERT]: {response}")
        elif NO_REPLY_TOKEN in response:
            print("[Scheduler]: No reply - Nothing to report")
        else:
            print(f"\n[Jarvis (Heartbeat)]: {response}")
            
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
    Main entry point for Jarvis.
    Starts the heartbeat scheduler and interactive chat loop.
    """
    print("=" * 60)
    print("  JARVIS - Intelligent IFA Helper")
    print("=" * 60)
    print()
    
    # Start Scheduler in background
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print(f"✓ Heartbeat scheduler started ({HEARTBEAT_INTERVAL_MINUTES} min interval)")
    print()
    
    # Main Chat Loop
    print("Jarvis is ready. Type 'exit' to quit.")
    print("-" * 60)
    
    while True:
        try:
            user_input = input("\n[Advisor]: ")
            
            if user_input.lower() in ["exit", "quit"]:
                print("\nGoodbye, Abi!")
                break
            
            if not user_input.strip():
                continue
            
            # Trigger immediate heartbeat with /heartbeat command
            if user_input.strip() == "/heartbeat":
                print("Triggering manual heartbeat...")
                heartbeat_job()
                continue
            
            # Create agent and invoke
            agent = create_jarvis_agent()
            result = agent.invoke({"messages": [{"role": "user", "content": user_input}]})
            response = result["messages"][-1].content
            
            # Handle special tokens
            if NO_REPLY_TOKEN in response:
                continue  # Silent
            
            print(f"\n[Jarvis]: {response}")
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\n[Error]: {e}")


if __name__ == "__main__":
    main()
