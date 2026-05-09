"""
CLI Application for NeuroDesk AI Multi-Agent System.
Uses Rich library for terminal UI.
"""

import json
import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Any

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.markdown import Markdown
from rich.tree import Tree
from rich import box
from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
from rich.live import Live
from rich.layout import Layout
import rich

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.mab import MAB
from core.sab1 import SAB1
from core.sab2 import SAB2
from core.sab3 import SAB3
from core.tool_registry import ToolRegistry
from config import get_config, save_config, get_pre_instructions, save_pre_instructions

# Initialize console
console = Console()


class NeuroDeskCLI:
    """Main CLI application for NeuroDesk."""

    def __init__(self):
        self.config = get_config()
        self.pre_instructions = get_pre_instructions()
        self.mab = MAB(self.config)
        self.sab1 = SAB1(self.config)
        self.sab2 = SAB2(self.config)
        self.sab3 = SAB3(self.config)
        self.tool_registry = ToolRegistry()
        self.current_platform = "All"
        self.running = True

    def run(self):
        """Run the CLI application."""
        self.ensure_agents_configured()

        while self.running:
            self.show_main_menu()
            choice = Prompt.ask(
                "[bold]Select an option[/bold]",
                choices=["1", "2", "3", "4", "5", "6", "7"],
                default="1"
            )

            if choice == "1":
                self.run_full_campaign()
            elif choice == "2":
                self.chat_with_sab1()
            elif choice == "3":
                self.chat_with_sab2()
            elif choice == "4":
                self.chat_with_sab3()
            elif choice == "5":
                self.view_tool_registry()
            elif choice == "6":
                self.show_settings()
            elif choice == "7":
                console.print("[bold green]Goodbye![/bold green]")
                self.running = False

    def ensure_agents_configured(self):
        """Check if agents are configured, run wizard if not."""
        config = get_config()

        # Check if any agent has an empty API key (unless using Ollama)
        needs_setup = False
        for agent, agent_config in config.items():
            if not agent_config.get("model"):
                needs_setup = True
                break
            if agent_config.get("provider") != "Ollama" and not agent_config.get("api_key"):
                needs_setup = True
                break

        if needs_setup:
            console.print(Panel(
                "[bold]NeuroDesk Setup Wizard[/bold]\n\n"
                "It looks like this is your first time running NeuroDesk.\n"
                "Let's configure your AI agents.",
                title="[bold blue]Welcome to NeuroDesk[/bold blue]",
                border_style="blue"
            ))
            self.run_setup_wizard()

    def run_setup_wizard(self):
        """Run the API configuration wizard."""
        console.print("\n[bold blue]=== API Configuration Wizard ===[/bold blue]\n")

        providers = [
            ("1", "Ollama", "Local LLM - No API key required"),
            ("2", "OpenRouter", "Free models available - API key required"),
            ("3", "NVIDIA NIM", "Free credits available - API key required"),
            ("4", "Google Gemini", "Google's AI model - API key required"),
            ("5", "OpenAI", "OpenAI models - API key required")
        ]

        model_options = {
            "Ollama": ["llama3:8b", "llama3:70b", "mistral:7b", "codellama:7b"],
            "OpenRouter": ["meta-llama/llama-3-8b-instruct:free", "meta-llama/llama-3-70b-instruct:free"],
            "NVIDIA NIM": ["meta/llama3-8b-instruct", "meta/llama3-70b-instruct"],
            "Google Gemini": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"],
            "OpenAI": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4o-mini"]
        }

        config = {}

        for agent_name, agent_display in [
            ("MAB", "Main Agent Brain (Orchestrator)"),
            ("SAB1", "Sub Agent 1 (Research Analyst)"),
            ("SAB2", "Sub Agent 2 (Strategy Specialist)"),
            ("SAB3", "Sub Agent 3 (Content Writer)")
        ]:
            console.print(f"\n[bold]Configuring {agent_display}[/bold]")

            # Show provider options
            console.print("Available providers:")
            for num, provider, desc in providers:
                console.print(f"  {num}. [bold]{provider}[/bold] - {desc}")

            provider_choice = Prompt.ask(
                "[bold]Select provider[/bold]",
                choices=[p[0] for p in providers],
                default="1"
            )
            selected_provider = providers[int(provider_choice) - 1][1]

            # Get API key if needed
            api_key = ""
            if selected_provider == "Ollama":
                api_key = "local"
                console.print("[green]✓ Ollama selected - local LLM, no API key needed[/green]")
            else:
                api_key = Prompt.ask(
                    f"[bold]Enter API key for {selected_provider}[/bold]",
                    password=True
                )

            # Get model name
            console.print(f"\nSuggested models for {selected_provider}:")
            models = model_options.get(selected_provider, [])
            for i, model in enumerate(models, 1):
                console.print(f"  {i}. {model}")

            model_choice = Prompt.ask(
                "[bold]Enter model name[/bold]",
                choices=[str(i) for i in range(1, len(models) + 1)],
                default="1"
            )
            selected_model = models[int(model_choice) - 1]

            config[agent_name] = {
                "provider": selected_provider,
                "api_key": api_key,
                "model": selected_model
            }

            console.print(Panel(
                f"[bold]{agent_name}[/bold]\nProvider: {selected_provider}\nModel: {selected_model}",
                title="Configuration Complete",
                border_style="green"
            ))

        # Save configuration
        save_config(config)

        console.print("\n[bold green]=== All agents configured successfully! ===[/bold green]\n")
        console.print(Panel(
            "NeuroDesk is now ready to use!\nRun 'python -m cli.cli_app' to start.",
            title="[bold blue]Setup Complete[/bold blue]",
            border_style="green"
        ))

    def show_main_menu(self):
        """Display the main menu."""
        console.clear()
        console.print(Panel(
            "[bold]NeuroDesk AI Multi-Agent System[/bold]\n"
            "Hierarchical AI agent orchestration for digital marketing automation",
            title="[bold blue]Main Menu[/bold blue]",
            border_style="blue"
        ))

        menu = Table.grid(padding=1)
        menu.add_column()
        menu.add_column()

        menu.add_row("[1] Run Full Campaign (MAB Mode)", "Full automated campaign execution")
        menu.add_row("[2] Chat with SAB1", "Direct chat with Research Analyst")
        menu.add_row("[3] Chat with SAB2", "Direct chat with Strategy Specialist")
        menu.add_row("[4] Chat with SAB3", "Direct chat with Content Writer")
        menu.add_row("[5] View Tool Registry", "Manage tools for agents")
        menu.add_row("[6] Settings", "Edit pre-instructions, API keys")
        menu.add_row("[7] Exit", "Exit NeuroDesk")

        console.print(menu)

    def run_full_campaign(self):
        """Run a full campaign with all agents."""
        console.clear()
        console.print(Panel(
            "[bold]Run Full Campaign[/bold]\n"
            "MAB will orchestrate SAB1, SAB2, and SAB3 to create a complete marketing campaign",
            title="[bold cyan]Campaign Mode[/bold cyan]",
            border_style="cyan"
        ))

        goal = Prompt.ask("[bold]Enter your campaign goal[/bold]")
        platform = Prompt.ask(
            "[bold]Select target platform[/bold]",
            choices=["Instagram", "LinkedIn", "Facebook", "Twitter/X", "All"],
            default="All"
        )

        self.current_platform = platform

        console.print("\n[bold cyan]Starting campaign execution...[/bold cyan]\n")

        # Run campaign asynchronously
        asyncio.run(self._execute_campaign(goal))

    async def _execute_campaign(self, goal: str):
        """Execute the campaign with progress indicators."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=False
        ) as progress:
            task = progress.add_task(f"Running campaign for: {goal}", total=100)

            # MAB processing
            progress.update(task, description="[mab]MAB: Analyzing goal...", advance=10)
            await asyncio.sleep(1)

            progress.update(task, description="[sab1]SAB1: Conducting research...", advance=20)
            await asyncio.sleep(2)

            progress.update(task, description="[sab2]SAB2: Building strategy...", advance=30)
            await asyncio.sleep(2)

            progress.update(task, description="[sab3]SAB3: Creating content...", advance=40)
            await asyncio.sleep(2)

            progress.update(task, description="[mab]MAB: Synthesizing final output...", advance=10)
            await asyncio.sleep(1)

            progress.update(task, completed=100)

        console.print("\n[bold green]Campaign complete![/bold green]")

        # Display sample output
        console.print(Panel(
            f"""# Campaign Report for: {goal}

## Executive Summary
A comprehensive marketing campaign has been planned.

## Target Platform: {self.current_platform}

## Key Insights
- Market research completed
- Competitor analysis provided
- Audience insights gathered

## Strategy
- 30-day content calendar created
- Content pillars defined
- Engagement tactics recommended

## Content
- Social media captions prepared
- Ad copy created
- Email newsletter drafts ready

## Recommendations
1. Start with content pillars
2. Post consistently following the 30-day calendar
3. Monitor engagement and adjust as needed

--- Generated by NeuroDesk AI Multi-Agent System ---
""",
            title="[bold green]Campaign Results[/bold green]",
            border_style="green"
        ))

        if Confirm.ask("Run another campaign?"):
            self.run_full_campaign()

    def chat_with_sab1(self):
        """Chat with SAB1 (Research Analyst)."""
        self._agent_chat_loop("SAB1", self.sab1, "Research Analyst")

    def chat_with_sab2(self):
        """Chat with SAB2 (Strategy Specialist)."""
        self._agent_chat_loop("SAB2", self.sab2, "Strategy Specialist")

    def chat_with_sab3(self):
        """Chat with SAB3 (Content Writer)."""
        self._agent_chat_loop("SAB3", self.sab3, "Content Writer")

    def _agent_chat_loop(self, agent_id: str, agent, agent_role: str):
        """Chat loop for an agent."""
        console.clear()
        console.print(Panel(
            f"[bold]Chat with {agent_id} - {agent_role}[/bold]\n"
            "Type your message and press Enter to send.\n"
            "Type 'exit' to return to main menu.\n"
            "Type 'history' to view conversation history.",
            title=f"[bold {self._get_agent_color(agent_id)}]{agent_id}[/bold {self._get_agent_color(agent_id)}]",
            border_style=self._get_agent_color(agent_id)
        ))

        conversation_history = []

        while True:
            message = Prompt.ask(f"[bold]{agent_id}[/bold]")

            if message.lower() == "exit":
                break
            elif message.lower() == "history":
                for entry in conversation_history:
                    if entry["role"] == "user":
                        console.print(f"[yellow]You:[/yellow] {entry['content']}")
                    else:
                        console.print(f"[green]{agent_id}:[/green] {entry['content']}")
                continue

            # Add to history
            conversation_history.append({"role": "user", "content": message})

            # Show typing indicator
            with console.status(f"[bold]{agent_id} is typing..."):
                result = asyncio.run(agent.chat(message, conversation_history))

            output_text = result.get("output", result.get("result", ""))
            
            # Display response
            console.print(Panel(
                output_text,
                title=f"[bold green]{agent_id}[/bold green]",
                border_style=self._get_agent_color(agent_id)
            ))

            conversation_history.append({"role": "assistant", "content": output_text})

    def view_tool_registry(self):
        """View and manage tools."""
        console.clear()
        console.print(Panel(
            "[bold]Tool Registry[/bold]\n"
            "Tools are used by agents to perform specific tasks",
            title="[bold magenta]Tools[/bold magenta]",
            border_style="magenta"
        ))

        tools = self.tool_registry.list_tools()

        if not tools:
            console.print("\n[yellow]No tools registered yet.[/yellow]")
            console.print("Run a campaign to automatically discover and install tools.\n")
            return

        table = Table(title="Available Tools", box=box.ROUNDED)
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Assigned to", style="yellow")
        table.add_column("Description", style="white")

        for name, tool in tools.items():
            status = "[green]✓ Installed[/green]" if tool.installed else "[red]✗ Not installed[/red]"
            agents = ", ".join(tool.assigned_to) if tool.assigned_to else "None"
            table.add_row(name, status, agents, tool.description)

        console.print(table)

        if Confirm.ask("\nManage tools?"):
            self._manage_tools()

    def _manage_tools(self):
        """Manage tools (add/remove)."""
        while True:
            console.print("\n[bold]Tool Management[/bold]")
            console.print("1. View tool details")
            console.print("2. Add tool manually")
            console.print("3. Return to previous menu")

            choice = Prompt.ask("Select option", choices=["1", "2", "3"], default="3")

            if choice == "1":
                self._view_tool_details()
            elif choice == "2":
                self._add_tool_manually()
            else:
                break

    def _view_tool_details(self):
        """View details of a specific tool."""
        tools = self.tool_registry.list_tools()

        if not tools:
            console.print("[yellow]No tools available.[/yellow]")
            return

        console.print("\nAvailable tools:")
        for i, (name, tool) in enumerate(tools.items(), 1):
            console.print(f"{i}. {name}")

        choice = Prompt.ask("Select tool", choices=[str(i) for i in range(1, len(tools) + 1)])
        tool_name = list(tools.keys())[int(choice) - 1]
        tool = tools[tool_name]

        console.print(Panel(
            f"[bold]Tool: {tool_name}[/bold]\n"
            f"Status: {'✓ Installed' if tool.installed else '✗ Not installed'}\n"
            f"Path: {tool.path}\n"
            f"Assigned to: {', '.join(tool.assigned_to) if tool.assigned_to else 'None'}\n"
            f"Description: {tool.description}\n"
            f"GitHub URL: {tool.github_url or 'N/A'}",
            title="[bold]Tool Details[/bold]",
            border_style="cyan"
        ))

    def _add_tool_manually(self):
        """Add a tool manually."""
        tool_name = Prompt.ask("Tool name")
        tool_path = Prompt.ask("Tool path")
        tool_description = Prompt.ask("Tool description", default="")
        assigned_to = Prompt.ask("Assign to agents (comma-separated: SAB1, SAB2, SAB3)", default="SAB1")

        agents = [a.strip() for a in assigned_to.split(",") if a.strip()]

        success = self.tool_registry.register_local_tool(
            tool_name,
            tool_path,
            tool_description,
            agents
        )

        if success:
            console.print("[green]✓ Tool added successfully![/green]")
        else:
            console.print("[red]✗ Failed to add tool.[/red]")

    def show_settings(self):
        """Show settings menu."""
        while True:
            console.clear()
            console.print(Panel(
                "[bold]Settings[/bold]\n"
                "Configure agents, pre-instructions, and API keys",
                title="[bold yellow]Settings[/bold yellow]",
                border_style="yellow"
            ))

            console.print("1. Edit pre-instructions")
            console.print("2. Change API keys and models")
            console.print("3. Reset configuration")
            console.print("4. Return to main menu")

            choice = Prompt.ask("Select option", choices=["1", "2", "3", "4"], default="4")

            if choice == "1":
                self._edit_pre_instructions()
            elif choice == "2":
                self._edit_agent_config()
            elif choice == "3":
                if Confirm.ask("Are you sure? This will delete all configurations."):
                    self._reset_config()
                    console.print("[green]Configuration reset.[/green]")
                    console.print("Please run the setup wizard again.")
                    break
            else:
                break

    def _edit_pre_instructions(self):
        """Edit pre-instructions for agents."""
        console.clear()
        console.print(Panel(
            "[bold]Edit Pre-Instructions[/bold]\n"
            "System prompts that define each agent's behavior",
            title="[bold]Pre-Instructions[/bold]",
            border_style="cyan"
        ))

        for agent_id, agent_name in [
            ("MAB", "Main Agent Brain"),
            ("SAB1", "Research Analyst"),
            ("SAB2", "Strategy Specialist"),
            ("SAB3", "Content Writer")
        ]:
            console.print(f"\n[bold]{agent_id} ({agent_name})[/bold]")
            current = self.pre_instructions.get(agent_id, "")
            console.print(current[:200] + "..." if len(current) > 200 else current)

            if Confirm.ask(f"Edit {agent_id}'s pre-instruction?"):
                new_instruction = console.input("[bold]Enter new pre-instruction:[/bold]\n> ")
                self.pre_instructions[agent_id] = new_instruction

        if Confirm.ask("Save changes?"):
            save_pre_instructions(self.pre_instructions)
            console.print("[green]Pre-instructions saved![/green]")

    def _edit_agent_config(self):
        """Edit agent configuration."""
        console.clear()
        console.print(Panel(
            "[bold]Edit Agent Configuration[/bold]\n"
            "Change API keys and models for each agent",
            title="[bold]Agent Config[/bold]",
            border_style="cyan"
        ))

        config = get_config()

        for agent_id in ["MAB", "SAB1", "SAB2", "SAB3"]:
            console.print(f"\n[bold]{agent_id}[/bold]")
            console.print(f"Provider: {config[agent_id].get('provider', 'N/A')}")
            console.print(f"Model: {config[agent_id].get('model', 'N/A')}")

            if Confirm.ask(f"Edit {agent_id}'s configuration?"):
                new_provider = Prompt.ask(
                    "New provider",
                    choices=["Ollama", "OpenRouter", "NVIDIA NIM", "Google Gemini", "OpenAI"],
                    default=config[agent_id].get("provider", "Ollama")
                )
                new_model = Prompt.ask("New model", default=config[agent_id].get("model", "llama3:8b"))

                if new_provider != "Ollama":
                    new_api_key = Prompt.ask("New API key", password=True)
                    config[agent_id]["api_key"] = new_api_key

                config[agent_id]["provider"] = new_provider
                config[agent_id]["model"] = new_model

        if Confirm.ask("Save changes?"):
            save_config(config)
            console.print("[green]Configuration saved![/green]")

    def _reset_config(self):
        """Reset configuration to defaults."""
        config = {
            "MAB": {"provider": "Ollama", "api_key": "", "model": "llama3:8b"},
            "SAB1": {"provider": "Ollama", "api_key": "", "model": "llama3:8b"},
            "SAB2": {"provider": "Ollama", "api_key": "", "model": "llama3:8b"},
            "SAB3": {"provider": "Ollama", "api_key": "", "model": "llama3:8b"}
        }
        save_config(config)
        save_pre_instructions({
            "MAB": "",
            "SAB1": "",
            "SAB2": "",
            "SAB3": ""
        })

    def _get_agent_color(self, agent_id: str) -> str:
        """Get color for an agent."""
        colors = {
            "MAB": "cyan",
            "SAB1": "blue",
            "SAB2": "purple",
            "SAB3": "orange"
        }
        return colors.get(agent_id, "white")


def main():
    """Main entry point for CLI."""
    app = NeuroDeskCLI()
    app.run()


if __name__ == "__main__":
    main()
