import re
import uuid
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from apps.api.schemas.mission import CreateMissionRequest
from apps.api.dependencies import get_orchestrator, CommanderOrchestrator, verify_api_key
from core.execution.sandbox import ExecutionSandbox
from database.models import MissionStatus

router = APIRouter(prefix="/api/missions", tags=["missions"])

SAFE_MISSION_ID_REGEX = re.compile(r"^m-[a-zA-Z0-9_\-]{6,32}$")
MAX_PROMPT_LENGTH = 4000

# Registry of active mission tasks for lifecycle management and cancellation
active_mission_tasks: Dict[str, asyncio.Task] = {}


def validate_mission_id(mission_id: str) -> str:
    if not SAFE_MISSION_ID_REGEX.match(mission_id):
        raise HTTPException(status_code=400, detail="Invalid mission ID format.")
    return mission_id


@router.post("", dependencies=[Depends(verify_api_key)])
async def create_mission(
    req: CreateMissionRequest,
    background_tasks: BackgroundTasks,
    orchestrator: CommanderOrchestrator = Depends(get_orchestrator),
):
    """Initiates an autonomous workforce mission."""
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Mission prompt cannot be empty.")
    
    if len(req.prompt) > MAX_PROMPT_LENGTH:
        raise HTTPException(
            status_code=400, 
            detail=f"Mission prompt exceeds maximum allowed length of {MAX_PROMPT_LENGTH} characters."
        )

    mission_id = f"m-{uuid.uuid4().hex[:8]}"

    async def _run_and_track():
        try:
            await orchestrator.launch_mission(
                prompt=req.prompt,
                mission_title=req.title,
                platform=req.platform or "discord",
                channel_id=req.channel_id or "web",
                user_id=req.user_id or "user",
                mission_id=mission_id,
            )
        finally:
            active_mission_tasks.pop(mission_id, None)

    task = asyncio.create_task(_run_and_track())
    active_mission_tasks[mission_id] = task

    return {
        "status": "accepted",
        "mission_id": mission_id,
        "message": "Mission dispatched to Commander",
        "preview_url": f"/preview/{mission_id}/index.html"
    }


@router.get("")
async def list_missions(
    orchestrator: CommanderOrchestrator = Depends(get_orchestrator),
):
    """Lists all missions and their current execution statuses."""
    return orchestrator.state_manager.list_missions()


@router.get("/{mission_id}")
async def get_mission(
    mission_id: str,
    orchestrator: CommanderOrchestrator = Depends(get_orchestrator),
):
    """Retrieves full mission details including tasks and workspace files."""
    validate_mission_id(mission_id)
    mission = orchestrator.state_manager.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    sandbox = ExecutionSandbox("./workspaces", mission_id)
    files = sandbox.list_files()

    return {
        **mission,
        "artifacts": files,
        "summary": sandbox.get_summary(),
        "is_active": mission_id in active_mission_tasks,
    }


@router.post("/{mission_id}/cancel", dependencies=[Depends(verify_api_key)])
async def cancel_mission(
    mission_id: str,
    orchestrator: CommanderOrchestrator = Depends(get_orchestrator),
):
    """Cancels an in-flight mission execution."""
    validate_mission_id(mission_id)
    mission = orchestrator.state_manager.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    task = active_mission_tasks.pop(mission_id, None)
    if task and not task.done():
        task.cancel()
        await orchestrator.state_manager.update_mission_status(mission_id, MissionStatus.FAILED)
        return {"status": "cancelled", "mission_id": mission_id}
    
    return {"status": "not_active", "mission_id": mission_id, "current_status": mission["status"]}


@router.get("/{mission_id}/files/{file_path:path}")
async def get_mission_file(
    mission_id: str,
    file_path: str,
    orchestrator: CommanderOrchestrator = Depends(get_orchestrator),
):
    """Fetches the content of a specific generated artifact safely."""
    validate_mission_id(mission_id)
    # Block path traversal attempts in file_path
    if ".." in file_path or file_path.startswith("/") or "\\" in file_path:
        raise HTTPException(status_code=400, detail="Invalid file path.")

    sandbox = ExecutionSandbox("./workspaces", mission_id)
    if not sandbox.file_exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    content = await sandbox.read_file(file_path)
    return {"path": file_path, "content": content}
