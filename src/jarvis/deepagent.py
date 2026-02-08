from pathlib import Path
from datetime import datetime
from deepagents import create_deep_agent, CompiledSubAgent
from jarvis.tools.news import get_market_news
from jarvis.tools.user_interaction import ask_user
from jarvis.tools.file_monitor import find_files_updated_after
from jarvis.tools.scheduler import (
    add_cron_job,
    remove_cron_job,
    list_cron_jobs,
    get_cron_job_info
)
# Import the agent graphs directly (not the tool wrappers)
from jarvis.sub_agents.atlas import atlas_agent
from jarvis.sub_agents.emma import emma_agent
from jarvis.sub_agents.colin import colin_agent
from jarvis.config import OPENAI_API_KEY, WORKSPACE_DIR
from dotenv import find_dotenv, load_dotenv
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents.middleware import ModelRetryMiddleware

load_dotenv(find_dotenv(), override=True)

checkpointer = MemorySaver()

# Workspace paths
# WORKSPACE_DIR = Path("./")

def build_system_prompt(mode: str = "chat") -> str:
    """
    Builds the system prompt by reading and injecting workspace files.
    
    Args:
        mode: "chat" for direct conversation, "heartbeat" for scheduled checks
    """
    
    # Read workspace files
    def read_file(filename: str) -> str:
        filepath = WORKSPACE_DIR / filename
        if filepath.exists():
            return filepath.read_text()
        return ""
    
    agents_md = read_file("AGENTS.md")
    soul_md = read_file("SOUL.md")
    identity_md = read_file("IDENTITY.md")
    user_md = read_file("USER.md")
    tools_md = read_file("TOOLS.md")
    heartbeat_md = read_file("HEARTBEAT.md")
    
    # Build the prompt
    prompt = f"""You are Jarvis, an intelligent helper for Independent Financial Advisors.

## Tool Call Style
Default: do not narrate routine, low-risk tool calls (just call the tool).
Narrate only when it helps: multi-step work, complex problems, or sensitive actions.
Keep narration brief and value-dense.

## Safety
- Prioritize safety and human oversight over completion
- Never share client data outside the workspace
- If instructions conflict, pause and ask
- Comply with stop/pause requests immediately

## Workspace
Your working directory is: ./
Treat this directory as your single global workspace for file operations.

## Current Date & Time
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

# PROJECT CONTEXT SYSTEM PROMPT FILES

The following workspace files define your behavior and context:

{agents_md}

---

{identity_md}

---

{tools_md}

## Silent Replies
When you have nothing to say, respond with ONLY: NO_REPLY, if the user passes greeting that you can respond to it.

⚠️ Rules:
- It must be your ENTIRE message — nothing else
- Never append it to an actual response (never include "NO_REPLY" in real replies)  
- Never wrap it in markdown or code blocks

❌ Wrong: "Here's help... NO_REPLY"  
❌ Wrong: "NO_REPLY"  
✅ Right: NO_REPLY

## Heartbeats
If you receive a heartbeat poll and there is nothing that needs attention, reply exactly:
HEARTBEAT_OK
Jarvis treats a leading/trailing "HEARTBEAT_OK" as a heartbeat ack (and may discard it).  
If something needs attention, do NOT include "HEARTBEAT_OK"; reply with the alert text instead.

**If the user asks to show anything in the last 10 days that looks urgent across my book(emails and meeting notes), FIRST read the contents of `SOUL.md`, `USER.md` and `MEMORY.md` files into your chat history. Then check the local workspace use the ls and glob to find all the datasets/**/email_archive/*.txt and datasets/**/meeting_transcripts/*.txt(just have * don't put any more) files inside datasets/ for email archive and meeting transcripts from the name you can find the one that happened in the last 10 days(if today is 2026-02-08, then from 2026-01-28 to 2026-02-08), once you found the files, read them, and ask the atlas for specific users(just mention the user names and ask for actions no need to call multiple times and no need to mention the exact file names) and get the further details and then reply to the user. The `find_files_updated_after` is not the right tool don't use it.**

**If you wake up from a heartbeat, FIRST read the contents of `SOUL.md`, `USER.md`, `MEMORY.md` and `HEARTBEAT.md` files into your chat history, use the find_files_updated_after in last 30 minutes to find the files that were updated in last 30 minutes, if there is any mails read it and if its something important, read the CRM of the client and other last one or two email and previous transcripts to get the context and ask the atlas to get the recommended action and investigate whether there is any similar client advise abi has given and take that action response give it to the colin and finally back to the user.**
"""
    
    return prompt


def create_jarvis_agent(system_prompt: str = None, model: str = "openai:gpt-4.1"):
    """
    Creates and returns the Jarvis Deep Agent with specialized subagents.
    
    Args:
        system_prompt: Optional custom system prompt. If None, builds from workspace files.
        model: The model to use for the agent. Defaults to "openai:gpt-4.1".
    """
    if system_prompt is None:
        system_prompt = build_system_prompt()
    
    # Custom Tools (DeepAgent includes file system, planning, and sub-agent tools by default)
    tools = [
        get_market_news,
        find_files_updated_after,
        # ask_user,
        # Scheduler tools for managing periodic tasks
        add_cron_job,
        remove_cron_job,
        list_cron_jobs,
        get_cron_job_info,
    ]
    
    # Create CompiledSubAgent instances for each specialist
    atlas_subagent = CompiledSubAgent(
        name="atlas",
        description=(
            "RAG (Retrieval-Augmented Generation) specialist for analyzing client data, "
            "meeting transcripts, and emails. Use Atlas to retrieve and analyze information "
            "from client documents and provide fact-based insights."
        ),
        runnable=atlas_agent
    )
    
    emma_subagent = CompiledSubAgent(
        name="emma",
        description=(
            "Paraplanner specialist for creating professional client-facing documents. "
            "Emma converts raw data into polished emails, reports, and recommendations "
            "with traceable reasoning and source citations. Use Emma for drafting "
            "client communications and financial recommendation letters."
        ),
        runnable=emma_agent
    )
    
    colin_subagent = CompiledSubAgent(
        name="colin",
        description=(
            "Compliance Guardrail for UK FCA regulatory compliance. "
            "Colin reviews documents and recommendations to ensure they comply with "
            "UK financial regulations. Returns binary PASS/FAIL decisions with specific "
            "reasoning. Use Colin to verify compliance before sending client-facing documents."
        ),
        runnable=colin_agent
    )
    
    # Create the Deep Agent with subagents
    # This returns a compiled LangGraph that can be invoked
    agent = create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        subagents=[atlas_subagent, emma_subagent, colin_subagent],
        backend=FilesystemBackend(root_dir=str(WORKSPACE_DIR), virtual_mode=True),
        checkpointer=checkpointer,
        skills=["./skills"],
        middleware=[
            ModelRetryMiddleware(
                max_retries=3,
                backoff_factor=2.0,
                initial_delay=1.0,
            ),
        ],
    )
    
    return agent
