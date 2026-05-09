"""
Sub Agent Brain 1 (SAB1) for NeuroDesk AI Multi-Agent System.
Market Research Analyst - research competitors, audience insights, market trends.
"""

import json
import asyncio
import time
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_client import LLMClient
from core.tool_registry import ToolRegistry
from config import get_config


class SAB1:
    """Sub Agent Brain 1 - Market Research Analyst."""

    def __init__(self, config: Dict = None, config_file: str = "config/config.json"):
        self.config = config or get_config(config_file)
        self.llm_client = None
        self.tool_registry = ToolRegistry()
        self.provider = self.config.get("SAB1", {}).get("provider", "Ollama")
        self.api_key = self.config.get("SAB1", {}).get("api_key", "")
        self.model = self.config.get("SAB1", {}).get("model", "llama3:8b")
        self._initialized = False
        self._load_pre_instructions()
        self._load_tools()

    def _load_pre_instructions(self):
        """Load pre-instructions from config."""
        pre_instructions_file = Path("config/pre_instructions.json")
        if pre_instructions_file.exists():
            try:
                with open(pre_instructions_file, 'r') as f:
                    data = json.load(f)
                    self.pre_instructions = data.get("SAB1", self._default_pre_instruction())
            except Exception:
                self.pre_instructions = self._default_pre_instruction()
        else:
            self.pre_instructions = self._default_pre_instruction()

    def _default_pre_instruction(self) -> str:
        """Return default pre-instruction for SAB1."""
        return """You are SAB1 — the Market Research Analyst of NeuroDesk.
You are an AI assistant called SAB1, part of the NeuroDesk AI platform built by the NeuroDesk team. Do NOT refer to yourself as any other AI model, language model, or product (e.g., GPT, Claude, Qwen, Gemini, etc.). Always introduce yourself as SAB1. Your job is:
1. Accept research tasks from MAB only.
2. Use available search tools to find competitor data, audience insights, market trends, and relevant statistics.
3. Return a structured, data-rich research report.
4. Be thorough and factual. Cite sources where possible.
5. Pass your output clearly labeled for SAB2 to use as context."""

    def _load_tools(self):
        """Load available tools for SAB1."""
        self.tools = {}
        tools_dir = Path("tools")

        # Check for Serper Search
        if (tools_dir / "serper_search.py").exists():
            self.tools["serper_search"] = {
                "name": "serper_search",
                "path": str(tools_dir / "serper_search.py"),
                "type": "search"
            }

        # Check for Website Scraper
        if (tools_dir / "website_scraper.py").exists():
            self.tools["website_scraper"] = {
                "name": "website_scraper",
                "path": str(tools_dir / "website_scraper.py"),
                "type": "scrape"
            }

    def initialize(self):
        """Initialize SAB1 by creating LLM client."""
        if not self._initialized:
            self.llm_client = LLMClient(
                provider=self.provider,
                api_key=self.api_key,
                model=self.model,
                config=self.config,
                base_url=self.config.get("SAB1", {}).get("base_url", "http://localhost:8000/v1")
            )
            self._initialized = True

    async def run_task(self, task: str, context: str = "", stream_callback: Callable = None) -> Dict[str, Any]:
        """Execute a research task."""
        self.initialize()

        start_time = time.time()
        full_output = ""

        # Step 1: Prepare prompt
        prompt = self._build_prompt(task, context)

        # Step 2: Stream processing status
        await self._stream("working", "🔍 SAB1: Analyzing research task...", stream_callback)

        # Step 3: Execute with LLM
        try:
            response = await self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=self.pre_instructions,
                stream=True
            )

            # Stream the response
            async for chunk in response:
                chunk_text = chunk if isinstance(chunk, str) else (chunk.text if hasattr(chunk, 'text') else str(chunk))
                full_output += chunk_text
                await self._stream("working", chunk_text, stream_callback, elapsed=time.time() - start_time)

        except Exception as e:
            full_output = f"Error during research: {str(e)}"
            await self._stream("error", f"❌ SAB1: Error during research - {str(e)}", stream_callback)

        # Step 4: Save to database memory if session exists
        elapsed = time.time() - start_time
        if stream_callback:
            await self._stream("done", f"✅ SAB1: Research complete in {elapsed:.2f}s", stream_callback)

        return {
            "success": True,
            "output": full_output,
            "elapsed_seconds": elapsed
        }

    async def _stream(self, status: str, message: str, callback: Callable = None, elapsed: float = 0):
        """Stream a message to the callback."""
        if callback:
            await callback({
                "type": f"sab_{status}",
                "agent": "SAB1",
                "message": message,
                "elapsed_seconds": elapsed
            })

    def _build_prompt(self, task: str, context: str = "") -> str:
        """Build the prompt for SAB1."""
        prompt_parts = [self.pre_instructions]
        prompt_parts.append(f"\n\n[Current Task]\n{task}")

        if context:
            prompt_parts.append(f"\n\n[Previous Context]\n{context}")

        prompt_parts.append("\n\nPlease execute this research task and return a structured report.")

        return "\n".join(prompt_parts)


    async def search_web(self, query: str, stream_callback: Callable = None) -> Dict[str, Any]:
        """Perform web search using available tools."""
        if not self.tools.get("serper_search"):
            await self._stream("error", "⚠️ SAB1: Serper Search tool not available", stream_callback)
            return {"success": False, "error": "Tool not available"}

        await self._stream("working", "🔍 SAB1: Searching the web...", stream_callback)

        try:
            # Import and use the serper_search module
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "serper_search",
                Path("tools/serper_search.py")
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            results = module.serper_search(query)
            return {"success": True, "results": results}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_agent_info(self) -> Dict[str, Any]:
        """Get SAB1 agent information."""
        return {
            "agent_id": "SAB1",
            "name": "Research Analyst",
            "provider": self.provider,
            "model": self.model,
            "tools": list(self.tools.keys())
        }

    async def chat(self, message: str, history: List[Dict] = None, stream_callback: Callable = None) -> Dict[str, Any]:
        """Direct chat with SAB1."""
        self.initialize()

        start_time = time.time()
        full_output = ""

        # Build conversation context
        # Build conversation context - check for duplicates and truncate
        messages = []
        if history:
            # Truncate history to last 10 messages to save tokens
            recent_history = history[-10:] if len(history) > 10 else history
            
            if recent_history[-1].get("content") == message:
                messages.extend(recent_history)
            else:
                messages.extend(recent_history)
                messages.append({"role": "user", "content": message})
        else:
            messages.append({"role": "user", "content": message})

        # Memory is handled by MAB, SABs rely on prompt context
        memory_context = ""

        system_prompt = self.pre_instructions + memory_context

        try:
            response = await self.llm_client.chat(
                messages=messages,
                system_prompt=system_prompt,
                stream=True
            )

            async for chunk in response:
                chunk_text = chunk if isinstance(chunk, str) else (chunk.text if hasattr(chunk, 'text') else str(chunk))
                full_output += chunk_text
                await self._stream("working", chunk_text, stream_callback, elapsed=time.time() - start_time)

        except Exception as e:
            full_output = f"Error: {str(e)}"

        elapsed = time.time() - start_time
        await self._stream("done", f"✅ SAB1: Response complete in {elapsed:.2f}s", stream_callback)

        return {
            "success": True,
            "output": full_output,
            "elapsed_seconds": elapsed
        }
