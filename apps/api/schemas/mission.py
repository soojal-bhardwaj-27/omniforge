from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class CreateMissionRequest(BaseModel):
    prompt: str
    title: Optional[str] = None
    platform: Optional[str] = "discord"
    channel_id: Optional[str] = "demo-channel"
    user_id: Optional[str] = "developer"


class MissionResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    status: str
    progress: int
    platform: str
    workspace_path: str
    created_at: str
    completed_at: Optional[str] = None


class SwitchWebhookRequest(BaseModel):
    event: Optional[str] = "message_created"
    data: Optional[Dict[str, Any]] = None
    content: Optional[str] = None
    channel_id: Optional[str] = None
    user_id: Optional[str] = None
    platform: Optional[str] = "discord"
