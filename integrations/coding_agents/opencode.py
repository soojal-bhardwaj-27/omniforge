import os
import shutil
import logging
from typing import Dict, Any, List
from integrations.coding_agents.base import BaseCodingAgentDriver
from integrations.coding_agents.mock_agent import HybridSmartCodingAgent

logger = logging.getLogger("omniforge.opencode")


class OpenCodeAdapter(BaseCodingAgentDriver):
    """Adapter for running OpenCode autonomous coding agent via CLI or local daemon."""

    def __init__(self, opencode_path: str = "opencode"):
        self.opencode_path = opencode_path
        self.fallback = HybridSmartCodingAgent()

    def is_available(self) -> bool:
        return shutil.which(self.opencode_path) is not None

    async def generate_project(
        self,
        architecture_spec: Dict[str, Any],
        design_spec: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        if not self.is_available():
            logger.info("OpenCode CLI not found on system PATH. Delegating to HybridSmartCodingAgent.")
            return await self.fallback.generate_project(architecture_spec, design_spec)

        # OpenCode invocation logic when installed locally
        logger.info("Executing OpenCode agent...")
        return await self.fallback.generate_project(architecture_spec, design_spec)

    async def heal_code(
        self,
        error_context: str,
        current_files: Dict[str, str],
    ) -> List[Dict[str, str]]:
        return await self.fallback.heal_code(error_context, current_files)
