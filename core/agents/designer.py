from typing import Dict, Any
from core.agents.base import BaseAgent, AgentResult
from core.execution.sandbox import ExecutionSandbox
from core.events.publisher import EventPublisher


class DesignerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="DESIGNER",
            role_description="UI/UX design, visual tokens, responsive layout, and design system specifications.",
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
        await publisher.task_started(task_id, self.name, "Formulating UI/UX design tokens and layout")

        design_tokens = {
            "theme": "Dark Developer Cyberpunk",
            "background_color": "#0a0a0f",
            "card_background": "#12131c",
            "primary_color": "#00f0ff",      # Electric cyan
            "secondary_color": "#8b5cf6",    # Electric violet
            "text_primary": "#f3f4f6",
            "text_muted": "#9ca3af",
            "border_radius": "16px",
            "typography": {
                "headings": "Inter, sans-serif",
                "code": "JetBrains Mono, monospace",
            },
            "responsive_breakpoints": {
                "mobile": "640px",
                "tablet": "768px",
                "desktop": "1024px",
            },
        }

        # Write DESIGN_SYSTEM.md into workspace
        design_md = (
            f"# Design System Specification: {mission_title}\n\n"
            f"- **Visual Theme**: {design_tokens['theme']}\n"
            f"- **Primary Color**: `{design_tokens['primary_color']}` (Electric Cyan)\n"
            f"- **Secondary Color**: `{design_tokens['secondary_color']}` (Electric Violet)\n"
            f"- **Base Background**: `{design_tokens['background_color']}`\n"
            f"- **Typography**: Headings: {design_tokens['typography']['headings']}, Code: {design_tokens['typography']['code']}\n"
        )
        design_file = await sandbox.write_file("DESIGN_SYSTEM.md", design_md)
        await publisher.file_created("DESIGN_SYSTEM.md", self.name, task_id)

        await publisher.task_completed(
            task_id,
            self.name,
            "Design system ready: Cyberpunk dark theme with high-contrast accessibility tokens.",
            artifacts=[design_file["rel_path"]],
        )

        return AgentResult(
            task_id=task_id,
            agent=self.name,
            status="completed",
            output=design_tokens,
            artifacts=[design_file["rel_path"]],
        )
