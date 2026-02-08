import os
from langchain.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from jarvis.utils.vector_store import query_vector_store, ingest_documents
from jarvis.config import OPENAI_API_KEY, LITELLM_API_KEY, LITELLM_URL
from langchain.chat_models import init_chat_model
from langchain.agents.middleware import TodoListMiddleware
from langchain.agents.middleware import ModelRetryMiddleware

# Initialize LLM for Atlas (consistent with simple_rag_agent.py)
llm = init_chat_model("gpt-4.1")

@tool
def retrieve_context(query: str):
    """
    Retrieve details from client documents and meeting transcripts.
    Always use this tool when asked about client specific information.
    """
    results = query_vector_store(query, k=5)
    
    if not results:
        return "No relevant information found in client documents."
        
    serialized = "\n\n".join(
        (f"Source: {doc.metadata.get('source_file', 'Unknown')}\nContent: {doc.page_content}")
        for doc in results
    )
    return serialized

# Create the Atlas Agent
atlas_system_prompt = (
    "You are Atlas, a RAG (Retrieval-Augmented Generation) specialist for a financial advisory firm. "
    "Your job is to analyze client data, meeting transcripts, and emails to provide accurate, "
    "fact-based insights to the advisor. "
    "Always rely on the information retrieved via the 'retrieve_context' tool. "
    "If the information is not present in the documents, state that clearly. "
    "Be concise, professional, and highlight specific details or numbers when found."
)

# The Atlas Agent Graph - to be used with CompiledSubAgent
atlas_agent = create_agent(
    model=llm, 
    tools=[retrieve_context], 
    system_prompt=atlas_system_prompt, 
    middleware=[
        TodoListMiddleware(),
        ModelRetryMiddleware(
                max_retries=3,
                backoff_factor=2.0,
                initial_delay=1.0,
            ),
        ],
    )


if __name__ == "__main__":
    print(atlas_agent.invoke({"messages": [HumanMessage(content="Summarize Sarah Thompson's meeting and then identify her primary financial goals.")]}))
    # print(retrieve_context.invoke({"query": "Sarah Thompson"}))