import logging
from typing import Dict, Any
from integrations.switch.adapter import SwitchGatewayAdapter
from core.orchestrator.commander import CommanderOrchestrator
from core.orchestrator.evaluator import MissionEvaluator
from core.events.event_bus import global_event_bus, MissionEvent

logger = logging.getLogger("omniforge.switch.router")


class SwitchMessageRouter:
    """Routes incoming Switch webhook events to Commander workflows with
    evaluation, clarification gates, and live milestone streaming.
    """

    def __init__(self, orchestrator: CommanderOrchestrator, switch_adapter: SwitchGatewayAdapter):
        self.orchestrator = orchestrator
        self.switch_adapter = switch_adapter
        self.evaluator = MissionEvaluator()

        # Register event listener to stream updates to chat platform
        global_event_bus.register_callback(self._handle_mission_event)

    async def _handle_mission_event(self, event: MissionEvent):
        """Streams key milestones back to bridged channel."""
        priority_events = ["mission_started", "task_completed", "test_passed", "test_failed", "approval_requested"]
        if event.event_type in priority_events:
            mission = self.orchestrator.state_manager.get_mission(event.mission_id)
            if mission and mission.get("channel_id"):
                channel_id = mission["channel_id"]
                platform = mission.get("platform", "discord")
                formatted = f"**[{event.agent}]** {event.message}"
                await self.switch_adapter.send_message(channel_id, formatted, platform=platform)

    async def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Entry point for incoming Switch webhooks."""
        parsed = self.switch_adapter.parse_incoming_message(payload)
        prompt = parsed["prompt"]
        channel_id = parsed["channel_id"]
        platform = parsed["platform"]
        user_id = parsed["user_id"]

        if not prompt:
            return {"status": "ignored", "reason": "Empty prompt"}

        # Check for cancel
        if prompt.lower() == "cancel":
            if self.evaluator.get_pending(channel_id, user_id):
                self.evaluator.clear_pending(channel_id, user_id)
                await self.switch_adapter.send_message(channel_id, "🛑 Mission evaluation cancelled.", platform=platform)
            return {"status": "cancelled"}

        # Check if this channel has a pending evaluation awaiting confirmation
        pending = self.evaluator.get_pending(channel_id, user_id)
        if pending:
            if self.evaluator.is_confirmation(prompt):
                enriched_prompt = pending["original_prompt"]
                ack_note = "Proceeding with recommended architecture specifications."
            else:
                enriched_prompt = f"{pending['original_prompt']} [Custom preferences: {prompt}]"
                ack_note = f"Applying your custom preferences: *\"{prompt}\"*"

            self.evaluator.clear_pending(channel_id, user_id)

            ack_message = (
                f"⚡ **OMNIFORGE Specifications Locked & Confirmed!**\n"
                f"• {ack_note}\n\n"
                f"Assembling AI workforce: `ARCHITECT` · `DESIGNER` · `DEVELOPER` · `TESTER` · `SECURITY`...\n"
                f"Streaming live progress updates below:"
            )
            await self.switch_adapter.send_message(channel_id, ack_message, platform=platform)

            # Launch mission
            result = await self.orchestrator.launch_mission(
                prompt=enriched_prompt,
                platform=platform,
                channel_id=channel_id,
                user_id=user_id,
            )

            # Final report
            passed = result["mission"]["status"] == "completed"
            report_markdown = (
                f"**OMNIFORGE MISSION DELIVERED: `{result['mission']['id']}`**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• **Status:** {'✅ VERIFIED & COMPLETED' if passed else '❌ FAILED'}\n"
                f"• **Deliverables:** {result['workspace_summary']['total_files']} files synthesized\n"
                f"• **Design Standard:** `ui-skills` Compliant (Zero AI Slop)\n"
                f"• **Live Web Preview:** http://localhost:8000/preview/{result['mission']['id']}/index.html\n"
            )
            await self.switch_adapter.send_message(channel_id, report_markdown, platform=platform)
            return {"status": "success", "mission_id": result["mission"]["id"]}

        # If NO pending evaluation: Evaluate first and ask clarifying questions
        eval_data = self.evaluator.evaluate_intent(prompt)
        self.evaluator.store_pending(channel_id, user_id, eval_data)

        clarification_msg = self.evaluator.format_clarification_message(eval_data, user_id)
        await self.switch_adapter.send_message(channel_id, clarification_msg, platform=platform)

        return {
            "status": "clarification_requested",
            "domain": eval_data["domain"],
            "questions": eval_data["questions"],
        }
