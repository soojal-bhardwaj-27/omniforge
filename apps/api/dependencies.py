import os
from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, Security
from fastapi.security import APIKeyHeader
from core.orchestrator.commander import CommanderOrchestrator
from integrations.switch.adapter import SwitchGatewayAdapter
from integrations.switch.router import SwitchMessageRouter

# Global application singleton instances
orchestrator_instance = CommanderOrchestrator(workspace_root="./workspaces")
switch_adapter_instance = SwitchGatewayAdapter()
switch_router_instance = SwitchMessageRouter(orchestrator_instance, switch_adapter_instance)

# Live bridge registry for authentic health reporting
bridge_registry: Dict[str, Any] = {
    "telegram": None,
    "discord": None,
}

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_orchestrator() -> CommanderOrchestrator:
    return orchestrator_instance


def get_switch_adapter() -> SwitchGatewayAdapter:
    return switch_adapter_instance


def get_switch_router() -> SwitchMessageRouter:
    return switch_router_instance


def set_live_bridge(platform: str, bridge_instance: Any):
    bridge_registry[platform] = bridge_instance


def get_live_bridge(platform: str) -> Optional[Any]:
    return bridge_registry.get(platform)


async def verify_api_key(
    x_api_key: Optional[str] = Security(api_key_header),
    authorization: Optional[str] = Header(None)
):
    """Enforces API key authentication when configured in environment.
    Allows local development mode when OMNIFORGE_API_KEY is unset.
    """
    configured_key = os.getenv("OMNIFORGE_API_KEY", "").strip()
    if not configured_key:
        return True  # Dev mode: open

    # Check X-API-Key
    if x_api_key and x_api_key == configured_key:
        return True

    # Check Bearer token
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        if token == configured_key:
            return True

    raise HTTPException(status_code=401, detail="Unauthorized: Invalid or missing API key.")
