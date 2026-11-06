import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from core.execution.sandbox import ExecutionSandbox
from core.events.publisher import EventPublisher

logger = logging.getLogger("omniforge.agent")


@dataclass
class AgentResult:
    task_id: str
    agent: str
    status: str  # completed, failed, needs_approval
    output: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    requires_approval: bool = False
    permission_level: int = 0
    approval_action: str = ""
    error_message: Optional[str] = None

    def to_dict(self):
        return asdict(self)


class BaseAgent(ABC):
    """Abstract base agent providing structured output, event emitting, and sandbox access."""

    def __init__(self, name: str, role_description: str):
        self.name = name
        self.role_description = role_description

    @abstractmethod
    async def execute(
        self,
        task_id: str,
        mission_title: str,
        task_title: str,
        task_context: Dict[str, Any],
        sandbox: ExecutionSandbox,
        publisher: EventPublisher,
    ) -> AgentResult:
        pass

    def format_json_output(self, raw_text: str) -> Dict[str, Any]:
        """Attempts to parse clean JSON from agent LLM response."""
        try:
            # Strip markdown fences if present
            cleaned = raw_text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                cleaned = "\n".join(lines).strip()
            return json.loads(cleaned)
        except Exception:
            return {"raw": raw_text}
