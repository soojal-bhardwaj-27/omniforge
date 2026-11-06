from typing import Dict, Any
from core.agents.base import BaseAgent, AgentResult
from core.execution.sandbox import ExecutionSandbox
from core.events.publisher import EventPublisher


class ArchitectAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ARCHITECT",
            role_description="Technical architecture, technology selection, and file structure specification.",
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
        await publisher.task_started(task_id, self.name, f"Architecting solution for '{mission_title}'")

        # Architectural specification
        arch_spec = {
            "project_name": mission_title,
            "architecture_type": "Responsive Web Application",
            "framework": "Modern Vanilla JS / HTML5 / CSS3 Grid",
            "components": [
                "Sticky Blurred Navigation Header",
                "High-Impact Dark Hero with Call to Action",
                "3-Column Responsive Features Matrix",
                "Tiered Pricing Comparison Grid",
                "Interactive Mission Consultation Form",
                "Operational Status Footer",
            ],
            "target_files": [
                "index.html",
                "styles.css",
                "app.js",
                "test_suite.py",
            ],
            "dependencies": ["JetBrains Mono font", "Inter font"],
        }

        # Store architecture manifest into workspace
        spec_content = (
            f"# Architecture Specification: {mission_title}\n\n"
            f"- **Framework**: {arch_spec['framework']}\n"
            f"- **Target Files**: {', '.join(arch_spec['target_files'])}\n"
            f"- **Components**: \n"
            + "\n".join(f"  - {c}" for c in arch_spec["components"])
        )
        spec_file = await sandbox.write_file("ARCHITECTURE.md", spec_content)
        await publisher.file_created("ARCHITECTURE.md", self.name, task_id)

        await publisher.task_completed(
            task_id,
            self.name,
            f"Technical architecture defined: {len(arch_spec['target_files'])} target files planned.",
            artifacts=[spec_file["rel_path"]],
        )

        return AgentResult(
            task_id=task_id,
            agent=self.name,
            status="completed",
            output=arch_spec,
            artifacts=[spec_file["rel_path"]],
        )
