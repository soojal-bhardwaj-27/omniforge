import os
from typing import Dict, Any
from core.agents.base import BaseAgent, AgentResult
from core.execution.sandbox import ExecutionSandbox
from core.execution.verification import VerificationEngine
from core.events.publisher import EventPublisher


class TesterAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="TESTER",
            role_description="Quality assurance, automated testing, assertion verification, and error diagnosis.",
        )

    async def execute(
        self,
        task_id: str,
        mission_title: str,
        task_title: str,
        task_context: Dict[str, Any],
        sandbox: ExecutionSandbox,
        publisher: EventPublisher,
    ) -> AgentResult:
        await publisher.task_started(task_id, self.name, "Running automated test suites and sanity verification")

        verification_engine = VerificationEngine(sandbox)

        # Determine expected deliverables dynamically based on workspace contents and context
        context_files = task_context.get("expected_files", [])
        workspace_file_dicts = sandbox.list_files()
        workspace_paths = [f["rel_path"] for f in workspace_file_dicts]
        
        if context_files:
            expected_files = context_files
        elif workspace_paths:
            # Check all workspace files created up to this point (excluding hidden files and markdown reports)
            expected_files = [p for p in workspace_paths if not p.startswith(".") and not p.endswith(".md")]
        else:
            expected_files = ["index.html", "styles.css", "app.js"]

        # Run test commands in sandbox (python -m pytest or python test_suite.py)
        test_commands = []
        if sandbox.file_exists("test_suite.py"):
            test_commands.append("python -m pytest test_suite.py")

        report = await verification_engine.verify_mission(
            mission_id=sandbox.mission_id,
            expected_files=expected_files,
            test_commands=test_commands,
        )

        # Save verification report as an artifact
        report_md = report.to_discord_markdown(mission_title)
        report_file = await sandbox.write_file("VERIFICATION_REPORT.md", report_md)
        await publisher.file_created("VERIFICATION_REPORT.md", self.name, task_id)

        await publisher.test_result(
            passed=report.passed,
            summary=f"{report.passed_checks}/{report.total_checks} checks passed across {report.files_created} files",
            details={
                "total_checks": report.total_checks,
                "passed_checks": report.passed_checks,
                "failed_checks": report.failed_checks,
                "errors": report.errors,
            },
            task_id=task_id,
        )

        status = "completed" if report.passed else "failed"
        return AgentResult(
            task_id=task_id,
            agent=self.name,
            status=status,
            output={
                "passed": report.passed,
                "report_markdown": report_md,
                "passed_checks": report.passed_checks,
                "failed_checks": report.failed_checks,
                "errors": report.errors,
            },
            artifacts=[report_file["rel_path"]],
            error_message="; ".join(report.errors) if not report.passed else None,
        )
