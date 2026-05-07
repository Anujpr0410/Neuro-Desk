"""
Tool Registry System for NeuroDesk AI Multi-Agent System.
Manages tools installation, discovery, and assignment to agents.
"""

import json
import os
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import httpx
import asyncio


@dataclass
class ToolInfo:
    """Information about a tool."""
    name: str
    installed: bool = False
    path: str = ""
    assigned_to: List[str] = field(default_factory=list)
    description: str = ""
    github_url: str = ""
    last_modified: str = ""


class ToolRegistry:
    """Manages tool registry for NeuroDesk agents."""

    def __init__(self, tools_dir: str = "tools", registry_file: str = "tools/registry.json"):
        self.tools_dir = Path(tools_dir)
        self.registry_file = Path(registry_file)
        self.tools: Dict[str, ToolInfo] = {}
        self._load_registry()

    def _load_registry(self):
        """Load tool registry from file."""
        self.tools_dir.mkdir(parents=True, exist_ok=True)

        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r') as f:
                    data = json.load(f)
                    for name, info in data.items():
                        self.tools[name] = ToolInfo(
                            name=name,
                            installed=info.get("installed", False),
                            path=info.get("path", ""),
                            assigned_to=info.get("assigned_to", []),
                            description=info.get("description", "")
                        )
            except (json.JSONDecodeError, IOError):
                self.tools = {}

    def _save_registry(self):
        """Save tool registry to file."""
        data = {}
        for name, info in self.tools.items():
            data[name] = {
                "installed": info.installed,
                "path": info.path,
                "assigned_to": info.assigned_to,
                "description": info.description,
                "github_url": info.github_url,
                "last_modified": info.last_modified
            }

        with open(self.registry_file, 'w') as f:
            json.dump(data, f, indent=2)

    def is_available(self, tool_name: str) -> bool:
        """Check if a tool is available."""
        if tool_name not in self.tools:
            return False
        return self.tools[tool_name].installed

    def get_tool(self, tool_name: str) -> Optional[ToolInfo]:
        """Get tool information."""
        return self.tools.get(tool_name)

    def list_tools(self) -> Dict[str, ToolInfo]:
        """List all tools."""
        return self.tools

    def assign_tool(self, tool_name: str, agent_id: str) -> bool:
        """Assign a tool to an agent."""
        if tool_name not in self.tools:
            return False

        if agent_id not in self.tools[tool_name].assigned_to:
            self.tools[tool_name].assigned_to.append(agent_id)
            self._save_registry()
            return True
        return False

    def unassign_tool(self, tool_name: str, agent_id: str) -> bool:
        """Remove tool assignment from an agent."""
        if tool_name not in self.tools:
            return False

        if agent_id in self.tools[tool_name].assigned_to:
            self.tools[tool_name].assigned_to.remove(agent_id)
            self._save_registry()
            return True
        return False

    def search_github(self, tool_name: str) -> Optional[str]:
        """Search GitHub for a tool."""
        search_query = f"{tool_name} language:python"

        try:
            async def search():
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "https://api.github.com/search/repositories",
                        params={"q": search_query},
                        timeout=10.0
                    )
                    response.raise_for_status()
                    return response.json()

            result = asyncio.run(search())

            if "items" in result and len(result["items"]) > 0:
                return result["items"][0]["html_url"]
            return None
        except Exception:
            return None

    async def download_tool(self, tool_name: str, repo_url: str) -> bool:
        """Download and install a tool from GitHub."""
        # Extract owner/repo from URL
        match = re.match(r'https://github\.com/([^/]+)/([^/]+)', repo_url)
        if not match:
            return False

        owner, repo = match.groups()
        clone_url = f"https://github.com/{owner}/{repo}.git"
        target_dir = self.tools_dir / tool_name

        try:
            # Clone the repository
            result = subprocess.run(
                ["git", "clone", clone_url, str(target_dir)],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                return False

            # Update registry
            if tool_name in self.tools:
                self.tools[tool_name].installed = True
                self.tools[tool_name].github_url = repo_url
                self.tools[tool_name].last_modified = str(os.urandom(8).hex())
            else:
                self.tools[tool_name] = ToolInfo(
                    name=tool_name,
                    installed=True,
                    path=f"tools/{tool_name}",
                    assigned_to=[],
                    description=f"Downloaded tool: {repo}",
                    github_url=repo_url
                )

            self._save_registry()
            return True
        except Exception:
            return False

    def register_local_tool(self, tool_name: str, tool_path: str, description: str = "", assigned_to: List[str] = None) -> bool:
        """Register a locally existing tool."""
        if assigned_to is None:
            assigned_to = []

        # Check if file exists
        if not Path(tool_path).exists():
            return False

        if tool_name in self.tools:
            return False

        self.tools[tool_name] = ToolInfo(
            name=tool_name,
            installed=True,
            path=tool_path,
            assigned_to=assigned_to,
            description=description
        )

        self._save_registry()
        return True

    def remove_tool(self, tool_name: str) -> bool:
        """Remove a tool from registry."""
        if tool_name not in self.tools:
            return False

        del self.tools[tool_name]
        self._save_registry()
        return True

    def get_tools_for_agent(self, agent_id: str) -> List[ToolInfo]:
        """Get tools assigned to a specific agent."""
        return [tool for tool in self.tools.values() if agent_id in tool.assigned_to]

    def get_all_tools_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all tools."""
        return {
            name: {
                "name": info.name,
                "installed": info.installed,
                "path": info.path,
                "assigned_to": info.assigned_to,
                "description": info.description,
                "github_url": info.github_url
            }
            for name, info in self.tools.items()
        }
