from langchain_core.tools import tool

@tool
def ask_user(question: str) -> str:
    """
    Pauses execution to ask the user (Financial Advisor) a question and waits for their response.
    Use this when you need confirmation, clarification, or permission to proceed with a sensitive action.
    """
    print(f"\n[Jarvis asks]: {question}")
    response = input("[Advisor]: ")
    return response
