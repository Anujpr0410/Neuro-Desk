"""
SerperDev Search Tool for NeuroDesk AI Multi-Agent System.
Web search functionality using SerperDev API for market research.
"""

import os
import json
from typing import Dict, List, Optional, Any
import requests
from pathlib import Path


def serper_search(query: str, api_key: str = None) -> Dict[str, Any]:
    """
    Perform a web search using SerperDev API.

    Args:
        query: Search query string
        api_key: SerperDev API key (optional, reads from SERPER_API_KEY env var)

    Returns:
        Dictionary containing search results
    """
    if api_key is None:
        api_key = os.environ.get("SERPER_API_KEY")

    if not api_key:
        raise ValueError(
            "SerperDev API key not provided. "
            "Set SERPER_API_KEY environment variable or pass api_key parameter."
        )

    url = "https://google.serper.dev/search"

    payload = json.dumps({
        "q": query,
        "gl": "us",
        "hl": "en"
    })

    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, data=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "results": []
        }


def extract_search_results(results: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Extract and format search results from SerperDev response.

    Args:
        results: Raw SerperDev API response

    Returns:
        List of formatted search results
    """
    formatted_results = []

    # Organic search results
    organic_results = results.get("organic", [])
    for i, result in enumerate(organic_results[:10], 1):
        formatted_results.append({
            "position": i,
            "title": result.get("title", ""),
            "link": result.get("link", ""),
            "snippet": result.get("snippet", ""),
            "source": result.get("source", "")
        })

    # People also ask
    people_also_ask = results.get("peopleAlsoAsk", [])
    for i, question in enumerate(people_also_ask[:5], 1):
        formatted_results.append({
            "position": f"PAQ-{i}",
            "title": question.get("question", ""),
            "snippet": question.get("snippet", "")
        })

    # Related searches
    related_searches = results.get("relatedSearches", [])
    for i, search in enumerate(related_searches[:5], 1):
        formatted_results.append({
            "position": f"RS-{i}",
            "title": search.get("query", ""),
            "type": "related_search"
        })

    return formatted_results


def search_with_sources(query: str, api_key: str = None, top_n: int = 5) -> str:
    """
    Perform search and return formatted results with sources.

    Args:
        query: Search query
        api_key: SerperDev API key
        top_n: Number of results to return

    Returns:
        Formatted string with search results
    """
    results = serper_search(query, api_key)

    if "error" in results:
        return f"Error performing search: {results['error']}"

    formatted = extract_search_results(results)

    output = [f"Search results for: '{query}'\n"]
    output.append("=" * 60)
    output.append("")

    for i, result in enumerate(formatted[:top_n], 1):
        if "type" in result and result["type"] == "related_search":
            output.append(f"[Related Search] {result['title']}")
            output.append("")
        elif "PAQ" in str(result.get("position", "")):
            output.append(f"[People Also Ask] {result['title']}")
            output.append(f"  {result.get('snippet', '')}")
            output.append("")
        else:
            output.append(f"[{i}] {result['title']}")
            output.append(f"    URL: {result['link']}")
            output.append(f"    {result['snippet']}")
            output.append("")

    return "\n".join(output)


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SerperDev Search Tool")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--key", help="SerperDev API key")
    parser.add_argument("--top", type=int, default=5, help="Number of results")

    args = parser.parse_args()

    result = search_with_sources(args.query, args.key, args.top)
    print(result)
