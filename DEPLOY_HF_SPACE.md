# Deploying NeuroDesk AMD as a Hugging Face Space

This guide shows how to deploy NeuroDesk AMD to Hugging Face Spaces for public access.

## Prerequisites

- Hugging Face account (free)
- Git installed
- Basic understanding of Gradio/Python

## Option 1: Quick Deploy (Auto)

### Method: Using `.spaces/` Directory

Create a simple Hugging Face Space with automatic deployment:

1. Create a new directory structure:
```
neurodesk-amd/
├── app.py                    # Main Gradio app
├── README.md                 # Space metadata
└── requirements.txt          # Dependencies
```

2. Create `app.py`:

```python
import gradio as gr
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

# Import NeuroDesk modules
from demo_app import NeuroDeskDemo

# Create and launch demo
demo = NeuroDeskDemo().create_demo()

if __name__ == "__main__":
    demo.launch()
```

3. Create `README.md`:

```markdown
---
title: NeuroDesk AMD
emoji: 🧠
colorFrom: indigo
colorTo: purple
sdk: gradio
pinned: false
license: mit
---

# NeuroDesk AMD

A multi-agent marketing operations copilot powered by AMD Developer Cloud.

## Features

- 🧠 Multi-agent AI orchestration (MAB + 3 SABs)
- ⚡ AMD MI300X GPU acceleration
- 📊 Performance dashboard
- 📈 Benchmark comparison
- 🎯 Campaign planning & execution

## Usage

1. Enter your marketing campaign goal
2. Select target platform(s)
3. Click "Run Campaign"
4. View results with business value analysis

## Architecture

```
User Goal → MAB → SAB1 → SAB2 → SAB3 → Report
           (Orchestrator) (Research) (Strategy) (Content)
```

## Powered by

- **AMD Developer Cloud** - MI300X GPUs
- **vLLM** - High-throughput inference
- **Gradio** - Web interface

---
*Built for the AMD Developer Hackathon 2024*
```

4. Create `requirements.txt`:

```
gradio>=4.0.0
numpy
```

5. Commit and push to GitHub

6. On Hugging Face, click "New Space" → "From Git" → Select your repo

---

## Option 2: Deploy from Local Demo

### Using the Demo App

The `demo_app.py` is designed for HF Spaces deployment:

```bash
# Test locally first
python demo_app.py --port 7860

# Then deploy to HF
# 1. Create space on Hugging Face
# 2. Clone with SSH: git clone git@hf.co:spaces/username/neurodesk-amd
# 3. Copy files and push
```

---

## Option 3: Minimal Gradio Space

For a lightweight deployment, use this minimal `app.py`:

```python
import gradio as gr
import asyncio
import os

# Mock data for demo purposes
MOCK_RESPONSES = {
    "SAB1": "Based on my research, AI-powered marketing tools are gaining significant traction...",
    "SAB2": "Here's a 30-day content strategy focusing on video content and email campaigns...",
    "SAB3": "Here are your marketing captions and ad copy ready for publication..."
}

def run_campaign(goal, platform):
    """Simulate campaign execution."""
    output = f"""# Marketing Campaign Report

## Goal: {goal}

## Target Platform: {platform}

## Strategy

A comprehensive campaign has been planned for your goal.

## Deliverables

### Research (SAB1)
{MOCK_RESPONSES["SAB1"]}

### Strategy (SAB2)
{MOCK_RESPONSES["SAB2"]}

### Content (SAB3)
{MOCK_RESPONSES["SAB3"]}

---

## Business Value

- Time saved: ~8 hours per campaign
- Expected ROI: 3-5x
- Quality: High (AI-generated, human-reviewed)

*Powered by NeuroDesk AMD - AMD Developer Cloud*
"""
    return output, f" Campaign completed for {platform}", "✅ No drift detected", "Campaign generated successfully"

with gr.Blocks(theme=gr.themes.Soft(), title="NeuroDesk AMD") as demo:
    gr.Markdown("# 🚀 NeuroDesk AMD\n### Multi-Agent Marketing Copilot")
    
    with gr.Row():
        with gr.Column():
            goal = gr.Textbox(label="Campaign Goal", lines=4)
            platform = gr.Dropdown(["Instagram", "LinkedIn", "Facebook", "Twitter/X", "All"], value="All", label="Platform")
            run_btn = gr.Button("🚀 Run Campaign", variant="primary")
        
        with gr.Column():
            output = gr.Markdown(label="Campaign Report")
            status = gr.Textbox(label="Status")
            drift = gr.Markdown(label="Drift Analysis")
    
    run_btn.click(run_campaign, [goal, platform], [output, status, drift])

if __name__ == "__main__":
    demo.launch()
```

---

## HF Spaces Configuration (.spaces/config.json)

```json
{
  "sdk": "gradio",
  "env": {
    "GRADIO_ANALYTICS_ENABLED": "false"
  },
  "requirements": {
    "gradio": ">=4.0.0"
  }
}
```

---

## Public-Safe Mode for HF Spaces

The demo app automatically runs in "safe mode" that:
- Uses mock/sample data for reliable demos
- Never exposes real API keys
- Runs entirely client-side where possible
- Shows AMD branding without requiring real GPU access

To enforce safe mode, set in `config/__init__.py`:
```python
"SAFE_MODE": {
    "enabled": True,
    "description": "Public-safe mode for HF Spaces (no external APIs)"
}
```

---

## Testing Your HF Space

Before publishing:
1. Test locally: `python app.py`
2. Check responsive design
3. Verify all buttons work
4. Test campaign flow end-to-end

---

## Publishing Your Space

1. Push to GitHub
2. Go to https://huggingface.co/new-space
3. Select "From Git"
4. Choose your repo
5. Click "Create Space"

---

## Custom Domain (Optional)

For custom domain on HF Spaces:
1. Upgrade to HF Pro or Team plan
2. Go to Space settings
3. Add custom domain
4. Update DNS records

---

## Resources

- [HF Spaces Docs](https://huggingface.co/docs/hub/spaces-overview)
- [Gradio Docs](https://www.gradio.app/docs)
- [HF Python SDK](https://huggingface.co/docs/huggingface_hub/)

---

*Need help? Join the NeuroDesk Discord or open an issue on GitHub.*
