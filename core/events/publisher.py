from typing import Dict, Any, Optional
from core.events.event_bus import global_event_bus, MissionEvent


class EventPublisher:
    def __init__(self, mission_id: str, default_agent: str = "SYSTEM"):
        self.mission_id = mission_id
        self.default_agent = default_agent

    async def emit(
        self,
        event_type: str,
        message: str,
        agent: Optional[str] = None,
        task_id: str = "",
        payload: Optional[Dict[str, Any]] = None,
    ):
        event = MissionEvent(
            mission_id=self.mission_id,
            agent=agent or self.default_agent,
            event_type=event_type,
            message=message,
            task_id=task_id,
            payload=payload or {},
        )
        await global_event_bus.publish(event)
        return event

    async def mission_started(self, title: str):
        return await self.emit("mission_started", f"Mission initiated: {title}", agent="COMMANDER")

    async def task_planned(self, task_id: str, title: str, assigned_agent: str):
        return await self.emit(
            "task_planned",
            f"Task {task_id} planned: '{title}' assigned to {assigned_agent}",
            agent="COMMANDER",
            task_id=task_id,
            payload={"task_id": task_id, "title": title, "assigned_to": assigned_agent},
        )

    async def task_started(self, task_id: str, agent: str, details: str = ""):
        return await self.emit(
            "task_started",
            f"Agent {agent} started work on task {task_id}. {details}".strip(),
            agent=agent,
            task_id=task_id,
        )

    async def task_completed(self, task_id: str, agent: str, summary: str, artifacts: list = None):
        return await self.emit(
            "task_completed",
            f"Agent {agent} completed task {task_id}: {summary}",
            agent=agent,
            task_id=task_id,
            payload={"summary": summary, "artifacts": artifacts or []},
        )

    async def file_created(self, file_path: str, agent: str, task_id: str = ""):
        return await self.emit(
            "file_created",
            f"File created: {file_path}",
            agent=agent,
            task_id=task_id,
            payload={"file_path": file_path},
        )

    async def command_executed(self, command: str, exit_code: int, output_preview: str, agent: str, task_id: str = ""):
        return await self.emit(
            "command_executed",
            f"Command `{command}` finished with exit code {exit_code}",
            agent=agent,
            task_id=task_id,
            payload={"command": command, "exit_code": exit_code, "output": output_preview},
        )

    async def test_result(self, passed: bool, summary: str, details: Dict[str, Any], task_id: str = ""):
        event_type = "test_passed" if passed else "test_failed"
        return await self.emit(
            event_type,
            f"Verification: {summary}",
            agent="TESTER",
            task_id=task_id,
            payload={"passed": passed, "details": details},
        )

    async def approval_requested(self, approval_id: str, action: str, level: int, task_id: str = ""):
        return await self.emit(
            "approval_requested",
            f"Security Gate: Approval required for '{action}' (Permission Level {level})",
            agent="SECURITY",
            task_id=task_id,
            payload={"approval_id": approval_id, "action": action, "permission_level": level},
        )

    async def mission_completed(self, summary: str, stats: Dict[str, Any]):
        return await self.emit(
            "mission_completed",
            f"Mission completed successfully! {summary}",
            agent="COMMANDER",
            payload={"stats": stats},
        )

    async def mission_failed(self, reason: str):
        return await self.emit(
            "mission_failed",
            f"Mission aborted: {reason}",
            agent="COMMANDER",
            payload={"reason": reason},
        )
