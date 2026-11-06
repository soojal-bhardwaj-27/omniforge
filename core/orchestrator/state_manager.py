import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from database.models import Mission, Task, Event, Approval, Artifact, MissionStatus, TaskStatus, AgentRole
from database.session import async_session_factory
from sqlalchemy import select, update


class MissionStateManager:
    """Manages active mission lifecycle, task dependencies, progress calculation, and DB persistence."""

    def __init__(self):
        # Fast in-memory cache for live streaming & low latency
        self._missions: Dict[str, Dict[str, Any]] = {}

    async def create_mission(
        self,
        mission_id: str,
        title: str,
        description: str,
        platform: str = "discord",
        channel_id: str = "",
        user_id: str = "",
        workspace_path: str = "",
    ) -> Dict[str, Any]:
        mission_data = {
            "id": mission_id,
            "title": title,
            "description": description,
            "status": MissionStatus.PENDING.value,
            "platform": platform,
            "channel_id": channel_id,
            "user_id": user_id,
            "workspace_path": workspace_path,
            "progress": 0,
            "tasks": {},
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": None,
        }
        self._missions[mission_id] = mission_data

        async with async_session_factory() as session:
            db_mission = Mission(
                id=mission_id,
                title=title,
                description=description,
                status=MissionStatus.PENDING,
                platform=platform,
                channel_id=channel_id,
                user_id=user_id,
                workspace_path=workspace_path,
                progress=0,
            )
            session.add(db_mission)
            await session.commit()

        return mission_data

    async def add_tasks(self, mission_id: str, tasks: List[Dict[str, Any]]):
        if mission_id in self._missions:
            for t in tasks:
                self._missions[mission_id]["tasks"][t["id"]] = {
                    **t,
                    "status": TaskStatus.PENDING.value,
                    "output": None,
                    "error": None,
                }

        async with async_session_factory() as session:
            for t in tasks:
                db_task = Task(
                    id=t["id"],
                    mission_id=mission_id,
                    title=t["title"],
                    description=t.get("description", ""),
                    agent=AgentRole(t["agent"]),
                    status=TaskStatus.PENDING,
                    priority=t.get("priority", 1),
                    dependencies=json.dumps(t.get("dependencies", [])),
                )
                session.add(db_task)
            await session.commit()

    async def update_task_status(
        self,
        mission_id: str,
        task_id: str,
        status: TaskStatus,
        output: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ):
        if mission_id in self._missions and task_id in self._missions[mission_id]["tasks"]:
            task = self._missions[mission_id]["tasks"][task_id]
            task["status"] = status.value
            if output:
                task["output"] = output
            if error:
                task["error"] = error
            self._recalculate_progress(mission_id)

        async with async_session_factory() as session:
            stmt = select(Task).where(Task.id == task_id)
            res = await session.execute(stmt)
            db_task = res.scalar_one_or_none()
            if db_task:
                db_task.status = status
                if output:
                    db_task.output_summary = json.dumps(output)
                if status == TaskStatus.COMPLETED:
                    db_task.completed_at = datetime.utcnow()
                await session.commit()

    def _recalculate_progress(self, mission_id: str):
        if mission_id not in self._missions:
            return
        tasks = self._missions[mission_id]["tasks"]
        if not tasks:
            return
        completed = sum(1 for t in tasks.values() if t["status"] == TaskStatus.COMPLETED.value)
        total = len(tasks)
        progress = int((completed / total) * 100)
        self._missions[mission_id]["progress"] = progress

    async def update_mission_status(self, mission_id: str, status: MissionStatus):
        if mission_id in self._missions:
            self._missions[mission_id]["status"] = status.value
            if status == MissionStatus.COMPLETED:
                self._missions[mission_id]["progress"] = 100
                self._missions[mission_id]["completed_at"] = datetime.utcnow().isoformat()

        async with async_session_factory() as session:
            stmt = select(Mission).where(Mission.id == mission_id)
            res = await session.execute(stmt)
            db_mission = res.scalar_one_or_none()
            if db_mission:
                db_mission.status = status
                if status == MissionStatus.COMPLETED:
                    db_mission.progress = 100
                    db_mission.completed_at = datetime.utcnow()
                await session.commit()

    def get_mission(self, mission_id: str) -> Optional[Dict[str, Any]]:
        return self._missions.get(mission_id)

    def list_missions(self) -> List[Dict[str, Any]]:
        return list(self._missions.values())

    async def hydrate_from_db(self):
        """Loads existing missions and their tasks from persistent storage on startup."""
        try:
            async with async_session_factory() as session:
                stmt = select(Mission).order_by(Mission.created_at.desc()).limit(100)
                res = await session.execute(stmt)
                db_missions = res.scalars().all()
                for m in db_missions:
                    self._missions[m.id] = {
                        "id": m.id,
                        "title": m.title,
                        "description": m.description,
                        "status": m.status.value if hasattr(m.status, "value") else str(m.status),
                        "platform": m.platform,
                        "channel_id": m.channel_id,
                        "user_id": m.user_id,
                        "workspace_path": m.workspace_path,
                        "progress": m.progress or 0,
                        "tasks": {},
                        "created_at": m.created_at.isoformat() if m.created_at else None,
                        "completed_at": m.completed_at.isoformat() if m.completed_at else None,
                    }
        except Exception as e:
            pass
