from typing import Dict, Any, List
from core.agents.base import BaseAgent, AgentResult
from core.execution.sandbox import ExecutionSandbox
from core.events.publisher import EventPublisher
from integrations.coding_agents import get_coding_agent_driver


class DeveloperAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="DEVELOPER",
            role_description="Software implementation, file synthesis, code generation, and bug fixing.",
        )
        self.coding_driver = get_coding_agent_driver()

    async def execute(
        self,
        task_id: str,
        mission_title: str,
        task_title: str,
        task_context: Dict[str, Any],
        sandbox: ExecutionSandbox,
        publisher: EventPublisher,
    ) -> AgentResult:
        await publisher.task_started(task_id, self.name, f"Synthesizing implementation for '{task_title}'")

        # Retrieve architecture and design specs from prior tasks in DAG
        arch_spec = task_context.get("architecture", {})
        design_spec = task_context.get("design", {})

        # Execute coding agent
        files_to_create = await self.coding_driver.generate_project(arch_spec, design_spec)

        created_artifacts: List[str] = []
        for file_info in files_to_create:
            rel_path = file_info["path"]
            content = file_info["content"]

            written = await sandbox.write_file(rel_path, content)
            created_artifacts.append(written["rel_path"])
            await publisher.file_created(written["rel_path"], self.name, task_id)

        await publisher.task_completed(
            task_id,
            self.name,
            f"Implementation complete: {len(created_artifacts)} code files successfully written to workspace.",
            artifacts=created_artifacts,
        )

        return AgentResult(
            task_id=task_id,
            agent=self.name,
            status="completed",
            output={"files_written": created_artifacts, "count": len(created_artifacts)},
            artifacts=created_artifacts,
        )
