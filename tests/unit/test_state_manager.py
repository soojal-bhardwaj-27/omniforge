import uuid
import pytest
import pytest_asyncio
from database.session import init_db
from core.orchestrator.state_manager import MissionStateManager
from database.models import MissionStatus, TaskStatus, AgentRole


@pytest.mark.asyncio
async def test_mission_lifecycle():
    await init_db()
    manager = MissionStateManager()

    test_id = f"test-m1-{uuid.uuid4().hex[:6]}"
    t1_id = f"{test_id}-t1"
    t2_id = f"{test_id}-t2"

    mission = await manager.create_mission(
        mission_id=test_id,
        title="Test Mission",
        description="Verify state transitions",
        platform="discord",
        channel_id="chan-123",
        workspace_path=f"./workspaces/{test_id}",
    )

    assert mission["id"] == test_id
    assert mission["status"] == MissionStatus.PENDING.value
    assert mission["progress"] == 0

    # Add tasks
    tasks = [
        {"id": t1_id, "title": "Task 1", "agent": AgentRole.ARCHITECT.value, "dependencies": []},
        {"id": t2_id, "title": "Task 2", "agent": AgentRole.DEVELOPER.value, "dependencies": [t1_id]},
    ]
    await manager.add_tasks(test_id, tasks)

    # Complete task 1
    await manager.update_task_status(test_id, t1_id, TaskStatus.COMPLETED, output={"spec": "done"})
    cached = manager.get_mission(test_id)
    assert cached["tasks"][t1_id]["status"] == TaskStatus.COMPLETED.value
    assert cached["progress"] == 50

    # Complete task 2
    await manager.update_task_status(test_id, t2_id, TaskStatus.COMPLETED, output={"code": "done"})
    cached = manager.get_mission(test_id)
    assert cached["progress"] == 100
