from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from langchain_core.tools import tool
from typing import Dict
import time

# Global scheduler instance
scheduler = BackgroundScheduler()
scheduler.start()


@tool
def add_cron_job(name: str, cron: str, task_description: str) -> str:
    """
    Add a new scheduled cron job that will print a message at specified times.
    
    Args:
        name: Unique identifier for the job (e.g., "morning_report", "daily_check")
        cron: Cron expression in format "minute hour day month day_of_week"
              Examples: 
              - "0 9 * * *" = Every day at 9:00 AM
              - "*/5 * * * *" = Every 5 minutes
              - "0 9 * * 1" = Every Monday at 9:00 AM
        task_description: The detailed description of the task to be performed by the jarvis.
    
    Returns:
        Success or error message
    
    Example:
        add_cron_job("morning_report", "0 9 * * *", "Good morning! Daily report.")
    """
    try:
        # Check if job with same name already exists
        existing_job = scheduler.get_job(name)
        if existing_job:
            return f"Error: Job '{name}' already exists. Remove it first or use a different name."
        
        # Parse cron expression
        cron_parts = cron.split()
        if len(cron_parts) != 5:
            return f"Error: Invalid cron format. Expected 5 fields (minute hour day month day_of_week), got {len(cron_parts)}. Example: '0 9 * * *'"
        
        minute, hour, day, month, day_of_week = cron_parts
        
        # Create the task function
        def task():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] [{name}] {message}")
        
        # Add job to scheduler
        scheduler.add_job(
            func=task,
            trigger=CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week
            ),
            id=name,
            name=name
        )
        
        return f"Success: Job '{name}' added with schedule '{cron}'. Message: '{message}'"
        
    except Exception as e:
        return f"Error adding job: {str(e)}"


@tool
def remove_cron_job(name: str) -> str:
    """
    Remove a scheduled cron job by its name.
    
    Args:
        name: Name of the job to remove
    
    Returns:
        Success or error message
    
    Example:
        remove_cron_job("morning_report")
    """
    try:
        job = scheduler.get_job(name)
        if not job:
            return f"Error: Job '{name}' not found. Use list_cron_jobs to see available jobs."
        
        scheduler.remove_job(name)
        return f"Success: Job '{name}' has been removed."
        
    except Exception as e:
        return f"Error removing job: {str(e)}"


@tool
def list_cron_jobs() -> str:
    """
    List all currently scheduled cron jobs with their details.
    Shows job name, schedule, and next run time.
    
    Returns:
        Formatted string of all scheduled jobs
    
    Example:
        list_cron_jobs()
    """
    try:
        jobs = scheduler.get_jobs()
        
        if not jobs:
            return "No scheduled jobs found."
        
        output = []
        output.append("=" * 80)
        output.append("SCHEDULED CRON JOBS")
        output.append("=" * 80)
        
        for job in jobs:
            output.append(f"\nName: {job.id}")
            output.append(f"Schedule: {job.trigger}")
            output.append(f"Next run: {job.next_run_time}")
            output.append("-" * 80)
        
        output.append(f"\nTotal jobs: {len(jobs)}")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"Error listing jobs: {str(e)}"


@tool
def get_cron_job_info(name: str) -> str:
    """
    Get detailed information about a specific cron job.
    
    Args:
        name: Name of the job to get information about
    
    Returns:
        Detailed information about the job or error message
    
    Example:
        get_cron_job_info("morning_report")
    """
    try:
        job = scheduler.get_job(name)
        if not job:
            return f"Error: Job '{name}' not found. Use list_cron_jobs to see available jobs."
        
        output = []
        output.append(f"Job Name: {job.id}")
        output.append(f"Schedule: {job.trigger}")
        output.append(f"Next Run Time: {job.next_run_time}")
        output.append(f"Pending: {job.pending}")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"Error getting job info: {str(e)}"


# Example usage with LangChain agent
if __name__ == "__main__":
    pass
    # from langchain_anthropic import ChatAnthropic
    # from langgraph.prebuilt import create_react_agent
    
    # # Initialize the model
    # model = ChatAnthropic(model="claude-sonnet-4-20250514")
    
    # # Create tools list
    # tools = [
    #     add_cron_job,
    #     remove_cron_job,
    #     list_cron_jobs,
    #     get_cron_job_info
    # ]
    
    # # Create the agent
    # agent = create_react_agent(model, tools)
    
    # # Test the agent
    # print("=== Testing LangChain Agent with Cron Job Tools ===\n")
    
    # # Example 1: Add a job
    # print("Example 1: Adding a daily report job")
    # response = agent.invoke({
    #     "messages": [("user", "Add a cron job named 'daily_report' that runs every day at 9 AM and prints 'Daily report generated'")]
    # })
    # print(response["messages"][-1].content)
    # print("\n" + "=" * 80 + "\n")
    
    # # Example 2: List jobs
    # print("Example 2: Listing all jobs")
    # response = agent.invoke({
    #     "messages": [("user", "Show me all scheduled cron jobs")]
    # })
    # print(response["messages"][-1].content)
    # print("\n" + "=" * 80 + "\n")
    
    # # Example 3: Add another job
    # print("Example 3: Adding a job that runs every 5 minutes")
    # response = agent.invoke({
    #     "messages": [("user", "Create a cron job called 'quick_check' that runs every 5 minutes and prints 'Quick system check'")]
    # })
    # print(response["messages"][-1].content)
    # print("\n" + "=" * 80 + "\n")
    
    # # Example 4: Get specific job info
    # print("Example 4: Getting info about a specific job")
    # response = agent.invoke({
    #     "messages": [("user", "Tell me about the 'daily_report' job")]
    # })
    # print(response["messages"][-1].content)
    # print("\n" + "=" * 80 + "\n")
    
    # # Example 5: Remove a job
    # print("Example 5: Removing a job")
    # response = agent.invoke({
    #     "messages": [("user", "Remove the 'quick_check' cron job")]
    # })
    # print(response["messages"][-1].content)
    # print("\n" + "=" * 80 + "\n")
    
    # # Example 6: Complex request
    # print("Example 6: Complex request")
    # response = agent.invoke({
    #     "messages": [("user", "I need a job that checks for updates every Monday at 10 AM. Call it 'weekly_update_check'")]
    # })
    # print(response["messages"][-1].content)
    
    # print("\n" + "=" * 80 + "\n")
    # print("Agent testing complete. Scheduler is still running in background.")
    # print("Jobs will execute at their scheduled times.")
    # print("Press Ctrl+C to stop.")
    
    # # Keep the scheduler running
    # try:
    #     while True:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     print("\nShutting down scheduler...")
    #     scheduler.shutdown()
    #     print("Scheduler stopped.")