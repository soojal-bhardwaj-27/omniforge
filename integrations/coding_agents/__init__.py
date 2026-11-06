import os
from integrations.coding_agents.base import BaseCodingAgentDriver
from integrations.coding_agents.mock_agent import HybridSmartCodingAgent
from integrations.coding_agents.opencode import OpenCodeAdapter
from integrations.coding_agents.codex import CodexAdapter


def get_coding_agent_driver(driver_name: str = None) -> BaseCodingAgentDriver:
    name = driver_name or os.getenv("CODING_AGENT_DRIVER", "hybrid").lower()

    if name == "opencode":
        return OpenCodeAdapter()
    elif name == "codex":
        return CodexAdapter()
    else:
        return HybridSmartCodingAgent()
