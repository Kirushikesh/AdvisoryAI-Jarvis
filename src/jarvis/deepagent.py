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
from jarvis.config import OPENAI_API_KEY
from dotenv import find_dotenv, load_dotenv
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver

load_dotenv(find_dotenv(), override=True)

checkpointer = MemorySaver()

# Workspace paths
WORKSPACE_DIR = Path("/Users/kirushikeshdb/Documents/Hackathon/Advisory AI/jarvis/workspace")

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
Your working directory is: {WORKSPACE_DIR}
Treat this directory as your single global workspace for file operations.

## Current Date & Time
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

# PROJECT CONTEXT FILES

The following workspace files define your behavior and context:

## AGENTS.md (Workspace Instructions)
{agents_md}

---

## SOUL.md (Identity & Personality)
{soul_md}

---

## IDENTITY.md (Who You Are)
{identity_md}

---

## USER.md (About the Advisor)
{user_md}

---

## TOOLS.md (Tool Usage Guide)
{tools_md}

## Silent Replies
When you have nothing to say, respond with ONLY: NO_REPLY

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
"""
    
    return prompt


def create_jarvis_agent(system_prompt: str = None):
    """
    Creates and returns the Jarvis Deep Agent with specialized subagents.
    
    Args:
        system_prompt: Optional custom system prompt. If None, builds from workspace files.
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
        tools=tools,
        system_prompt=system_prompt,
        subagents=[atlas_subagent, emma_subagent, colin_subagent],
        backend=FilesystemBackend(root_dir=str(WORKSPACE_DIR), virtual_mode=True),
        checkpointer=checkpointer,
        skills=[str(WORKSPACE_DIR / "skills")],
    )
    
    return agent
