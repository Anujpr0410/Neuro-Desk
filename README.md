# NeuroDesk AMD - AI Multi-Agent System (Hackathon Edition)

[![AMD Developer Cloud](https://img.shields.io/badge/AMD-Developer%20Cloud-ED1C24.svg)](https://developer.amd.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A hierarchical AI agent orchestration platform for digital marketing automation, **powered by AMD Developer Cloud and MI300X GPUs**.

![NeuroDesk](https://img.shields.io/badge/version-2.0.0-amd-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)

---

## Overview

NeuroDesk features **One Main Agent Brain (MAB)** that manages **Three Sub Agent Brains (SAB1, SAB2, SAB3)**:

| Agent | Role | Description |
|-------|------|-------------|
| **MAB** | Orchestrator | Manages the entire campaign, plans tasks, coordinates agents |
| **SAB1** | Research Analyst | Market research, competitor analysis, audience insights |
| **SAB2** | Strategy Specialist | 30-day content strategy, platform-specific formats |
| **SAB3** | Content Writer | Social media captions, ad copy, email newsletters |

**Flow:** User Goal → MAB Plans → SAB1 Research → SAB2 Strategy → SAB3 Content → Final Report

---

## 🚀 Hackathon Features

| Feature | Description |
|---------|-------------|
| **AMD Cloud (vLLM)** | First-class support for AMD MI300X GPUs |
| **Performance Dashboard** | Real-time metrics showing AMD acceleration |
| **Demo Mode** | Mock data for reliable demos |
| **Strategy Drift Checker** | Original feature detecting content drift |
| **Business Value Layer** | ROI analysis in final reports |
| **Hugging Face Ready** | Lightweight Gradio demo for public deployment |

**This is the AMD Developer Hackathon 2024 optimized version.**

---

## Features

- **Multi-Agent Architecture**: Hierarchical task delegation with specialized agents
- **Multi-Provider Support**: AMD Cloud (vLLM), Ollama, OpenRouter, NVIDIA NIM, Google Gemini, OpenAI
- **Real-Time Streaming**: WebSocket-based activity feed with progress indicators

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [README_AMD.md](./README_AMD.md) | Full AMD Developer Cloud documentation |
| [HACKATHON_SUBMISSION.md](./HACKATHON_SUBMISSION.md) | Hackathon submission details |
| [BENCHMARKS.md](./BENCHMARKS.md) | Performance benchmark results |
| [DEPLOY_AMD_CLOUD.md](./DEPLOY_AMD_CLOUD.md) | Deploy on AMD Developer Cloud |
| [DEPLOY_HF_SPACE.md](./DEPLOY_HF_SPACE.md) | Deploy as Hugging Face Space |
| [DEMO_SCRIPT.md](./DEMO_SCRIPT.md) | 3-minute demo for judges |
| [QUICKSTART.md](./QUICKSTART.md) | Quick start guide |
| [PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md) | Complete project summary |

---

## 🎯 Quick Start

```bash
pip install -r requirements.txt
python main.py --mode web
```

For full documentation, see [README_AMD.md](./README_AMD.md).
- **Tool Registry**: Automatic tool discovery and installation from GitHub
- **ChromaDB Memory**: Persistent vector memory for each agent
- **Web UI**: Modern dark/light themed interface inspired by Linear/Vercel
- **CLI Mode**: Rich terminal interface with live progress indicators
- **Platform Support**: Instagram, LinkedIn, Facebook, Twitter/X, All Platforms

---

## Quick Start

### Prerequisites

- Python 3.11+
- pip package manager

### Installation

```bash
# Clone or navigate to the project directory
cd neurodesk

# Install dependencies
pip install -r requirements.txt
```

### First-Time Setup

Run the setup wizard to configure your API keys and models:

```bash
# Web setup (recommended for first-time users)
python setup.py --mode web

# Or CLI setup
python setup.py --mode cli
```

The wizard will ask you to configure each agent with:
- Provider choice (Ollama, OpenRouter, NVIDIA NIM, Google Gemini, or OpenAI)
- API key (or "local" for Ollama)
- Model name

### Running NeuroDesk

```bash
# Start the web server (default)
python main.py --mode web

# Run in CLI mode
python main.py --mode cli
```

Open your browser to `http://localhost:8000/app` to use the web interface.

---

## Configuration

### API Configuration

Edit `config/config.json` to modify agent settings:

```json
{
  "MAB": {
    "provider": "OpenAI",
    "api_key": "sk-...",
    "model": "gpt-4o"
  },
  "SAB1": { ... },
  "SAB2": { ... },
  "SAB3": { ... }
}
```

### Pre-Instructions (System Prompts)

Edit `config/pre_instructions.json` to customize agent behavior:

```json
{
  "MAB": "You are NeuroDesk's Main Agent Brain...",
  "SAB1": "You are SAB1 — the Market Research Analyst...",
  "SAB2": "You are SAB2 — the Marketing Strategy Specialist...",
  "SAB3": "You are SAB3 — the Senior Copywriter..."
}
```

---

## Usage Guide

### Campaign Mode (MAB)

1. Enter your marketing goal in the main chat
2. Select your target platform(s)
3. Click "Run Full Campaign"
4. Watch agents work in real-time via the activity stream
5. Review the final campaign report

### Direct Agent Chat

Each agent has its own dedicated chat tab:

- **SAB1**: Ask for research, competitor analysis, market trends
- **SAB2**: Request strategy adjustments, content calendar changes
- **SAB3**: Generate new copy, request tone changes, get variations

### Tool Registry

Tools are automatically discovered and installed when needed:

- `serper_search`: Web search via SerperDev API
- `website_scraper`: Scrape competitor websites

View and manage tools in the Settings tab.

---

## Project Structure

```
neurodesk/
├── api/                 # FastAPI server + WebSocket
│   └── server.py
├── cli/                 # Rich-based CLI application
│   └── cli_app.py
├── config/              # Configuration files
│   ├── config.json
│   ├── pre_instructions.json
│   └── __init__.py
├── core/                # Agent logic and tools
│   ├── llm_client.py    # Unified LLM client
│   ├── mab.py           # Main Agent Brain
│   ├── sab1.py          # Sub Agent 1 (Research)
│   ├── sab2.py          # Sub Agent 2 (Strategy)
│   ├── sab3.py          # Sub Agent 3 (Content)
│   ├── memory_manager.py # ChromaDB wrapper
│   ├── task_manager.py  # Task planning
│   └── tool_registry.py # Tool management
├── frontend/            # Web UI
│   ├── index.html
│   ├── style.css
│   └── app.js
├── tools/               # Agent tools
│   ├── serper_search.py
│   ├── website_scraper.py
│   └── registry.json
├── memory/              # ChromaDB data (auto-created)
├── main.py              # Entry point
├── setup.py             # Setup wizard
└── requirements.txt
```

---

## API Provider Configuration

### Provider Options (Priority Order)

#### Free / Local (Priority 1)
| Provider | API Key Required | Description |
|----------|------------------|-------------|
| **Ollama** | No | Local LLM - run models on your machine |
| **OpenRouter** | Yes | Free models available, API key required |
| **NVIDIA NIM** | Yes | Free credits available |

#### Paid (Priority 2)
| Provider | API Key Required | Description |
|----------|------------------|-------------|
| **Google Gemini** | Yes | Google's AI models |
| **OpenAI** | Yes | GPT-4, GPT-3.5, etc. |

### Recommended Models

| Provider | Suggested Model |
|----------|-----------------|
| Ollama | llama3:8b, llama3:70b |
| OpenRouter | meta-llama/llama-3-8b-instruct:free |
| NVIDIA NIM | meta/llama3-8b-instruct |
| Google Gemini | gemini-1.5-flash |
| OpenAI | gpt-4o-mini, gpt-4o |

---

## Development

### Running in Development Mode

```bash
# Enable hot reload for development
python -m uvicorn api.server:app --reload --port 8000
```

### Adding New Tools

1. Create a new tool file in `tools/`
2. Implement the `tool_name()` function
3. Update `tools/registry.json` with the new tool

Example tool structure:

```python
# tools/my_new_tool.py
def my_new_tool(query: str) -> str:
    # Tool implementation
    return "result"
```

### Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## License

MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

Built with:
- FastAPI for the web framework
- Rich for CLI interface
- ChromaDB for memory management
- OpenAI, Google, and OSS communities

---

## Troubleshooting

### Common Issues

**"API key not provided"**
- Run `python setup.py` to configure API keys
- Check `config/config.json` is valid JSON

**"Model not found"**
- Verify the model name is correct for your provider
- For Ollama, pull the model first: `ollama pull llama3:8b`

**"Connection refused"**
- Ensure your provider's API is accessible
- Check firewall settings
- Verify API key is valid

---

## Support

- Report bugs via GitHub Issues
- Feature requests welcome
- Documentation improvements encouraged

---

*Built for efficient, scalable digital marketing automation with AI.*
