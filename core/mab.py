"""
Main Agent Brain (MAB) for NeuroDesk AI Multi-Agent System.
The orchestrator and manager of the multi-agent team.
"""

import json
import asyncio
import time
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_client import LLMClient
from core.tool_registry import ToolRegistry
from core.task_manager import TaskManager, Task
from config import get_config
import memory.db as db


class MAB:
    """Main Agent Brain - Orchestrator and Manager."""

    def __init__(self, config: Dict = None, config_file: str = "config/config.json"):
        self.config = config or get_config(config_file)
        self.llm_client = None
        self.tool_registry = ToolRegistry()
        self.task_manager = TaskManager()
        self.provider = self.config.get("MAB", {}).get("provider", "Ollama")
        self.api_key = self.config.get("MAB", {}).get("api_key", "")
        self.model = self.config.get("MAB", {}).get("model", "llama3:8b")
        self._initialized = False
        self._load_pre_instructions()

    def _load_pre_instructions(self):
        """Load pre-instructions from config."""
        pre_instructions_file = Path("config/pre_instructions.json")
        if pre_instructions_file.exists():
            try:
                with open(pre_instructions_file, 'r') as f:
                    data = json.load(f)
                    self.pre_instructions = data.get("MAB", "")
            except Exception:
                self.pre_instructions = self._default_pre_instruction()
        else:
            self.pre_instructions = self._default_pre_instruction()

    def _default_pre_instruction(self) -> str:
        """Return default pre-instruction for MAB."""
        return """You are NeuroDesk's Main Agent Brain (MAB) — the orchestrator and manager of a multi-agent digital marketing team.
You are an AI assistant called MAB (Main Agent Brain), part of the NeuroDesk AI platform built by the NeuroDesk team. Do NOT refer to yourself as any other AI model, language model, or product (e.g., GPT, Claude, Qwen, Gemini, etc.). Always introduce yourself as MAB.

CONVERSATIONAL RULE (HIGHEST PRIORITY): If the user sends a greeting, a casual message, a question, or anything that is NOT a specific marketing campaign goal, respond naturally and conversationally like a helpful assistant. Do NOT generate a campaign plan, task breakdown, or report unless the user has clearly stated a marketing goal.

When the user DOES provide a campaign goal, your responsibilities are:
1. Understand the user's marketing goal clearly.
2. Ask any clarifying questions you need before proceeding.
3. Break the goal into exactly 3 tasks: Research (T1), Strategy (T2), Content Creation (T3).
4. Before assigning tasks, check which tools are required for each task.
5. Verify if those tools exist in the tools registry.
6. If a tool is missing, notify the user.
7. Show the user a clear plan and wait for their confirmation before running the campaign.
8. Assign T1 to SAB1, T2 to SAB2, T3 to SAB3 with full context.
9. Monitor task completion in real time and stream status to the user.
10. After all tasks are complete, collect outputs from SAB1, SAB2, SAB3.
11. Synthesize a final, polished, comprehensive marketing campaign report and deliver it to the user. Never perform tasks yourself that belong to a SAB. You are the manager."""

    def initialize(self):
        """Initialize MAB by creating LLM client."""
        if not self._initialized:
            self.llm_client = LLMClient(
                provider=self.provider,
                api_key=self.api_key,
                model=self.model
            )
            self._initialized = True

    async def run(self, user_goal: str, stream_callback: Callable = None) -> Dict[str, Any]:
        """Execute MAB workflow with real-time streaming."""
        try:
            self.initialize()

            context = []

            # Step 1: Understand goal
            await self._stream("thinking", "🧠 MAB: Understanding your marketing goal...", stream_callback)
            context.append(f"User Goal: {user_goal}")

            # Step 2: Plan tasks
            await self._stream("thinking", "🧠 MAB: Breaking your goal into 3 tasks...", stream_callback)
            task_plan = await self._create_task_plan(user_goal, stream_callback)
            context.append(f"Task Plan: {json.dumps(task_plan, indent=2)}")

            # Step 3: Tool check
            await self._stream("tool_check", f"🔍 MAB: Checking tools... {len(task_plan.get('tools_required', []))} required", stream_callback)
            tool_status = await self._check_tools(task_plan.get('tools_required', []), stream_callback)
            context.append(f"Tools: {json.dumps(tool_status, indent=2)}")

            # Step 4: Assign and execute tasks
            await self._stream("thinking", "🧠 MAB: Assigning tasks to sub-agents...", stream_callback)
            task_results = await self._execute_tasks(task_plan.get('tasks', []), stream_callback)
            context.append(f"Task Results: {json.dumps(task_results, indent=2)}")

            # Synthesize final output
            await self._stream("thinking", "🧠 MAB: Synthesizing final campaign report...", stream_callback)
            final_output = await self._synthesize_output(task_results, stream_callback)
            context.append(f"Final Output: {final_output}")

            return {
                "success": True,
                "user_goal": user_goal,
                "final_output": final_output,
                "tasks": task_results,
                "tools": tool_status
            }
        except Exception as e:
            await self._stream("error", f"❌ MAB Error: {str(e)}", stream_callback)
            return {
                "success": False,
                "error": str(e),
                "result": f"Execution failed: {str(e)}"
            }

    async def _stream(self, message_type: str, message: str, callback: Callable = None, **kwargs):
        """Stream a message to the callback."""
        if callback:
            await callback({
                "type": message_type,
                "message": message,
                "agent": "MAB",
                **kwargs
            })

    async def _create_task_plan(self, user_goal: str, stream_callback: Callable = None) -> Dict:
        """Create task plan from user goal using LLM."""
        messages = [
            {"role": "user", "content": f"Create a task plan for this goal:\n\n{user_goal}"}
        ]

        try:
            response = await self.llm_client.chat(
                messages=messages,
                system_prompt=self.pre_instructions,
                stream=False
            )

            # Parse response to extract task plan
            result_text = response.text if hasattr(response, 'text') else str(response)

            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            # Fallback parsing
            return {
                "goal": user_goal,
                "tasks": [
                    {"id": "T1", "name": "Research", "agent": "SAB1", "tools": ["serper_search"]},
                    {"id": "T2", "name": "Strategy", "agent": "SAB2", "tools": []},
                    {"id": "T3", "name": "Content", "agent": "SAB3", "tools": []}
                ],
                "tools_required": ["serper_search"]
            }
        except Exception as e:
            return {
                "goal": user_goal,
                "tasks": [
                    {"id": "T1", "name": "Research", "agent": "SAB1", "tools": ["serper_search"]},
                    {"id": "T2", "name": "Strategy", "agent": "SAB2", "tools": []},
                    {"id": "T3", "name": "Content", "agent": "SAB3", "tools": []}
                ],
                "tools_required": ["serper_search"],
                "error": str(e)
            }

    async def _check_tools(self, required_tools: List[str], stream_callback: Callable = None) -> Dict[str, Any]:
        """Check and install required tools."""
        status = {
            "required": required_tools,
            "available": [],
            "missing": [],
            "installed": []
        }

        for tool in required_tools:
            if self.tool_registry.is_available(tool):
                status["available"].append(tool)
                status["installed"].append(tool)
                await self._stream("tool_check", f"🔍 Tool '{tool}' already available", stream_callback)
            else:
                status["missing"].append(tool)
                await self._stream("tool_check", f"⚠️ Tool '{tool}' not found. Searching GitHub...", stream_callback)

                # Try to find and install
                github_url = await self.tool_registry.search_github(tool)
                if github_url:
                    await self._stream("tool_check", f"📂 Found '{tool}' on GitHub: {github_url}", stream_callback)
                    success = await self.tool_registry.download_tool(tool, github_url)
                    if success:
                        status["installed"].append(tool)
                        await self._stream("tool_check", f"✅ Tool '{tool}' installed successfully", stream_callback)
                    else:
                        await self._stream("error", f"❌ Failed to install '{tool}'", stream_callback)
                else:
                    await self._stream("error", f"⚠️ Tool '{tool}' not found on GitHub. Please add manually.", stream_callback)

        return status

    async def _execute_tasks(self, tasks: List[Dict], stream_callback: Callable = None) -> Dict[str, Any]:
        """Execute tasks by assigning to SABs."""
        results = {}

        for task in tasks:
            agent_id = task.get("agent", "SAB1")
            task_id = task.get("id", "unknown")
            task_desc = task.get("description", "")

            await self._stream("task_assign", f"➡️ Assigning {task_id} to {agent_id}...", stream_callback)

            # Get context from previous tasks
            context = self._get_task_context(task_id, results)

            # Execute task (simulated for now - in real implementation, this would call SAB)
            results[agent_id] = {
                "task_id": task_id,
                "status": "completed",
                "output": await self._simulate_sab_execution(agent_id, task_desc, context, stream_callback)
            }

        return results

    def _get_task_context(self, current_task: str, results: Dict) -> str:
        """Get context from previous task results."""
        context_parts = []
        for agent_id, task_result in results.items():
            if agent_id != current_task:
                context_parts.append(f"[{agent_id} Output]\n{task_result.get('output', '')}")
        return "\n\n".join(context_parts)

    async def _simulate_sab_execution(self, agent_id: str, task_desc: str, context: str, stream_callback: Callable = None) -> str:
        """Simulate SAB execution (in real app, this would delegate to actual SAB agents)."""
        start_time = time.time()

        # Stream working status
        await self._stream("sab_working", f"🔍 {agent_id}: Processing task...", stream_callback)

        # Create a simple response
        output = f"[{agent_id} Execution]\n\nTask: {task_desc}\n\nThis would contain the actual output from {agent_id} after processing the task with its assigned LLM and tools."

        elapsed = time.time() - start_time
        await self._stream("sab_done", f"✅ {agent_id}: Task completed in {elapsed:.2f}s", stream_callback)

        return output

    async def _synthesize_output(self, task_results: Dict, stream_callback: Callable = None) -> str:
        """Synthesize final output from all task results."""
        all_results = []
        for agent_id, result in task_results.items():
            all_results.append(f"[{agent_id} Results]\n{result.get('output', '')}")

        messages = [
            {"role": "user", "content": f"Synthesize these results into a final campaign report:\n\n{''.join(all_results)}"}
        ]

        try:
            response = await self.llm_client.chat(
                messages=messages,
                system_prompt="Synthesize the provided task results into a comprehensive, polished marketing campaign report.",
                stream=False
            )
            raw = response.text if hasattr(response, 'text') else str(response)
            return self._finalize_report(raw)
        except Exception as e:
            return f"Synthesis complete. Final output:\n\n{''.join(all_results)}\n\n(Note: Synthesis failed with error: {str(e)})"

    def _finalize_report(self, report_text: str) -> str:
        """Post-process the report: replace any LLM-hallucinated dates with today's real date."""
        today = datetime.now().strftime("%B %d, %Y")
        # Match patterns like: "April 5, 2024", "January 1, 2023", "March 15, 2025"
        date_pattern = r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b'
        report_text = re.sub(date_pattern, today, report_text)
        # Also replace short year-only patterns like "Q2 2024" → "Q2 <current year>"
        current_year = str(datetime.now().year)
        report_text = re.sub(r'\b20(?:2[0-3])\b', current_year, report_text)  # Replace 2020-2023
        return report_text

    async def chat(self, message: str, history: List[Dict] = None, stream_callback: Callable = None) -> Dict[str, Any]:
        """Direct chat with MAB."""
        self.initialize()

        import time
        start_time = time.time()
        full_output = ""

        # Build conversation context
        messages = []
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": message})

        # Inject long-term memory: query SQLite for recent campaigns
        memory_context = ""
        try:
            recent_memories = db.get_recent_memories(limit=3)
            if recent_memories:
                memory_context = "\n\n--- LONG-TERM MEMORY (from past campaigns) ---\n"
                for i, mem in enumerate(recent_memories, 1):
                    memory_context += f"Campaign {i}:\nGoal: {mem['goal']}\nSummary: {mem['summary']}\n\n"
                memory_context += "--- END OF MEMORY ---\n"
        except Exception:
            pass  # If memory query fails, continue without it

        system_prompt = self.pre_instructions + memory_context + "\n\nIMPORTANT: If the user explicitly asks you to proceed or run the campaign, or confirms the plan, you MUST include the exact string '[START_CAMPAIGN]' somewhere in your response. This acts as a trigger to start the automated multi-agent workflow."

        try:
            response = await self.llm_client.chat(
                messages=messages,
                system_prompt=system_prompt,
                stream=True
            )

            async for chunk in response:
                if isinstance(chunk, str):
                    full_output += chunk
                    await self._stream("working", chunk, stream_callback)
                elif hasattr(chunk, 'text'):
                    full_output += chunk.text
                    await self._stream("working", chunk.text, stream_callback)

        except Exception as e:
            full_output = f"Error: {str(e)}"

        # Restoring trigger logic: Check if we should automatically start the campaign
        # If START_CAMPAIGN is present, we return it so the frontend can trigger the /campaign/run call
        # We also add a small note in the activity stream
        if "[START_CAMPAIGN]" in full_output:
            await self._stream("info", "🚀 MAB: Plan confirmed. Auto-starting campaign...", stream_callback)

        elapsed = time.time() - start_time
        await self._stream("done", f"✅ MAB: Response complete in {elapsed:.2f}s", stream_callback)

        return {
            "success": True,
            "result": full_output
        }

    def get_agent_info(self) -> Dict[str, Any]:
        """Get MAB agent information."""
        return {
            "agent_id": "MAB",
            "provider": self.provider,
            "model": self.model,
            "pre_instruction": self.pre_instructions[:100] + "..." if len(self.pre_instructions) > 100 else self.pre_instructions
        }
