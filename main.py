#!/usr/bin/env python3
"""
NeuroDesk Main Application
Entry point for the AI Multi-Agent System.
Supports both web and CLI modes.
"""

import sys
import argparse
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))


def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        "fastapi",
        "uvicorn",
        "rich",
        "chromadb",
        "openai",
        "google.generativeai",
        "bs4"
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing.append(package)

    if missing:
        print("⚠️  Missing required dependencies:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\nRun: pip install -r requirements.txt")
        sys.exit(1)


def check_config():
    """Check if config exists, run setup if not."""
    config_path = Path("config/config.json")

    if not config_path.exists():
        print("\n⚠️  Configuration not found!")
        print("\nNeuroDesk uses a hierarchical multi-agent system where:")
        print("  MAB = Main Agent Brain (Orchestrator)")
        print("  SAB1 = Sub Agent 1 (Research Analyst)")
        print("  SAB2 = Sub Agent 2 (Strategy Specialist)")
        print("  SAB3 = Sub Agent 3 (Content Writer)")
        print("\nEach agent can use a different LLM provider.")
        print("\nPlease configure your agents first.\n")
        return False

    return True


def run_web_server(port: int = 8000):
    """Start the FastAPI web server."""
    import uvicorn

    print(f"\n{'=' * 60}")
    print("  NeuroDesk - Starting Web Server")
    print("=" * 60)
    print(f"\nOpen your browser and go to: http://localhost:{port}")
    print("Press Ctrl+C to stop the server.\n")

    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )


def run_cli():
    """Start the CLI application."""
    from cli.cli_app import main as cli_main

    print("\n" + "=" * 60)
    print("  NeuroDesk - CLI Mode")
    print("=" * 60)

    cli_main()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="NeuroDesk AI Multi-Agent System")
    parser.add_argument("--mode", choices=["web", "cli"], default="web",
                        help="Mode to run NeuroDesk in (default: web)")
    parser.add_argument("--port", type=int, default=8000,
                        help="Port for web mode (default: 8000)")
    parser.add_argument("--setup", action="store_true",
                        help="Run setup wizard before starting")

    args = parser.parse_args()

    # Check dependencies
    check_dependencies()

    # Check/run setup if needed
    if args.setup or not check_config():
        import subprocess
        result = subprocess.run([sys.executable, "setup.py", "--mode", "cli"])
        if result.returncode != 0:
            sys.exit(1)

    # Check config again after setup
    if not check_config():
        print("Configuration still not found. Exiting.")
        sys.exit(1)

    # Run the selected mode
    if args.mode == "web":
        run_web_server(args.port)
    else:
        run_cli()


if __name__ == "__main__":
    main()
