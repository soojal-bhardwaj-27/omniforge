from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseCodingAgentDriver(ABC):
    """Abstract interface for swappable coding agents (OpenCode, Codex, Direct LLM, or Mock fallback)."""

    @abstractmethod
    async def generate_project(
        self,
        architecture_spec: Dict[str, Any],
        design_spec: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """Generates files for the project.
        Returns a list of dicts: [{"path": "index.html", "content": "..."}]
        """
        pass

    @abstractmethod
    async def heal_code(
        self,
        error_context: str,
        current_files: Dict[str, str],
    ) -> List[Dict[str, str]]:
        """Fixes code based on test or verification failure error report."""
        pass
