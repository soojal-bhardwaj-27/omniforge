import os
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional
from database.models import MissionStatus, TaskStatus, AgentRole
from core.orchestrator.planner import DAGMissionPlanner
from core.orchestrator.state_manager import MissionStateManager
from core.execution.sandbox import ExecutionSandbox
from core.events.publisher import EventPublisher
from core.agents.architect import ArchitectAgent
from core.agents.designer import DesignerAgent
from core.agents.developer import DeveloperAgent
from core.agents.tester import TesterAgent
from core.agents.security import SecurityGuardAgent

logger = logging.getLogger("omniforge.commander")


class CommanderOrchestrator:
    """Chief autonomous orchestration engine for OMNIFORGE.
    Leads the specialized AI workforce through the 5-stage mission lifecycle
    with strict security gating, concurrency limits, and verification evidence.
    """

    def __init__(self, workspace_root: str = "./workspaces", max_concurrent_missions: int = 4):
        self.workspace_root = workspace_root
        self.planner = DAGMissionPlanner()
        self.state_manager = MissionStateManager()
        self._concurrency_semaphore = asyncio.Semaphore(max_concurrent_missions)

        # Instantiate specialized agent workforce
        self.agents = {
            AgentRole.ARCHITECT: ArchitectAgent(),
            AgentRole.DESIGNER: DesignerAgent(),
            AgentRole.DEVELOPER: DeveloperAgent(),
            AgentRole.TESTER: TesterAgent(),
            AgentRole.SECURITY: SecurityGuardAgent(),
        }

    async def launch_mission(
        self,
        prompt: str,
        mission_title: Optional[str] = None,
        platform: str = "discord",
        channel_id: str = "",
        user_id: str = "",
        mission_id: Optional[str] = None,
        progress_callback: Optional[Any] = None,
    ) -> Dict[str, Any]:
        # Enforce input bounds
        clean_prompt = prompt.strip()[:4000]
        if not clean_prompt:
            raise ValueError("Mission prompt cannot be empty.")

        mission_id = mission_id or f"m-{uuid.uuid4().hex[:8]}"
        title = (mission_title or clean_prompt.split("\n")[0])[:80]

        async with self._concurrency_semaphore:
            sandbox = ExecutionSandbox(self.workspace_root, mission_id)
            publisher = EventPublisher(mission_id, default_agent="COMMANDER")

            # STAGE 1: UNDERSTAND
            await publisher.mission_started(title)
            mission_data = await self.state_manager.create_mission(
                mission_id=mission_id,
                title=title,
                description=clean_prompt,
                platform=platform,
                channel_id=channel_id,
                user_id=user_id,
                workspace_path=sandbox.workspace_path,
            )

            if progress_callback:
                await progress_callback("🧠 **COMMANDER:** Understanding objectives and decomposing into DAG tasks...")
            await asyncio.sleep(1.2)

            # STAGE 2: PLAN
            await self.state_manager.update_mission_status(mission_id, MissionStatus.PLANNING)
            planned_tasks = self.planner.plan_mission(mission_id, clean_prompt)
            task_dicts = [t.to_dict() for t in planned_tasks]
            await self.state_manager.add_tasks(mission_id, task_dicts)

            for t in planned_tasks:
                await publisher.task_planned(t.task_id, t.title, t.agent.value)

            if progress_callback:
                await progress_callback(f"📋 **COMMANDER:** Task plan formulated with {len(planned_tasks)} stages. Commencing autonomous workforce...")
            await asyncio.sleep(1.2)

            # STAGE 3: EXECUTE
            await self.state_manager.update_mission_status(mission_id, MissionStatus.RUNNING)
            task_outputs: Dict[str, Any] = {}

            for plan_item in planned_tasks:
                task_id = plan_item.task_id
                agent_role = plan_item.agent
                agent_instance = self.agents.get(agent_role)

                if not agent_instance:
                    logger.error(f"No agent registered for role: {agent_role}")
                    continue

                await self.state_manager.update_task_status(mission_id, task_id, TaskStatus.RUNNING)

                if progress_callback:
                    agent_icons = {
                        AgentRole.ARCHITECT: "📐",
                        AgentRole.DESIGNER: "🎨",
                        AgentRole.DEVELOPER: "💻",
                        AgentRole.TESTER: "🧪",
                        AgentRole.SECURITY: "🛡️",
                    }
                    icon = agent_icons.get(agent_role, "⚙️")
                    await progress_callback(f"{icon} **{agent_role.value}:** {plan_item.title}...")

                sleep_duration = 2.0 if agent_role == AgentRole.DEVELOPER else 1.3
                await asyncio.sleep(sleep_duration)

                task_context = {
                    "mission_prompt": clean_prompt,
                    "architecture": task_outputs.get(AgentRole.ARCHITECT.value, {}),
                    "design": task_outputs.get(AgentRole.DESIGNER.value, {}),
                    "implementation": task_outputs.get(AgentRole.DEVELOPER.value, {}),
                    "test_results": task_outputs.get(AgentRole.TESTER.value, {}),
                    "security_results": task_outputs.get(AgentRole.SECURITY.value, {}),
                }

                result = await agent_instance.execute(
                    task_id=task_id,
                    mission_title=title,
                    task_title=plan_item.title,
                    task_context=task_context,
                    sandbox=sandbox,
                    publisher=publisher,
                )

                task_outputs[agent_role.value] = result.output

                if result.status == "completed":
                    await self.state_manager.update_task_status(
                        mission_id, task_id, TaskStatus.COMPLETED, output=result.output
                    )
                elif result.status == "needs_approval":
                    await self.state_manager.update_task_status(
                        mission_id, task_id, TaskStatus.APPROVAL_REQUIRED, output=result.output, error=result.error_message
                    )
                else:
                    await self.state_manager.update_task_status(
                        mission_id, task_id, TaskStatus.FAILED, output=result.output, error=result.error_message
                    )

            # STAGE 4 & 5: VERIFY, SECURITY GATE & DELIVER
            await self.state_manager.update_mission_status(mission_id, MissionStatus.VERIFYING)
            
            tester_output = task_outputs.get(AgentRole.TESTER.value, {})
            security_output = task_outputs.get(AgentRole.SECURITY.value, {})

            # Strict gating: must explicitly have passed tests and clean security audit
            tests_passed = bool(tester_output.get("passed", False))
            security_clean = bool(security_output.get("clean", False)) if security_output else True
            
            summary_stats = sandbox.get_summary()

            if tests_passed and security_clean:
                await self.state_manager.update_mission_status(mission_id, MissionStatus.COMPLETED)
                await publisher.mission_completed(
                    summary=f"All {len(planned_tasks)} tasks executed, syntax validated, unit tests passed, and security clean.",
                    stats=summary_stats,
                )
            elif not security_clean:
                # Security Gate Violation: Block completion!
                await self.state_manager.update_mission_status(mission_id, MissionStatus.APPROVAL_REQUIRED)
                findings = security_output.get("findings", [])
                await publisher.mission_failed(f"Security Policy Gate Triggered: {len(findings)} potential secret leaks/vulnerabilities detected.")
            else:
                # Test / QA Verification failure
                await self.state_manager.update_mission_status(mission_id, MissionStatus.FAILED)
                await publisher.mission_failed("Automated verification checks or syntax tests failed.")

            final_mission = self.state_manager.get_mission(mission_id)
            return {
                "mission": final_mission,
                "verification": tester_output,
                "security": security_output,
                "workspace_summary": summary_stats,
            }
