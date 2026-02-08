import os
from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv(), override=True)

from langchain.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from tavily import TavilyClient
from jarvis.config import OPENAI_API_KEY
from langchain.chat_models import init_chat_model
from langchain.agents.middleware import ModelRetryMiddleware

# Initialize LLM for Colin
llm = init_chat_model("gpt-4.1")

# Initialize DuckDuckGo search tool
tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

@tool
def search_uk_compliance(
    query: str,
    max_results: int = 5,
    topic: str = "finance",
    include_raw_content: bool = False,
) -> str:
    """
    Search for UK financial compliance rules and regulations using DuckDuckGo.
    Use this to verify if a recommendation or document complies with FCA regulations.

    topic: Category of the search
    """
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )

# Create the Colin Agent (Compliance Guardrail)
colin_system_prompt = (
    "You are Colin, the Compliance Guardrail for a UK financial advisory firm. "
    "Your role is to review documents and recommendations created by Emma (the Paraplanner) "
    "to ensure they comply with UK financial regulations, particularly FCA (Financial Conduct Authority) rules.\n"
    "\n"
    "KEY CHARACTERISTIC: Binary Pass/Fail\n"
    "- You do NOT give vague advice or suggestions\n"
    "- You return a clear PASS or FAIL decision\n"
    "- If FAIL, you must specify exactly which regulation is violated and why\n"
    "- If PASS, you confirm the document is compliant\n"
    "\n"
    "COMPLIANCE CHECKS:\n"
    "1. Check for proper risk warnings and disclosures\n"
    "2. Verify advice is suitable and personalized (not generic)\n"
    "3. Ensure no guarantees of returns or misleading statements\n"
    "4. Check for proper treatment of vulnerable clients\n"
    "5. Verify fees and costs are disclosed clearly\n"
    "6. Ensure recommendations are in the client's best interest\n"
    "\n"
    "PROCESS:\n"
    "1. Read the document/recommendation carefully\n"
    "2. Use the search tool to verify current FCA regulations if uncertain\n"
    "3. Return your verdict in this format:\n"
    "\n"
    "VERDICT: [PASS or FAIL]\n"
    "REASON: [Specific regulation reference and explanation]\n"
    "ACTION REQUIRED: [If FAIL, what needs to change]\n"
    "\n"
    "REMEMBER: You are the safety net. If something violates UK regulations, you MUST block it. "
    "Do not be lenient. Client protection and regulatory compliance are paramount."
    "Always use the web search tool to double check your response."
)

# The Colin Agent Graph - to be used with CompiledSubAgent
colin_agent = create_agent(
    model=llm,
    tools=[search_uk_compliance],
    system_prompt=colin_system_prompt,
    middleware=[
        ModelRetryMiddleware(
            max_retries=3,
            backoff_factor=2.0,
            initial_delay=1.0,
        ),
    ],
)


if __name__ == "__main__":
    # Test Colin with a sample document
    test_document = """
    Dear Client,
    
    I recommend you invest all your money in Bitcoin as it is guaranteed to double in value 
    within the next year. This is a can't-miss opportunity!
    
    Best regards,
    Financial Advisor
    """
    print(colin_agent.invoke({"messages": [{"role": "user", "content": test_document}]}))
