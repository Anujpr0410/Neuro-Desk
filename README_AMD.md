# NeuroDesk AMD — Multi-Agent Marketing Copilot

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![AMD Developer Cloud](https://img.shields.io/badge/AMD-Developer%20Cloud-ED1C24.svg)](https://developer.amd.com/)
[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-Deploy-blue.svg)](https://huggingface.co/)

A hierarchical multi-agent AI system for digital marketing automation, powered by AMD Developer Cloud and MI300X GPUs.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip package manager

### Installation
```bash
cd neurodesk-amd
pip install -r requirements.txt
```

### First-Time Setup
```bash
python setup.py --mode web
# Or for CLI: python setup.py --mode cli
```

### Running NeuroDesk AMD
```bash
# Start the web server (default)
python main.py --mode web

# Or run in CLI mode
python main.py --mode cli
```

---

## 🎯 Product Positioning

**NeuroDesk AMD** is a multi-agent marketing operations copilot optimized for:

- **AMD Developer Cloud** - Deployed on AMD MI300X GPUs
- **vLLM/SGLang** - OpenAI-compatible inference endpoints
- **Open-source models** - Qwen2.5, Llama 3.1, Mistral
- **ROCm stack** - Native AMD GPU acceleration

---

## 🏗️ Architecture

```
User Goal → MAB (Orchestrator) → SAB1 (Research) → SAB2 (Strategy) → SAB3 (Content) → Report
```

| Agent | Role | Description |
|-------|------|-------------|
| **MAB** | Orchestrator | Manages campaign, plans tasks, coordinates agents |
| **SAB1** | Research Analyst | Market research, competitor analysis, audience insights |
| **SAB2** | Strategy Specialist | 30-day content strategy, platform formats |
| **SAB3** | Content Writer | Social media captions, ad copy, email newsletters |

---

## ⚡ AMD Developer Cloud Integration

### Powered By
- **AMD MI300X GPUs** - High-performance AI inference
- **vLLM** - High-throughput LLM serving with OpenAI-compatible API
- **ROCm** - AMD GPU compute stack

### Supported Endpoints
```json
{
  "provider": "AMD Cloud (vLLM)",
  "base_url": "http://<amd-server-ip>:8000/v1",
  "model": "Qwen/Qwen2.5-7B-Instruct"
}
```

---

## 🔧 Configuration

### API Configuration
Edit `config/config.json`:
```json
{
  "MAB": {
    "provider": "AMD Cloud (vLLM)",
    "api_key": "",
    "model": "Qwen/Qwen2.5-7B-Instruct"
  },
  "SAB1": { ... },
  "SAB2": { ... },
  "SAB3": { ... }
}
```

### Demo Mode Toggle
```json
{
  "DEMO_MODE": {
    "enabled": true,
    "description": "Uses mock sample data for reliable demos"
  }
}
```

---

## 📊 Performance Dashboard

The app includes a dedicated Performance tab showing:
- Active provider for each agent
- Request latency per agent
- Tokens generated and tokens/sec
- Benchmark history with AMD vs non-AMD comparison
- AMD Cloud metrics highlighting

---

## 📁 Project Structure

```
neurodesk-amd/
├── core/                 # Agent logic and tools
│   ├── llm_client.py     # Unified LLM client (AMD Cloud, Ollama, OpenAI, etc.)
│   ├── mab.py            # Main Agent Brain
│   ├── sab1.py           # Sub Agent 1 (Research)
│   ├── sab2.py           # Sub Agent 2 (Strategy)
│   ├── sab3.py           # Sub Agent 3 (Content)
│   ├── task_manager.py   # Task planning
│   ├── tool_registry.py  # Tool management
│   ├── performance_logger.py  # AMD performance metrics
│   └── benchmark_runner.py    # Provider comparison benchmarks
├── config/               # Configuration files
├── frontend/             # Web UI (FastAPI + vanilla JS)
├── api/                  # FastAPI server + WebSocket
├── tools/                # Agent tools
│   ├── serper_search.py
│   └── website_scraper.py
├── memory/               # SQLite memory storage
├── data/                 # Benchmark and metrics storage
├── main.py               # Entry point
├── setup.py              # Setup wizard
├── requirements.txt      # Production dependencies
├── requirements_demo.txt # Hugging Face Space dependencies
├── demo_app.py           # Gradio demo for HF Spaces
└── README.md
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [HACKATHON_SUBMISSION.md](./HACKATHON_SUBMISSION.md) | AMD Developer Hackathon submission details |
| [BENCHMARKS.md](./BENCHMARKS.md) | Performance benchmarks and provider comparison |
| [DEPLOY_AMD_CLOUD.md](./DEPLOY_AMD_CLOUD.md) | Deploying on AMD Developer Cloud |
| [DEPLOY_HF_SPACE.md](./DEPLOY_HF_SPACE.md) | Deploying as Hugging Face Space |
| [DEMO_SCRIPT.md](./DEMO_SCRIPT.md) | 3-minute demo flow for judges |

---

## 🚀 AMD Deployment

### Getting Started on AMD Developer Cloud
1. Sign up at [AMD Developer Cloud](https://developer.amd.com/)
2. Create a VM with AMD MI300X
3. Install vLLM or SGLang:
   ```bash
   pip install vllm
   python -m vllm.entrypoints.openai.api_server \
       --model Qwen/Qwen2.5-7B-Instruct \
       --host 0.0.0.0 \
       --port 8000
   ```
4. Configure NeuroDesk to use the endpoint
5. Start NeuroDesk: `python main.py --mode web`

See [DEPLOY_AMD_CLOUD.md](./DEPLOY_AMD_CLOUD.md) for detailed instructions.

---

## 🤖 Hugging Face Space

Deploy as a public Hugging Face Space:

```bash
# Using Gradio demo
python demo_app.py --port 7860
```

See [DEPLOY_HF_SPACE.md](./DEPLOY_HF_SPACE.md) for deployment instructions.

---

## 🎯 Originality Features

### Strategy vs Copy Drift Checker
Detects when SAB3 content drifts away from SAB2 strategy. Shows consistency scores in final reports.

### AMD Performance Dashboard
Real-time metrics showing AMD GPU-accelerated inference vs other providers.

---

## 📱 Usage

### Campaign Mode
1. Enter your marketing goal
2. Select target platform(s)
3. Click "Run Full Campaign"
4. Watch agents work via activity stream
5. Review final campaign report with business value analysis

### Direct Agent Chat
Each agent has its own chat tab for specific queries.

---

## 🧪 Benchmarking

Run provider comparisons:
```python
from core.benchmark_runner import BenchmarkRunner

runner = BenchmarkRunner()
results = await runner.benchmark_all(config)
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with:
- FastAPI for web framework
- AMD MI300X GPUs for LLM inference
- vLLM for high-throughput serving
- Open-source model community

---

## 📣 Build in Public

This project is built for the AMD Developer Hackathon 2024.

- GitHub: [neurodesk-amd](https://github.com/neurodesk-amd)
- Hugging Face: [NeuroDesk AMD](https://huggingface.co/neurodesk-amd)
- Twitter: [@NeuroDeskAI](https://twitter.com/NeuroDeskAI)

---

*AMD, the AMD Arrow logo, Radeon, Radeon RX, Vega, AMD Instinct, MI300, and combinations thereof are trademarks of Advanced Micro Devices, Inc.*
