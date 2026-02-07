import os
from langchain.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from jarvis.config import OPENAI_API_KEY
from langchain.chat_models import init_chat_model
from langchain.agents.middleware import TodoListMiddleware

# Initialize LLM for Emma
llm = init_chat_model("gpt-4.1")


# Create the Emma Agent (Paraplanner)
emma_system_prompt = (
    "You are Emma, the Paraplanner for a financial advisory firm. "
    "Your role is to convert raw client data into professional, client-facing documents such as "
    "emails, reports, and recommendations. "
    "\n\n"
    "KEY CHARACTERISTIC: Traceable Reasoning\n"
    "- Always cite your sources when making recommendations or statements.\n"
    "- Format citations as: [Source: Meeting Note 12/01/25] or [Source: Email from client 15/01/25]\n"
    "- If you retrieve information from Atlas, explicitly mention it in your output.\n"
    "- Never make generic statements like ChatGPT. Always ground your advice in specific client data.\n"
    "\n\n"
    "PROCESS:\n"
    "1. When asked to create a document, first gather relevant client information using available tools\n"
    "2. Structure your output professionally (use proper formatting for emails/reports)\n"
    "3. Include specific details and numbers where applicable\n"
    "4. Cite every key fact or recommendation with its source\n"
    "5. Maintain a professional but warm tone\n"
    "\n\n"
    "REMEMBER: You are creating documents FOR clients, not just analyzing data. "
    "Your output should be polished and ready to send (or very close to it)."
    """**Structure:** Follow standard FCA Suitability Report structure:
- Executive Summary
- Your Current Position
- Your Goals (Objectives)
- Our Recommendation (The "Why")
- Risks & Disadvantages (Crucial for compliance)
- Costs & Charges"""
    "Dont use the email format, use the markdown format for the document"
    "You can call the atlas to get the information multiple times if needed"
)

# The Emma Agent Graph - to be used with CompiledSubAgent
# Note: Emma will communicate with Atlas through the deep agent's subagent system
emma_agent = create_agent(
    model=llm,
    tools=[],  # Tools removed - deep agent handles subagent communication
    system_prompt=emma_system_prompt,
    middleware=[TodoListMiddleware()],
)


if __name__ == "__main__":
    # Test Emma
    test_query = (
        "Draft an email to Sarah Thompson recommending she consolidate her ISAs. "
        "Include specific reasons based on her situation."
    )
    print(emma_agent.invoke({"messages": [HumanMessage(content=test_query)]}))
