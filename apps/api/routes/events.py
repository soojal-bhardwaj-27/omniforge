import re
import os
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from core.events.event_bus import global_event_bus, MissionEvent

router = APIRouter(tags=["events"])

SAFE_MISSION_ID_REGEX = re.compile(r"^m-[a-zA-Z0-9_\-]{6,32}$")


def _is_ws_authorized(websocket: WebSocket) -> bool:
    configured_key = os.getenv("OMNIFORGE_API_KEY", "").strip()
    if not configured_key:
        return True
    
    # Check token in query params (?token=... or ?apiKey=...)
    token = websocket.query_params.get("token") or websocket.query_params.get("apiKey")
    if token and token == configured_key:
        return True
    
    # Check headers
    auth_header = websocket.headers.get("x-api-key")
    if auth_header and auth_header == configured_key:
        return True
    return False


@router.websocket("/ws/events")
async def websocket_global_events(websocket: WebSocket):
    """Streams live events across all missions in real-time to Mission Control dashboard."""
    if not _is_ws_authorized(websocket):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    queue = global_event_bus.subscribe()
    try:
        while True:
            event: MissionEvent = await queue.get()
            await websocket.send_json(event.to_dict())
    except WebSocketDisconnect:
        global_event_bus.unsubscribe(queue)
    except Exception:
        global_event_bus.unsubscribe(queue)


@router.websocket("/ws/events/{mission_id}")
async def websocket_mission_events(websocket: WebSocket, mission_id: str):
    """Streams live events for a specific mission to the dashboard."""
    if not SAFE_MISSION_ID_REGEX.match(mission_id):
        await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
        return

    if not _is_ws_authorized(websocket):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    queue = global_event_bus.subscribe(mission_id)
    try:
        while True:
            event: MissionEvent = await queue.get()
            await websocket.send_json(event.to_dict())
    except WebSocketDisconnect:
        global_event_bus.unsubscribe(queue, mission_id)
    except Exception:
        global_event_bus.unsubscribe(queue, mission_id)
