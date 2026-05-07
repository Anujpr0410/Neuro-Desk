"""
Website Scraper Tool for NeuroDesk AI Multi-Agent System.
Extract content from websites for competitor analysis and research.
"""

import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from urllib.parse import urljoin, urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Dependencies not installed. Run: pip install requests beautifulsoup4")
    raise


def scrape_website(url: str, max_length: int = 2000) -> Dict[str, Any]:
    """
    Scrape content from a website.

    Args:
        url: URL to scrape
        max_length: Maximum characters to extract

    Returns:
        Dictionary containing scraped content
    """
    try:
        # Fetch the page
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract title
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else ""

        # Extract main content (try common article containers)
        main_content = ""
        content_selectors = [
            'article',
            '.content',
            '.article',
            '#content',
            '#main',
            '.main-content',
            'main'
        ]

        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                main_content = element.get_text()
                break

        # Fallback to body content
        if not main_content:
            body = soup.find('body')
            if body:
                # Remove scripts and styles
                for script in body(['script', 'style']):
                    script.decompose()
                main_content = body.get_text()

        # Clean up whitespace
        lines = [line.strip() for line in main_content.split('\n')]
        lines = [line for line in lines if line]
        clean_content = '\n'.join(lines)

        # Truncate if necessary
        if len(clean_content) > max_length:
            clean_content = clean_content[:max_length] + "..."

        # Extract meta information
        meta_tags = {}
        for meta in soup.find_all('meta'):
            name = meta.get('name', meta.get('property', ''))
            content = meta.get('content', '')
            if name:
                meta_tags[name] = content

        # Extract images
        images = []
        for img in soup.find_all('img')[:10]:  # First 10 images
            src = img.get('src', '')
            alt = img.get('alt', '')
            if src:
                # Convert relative URLs to absolute
                absolute_url = urljoin(url, src)
                images.append({
                    "src": absolute_url,
                    "alt": alt
                })

        # Extract links
        links = []
        for a in soup.find_all('a')[:20]:  # First 20 links
            href = a.get('href', '')
            if href:
                absolute_url = urljoin(url, href)
                links.append({
                    "href": absolute_url,
                    "text": a.get_text(strip=True)
                })

        return {
            "success": True,
            "url": url,
            "title": title,
            "content": clean_content,
            "meta": meta_tags,
            "images": images[:5],
            "links": links,
            "scrape_date": None  # Would add datetime here if needed
        }

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "url": url,
            "error": str(e)
        }


def scrape_multiple_urls(urls: List[str], max_length: int = 2000) -> List[Dict[str, Any]]:
    """
    Scrape multiple websites.

    Args:
        urls: List of URLs to scrape
        max_length: Maximum characters per page

    Returns:
        List of scrape results
    """
    results = []
    for url in urls:
        result = scrape_website(url, max_length)
        results.append(result)
    return results


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Website Scraper Tool")
    parser.add_argument("url", help="URL to scrape")
    parser.add_argument("--output", "-o", help="Output file (JSON)")
    parser.add_argument("--max-length", "-m", type=int, default=2000,
                        help="Maximum content length")

    args = parser.parse_args()

    result = scrape_website(args.url, args.max_length)

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(result, indent=2))
