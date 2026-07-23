import json
import logging
import time
from contextvars import ContextVar, Token
from threading import Lock
from typing import Any
from uuid import uuid4

from langchain_core.callbacks import BaseCallbackHandler


request_id_context: ContextVar[str] = ContextVar("request_id", default="-")
conversation_id_context: ContextVar[str] = ContextVar(
    "conversation_id",
    default="-",
)


class JsonFormatter(logging.Formatter):
    """Emit machine-readable logs with request correlation fields."""

    _standard_fields = set(logging.makeLogRecord({}).__dict__) | {
        "message",
        "asctime",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_context.get(),
            "conversation_id": conversation_id_context.get(),
        }
        for key, value in record.__dict__.items():
            if key not in self._standard_fields and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, ensure_ascii=False)


class ApplicationMetrics:
    """Small process-local counters for structured operational logging."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._requests = 0
        self._errors = 0

    def record_request(self, failed: bool) -> dict[str, float | int]:
        with self._lock:
            self._requests += 1
            self._errors += int(failed)
            return {
                "request_count": self._requests,
                "error_count": self._errors,
                "error_rate": self._errors / self._requests,
            }


application_metrics = ApplicationMetrics()


def bind_request_context(
    request_id: str | None = None,
    conversation_id: int | str | None = None,
) -> tuple[Token, Token]:
    return (
        request_id_context.set(request_id or str(uuid4())),
        conversation_id_context.set(
            str(conversation_id) if conversation_id is not None else "-"
        ),
    )


def reset_request_context(tokens: tuple[Token, Token]) -> None:
    request_id_context.reset(tokens[0])
    conversation_id_context.reset(tokens[1])


class LangSmithMetricsCallback(BaseCallbackHandler):
    """Log LLM and tool telemetry while LangSmith stores the complete traces."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("observability.langsmith")
        self._started: dict[str, float] = {}
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0
        self.llm_latency_ms = 0.0

    def _start(self, run_id: Any) -> None:
        self._started[str(run_id)] = time.perf_counter()

    def _elapsed(self, run_id: Any) -> float:
        started = self._started.pop(str(run_id), time.perf_counter())
        return round((time.perf_counter() - started) * 1000, 2)

    def on_llm_start(self, serialized, prompts, *, run_id, **kwargs) -> None:
        self._start(run_id)

    def on_chat_model_start(
        self,
        serialized,
        messages,
        *,
        run_id,
        **kwargs,
    ) -> None:
        self._start(run_id)

    def on_llm_end(self, response, *, run_id, **kwargs) -> None:
        latency_ms = self._elapsed(run_id)
        self.llm_latency_ms += latency_ms
        usage = (response.llm_output or {}).get("token_usage", {})
        if not usage and response.generations:
            message = getattr(response.generations[0][0], "message", None)
            usage = getattr(message, "usage_metadata", None) or {}

        input_tokens = int(
            usage.get("input_tokens", usage.get("prompt_tokens", 0)) or 0
        )
        output_tokens = int(
            usage.get("output_tokens", usage.get("completion_tokens", 0)) or 0
        )
        total_tokens = int(
            usage.get("total_tokens", input_tokens + output_tokens) or 0
        )
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens += total_tokens
        self.logger.info(
            "LLM call completed",
            extra={
                "event": "llm.completed",
                "llm_latency_ms": latency_ms,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost_tracking": "langsmith_automatic",
            },
        )

    def on_llm_error(self, error, *, run_id, **kwargs) -> None:
        self.logger.error(
            "LLM call failed",
            extra={
                "event": "llm.failed",
                "llm_latency_ms": self._elapsed(run_id),
                "error_type": type(error).__name__,
            },
        )

    def on_tool_start(
        self,
        serialized,
        input_str,
        *,
        run_id,
        name=None,
        **kwargs,
    ) -> None:
        self._start(run_id)
        self.logger.info(
            "Tool execution started",
            extra={
                "event": "tool.started",
                "tool_name": name or serialized.get("name", "unknown"),
            },
        )

    def on_tool_end(self, output, *, run_id, name=None, **kwargs) -> None:
        self.logger.info(
            "Tool execution completed",
            extra={
                "event": "tool.completed",
                "tool_name": name or "unknown",
                "tool_latency_ms": self._elapsed(run_id),
            },
        )

    def on_tool_error(self, error, *, run_id, name=None, **kwargs) -> None:
        self.logger.error(
            "Tool execution failed",
            extra={
                "event": "tool.failed",
                "tool_name": name or "unknown",
                "tool_latency_ms": self._elapsed(run_id),
                "error_type": type(error).__name__,
            },
        )

