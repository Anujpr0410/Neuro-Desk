"""
Task Manager for NeuroDesk AI Multi-Agent System.
Handles task planning, assignment, and tracking.
"""

import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
import asyncio


@dataclass
class Task:
    """Represents a single task."""
    task_id: str
    name: str
    description: str
    assigned_to: str = ""
    tools: List[str] = field(default_factory=list)
    status: str = "pending"
    result: str = ""
    elapsed_time: float = 0.0


@dataclass
class TaskPlan:
    """Represents a complete task plan."""
    goal: str
    tasks: List[Task] = field(default_factory=list)
    tools_required: List[str] = field(default_factory=list)
    tools_available: List[str] = field(default_factory=list)
    tools_missing: List[str] = field(default_factory=list)


class TaskManager:
    """Manages task planning and assignment for NeuroDesk."""

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.current_plan: Optional[TaskPlan] = None

    def parse_mab_response(self, response: str) -> Optional[TaskPlan]:
        """Parse MAB's response to extract task plan."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                plan_data = json.loads(json_match.group())
                return self._parse_plan_data(plan_data)

            # Fallback to text parsing
            return self._parse_text_response(response)
        except Exception:
            return None

    def _parse_plan_data(self, data: Dict) -> Optional[TaskPlan]:
        """Parse task plan from structured data."""
        goal = data.get("goal", "Unknown goal")
        tasks_data = data.get("tasks", [])

        tasks = []
        tools_required = set()

        for task_data in tasks_data:
            task = Task(
                task_id=task_data.get("id", f"T{len(tasks)+1}"),
                name=task_data.get("name", "Unnamed Task"),
                description=task_data.get("description", ""),
                assigned_to=task_data.get("agent", ""),
                tools=task_data.get("tools", [])
            )

            for tool in task.tools:
                tools_required.add(tool)

            tasks.append(task)

        return TaskPlan(
            goal=goal,
            tasks=tasks,
            tools_required=list(tools_required)
        )

    def _parse_text_response(self, response: str) -> Optional[TaskPlan]:
        """Parse task plan from text response."""
        tasks = []
        tools_required = set()

        # Look for task patterns
        task_patterns = [
            (r'Task 1[:\s]+(.+?)(?=Task 2|$)', 'SAB1', 'Research'),
            (r'Task 2[:\s]+(.+?)(?=Task 3|$)', 'SAB2', 'Strategy'),
            (r'Task 3[:\s]+(.+?)$', 'SAB3', 'Content')
        ]

        for pattern, agent, name in task_patterns:
            match = re.search(pattern, response, re.DOTALL | re.MULTILINE)
            if match:
                description = match.group(1).strip()
                tasks.append(Task(
                    task_id=f"Task {len(tasks)+1}",
                    name=name,
                    description=description,
                    assigned_to=agent,
                    tools=[]
                ))

        # Look for tools mentioned
        tool_matches = re.findall(r'(serper_search|website_scraper|linkedin_scraper|twitter_scraper|image_generator|emoji_generator)', response.lower())
        tools_required.update(tool_matches)

        return TaskPlan(
            goal=response[:100],
            tasks=tasks,
            tools_required=list(tools_required)
        )

    def plan_tasks(self, user_goal: str, tool_registry=None) -> TaskPlan:
        """Create a task plan from user goal."""
        tasks = [
            Task(
                task_id="T1",
                name="Research Task",
                description="Conduct market research including competitors, audience insights, and market trends",
                assigned_to="SAB1",
                tools=["serper_search"]
            ),
            Task(
                task_id="T2",
                name="Strategy Task",
                description="Build comprehensive 30-day content strategy with content pillars, posting calendar, and platform-specific formats",
                assigned_to="SAB2",
                tools=[]
            ),
            Task(
                task_id="T3",
                name="Content Task",
                description="Create ready-to-publish marketing content including social media captions, ad copy, and email newsletters",
                assigned_to="SAB3",
                tools=[]
            )
        ]

        tools_required = ["serper_search"]

        return TaskPlan(
            goal=user_goal,
            tasks=tasks,
            tools_required=tools_required
        )

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a specific task."""
        return self.tasks.get(task_id)

    def update_task(self, task_id: str, **kwargs) -> bool:
        """Update task properties."""
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)

        return True

    def add_task(self, task: Task) -> bool:
        """Add a task to the registry."""
        if task.task_id in self.tasks:
            return False
        self.tasks[task.task_id] = task
        return True

    def get_pending_tasks(self, agent: str = None) -> List[Task]:
        """Get pending tasks, optionally filtered by agent."""
        tasks = [t for t in self.tasks.values() if t.status == "pending"]
        if agent:
            tasks = [t for t in tasks if t.assigned_to == agent]
        return tasks

    def get_tasks_by_status(self, status: str) -> List[Task]:
        """Get all tasks with a specific status."""
        return [t for t in self.tasks.values() if t.status == status]

    def mark_task_complete(self, task_id: str, result: str) -> bool:
        """Mark a task as complete with its result."""
        if task_id not in self.tasks:
            return False

        self.tasks[task_id].status = "completed"
        self.tasks[task_id].result = result
        return True

    def get_context_for_agent(self, agent_id: str) -> str:
        """Get context from previous agents for a specific agent."""
        context_parts = []

        if agent_id == "SAB2":
            # Get SAB1's output
            sab1_tasks = [t for t in self.tasks.values() if t.assigned_to == "SAB1" and t.status == "completed"]
            if sab1_tasks:
                context_parts.append(f"[SAB1 Research Results]\n{sab1_tasks[0].result}")

        elif agent_id == "SAB3":
            # Get both SAB1 and SAB2 outputs
            for task in self.tasks.values():
                if task.assigned_to in ["SAB1", "SAB2"] and task.status == "completed":
                    role = "SAB1 Research" if task.assigned_to == "SAB1" else "SAB2 Strategy"
                    context_parts.append(f"[{role}]\n{task.result}")

        return "\n\n".join(context_parts) if context_parts else ""
