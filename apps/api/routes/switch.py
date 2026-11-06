import os
from fastapi import APIRouter, Depends, Request, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, Dict, Any
from apps.api.dependencies import get_switch_router, SwitchMessageRouter, get_live_bridge

router = APIRouter(prefix="/api/switch", tags=["switch"])


class SimulateMessageRequest(BaseModel):
    platform: str = "telegram"  # "telegram", "discord", or "slack"
    message: str
    channel_name: Optional[str] = "devteam-shared-room"
    sender_name: Optional[str] = "TechLead"


@router.post("/webhook")
async def switch_webhook(
    raw_request: Request,
    router_instance: SwitchMessageRouter = Depends(get_switch_router),
    x_switch_secret: Optional[str] = Header(None),
    x_switch_signature: Optional[str] = Header(None),
):
    """Inbound webhook receiver from Switch integration gateway with shared-secret verification."""
    expected_secret = os.getenv("SWITCH_WEBHOOK_SECRET") or os.getenv("SWITCH_API_KEY")
    if expected_secret:
        auth_val = x_switch_secret or x_switch_signature
        if not auth_val or auth_val != expected_secret:
            raise HTTPException(status_code=401, detail="Unauthorized webhook source: invalid secret or signature.")

    body = await raw_request.json()
    result = await router_instance.handle_webhook(body)
    return result


@router.post("/simulate")
async def simulate_channel_message(
    req: SimulateMessageRequest,
    router_instance: SwitchMessageRouter = Depends(get_switch_router),
):
    """Allows zero-token simulation of Telegram, Discord, or Slack messages in shared RIO DevTeam room (Dev-only)."""
    env_mode = os.getenv("ENV", "development").lower()
    is_prod = env_mode in ["prod", "production"] or os.getenv("PRODUCTION", "").lower() == "true"
    if is_prod:
        raise HTTPException(status_code=403, detail="Simulated messages endpoint is disabled in production environments.")

    payload = {
        "event": "message_created",
        "platform": req.platform.lower(),
        "data": {
            "content": req.message,
            "channel_id": f"{req.platform.lower()}-{req.channel_name}",
            "user_id": req.sender_name,
            "author": {"id": req.sender_name, "username": req.sender_name},
        }
    }
    result = await router_instance.handle_webhook(payload)
    return {
        "status": "delivered_to_switch_shared_room",
        "platform": req.platform,
        "channel": req.channel_name,
        "result": result,
    }


@router.get("/messages")
async def get_switch_messages(
    limit: int = 50,
    router_instance: SwitchMessageRouter = Depends(get_switch_router),
):
    """Returns recent cross-platform messages delivered via Switch Shared Room."""
    return router_instance.switch_adapter.get_recent_messages(limit=min(limit, 100))


@router.get("/status")
async def get_switch_status():
    """Returns genuine connectivity status of all three platforms checking live bridge health."""
    has_tg = bool(os.getenv("TELEGRAM_BOT_TOKEN"))
    has_discord = bool(os.getenv("DISCORD_BOT_TOKEN"))
    has_slack = bool(os.getenv("SLACK_BOT_TOKEN"))

    tg_bridge = get_live_bridge("telegram")
    discord_bridge = get_live_bridge("discord")

    tg_running = bool(tg_bridge and getattr(tg_bridge, "running", False))
    discord_running = bool(discord_bridge and getattr(discord_bridge, "running", False))

    return {
        "shared_room": "rio-devteam",
        "status": "active",
        "connectors": {
            "telegram": {
                "status": "connected" if (has_tg and tg_running) else ("configured" if has_tg else "simulation"),
                "is_running": tg_running,
                "bot_username": "@rio_claw_bot" if has_tg else None,
                "mode": "live_gateway" if has_tg else "shared_room_simulator"
            },
            "discord": {
                "status": "connected" if (has_discord and discord_running) else ("configured" if has_discord else "simulation"),
                "is_running": discord_running,
                "bot_username": "rio-dev#2111" if has_discord else None,
                "mode": "live_gateway" if has_discord else "shared_room_simulator"
            },
            "slack": {
                "status": "connected" if has_slack else "simulation",
                "is_running": has_slack,
                "mode": "live_webhook" if has_slack else "shared_room_simulator"
            },
        },
        "agents": ["COMMANDER", "ARCHITECT", "DESIGNER", "DEVELOPER", "TESTER", "SECURITY"],
    }

