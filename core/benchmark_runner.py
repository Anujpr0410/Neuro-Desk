"""
Benchmark Runner for NeuroDesk AMD AI Multi-Agent System.
Compares performance across different LLM providers.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import json

from core.llm_client import LLMClient, PROVIDER_MODELS
from core.performance_logger import PerformanceLogger


@dataclass
class BenchmarkScenario:
    """A benchmark scenario with prompt and expected output."""
    name: str
    prompt: str
    expected_output_length: int
    complexity: str  # "short", "medium", "long"


class BenchmarkRunner:
    """Runs benchmarks comparing different LLM providers."""

    SCENARIOS = [
        BenchmarkScenario(
            name="short_planning",
            prompt="Create a 30-day marketing calendar for a small business. List content pillars and posting schedule.",
            expected_output_length=50,
            complexity="short"
        ),
        BenchmarkScenario(
            name="medium_research",
            prompt="Analyze the current trends in digital marketing for small businesses in 2024. Provide 5 key insights with supporting data points.",
            expected_output_length=150,
            complexity="medium"
        ),
        BenchmarkScenario(
            name="long_content",
            prompt="Write a comprehensive blog post about 'The Future of AI in Digital Marketing'. Include introduction, 3 main sections, and conclusion. Target 600 words.",
            expected_output_length=400,
            complexity="long"
        )
    ]

    def __init__(self, performance_logger: PerformanceLogger = None):
        self.performance_logger = performance_logger or PerformanceLogger()
        self.results_file = Path("data/benchmark_results.json")
        self.results_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_results()

    def _load_results(self):
        """Load previous benchmark results."""
        if self.results_file.exists():
            try:
                with open(self.results_file, 'r') as f:
                    self._results = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._results = []
        else:
            self._results = []

    def _save_results(self):
        """Save benchmark results."""
        with open(self.results_file, 'w') as f:
            json.dump(self._results, f, indent=2)

    def get_providers_to_benchmark(self) -> List[str]:
        """Get list of providers to benchmark (AMD first, then others)."""
        return [
            "AMD Cloud (vLLM)",
            "Ollama",
            "OpenRouter",
            "NVIDIA NIM",
            "Google Gemini",
            "OpenAI"
        ]

    async def benchmark_provider(
        self,
        provider: str,
        model: str,
        api_key: str = "",
        base_url: str = "",
        scenarios: List[BenchmarkScenario] = None
    ) -> Dict[str, Any]:
        """Run benchmark for a single provider/model combination."""
        if scenarios is None:
            scenarios = self.SCENARIOS

        results = {
            "provider": provider,
            "model": model,
            "timestamp": datetime.now().isoformat(),
            "scenarios": {}
        }

        for scenario in scenarios:
            # Initialize LLM client
            llm_config = {"base_url": base_url} if base_url else {}
            llm_client = LLMClient(
                provider=provider,
                api_key=api_key,
                model=model,
                config=llm_config
            )

            # Run benchmark
            scenario_result = await self._run_scenario(llm_client, scenario)
            results["scenarios"][scenario.name] = scenario_result

        # Save results
        self._results.append(results)
        self._save_results()

        return results

    async def _run_scenario(
        self,
        llm_client: LLMClient,
        scenario: BenchmarkScenario
    ) -> Dict[str, Any]:
        """Run a single benchmark scenario."""
        start_time = time.time()

        try:
            # Call LLM
            response = await llm_client.chat(
                messages=[{"role": "user", "content": scenario.prompt}],
                stream=False,
                temperature=0.7,
                max_tokens=2000
            )

            elapsed = (time.time() - start_time) * 1000
            output_text = response.text if hasattr(response, 'text') else str(response)

            return {
                "scenario": scenario.name,
                "prompt_length": len(scenario.prompt),
                "output_length": len(output_text),
                "elapsed_ms": round(elapsed, 2),
                "first_token_latency_ms": round(elapsed, 2),  # Simplified for now
                "tokens_per_second": round(len(output_text.split()) * 3 / (elapsed / 1000), 2),
                "success": True,
                "output_preview": output_text[:200]
            }

        except Exception as e:
            return {
                "scenario": scenario.name,
                "success": False,
                "error": str(e),
                "elapsed_ms": round((time.time() - start_time) * 1000, 2)
            }

    async def benchmark_all(
        self,
        config: Dict[str, Any],
        scenarios: List[BenchmarkScenario] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Run benchmarks for all providers in config."""
        if scenarios is None:
            scenarios = self.SCENARIOS

        all_results = {}

        for agent_key in ["MAB", "SAB1", "SAB2", "SAB3"]:
            agent_config = config.get(agent_key, {})
            provider = agent_config.get("provider", "Ollama")

            if provider not in all_results:
                api_key = agent_config.get("api_key", "")
                base_url = agent_config.get("base_url", "")

                # Get suggested model if available
                suggested_model = agent_config.get("model")
                if not suggested_model and provider in PROVIDER_MODELS:
                    suggested_model = PROVIDER_MODELS[provider]["suggested_models"][0]

                results = await self.benchmark_provider(
                    provider=provider,
                    model=suggested_model,
                    api_key=api_key,
                    base_url=base_url,
                    scenarios=scenarios
                )
                all_results[provider] = results

        return all_results

    def get_comparison(self) -> List[Dict[str, Any]]:
        """Get comparison across all benchmarked providers."""
        comparisons = []

        for result in self._results:
            provider = result["provider"]
            model = result["model"]

            for scenario_name, scenario_result in result.get("scenarios", {}).items():
                if scenario_result.get("success"):
                    comparisons.append({
                        "provider": provider,
                        "model": model,
                        "scenario": scenario_name,
                        "elapsed_ms": scenario_result["elapsed_ms"],
                        "tokens_per_second": scenario_result["tokens_per_second"],
                        "output_length": scenario_result["output_length"],
                        "first_token_ms": scenario_result.get("first_token_latency_ms", 0),
                        "is_amd": "AMD" in provider.upper()
                    })

        # Sort by provider and scenario
        comparisons.sort(key=lambda x: (x["provider"], x["scenario"]))
        return comparisons

    def export_summary(self, output_file: str = "BENCHMARKS.md") -> str:
        """Export benchmark summary to markdown."""
        comparisons = self.get_comparison()

        if not comparisons:
            return "# Benchmark Results\n\nNo benchmark data available yet."

        lines = [
            "# NeuroDesk AMD Benchmark Results",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Overview",
            "",
            f"Total benchmarks run: {len(comparisons)}",
            f"Unique providers: {len(set(c['provider'] for c in comparisons))}",
            ""
        ]

        # Performance comparison
        lines.extend([
            "## Performance Comparison",
            "",
            "### Scenario: Short Campaign Planning",
            "",
            "| Provider | Model | Latency (ms) | Tokens/sec |",
            "|----------|-------|--------------|------------|"
        ])

        short_results = [c for c in comparisons if c["scenario"] == "short_planning"]
        for r in sorted(short_results, key=lambda x: x["elapsed_ms"]):
            is_amd = "🚀" if r["is_amd"] else ""
            lines.append(
                f"| {r['provider']} | {r['model']} | {r['elapsed_ms']:.0f} {is_amd} | {r['tokens_per_second']:.1f} |"
            )

        lines.extend([
            "",
            "### Scenario: Medium Research Analysis",
            "",
            "| Provider | Model | Latency (ms) | Tokens/sec |",
            "|----------|-------|--------------|------------|"
        ])

        medium_results = [c for c in comparisons if c["scenario"] == "medium_research"]
        for r in sorted(medium_results, key=lambda x: x["elapsed_ms"]):
            is_amd = "🚀" if r["is_amd"] else ""
            lines.append(
                f"| {r['provider']} | {r['model']} | {r['elapsed_ms']:.0f} {is_amd} | {r['tokens_per_second']:.1f} |"
            )

        # AMD vs Non-AMD summary
        lines.extend([
            "",
            "## AMD vs Non-AMD Summary",
            ""
        ])

        amd_comparisons = [c for c in comparisons if c["is_amd"]]
        non_amd_comparisons = [c for c in comparisons if not c["is_amd"]]

        if amd_comparisons:
            avg_amd_latency = sum(c["elapsed_ms"] for c in amd_comparisons) / len(amd_comparisons)
            avg_amd_tps = sum(c["tokens_per_second"] for c in amd_comparisons) / len(amd_comparisons)
            lines.append(f"**AMD Cloud (vLLM) Performance:**")
            lines.append(f"- Average Latency: {avg_amd_latency:.0f} ms")
            lines.append(f"- Average Tokens/sec: {avg_amd_tps:.1f}")
            lines.append("")

        if non_amd_comparisons:
            avg_non_amd_latency = sum(c["elapsed_ms"] for c in non_amd_comparisons) / len(non_amd_comparisons)
            avg_non_amd_tps = sum(c["tokens_per_second"] for c in non_amd_comparisons) / len(non_amd_comparisons)
            lines.append(f"**Other Providers Performance:**")
            lines.append(f"- Average Latency: {avg_non_amd_latency:.0f} ms")
            lines.append(f"- Average Tokens/sec: {avg_non_amd_tps:.1f}")

            if avg_amd_latency > 0 and avg_non_amd_latency > 0:
                improvement = ((avg_non_amd_latency - avg_amd_latency) / avg_non_amd_latency) * 100
                lines.append(f"- **Performance Difference: {improvement:+.1f}%**")

        lines.append("")

        # Detailed results
        lines.extend([
            "## Detailed Results",
            ""
        ])

        for result in self._results:
            provider = result["provider"]
            model = result["model"]
            lines.append(f"### {provider} - {model}")
            lines.append("")

            for scenario_name, scenario_result in result.get("scenarios", {}).items():
                lines.append(f"**{scenario_name}:**")
                if scenario_result.get("success"):
                    lines.append(f"- Output length: {scenario_result['output_length']} tokens")
                    lines.append(f"- Total time: {scenario_result['elapsed_ms']:.2f} ms")
                    lines.append(f"- Tokens/sec: {scenario_result['tokens_per_second']:.2f}")
                else:
                    lines.append(f"- Error: {scenario_result.get('error', 'Unknown')}")
                lines.append("")

        content = "\n".join(lines)
        with open(output_file, 'w') as f:
            f.write(content)

        return content

    def get_benchmark_history(self, limit: int = 10) -> List[Dict]:
        """Get recent benchmark runs."""
        return self._results[-limit:]

    def clear_results(self):
        """Clear all benchmark results."""
        self._results = []
        self._save_results()
        return {"success": True, "message": "Results cleared"}
