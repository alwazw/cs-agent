import time
import asyncio
from typing import Dict, List, Any
from dataclasses import dataclass, field

@dataclass
class Alert:
    id: str
    severity: str  # "INFO", "WARNING", "CRITICAL"
    category: str  # "TOKEN_USAGE", "STACK_HEALTH", "LATENCY"
    message: str
    timestamp: float = field(default_factory=time.time)

class TelemetryMonitor:
    def __init__(self, token_threshold_per_min: int = 5000):
        self.token_threshold = token_threshold_per_min
        self.token_history: List[Dict[str, Any]] = []
        self.alerts: List[Alert] = []
        self.active_subscribers: List[asyncio.Queue] = []

    async def register_token_usage(self, prompt_tokens: int, completion_tokens: int, session_id: str):
        total_tokens = prompt_tokens + completion_tokens
        now = time.time()
        self.token_history.append({"timestamp": now, "tokens": total_tokens, "session_id": session_id})

        # Calculate tokens in the last 60 seconds
        cutoff = now - 60
        recent_tokens = sum(item["tokens"] for item in self.token_history if item["timestamp"] >= cutoff)

        # Clean history older than 5 minutes
        self.token_history = [item for item in self.token_history if item["timestamp"] >= now - 300]

        if recent_tokens > self.token_threshold:
            alert = Alert(
                id=f"alert_{int(now * 1000)}",
                severity="CRITICAL" if recent_tokens > (self.token_threshold * 1.5) else "WARNING",
                category="TOKEN_USAGE",
                message=f"High token consumption detected! {recent_tokens} tokens consumed in the last 60s (Threshold: {self.token_threshold})."
            )
            await self._dispatch_alert(alert)

    async def log_health_issue(self, service_name: str, message: str, severity: str = "CRITICAL"):
        alert = Alert(
            id=f"alert_{int(time.time() * 1000)}",
            severity=severity,
            category="STACK_HEALTH",
            message=f"Health degradation on service [{service_name}]: {message}"
        )
        await self._dispatch_alert(alert)

    async def _dispatch_alert(self, alert: Alert):
        self.alerts.append(alert)
        for queue in self.active_subscribers:
            await queue.put(alert)

    def get_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [
            {
                "id": a.id,
                "severity": a.severity,
                "category": a.category,
                "message": a.message,
                "timestamp": a.timestamp
            } for a in reversed(self.alerts[-limit:])
        ]

telemetry_engine = TelemetryMonitor(token_threshold_per_min=5000)
