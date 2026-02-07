from tavily import TavilyClient
from langchain_core.tools import tool
import os
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(), override=True)

tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

@tool
def get_market_news(query: str,
    max_results: int = 5,
    topic: str = "general",
    include_raw_content: bool = False) -> str:
    """
    Searches for the latest market news based on the query using Tavily.
    Useful for finding recent financial news, compliance updates, or market trends.
    """
    try:
        return tavily_client.search(query=query, max_results=max_results, topic=topic, include_raw_content=include_raw_content)
    except Exception as e:
        return f"Error fetching news: {e}"
