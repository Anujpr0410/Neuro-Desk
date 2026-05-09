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
from core.performance_logger import PerformanceLogger
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

        # Performance logger for AMD metrics
        self.performance_logger = PerformanceLogger()

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
                model=self.model,
                config=self.config,
                base_url=self.config.get("MAB", {}).get("base_url", "http://localhost:8000/v1")
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

            # Fallback parsing with detailed descriptions
            return {
                "goal": user_goal,
                "tasks": [
                    {
                        "id": "T1", 
                        "name": "Research", 
                        "agent": "SAB1", 
                        "description": f"Perform comprehensive market research and target audience analysis for: {user_goal}. Identify key trends, competitor strategies, and audience pain points.",
                        "tools": ["serper_search"]
                    },
                    {
                        "id": "T2", 
                        "name": "Strategy", 
                        "agent": "SAB2", 
                        "description": "Develop a detailed 30-day marketing strategy based on the T1 research. Include content pillars, platform selection, and engagement tactics.",
                        "tools": []
                    },
                    {
                        "id": "T3", 
                        "name": "Content", 
                        "agent": "SAB3", 
                        "description": "Create high-converting marketing copy for social media, ads, and emails based on the T2 strategy. Ensure brand alignment and actionable hooks.",
                        "tools": []
                    }
                ],
                "tools_required": ["serper_search"]
            }
        except Exception as e:
            return {
                "goal": user_goal,
                "tasks": [
                    {"id": "T1", "name": "Research", "agent": "SAB1", "description": f"Research {user_goal}", "tools": ["serper_search"]},
                    {"id": "T2", "name": "Strategy", "agent": "SAB2", "description": "Build strategy", "tools": []},
                    {"id": "T3", "name": "Content", "agent": "SAB3", "description": "Write content", "tools": []}
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

            # Execute task using the appropriate mode
            results[agent_id] = await self._execute_sab_task(
                agent_id, task_desc, context, stream_callback
            )

        return results

    def _get_task_context(self, current_task: str, results: Dict) -> str:
        """Get context from previous task results."""
        context_parts = []
        for agent_id, task_result in results.items():
            if agent_id != current_task:
                context_parts.append(f"[{agent_id} Output]\n{task_result.get('output', '')}")
        return "\n\n".join(context_parts)

    def _is_demo_mode(self) -> bool:
        """Check if demo mode is enabled."""
        return self.config.get("DEMO_MODE", {}).get("enabled", True)

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

    async def _execute_sab_task(
        self,
        agent_id: str,
        task_desc: str,
        context: str,
        stream_callback: Callable = None
    ) -> Dict[str, Any]:
        """Execute a task for a specific SAB agent."""
        sab_class = {
            "SAB1": "core.sab1.SAB1",
            "SAB2": "core.sab2.SAB2",
            "SAB3": "core.sab3.SAB3"
        }.get(agent_id)

        if self._is_demo_mode():
            # Demo mode: Use mock data
            return await self._execute_demo_task(agent_id, task_desc, context, stream_callback)
        else:
            # Live mode: Execute actual task
            return await self._execute_live_task(agent_id, task_desc, context, stream_callback)

    async def _execute_demo_task(
        self,
        agent_id: str,
        task_desc: str,
        context: str,
        stream_callback: Callable = None
    ) -> Dict[str, Any]:
        """Execute task with demo/mock data."""
        import time
        start_time = time.time()

        # Get sample data based on agent role
        sample_outputs = {
            "SAB1": self._get_sab1_demo_output(task_desc, context),
            "SAB2": self._get_sab2_demo_output(task_desc, context),
            "SAB3": self._get_sab3_demo_output(task_desc, context)
        }

        output = sample_outputs.get(agent_id, f"[{agent_id} Demo Mode]\n\nTask: {task_desc}\n\nMock research results generated.")

        elapsed = time.time() - start_time

        # Stream completion status
        await self._stream("sab_done", f"✅ {agent_id}: Demo mode complete in {elapsed:.2f}s", stream_callback)

        return {
            "task_id": f"T{agent_id[-1]}",
            "agent": agent_id,
            "status": "completed",
            "output": output,
            "elapsed_seconds": round(elapsed, 2),
            "demo_mode": True
        }

    async def _execute_live_task(
        self,
        agent_id: str,
        task_desc: str,
        context: str,
        stream_callback: Callable = None
    ) -> Dict[str, Any]:
        """Execute task with actual SAB agent."""
        sab_module = {
            "SAB1": __import__("core.sab1", fromlist=["SAB1"]),
            "SAB2": __import__("core.sab2", fromlist=["SAB2"]),
            "SAB3": __import__("core.sab3", fromlist=["SAB3"])
        }.get(agent_id)

        if sab_module:
            sab_class = getattr(sab_module, agent_id)
            sab = sab_class(config=self.config)
            result = await sab.run_task(task_desc, context, stream_callback)
            return {
                "task_id": f"T{agent_id[-1]}",
                "agent": agent_id,
                "status": "completed",
                "output": result.get("output", result.get("result", "")),
                "elapsed_seconds": result.get("elapsed_seconds", 0),
                "demo_mode": False
            }

        return await self._simulate_sab_execution(agent_id, task_desc, context, stream_callback)

    def _get_sab1_demo_output(self, task: str, context: str) -> str:
        """Generate demo output for SAB1 (Research)."""
        return f"""[SAB1 Demo Mode - Research Output]

Task: {task}

## Research Findings (Demo Data)

### Market Trends
- AI-powered marketing tools adoption up 45% YoY
- Video content engagement increasing by 30% month-over-month
- Influencer marketing ROI reaching 164%

### Target Audience Insights
- Primary: 25-45 year old professionals
- Secondary: Small business owners (35-55)
- Tertiary: Creative professionals (22-35)

### Competitor Analysis
Top competitors are focusing on:
1. AI-powered content creation
2. Interactive video experiences
3. Personalized email campaigns

---
*Note: This is demo data. Enable Live Tool Mode for real research.*
"""

    def _get_sab2_demo_output(self, task: str, context: str) -> str:
        """Generate demo output for SAB2 (Strategy)."""
        return f"""[SAB2 Demo Mode - Strategy Output]

Task: {task}

## 30-Day Content Strategy (Demo Data)

### Content Pillars
1. AI in Marketing - Exploring emerging technologies
2. Practical Growth Hacks - Actionable tips
3. Industry Insights - Trends and predictions

### Posting Calendar (Demo)
Week 1: Brand awareness focus
- Monday: LinkedIn thought piece
- Wednesday: Instagram Reel
- Friday: Twitter thread

Week 2: Lead generation
- Monday: Facebook ad campaign
- Wednesday: Email newsletter
- Friday: Instagram Story

Week 3: Community building
- Monday: LinkedIn group post
- Wednesday: Instagram Q&A
- Friday: Twitter chat

Week 4: Conversion
- Monday: Email sequence
- Wednesday: Instagram carousel
- Friday: Retargeting ad

---
*Note: This is demo data. Enable Live Tool Mode for real strategy generation.*
"""

    def _get_sab3_demo_output(self, task: str, context: str) -> str:
        """Generate demo output for SAB3 (Content)."""
        return f"""[SAB3 Demo Mode - Content Output]

Task: {task}

## Marketing Content (Demo Data)

### Social Media Captions
1. LinkedIn: "Ready to revolutionize your marketing? 🚀 AI is the future, and it's here today. Read our latest insights..."
2. Instagram: "Swipe to see how AI is transforming marketing! 💡 #AI #Marketing #Growth"
3. Twitter: "The future of marketing is here. Are you ready? 👇 #AIMarketing"

### Email Subject Lines
1. "Your guide to AI-powered marketing - inside!"
2. "30 days of growth: Your roadmap to success"
3. "Don't miss out: AI trends you need to know"

### Ad Copy (Demo)
**Headline:** Unlock Your Marketing Potential
**Primary Text:** AI is changing how we connect with customers. Learn how to harness its power for your business today.
**CTA:** Get Started Now

---
*Note: This is demo data. Enable Live Tool Mode for real content creation.*
"""

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
        return self._add_business_value(report_text)

    def _add_business_value(self, report_text: str) -> str:
        """Add business value analysis to the report."""
        today = datetime.now().strftime("%B %d, %Y")
        current_year = str(datetime.now().year)

        business_value = f"""
---
## Business Value Analysis

### Target Customer Type
- **Primary**: Small to medium business owners (35-55 years)
- **Secondary**: Marketing professionals seeking automation solutions
- **Tertiary**: Startups looking for AI-powered growth tools

### Expected Business Impact
- **Time Saved**: ~8-12 hours per campaign (from research to execution)
- **ROI Potential**: 3-5x on marketing investment through optimized content
- **Competitive Advantage**: AI-enhanced campaign execution at scale
- **Scalability**: Repeatable process for multiple campaigns simultaneously

### Where Human Review Is Recommended
1. **Content tone** - Review SAB3 output to ensure brand voice alignment
2. **Strategic decisions** - Verify SAB2 strategy aligns with business goals
3. **Data interpretation** - Validate SAB1 findings against local market knowledge
4. **Final approval** - Human oversight before campaign launch

### Next Actions
1. **Review** - Examine the campaign report and agent outputs
2. **Customize** - Adjust strategy and content to match brand guidelines
3. **Execute** - Implement the 30-day content calendar
4. **Measure** - Track performance against KPIs and optimize

---
*Note: This campaign was generated by NeuroDesk AMD using AMD MI300X-powered inference.*

*Report Generated on: {today}*

*AMD Cloud Model Endpoint: vLLM (OpenAI-compatible)*
"""
        return report_text.rstrip() + business_value

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
