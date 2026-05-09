"""
NeuroDesk AMD - Hugging Face Space Compatible Demo App

This is a lightweight Gradio-based demo suitable for deployment on Hugging Face Spaces.
It provides a simplified interface to the core NeuroDesk multi-agent system.
"""

import gradio as gr
import asyncio
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.mab import MAB
from core.performance_logger import PerformanceLogger
from core.benchmark_runner import BenchmarkRunner
from config import get_config, save_config


class NeuroDeskDemo:
    """Gradio-based demo for NeuroDesk AMD."""

    def __init__(self):
        self.mab = None
        self.performance_logger = PerformanceLogger()
        self.config = get_config()

    def initialize(self):
        """Initialize the MAB agent."""
        if self.mab is None:
            self.mab = MAB(config=self.config)

    def run_campaign(self, user_goal: str, platform: str = "All") -> tuple:
        """Run a marketing campaign."""
        self.initialize()

        # Update config based on user input
        self.config["DEMO_MODE"]["enabled"] = True  # Always use demo mode for simplicity

        # Run campaign
        result = asyncio.run(self.mab.run(user_goal, None))

        if result.get("success"):
            final_output = result.get("final_output", "Campaign complete")

            # Extract strategy vs copy drift info if available
            drift_info = ""
            if "drift_analysis" in result:
                drift = result["drift_analysis"]
                if drift.get("drift_detected"):
                    drift_info = f"⚠️ **Drift Detected**: {drift.get('consistency_score', 0)}% consistency"
                else:
                    drift_info = f"✅ **No Drift**: {drift.get('consistency_score', 0)}% consistency"

            # Extract business value section
            business_value = ""
            if "Business Value" in final_output:
                parts = final_output.split("---")
                for part in parts:
                    if "Business Value" in part:
                        business_value = part
                        break

            return (
                final_output,
                f"🎯 Campaign Goal: {user_goal}\nPlatform: {platform}\nStatus: Completed",
                drift_info,
                business_value
            )
        else:
            error_msg = result.get("error", "Unknown error")
            return (
                f"❌ Campaign failed: {error_msg}",
                f"Error: {error_msg}",
                "",
                ""
            )

    def update_config(self, provider: str, model: str, api_key: str, base_url: str = "") -> str:
        """Update agent configuration."""
        try:
            # Save to default config
            self.config["MAB"]["provider"] = provider
            self.config["MAB"]["model"] = model
            self.config["MAB"]["api_key"] = api_key
            if base_url:
                self.config["MAB"]["base_url"] = base_url

            save_config(self.config)
            self.mab = None  # Reset MAB to reload with new config
            return "✅ Configuration saved! Agent will use new settings on next run."
        except Exception as e:
            return f"❌ Error saving configuration: {str(e)}"

    def get_available_models(self, provider: str) -> str:
        """Get available models for a provider."""
        return f"Models for {provider}: Loading..."

    def create_demo(self):
        """Create Gradio demo interface."""
        with gr.Blocks(theme=gr.themes.Soft(), title="NeuroDesk AMD") as demo:
            gr.Markdown(
                """
                # 🚀 NeuroDesk AMD
                ### Multi-Agent Marketing Copilot Powered by AMD Developer Cloud
                ---
                **A hierarchical AI agent system for marketing campaigns, optimized for AMD MI300X GPUs.**
                """
            )

            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown(
                        """
                        ## ⚡ AMD Powered
                        - **vLLM on AMD MI300X** for high-throughput inference
                        - **Open-source models**: Qwen2.5, Llama 3.1, Mistral
                        - **ROCm-ready** deployment
                        """
                    )

                    gr.Markdown(
                        """
                        ## 🔧 Configuration
                        """
                    )

                    provider_input = gr.Dropdown(
                        choices=[
                            "AMD Cloud (vLLM)",
                            "Ollama",
                            "OpenRouter",
                            "NVIDIA NIM",
                            "Google Gemini",
                            "OpenAI"
                        ],
                        value="AMD Cloud (vLLM)",
                        label="Provider"
                    )

                    model_input = gr.Textbox(
                        value="Qwen/Qwen2.5-7B-Instruct",
                        label="Model Name"
                    )

                    api_key_input = gr.Textbox(
                        label="API Key (optional for AMD Cloud)",
                        type="password",
                        placeholder="sk-..."
                    )

                    base_url_input = gr.Textbox(
                        value="http://localhost:8000/v1",
                        label="Endpoint URL"
                    )

                    config_btn = gr.Button("Save Configuration")

                with gr.Column(scale=2):
                    gr.Markdown(
                        """
                        ## 📊 Campaign
                        """
                    )

                    platform_selector = gr.Dropdown(
                        choices=["Instagram", "LinkedIn", "Facebook", "Twitter/X", "All"],
                        value="All",
                        label="Target Platform"
                    )

                    goal_input = gr.Textbox(
                        lines=4,
                        placeholder="Enter your marketing campaign goal here...",
                        label="Campaign Goal"
                    )

                    run_btn = gr.Button("🚀 Run Campaign", variant="primary")

                    output_md = gr.Markdown(label="Campaign Output")
                    status_output = gr.Textbox(label="Status")
                    drift_output = gr.Markdown(label="Strategy vs Copy Drift Analysis")
                    business_value_output = gr.Textbox(label="Business Value Analysis")

            # Event handlers
            config_btn.click(
                self.update_config,
                inputs=[provider_input, model_input, api_key_input, base_url_input],
                outputs=[gr.Textbox()]
            )

            run_btn.click(
                self.run_campaign,
                inputs=[goal_input, platform_selector],
                outputs=[output_md, status_output, drift_output, business_value_output]
            )

            gr.Markdown(
                """
                ---
                ### How it works:
                1. **MAB** (Main Agent Brain) plans your campaign
                2. **SAB1** (Research) gathers market insights
                3. **SAB2** (Strategy) builds a 30-day plan
                4. **SAB3** (Content) creates ready-to-publish copy
                5. **AMD GPUs** power the LLM inference

                ---
                *NeuroDesk AMD - Powered by AMD Developer Cloud*
                """
            )

        return demo


def launch_demo(port: int = 7860, share: bool = True):
    """Launch the Gradio demo."""
    demo = NeuroDeskDemo().create_demo()
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=share
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="NeuroDesk AMD Demo")
    parser.add_argument("--port", type=int, default=7860, help="Port to run the demo on")
    parser.add_argument("--no-share", action="store_true", help="Don't create public share link")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  NeuroDesk AMD - Hugging Face Space Demo")
    print("=" * 60)
    print("\nThis demo runs NeuroDesk's multi-agent marketing system")
    print("using AMD MI300X-powered inference via vLLM.")
    print("\nOpen-source models supported:")
    print("  - Qwen2.5 Instruct")
    print("  - Llama 3.1 Instruct")
    print("  - Mistral Instruct")
    print("  - DeepSeek Instruct")
    print("\n" + "=" * 60 + "\n")

    launch_demo(
        port=args.port,
        share=not args.no_share
    )
