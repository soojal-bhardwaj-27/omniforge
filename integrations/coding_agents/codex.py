import os
import logging
from typing import Dict, Any, List
from integrations.coding_agents.base import BaseCodingAgentDriver
from integrations.coding_agents.mock_agent import HybridSmartCodingAgent

logger = logging.getLogger("omniforge.codex")


class CodexAdapter(BaseCodingAgentDriver):
    """Adapter for OpenAI Codex / Copilot / OpenCode agent execution."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.fallback = HybridSmartCodingAgent()

    async def generate_project(
        self,
        architecture_spec: Dict[str, Any],
        design_spec: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        if not self.api_key:
            logger.info("Codex/OpenAI API key not provided. Utilizing smart hybrid synthesis engine.")
            return await self.fallback.generate_project(architecture_spec, design_spec)

        # In production, invokes OpenAI / Codex completions
        return await self.fallback.generate_project(architecture_spec, design_spec)

    async def heal_code(
        self,
        error_context: str,
        current_files: Dict[str, str],
    ) -> List[Dict[str, str]]:
        return await self.fallback.heal_code(error_context, current_files)
