"""
Sub Agent Brain 2 (SAB2) for NeuroDesk AI Multi-Agent System.
Marketing Strategy Specialist - builds 30-day content strategies.
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
from core.memory_manager import get_memory_manager, MemoryManager
from config import get_config


class SAB2:
    """Sub Agent Brain 2 - Marketing Strategy Specialist."""

    def __init__(self, config: Dict = None, config_file: str = "config/config.json"):
        self.config = config or get_config(config_file)
        self.llm_client = None
        self.tool_registry = ToolRegistry()
        self.memory_manager = get_memory_manager("SAB2")
        self.provider = self.config.get("SAB2", {}).get("provider", "Ollama")
        self.api_key = self.config.get("SAB2", {}).get("api_key", "")
        self.model = self.config.get("SAB2", {}).get("model", "llama3:8b")
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
                    self.pre_instructions = data.get("SAB2", self._default_pre_instruction())
            except Exception:
                self.pre_instructions = self._default_pre_instruction()
        else:
            self.pre_instructions = self._default_pre_instruction()

    def _default_pre_instruction(self) -> str:
        """Return default pre-instruction for SAB2."""
        return """You are SAB2 — the Marketing Strategy Specialist of NeuroDesk.
You are an AI assistant called SAB2, part of the NeuroDesk AI platform built by the NeuroDesk team. Do NOT refer to yourself as any other AI model, language model, or product (e.g., GPT, Claude, Qwen, Gemini, etc.). Always introduce yourself as SAB2. Your job is:
1. Accept strategy tasks from MAB only.
2. Use SAB1's research output as your foundation.
3. Build a comprehensive 30-day content strategy including: content pillars, posting calendar, platform-specific formats, hashtag strategy, engagement tactics.
4. Return a structured strategy document clearly labeled for SAB3."""

    def _load_tools(self):
        """Load available tools for SAB2."""
        self.tools = {}
        tools_dir = Path("tools")

        if (tools_dir / "serper_search.py").exists():
            self.tools["serper_search"] = {
                "name": "serper_search",
                "path": str(tools_dir / "serper_search.py"),
                "type": "search"
            }

        if (tools_dir / "website_scraper.py").exists():
            self.tools["website_scraper"] = {
                "name": "website_scraper",
                "path": str(tools_dir / "website_scraper.py"),
                "type": "scrape"
            }

    def initialize(self):
        """Initialize SAB2 by creating LLM client."""
        if not self._initialized:
            self.llm_client = LLMClient(
                provider=self.provider,
                api_key=self.api_key,
                model=self.model
            )
            self._initialized = True

    async def run_task(self, task: str, context: str = "", stream_callback: Callable = None) -> Dict[str, Any]:
        """Execute a strategy task."""
        self.initialize()

        start_time = time.time()
        full_output = ""

        # Prepare prompt
        prompt = self._build_prompt(task, context)

        # Stream processing status
        await self._stream("working", "📊 SAB2: Building content strategy...", stream_callback)

        # Execute with LLM
        try:
            response = await self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=self.pre_instructions,
                stream=True
            )

            async for chunk in response:
                chunk_text = chunk if isinstance(chunk, str) else (chunk.text if hasattr(chunk, 'text') else str(chunk))
                full_output += chunk_text
                await self._stream("working", chunk_text, stream_callback, elapsed=time.time() - start_time)

        except Exception as e:
            full_output = f"Error during strategy creation: {str(e)}"
            await self._stream("error", f"❌ SAB2: Error during strategy creation - {str(e)}", stream_callback)

        # Save to memory
        await self._save_to_memory(task, full_output)

        elapsed = time.time() - start_time
        await self._stream("done", f"✅ SAB2: Strategy complete in {elapsed:.2f}s", stream_callback)

        return {
            "success": True,
            "result": full_output,
            "elapsed_seconds": elapsed
        }

    async def _stream(self, status: str, message: str, callback: Callable = None, elapsed: float = 0):
        """Stream a message to the callback."""
        if callback:
            await callback({
                "type": f"sab_{status}",
                "agent": "SAB2",
                "message": message,
                "elapsed_seconds": elapsed
            })

    def _build_prompt(self, task: str, context: str = "") -> str:
        """Build the prompt for SAB2."""
        prompt_parts = [self.pre_instructions]
        prompt_parts.append(f"\n\n[Current Task]\n{task}")

        if context:
            prompt_parts.append(f"\n\n[Research Context from SAB1]\n{context}")

        prompt_parts.append("\n\nPlease build a comprehensive 30-day content strategy based on this information.")

        return "\n".join(prompt_parts)

    async def _save_to_memory(self, task: str, output: str):
        """Save strategy results to SAB2's memory."""
        metadata = {
            "type": "strategy",
            "task": task,
            "agent": "SAB2"
        }
        self.memory_manager.add(
            document=f"Task: {task}\n\nStrategy: {output}",
            metadata=metadata
        )

    def get_agent_info(self) -> Dict[str, Any]:
        """Get SAB2 agent information."""
        return {
            "agent_id": "SAB2",
            "name": "Strategy Specialist",
            "provider": self.provider,
            "model": self.model,
            "tools": list(self.tools.keys()),
            "memory_count": self.memory_manager.get_stats()["document_count"]
        }

    async def chat(self, message: str, history: List[Dict] = None, stream_callback: Callable = None) -> Dict[str, Any]:
        """Direct chat with SAB2."""
        self.initialize()

        start_time = time.time()
        full_output = ""

        messages = []
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": message})

        # Inject long-term memory: query ChromaDB for relevant past strategy work
        memory_context = ""
        try:
            memory_results = self.memory_manager.query(message, n_results=3)
            past_docs = memory_results.get("documents", [[]])[0]
            past_distances = memory_results.get("distances", [[]])[0]
            relevant_docs = [
                doc for doc, dist in zip(past_docs, past_distances)
                if dist < 1.2
            ]
            if relevant_docs:
                memory_context = "\n\n--- LONG-TERM MEMORY (from past strategy tasks) ---\n"
                for i, doc in enumerate(relevant_docs, 1):
                    memory_context += f"{i}. {doc}\n"
                memory_context += "--- END OF MEMORY ---\n"
        except Exception:
            pass

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
        await self._stream("done", f"✅ SAB2: Response complete in {elapsed:.2f}s", stream_callback)

        return {
            "success": True,
            "result": full_output,
            "elapsed_seconds": elapsed
        }
