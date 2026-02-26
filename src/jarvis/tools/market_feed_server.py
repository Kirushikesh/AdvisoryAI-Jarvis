"""
Market Feed MCP Server for Jarvis.

Exposes three read-only market intelligence tools powered by Tavily search:
  • get_macro_indicators  – macro-economic indicators (interest rates, inflation, etc.)
  • search_financial_news – curated financial/regulatory news search
  • get_asset_performance – price/performance snapshot for a given asset/ticker

Run standalone:  uv run python src/jarvis/tools/market_feed_server.py
"""

from __future__ import annotations

import os
from enum import Enum
from datetime import date

from dotenv import find_dotenv, load_dotenv
from mcp.server.fastmcp import FastMCP
from tavily import TavilyClient

load_dotenv(find_dotenv(), override=True)

# ---------------------------------------------------------------------------
# FastMCP server
# ---------------------------------------------------------------------------
mcp = FastMCP("market_feed")

# ---------------------------------------------------------------------------
# Tavily client (shared across tools)
# ---------------------------------------------------------------------------
_tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _search(
    query: str,
    *,
    topic: str = "finance",
    time_range: str | None = "month",
    search_depth: str = "basic",
    max_results: int = 5,
) -> dict:
    """Run a Tavily search and return a clean result dict.

    Parameters map directly to the Tavily Search API:
      topic       – "general" | "news" | "finance"
      time_range  – "day" | "week" | "month" | "year" | None
      search_depth – "basic" | "basic"
    """
    try:
        kwargs: dict = dict(
            query=query,
            max_results=max_results,
            topic=topic,
            search_depth=search_depth,
            include_answer=True,         # short AI summary of results
            include_raw_content=False,   # keep payload small
            include_images=False,
        )
        if time_range:
            kwargs["time_range"] = time_range

        resp = _tavily.search(**kwargs)
        return {
            "answer": resp.get("answer", ""),
            "results": [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "published_date": r.get("published_date", ""),
                    "content": r.get("content", ""),
                    "score": r.get("score", 0),
                }
                for r in resp.get("results", [])
            ],
        }
    except Exception as exc:
        return {"error": str(exc), "results": []}


# ---------------------------------------------------------------------------
# Timeframe → Tavily time_range mapping
# ---------------------------------------------------------------------------
_TIMEFRAME_TO_TIME_RANGE: dict[str, str | None] = {
    "1D":  "day",
    "1W":  "week",
    "1M":  "month",
    "1Y":  "year",
    "YTD": "year",   # closest native range; query will also state YTD explicitly
}


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------

class IndicatorType(str, Enum):
    interest_rate = "interest_rate"
    inflation     = "inflation"
    cgt_allowance = "cgt_allowance"
    isa_allowance = "isa_allowance"
    state_pension = "state_pension"


_INDICATOR_QUERIES: dict[IndicatorType, str] = {
    IndicatorType.interest_rate: "{region} Bank of England base interest rate {year}",
    IndicatorType.inflation:     "{region} CPI inflation rate current {year}",
    IndicatorType.cgt_allowance: "{region} Capital Gains Tax annual exempt allowance {year}",
    IndicatorType.isa_allowance: "{region} ISA annual subscription allowance {year}/{year1}",
    IndicatorType.state_pension: "{region} new state pension weekly amount {year}",
}


@mcp.tool()
def get_macro_indicators(
    indicator_type: str,
    region: str = "UK",
) -> dict:
    """Fetch a current macro-economic or regulatory indicator for a given region.

    Args:
        indicator_type: The specific metric to fetch. One of:
            'interest_rate', 'inflation', 'cgt_allowance',
            'isa_allowance', 'state_pension'.
        region: Geographic region/country for the indicator (default: 'UK').

    Returns:
        Dict with 'answer' (AI summary) and 'results' (source articles).
    """
    try:
        ind = IndicatorType(indicator_type)
    except ValueError:
        valid = [e.value for e in IndicatorType]
        print(f"error: Unknown indicator_type '{indicator_type}'. Valid: {valid}")
        print("fallback to interest_rate")
        ind = IndicatorType.interest_rate

    year = date.today().year
    template = _INDICATOR_QUERIES[ind]
    query = template.format(region=region, year=year, year1=year + 1)

    # Macro indicators change infrequently; search within the past year is fine
    return _search(
        query,
        topic="finance",
        time_range="year",
        search_depth="basic",
        max_results=5,
    )


# ---------------------------------------------------------------------------

_CATEGORY_PREFIXES: dict[str, str] = {
    "general":         "",
    "tax_legislation": "UK tax legislation HMRC",
    "fca_regulation":  "UK FCA Financial Conduct Authority regulation",
    "equities":        "stock market equities",
}

# Map days_back to the nearest Tavily time_range bucket
def _days_to_time_range(days: int) -> str:
    if days <= 1:
        return "day"
    if days <= 7:
        return "week"
    if days <= 31:
        return "month"
    return "year"


@mcp.tool()
def search_financial_news(
    query: str,
    category: str = "general",
    days_back: int = 3,
) -> dict:
    """Search for recent financial or regulatory news using Tavily.

    Args:
        query: The financial topic to search for,
            e.g. 'UK interest rates', 'tech stocks', 'ISA deadline'.
        category: Narrow the search context. One of:
            'general', 'tax_legislation', 'fca_regulation', 'equities'.
        days_back: How many days back to search (default: 3).

    Returns:
        Dict with 'answer' (AI summary) and 'results' (source articles).
    """
    prefix = _CATEGORY_PREFIXES.get(category, "")
    full_query = f"{prefix} {query}".strip() if prefix else query
    time_range = _days_to_time_range(days_back)

    # Use "news" topic for recency-focused searches, "finance" for regulatory
    topic = "finance" if category in ("tax_legislation", "fca_regulation") else "news"

    return _search(
        full_query,
        topic=topic,
        time_range=time_range,
        search_depth="basic",
        max_results=7,
    )


# ---------------------------------------------------------------------------

@mcp.tool()
def get_asset_performance(
    symbol: str,
    timeframe: str = "1M",
) -> dict:
    """Get a performance snapshot for an asset, index, or fund via Tavily search.

    Args:
        symbol: Ticker symbol, index name, or fund name.
            Examples: 'FTSE100', 'S&P500', 'Vanguard LifeStrategy 80'.
        timeframe: Look-back window. One of: '1D', '1W', '1M', '1Y', 'YTD'.
            Defaults to '1M'.

    Returns:
        Dict with 'answer' (AI summary) and 'results' (source articles).
    """
    tf = timeframe.upper()
    time_range = _TIMEFRAME_TO_TIME_RANGE.get(tf, "month")

    label_map = {
        "1D":  "daily performance today",
        "1W":  "weekly performance past 7 days",
        "1M":  "monthly performance past month",
        "1Y":  "annual performance past year",
        "YTD": "year to date performance YTD",
    }
    label = label_map.get(tf, "performance")
    query = f"{symbol} {label} price return"

    return _search(
        query,
        topic="finance",
        time_range=time_range,
        search_depth="basic",
        max_results=5,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run(transport="stdio")
