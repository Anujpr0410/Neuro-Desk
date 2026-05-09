# Quick Start Guide - NeuroDesk AMD

## TL;DR

```bash
# Install
pip install -r requirements.txt

# Run
python main.py --mode web
```

Open `http://localhost:8000` to see NeuroDesk AMD.

---

## What's New in This Hackathon Version

| Feature | Description |
|---------|-------------|
| **AMD Cloud (vLLM)** | First-class support for AMD Developer Cloud |
| **Performance Dashboard** | Real-time metrics showing AMD acceleration |
| **Demo Mode** | Mock data for reliable demos |
| **Strategy Drift Checker** | Original feature detecting content drift |
| **Business Value Layer** | ROI analysis in final reports |
| **Hugging Face Ready** | Lightweight Gradio demo for public deployment |

---

## Quick Verification Checklist

After running, verify:

1. **AMD Provider Visible**
   - Settings tab → Provider dropdown shows "AMD Cloud (vLLM)"
   - "🚀 Powered by AMD MI300X" badge appears

2. **Performance Tab**
   - Navigate to "Performance" tab
   - KPI cards show metrics
   - Benchmark table displays results

3. **Campaign Run**
   - Enter goal in MAB
   - Click "Run Full Campaign"
   - Activity stream shows MAB → SAB1 → SAB2 → SAB3 workflow

4. **AMD Info**
   - "AMD Info" tab shows architecture details
   - Shows AMD Developer Cloud branding

---

## Demo Mode vs Live Mode

### Demo Mode (Default)
- Uses mock/sample data
- No external API keys needed
- Perfect for quick demos
- Configurable in `config/config.json`

```json
{
  "DEMO_MODE": {
    "enabled": true
  }
}
```

### Live Tool Mode
- Uses real tools (Serper search, website scraper)
- Requires API keys
- Produces grounded results
- Set `enabled: false` in config

---

## File Tree (Updated)

```
neurodesk-amd/
├── core/
│   ├── llm_client.py      # AMD Cloud (vLLM) + providers
│   ├── mab.py             # Main Agent Brain (orchestrator)
│   ├── sab1.py            # Research Analyst
│   ├── sab2.py            # Strategy Specialist
│   ├── sab3.py            # Content Writer (with Drift Checker)
│   ├── task_manager.py    # Task planning
│   ├── tool_registry.py   # Tool management (execute_tool added)
│   ├── performance_logger.py    # NEW: AMD performance metrics
│   └── benchmark_runner.py    # NEW: Provider comparison
├── config/
│   ├── config.json        # Agent config (AMD default)
│   ├── pre_instructions.json
│   └── __init__.py
├── api/
│   └── server.py          # FastAPI server (benchmark endpoints added)
├── frontend/
│   ├── index.html         # UI with AMD Info & Performance tabs
│   ├── app.js             # Client logic (new functions added)
│   └── style.css
├── tools/
│   ├── serper_search.py
│   ├── website_scraper.py
│   └── registry.json
├── memory/
│   ├── db.py
│   └── __init__.py
├── data/                  # NEW: Benchmark & metrics storage
├── main.py                # Entry point (AMD branding)
├── setup.py
├── requirements.txt       # Added vllm dependency
├── requirements_demo.txt  # NEW: Gradio dependencies
├── demo_app.py            # NEW: Gradio demo for HF Spaces
├── README_AMD.md          # NEW: AMD-focused README
├── HACKATHON_SUBMISSION.md  # NEW: Hackathon submission
├── BENCHMARKS.md          # NEW: Performance results
├── DEPLOY_AMD_CLOUD.md    # NEW: AMD deployment guide
├── DEPLOY_HF_SPACE.md     # NEW: Hugging Face guide
├── DEMO_SCRIPT.md         # NEW: 3-minute demo
└── QUICKSTART.md          # This file
```

---

## Key Changes Summary

### Backend Changes
- `llm_client.py`: Added `AMD Cloud (vLLM)` provider support
- `config/__init__.py`: AMD Cloud as default, Demo Mode config
- `mab.py`: Added demo mode, _execute_sab_task, _add_business_value
- `sab3.py`: Added _check_strategy_drift method
- `tool_registry.py`: Added execute_tool method
- `api/server.py`: Added /tools/execute, /benchmark/* endpoints
- `performance_logger.py`: NEW - Performance metrics tracking
- `benchmark_runner.py`: NEW - Provider comparison benchmarks

### Frontend Changes
- `index.html`: Added Performance & AMD Info tabs
- `app.js`: Added switchTab handlers, loadPerformanceData, loadAMDInfo

### Configuration Changes
- Default provider: AMD Cloud (vLLM)
- Default model: Qwen/Qwen2.5-7B-Instruct
- Demo Mode: enabled by default

---

## Next Steps

1. Run `python main.py --mode web`
2. Open http://localhost:8000
3. Navigate to Settings → Verify AMD Cloud configuration
4. Try running a campaign
5. Check Performance tab for metrics
6. Visit AMD Info tab for architecture overview

---

## AMD Deployment (Optional)

To use actual AMD MI300X GPUs:
1. Sign up at [AMD Developer Cloud](https://developer.amd.com/)
2. Launch MI300X instance
3. Install vLLM and serve a model
4. Configure endpoint in Settings

See `DEPLOY_AMD_CLOUD.md` for detailed instructions.

---

*This is NeuroDesk AMD - a hackathon-optimized multi-agent system powered by AMD Developer Cloud.*
