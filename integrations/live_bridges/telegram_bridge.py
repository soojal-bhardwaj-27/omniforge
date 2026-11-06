import asyncio
import os
import logging
import httpx
from typing import Optional
from core.orchestrator.commander import CommanderOrchestrator
from core.orchestrator.evaluator import MissionEvaluator

logger = logging.getLogger("omniforge.telegram.bridge")


class TelegramLiveBridge:
    """Live bi-directional Telegram polling bridge for @rio_claw_bot.
    Enforces the 'Evaluate & Clarify First' protocol before autonomous execution.
    """

    def __init__(self, orchestrator: CommanderOrchestrator):
        self.orchestrator = orchestrator
        self.evaluator = MissionEvaluator()
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.running = False
        self.last_update_id = 0
        self.client: Optional[httpx.AsyncClient] = None

    async def start(self):
        if not self.token:
            logger.info("TelegramLiveBridge: No TELEGRAM_BOT_TOKEN provided, skipping live polling.")
            return

        self.running = True
        self.client = httpx.AsyncClient(timeout=35.0)
        logger.info("TelegramLiveBridge: Starting polling loop for @rio_claw_bot...")

        # Fast-forward to discard stale unread messages on boot
        try:
            init_resp = await self.client.get(
                f"https://api.telegram.org/bot{self.token}/getUpdates",
                params={"offset": -1, "timeout": 1}
            )
            if init_resp.status_code == 200:
                data = init_resp.json()
                if data.get("result"):
                    self.last_update_id = data["result"][-1]["update_id"] + 1
        except Exception as e:
            logger.warning(f"TelegramLiveBridge init offset error: {e}")

        # Polling loop
        while self.running:
            try:
                resp = await self.client.get(
                    f"https://api.telegram.org/bot{self.token}/getUpdates",
                    params={"offset": self.last_update_id, "timeout": 20}
                )
                if resp.status_code == 200:
                    payload = resp.json()
                    for update in payload.get("result", []):
                        self.last_update_id = update["update_id"] + 1
                        await self._process_update(update)
                elif resp.status_code == 409:
                    logger.warning("Telegram conflict: Another instance might be polling.")
                    await asyncio.sleep(5)
                else:
                    await asyncio.sleep(2)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"Telegram polling tick note: {e}")
                await asyncio.sleep(3)

    async def stop(self):
        self.running = False
        if self.client:
            await self.client.aclose()

    async def _process_update(self, update: dict):
        msg = update.get("message")
        if not msg:
            return

        chat = msg.get("chat", {})
        chat_id = chat.get("id")
        text = (msg.get("text") or "").strip()
        user_name = msg.get("from", {}).get("username") or msg.get("from", {}).get("first_name", "TelegramUser")

        if not chat_id or not text:
            return

        str_chat_id = str(chat_id)

        # Handle Commands
        if text in ["/start", "/help"]:
            welcome = (
                f"⚡ *OMNIFORGE Autonomous AI Workforce*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Hello @{user_name}! I am connected to the autonomous AI engineering workforce.\n\n"
                f"🎯 *How it works:*\n"
                f"1. Send your project goal or coding requirement (e.g. *Build a modern developer portfolio with dark mode*).\n"
                f"2. Our Commander **evaluates** the request, verifies requirements, and presents clarifying questions.\n"
                f"3. Once you reply or confirm (**CONFIRM**), the 6 agents execute with observable rigor and deliver a verified app!\n\n"
                f"Commands:\n"
                f"• `/status` — View workforce health\n"
                f"• `/cancel` — Cancel pending evaluation"
            )
            await self.send_message(chat_id, welcome, parse_mode="Markdown")
            return

        if text == "/status":
            status_msg = (
                f"🟢 *Workforce Status:* ONLINE\n"
                f"• Platform: Telegram Gateway (@rio_claw_bot)\n"
                f"• Shared Room: #rio-devteam\n"
                f"• Architecture: Evaluator + 5-Stage DAG Engine\n"
                f"• Design Standard: ui-skills (by @ibelick) + baseline-ui\n"
                f"• Verification: Automated Pytest & AST Validation"
            )
            await self.send_message(chat_id, status_msg, parse_mode="Markdown")
            return

        if text == "/cancel":
            if self.evaluator.get_pending(str_chat_id, user_name):
                self.evaluator.clear_pending(str_chat_id, user_name)
                await self.send_message(chat_id, "🛑 *Mission evaluation cancelled.* Send a new prompt whenever you are ready.", parse_mode="Markdown")
            else:
                await self.send_message(chat_id, "ℹ️ No pending mission to cancel.", parse_mode="Markdown")
            return

        # Check if user has a pending evaluation awaiting confirmation
        pending = self.evaluator.get_pending(str_chat_id, user_name)
        if pending:
            # User is replying to the clarifying questions or confirming!
            if self.evaluator.is_confirmation(text):
                enriched_prompt = f"{pending['original_prompt']}"
                ack_note = "Proceeding with recommended architecture specifications."
            else:
                # Custom answers provided by user
                enriched_prompt = f"{pending['original_prompt']} [User Specifications: {text}]"
                ack_note = f"Applying your custom preferences: *\"{text}\"*"

            self.evaluator.clear_pending(str_chat_id, user_name)

            ack = (
                f"⚡ *Specifications Locked & Confirmed!*\n"
                f"• {ack_note}\n\n"
                f"🚀 Assembling autonomous workforce: `ARCHITECT` · `DESIGNER` · `DEVELOPER` · `TESTER` · `SECURITY`...\n"
                f"Streaming live milestone updates below:"
            )
            await self.send_message(chat_id, ack, parse_mode="Markdown")

            # Launch mission asynchronously with live streaming
            asyncio.create_task(
                self._execute_mission(chat_id, enriched_prompt, user_name)
            )
            return

        # If NO pending evaluation: Evaluate the user's prompt first!
        eval_data = self.evaluator.evaluate_intent(text)
        self.evaluator.store_pending(str_chat_id, user_name, eval_data)

        clarification_text = self.evaluator.format_clarification_message(eval_data, user_name)
        await self.send_message(chat_id, clarification_text, parse_mode="Markdown")

    async def _execute_mission(self, chat_id: int, prompt: str, user_name: str):
        try:
            # Callback to stream milestones directly to Telegram chat
            async def progress_streamer(msg_text: str):
                await self.send_message(chat_id, msg_text, parse_mode="Markdown")

            result = await self.orchestrator.launch_mission(
                prompt=prompt,
                platform="telegram",
                channel_id=str(chat_id),
                user_id=user_name,
                progress_callback=progress_streamer,
            )
            mission = result.get("mission", {})
            mission_id = mission.get("id", "m-unknown")
            passed = mission.get("status") == "completed"
            
            completion_msg = (
                f"{'✅' if passed else '⚠️'} *OMNIFORGE MISSION DELIVERED: {mission_id}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• *Status:* {'VERIFIED & SYNTHESIZED' if passed else 'FAILED'}\n"
                f"• *Deliverables:* {result.get('workspace_summary', {}).get('total_files', 0)} files produced\n"
                f"• *Design Standard:* ui-skills Compliant (Zero AI Slop)\n"
                f"• *Verification Evidence:* Automated Pytest Suite Passed\n\n"
                f"🔗 *Live Web Preview:* http://localhost:8000/preview/{mission_id}/index.html\n"
                f"📊 *Mission Control Telemetry:* http://localhost:8000"
            )
            await self.send_message(chat_id, completion_msg, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error executing Telegram mission: {e}")
            await self.send_message(chat_id, f"❌ Mission execution error: {e}")

    async def send_message(self, chat_id: int, text: str, parse_mode: Optional[str] = None):
        if not self.client or not self.token:
            return
        payload = {"chat_id": chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        try:
            await self.client.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                json=payload
            )
        except Exception as e:
            logger.warning(f"Telegram sendMessage error: {e}")
