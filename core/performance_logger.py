"""
Performance Logger for NeuroDesk AMD AI Multi-Agent System.
Tracks and analyzes LLM inference performance metrics for AMD Developer Cloud.
"""

import json
import time
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
import threading
from contextlib import contextmanager


@dataclass
class PerformanceMetric:
    """Performance metric for a single request."""
    timestamp: str
    provider: str
    model: str
    endpoint_type: str  # vLLM, Ollama, etc.
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    first_token_latency_ms: float
    total_latency_ms: float
    tokens_per_second: float
    cost_usd: Optional[float] = None
    benchmark_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)


class PerformanceLogger:
    """Logger for tracking LLM performance metrics."""

    def __init__(self, metrics_file: str = "data/performance_metrics.json"):
        self.metrics_file = Path(metrics_file)
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        self._metrics: List[Dict] = []
        self._lock = threading.Lock()
        self._load_metrics()

    def _load_metrics(self):
        """Load metrics from file."""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    self._metrics = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._metrics = []

    def _save_metrics(self):
        """Save metrics to file."""
        with open(self.metrics_file, 'w') as f:
            json.dump(self._metrics, f, indent=2)

    def log_request(
        self,
        provider: str,
        model: str,
        endpoint_type: str,
        prompt_tokens: int,
        completion_tokens: int,
        first_token_latency_ms: float,
        total_latency_ms: float,
        cost_usd: Optional[float] = None,
        benchmark_id: Optional[str] = None,
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """Log a performance metric for a request."""
        tags = tags or []

        tokens_per_second = completion_tokens / (total_latency_ms / 1000) if total_latency_ms > 0 else 0

        metric = {
            "timestamp": datetime.now().isoformat(),
            "provider": provider,
            "model": model,
            "endpoint_type": endpoint_type,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "first_token_latency_ms": round(first_token_latency_ms, 2),
            "total_latency_ms": round(total_latency_ms, 2),
            "tokens_per_second": round(tokens_per_second, 2),
            "cost_usd": round(cost_usd, 6) if cost_usd else None,
            "benchmark_id": benchmark_id,
            "tags": tags,
            "is_amd": "AMD" in provider.upper() or "vllm" in endpoint_type.lower()
        }

        with self._lock:
            self._metrics.append(metric)
            self._save_metrics()

        return metric

    def get_recent_metrics(self, limit: int = 50) -> List[Dict]:
        """Get recent metrics."""
        with self._lock:
            return self._metrics[-limit:]

    def get_metrics_by_provider(self, provider: str) -> List[Dict]:
        """Get metrics filtered by provider."""
        with self._lock:
            return [m for m in self._metrics if m["provider"] == provider]

    def get_amd_metrics(self) -> List[Dict]:
        """Get all AMD Cloud metrics."""
        with self._lock:
            return [m for m in self._metrics if m.get("is_amd", False)]

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        with self._lock:
            if not self._metrics:
                return {
                    "total_requests": 0,
                    "total_tokens": 0,
                    "avg_first_token_latency_ms": 0,
                    "avg_total_latency_ms": 0,
                    "avg_tokens_per_second": 0,
                    "amd_metric_count": 0,
                    "non_amd_metric_count": 0
                }

            metrics = self._metrics
            total_requests = len(metrics)

            total_tokens = sum(m["total_tokens"] for m in metrics)
            avg_first_token = sum(m["first_token_latency_ms"] for m in metrics) / total_requests
            avg_total_latency = sum(m["total_latency_ms"] for m in metrics) / total_requests
            avg_tps = sum(m["tokens_per_second"] for m in metrics) / total_requests
            amd_count = sum(1 for m in metrics if m.get("is_amd", False))
            non_amd_count = total_requests - amd_count

            return {
                "total_requests": total_requests,
                "total_tokens": total_tokens,
                "avg_first_token_latency_ms": round(avg_first_token, 2),
                "avg_total_latency_ms": round(avg_total_latency, 2),
                "avg_tokens_per_second": round(avg_tps, 2),
                "amd_metric_count": amd_count,
                "non_amd_metric_count": non_amd_count,
                "last_updated": datetime.now().isoformat()
            }

    def export_benchmark_results(self, output_file: str = "BENCHMARKS.md") -> str:
        """Export benchmark results to markdown."""
        with self._lock:
            if not self._metrics:
                return "# Benchmark Results\n\nNo benchmark data available yet."

            # Group by provider and model
            groups: Dict[str, List[Dict]] = {}
            for m in self._metrics:
                key = f"{m['provider']} - {m['model']}"
                if key not in groups:
                    groups[key] = []
                groups[key].append(m)

            lines = [
                "# NeuroDesk AMD Benchmark Results",
                "",
                "Performance metrics collected from AMD Developer Cloud inference.",
                "Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "",
                "## Summary",
                "",
                "| Metric | Value |",
                "|--------|-------|",
                f"| Total Requests | {len(self._metrics)} |",
                f"| Total Tokens | {sum(m['total_tokens'] for m in self._metrics):,} |",
                f"| Avg First Token Latency | {sum(m['first_token_latency_ms'] for m in self._metrics) / len(self._metrics):.2f} ms |",
                f"| Avg Tokens/sec | {sum(m['tokens_per_second'] for m in self._metrics) / len(self._metrics):.2f} |",
                ""
            ]

            # Add comparison section
            lines.extend([
                "## Provider Comparison",
                "",
                "### AMD Cloud (vLLM) vs Others",
                ""
            ])

            amd_metrics = [m for m in self._metrics if m.get("is_amd", False)]
            non_amd_metrics = [m for m in self._metrics if not m.get("is_amd", False)]

            if amd_metrics:
                lines.extend([
                    f"**AMD Cloud (vLLM)**:",
                    f"  - Requests: {len(amd_metrics)}",
                    f"  - Avg Latency: {sum(m['total_latency_ms'] for m in amd_metrics) / len(amd_metrics):.2f} ms",
                    f"  - Avg Tokens/sec: {sum(m['tokens_per_second'] for m in amd_metrics) / len(amd_metrics):.2f}",
                    ""
                ])

            if non_amd_metrics:
                lines.extend([
                    f"**Other Providers**:",
                    f"  - Requests: {len(non_amd_metrics)}",
                    f"  - Avg Latency: {sum(m['total_latency_ms'] for m in non_amd_metrics) / len(non_amd_metrics):.2f} ms",
                    f"  - Avg Tokens/sec: {sum(m['tokens_per_second'] for m in non_amd_metrics) / len(non_amd_metrics):.2f}",
                    ""
                ])

            # Detailed benchmark table
            lines.extend([
                "## Detailed Results",
                "",
                "| Provider | Model | First Token (ms) | Total (ms) | TPS | AMD?" + " |",
                "|----------|-------|------------------|------------|-----|-----|" + " |"
            ])

            for m in self._metrics:
                is_amd = "✅" if m.get("is_amd") else "❌"
                lines.append(
                    f"| {m['provider']} | {m['model']} | {m['first_token_latency_ms']:.2f} | "
                    f"{m['total_latency_ms']:.2f} | {m['tokens_per_second']:.2f} | {is_amd} |"
                )

            content = "\n".join(lines)
            with open(output_file, 'w') as f:
                f.write(content)

            return content

    @contextmanager
    def track_request(self, provider: str, model: str, endpoint_type: str = "vLLM"):
        """Context manager for tracking request performance."""
        start_time = time.time()
        first_token_time = None
        prompt_tokens = 0
        completion_tokens = 0

        class RequestTracker:
            def __init__(self, logger: 'PerformanceLogger'):
                self.logger = logger
                self.start = start_time
                self.first_token = None
                self.prompt_tokens = prompt_tokens
                self.completion_tokens = completion_tokens

            def mark_first_token(self):
                self.first_token = time.time()

            def set_tokens(self, prompt: int, completion: int):
                self.prompt_tokens = prompt
                self.completion_tokens = completion

            def finish(self):
                elapsed = (time.time() - self.start) * 1000
                first_token_ms = (self.first_token - self.start) * 1000 if self.first_token else elapsed
                tokens_per_sec = self.completion_tokens / (elapsed / 1000) if elapsed > 0 else 0

                return self.logger.log_request(
                    provider=provider,
                    model=model,
                    endpoint_type=endpoint_type,
                    prompt_tokens=self.prompt_tokens,
                    completion_tokens=self.completion_tokens,
                    first_token_latency_ms=first_token_ms,
                    total_latency_ms=elapsed,
                    tags=["benchmark"]
                )

        tracker = RequestTracker(self)
        try:
            yield tracker
        finally:
            tracker.finish()
