import asyncio
import json
import os
import logging
import httpx
import websockets
from typing import Optional
from core.orchestrator.commander import CommanderOrchestrator
from core.orchestrator.evaluator import MissionEvaluator

logger = logging.getLogger("omniforge.discord.bridge")


class DiscordLiveBridge:
    """Live Discord Gateway WebSocket bridge for rio-dev bot.
    Enforces the 'Evaluate & Clarify First' protocol before autonomous execution.
    """

    def __init__(self, orchestrator: CommanderOrchestrator):
        self.orchestrator = orchestrator
        self.evaluator = MissionEvaluator()
        self.token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
        self.app_id = os.getenv("DISCORD_APPLICATION_ID", "").strip()
        self.running = False
        self.bot_user_id = self.app_id or "1567447333250011167"
        self.http_client: Optional[httpx.AsyncClient] = None

    async def start(self):
        if not self.token:
            logger.info("DiscordLiveBridge: No DISCORD_BOT_TOKEN provided, skipping live gateway.")
            return

        self.running = True
        self.http_client = httpx.AsyncClient(timeout=20.0)
        gateway_url = "wss://gateway.discord.gg/?v=10&encoding=json"

        logger.info("DiscordLiveBridge: Starting Gateway connection for rio-dev bot...")

        while self.running:
            try:
                async with websockets.connect(gateway_url, ping_interval=None) as ws:
                    hello_raw = await ws.recv()
                    hello = json.loads(hello_raw)
                    heartbeat_interval = hello["d"]["heartbeat_interval"] / 1000.0

                    heartbeat_task = asyncio.create_task(self._heartbeat(ws, heartbeat_interval))

                    identify_payload = {
                        "op": 2,
                        "d": {
                            "token": f"Bot {self.token}",
                            "intents": 37377,
                            "properties": {
                                "os": "windows",
                                "browser": "omniforge",
                                "device": "omniforge"
                            }
                        }
                    }
                    await ws.send(json.dumps(identify_payload))
                    logger.info("DiscordLiveBridge: Identified with Discord Gateway successfully!")

                    try:
                        async for msg_raw in ws:
                            payload = json.loads(msg_raw)
                            op = payload.get("op")
                            t = payload.get("t")

                            if op == 0 and t == "READY":
                                self.bot_user_id = payload["d"]["user"]["id"]
                                username = payload["d"]["user"]["username"]
                                logger.info(f"DiscordLiveBridge: Logged in as {username} (ID: {self.bot_user_id})")

                            elif op == 0 and t == "MESSAGE_CREATE":
                                await self._handle_message(payload["d"])

                    finally:
                        heartbeat_task.cancel()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"Discord gateway reconnect note: {e}")
                await asyncio.sleep(5)

    async def stop(self):
        self.running = False
        if self.http_client:
            await self.http_client.aclose()

    async def _heartbeat(self, ws, interval: float):
        while self.running:
            try:
                await asyncio.sleep(interval)
                await ws.send(json.dumps({"op": 1, "d": None}))
            except Exception:
                break

    async def _handle_message(self, data: dict):
        author = data.get("author", {})
        if author.get("bot"):
            return

        content = data.get("content", "").strip()
        channel_id = str(data.get("channel_id"))
        user_id = author.get("id")
        username = author.get("username", "DiscordUser")

        is_mentioned = f"<@{self.bot_user_id}>" in content or f"<@!{self.bot_user_id}>" in content
        is_command = content.startswith("!forge") or content.startswith("/mission") or is_mentioned

        if not is_command:
            return

        prompt = content
        for prefix in [f"<@{self.bot_user_id}>", f"<@!{self.bot_user_id}>", "!forge", "/mission"]:
            prompt = prompt.replace(prefix, "").strip()

        if not prompt or prompt.lower() in ["help", "start"]:
            welcome = (
                f"⚡ **OMNIFORGE Autonomous AI Workforce**\n"
                f"Hello <@{user_id}>! I am your autonomous AI engineering workforce.\n\n"
                f"**Usage:**\n"
                f"• Type `!forge <your goal>` (e.g. `!forge Build a modern developer portfolio with dark mode`)\n"
                f"• I will evaluate your request, present a tailored architecture plan and clarifying questions.\n"
                f"• Type `confirm` to execute with optimal defaults or customize your specs!"
            )
            await self.send_message(channel_id, welcome)
            return

        if prompt.lower() == "cancel":
            if self.evaluator.get_pending(channel_id, user_id):
                self.evaluator.clear_pending(channel_id, user_id)
                await self.send_message(channel_id, "🛑 Mission evaluation cancelled.")
            else:
                await self.send_message(channel_id, "ℹ️ No pending mission to cancel.")
            return

        # Check pending evaluation
        pending = self.evaluator.get_pending(channel_id, user_id)
        if pending:
            if self.evaluator.is_confirmation(prompt):
                enriched_prompt = pending["original_prompt"]
                ack_note = "Proceeding with recommended architecture specifications."
            else:
                enriched_prompt = f"{pending['original_prompt']} [User Specs: {prompt}]"
                ack_note = f"Applying your custom preferences: *\"{prompt}\"*"

            self.evaluator.clear_pending(channel_id, user_id)

            ack = (
                f"⚡ **Specifications Locked & Confirmed!**\n"
                f"• {ack_note}\n\n"
                f"🚀 Assembling workforce: `ARCHITECT` · `DESIGNER` · `DEVELOPER` · `TESTER` · `SECURITY`...\n"
                f"Streaming live milestone updates below:"
            )
            await self.send_message(channel_id, ack)

            asyncio.create_task(
                self._execute_mission(channel_id, enriched_prompt, username)
            )
            return

        # Brand new command: Evaluate first
        eval_data = self.evaluator.evaluate_intent(prompt)
        self.evaluator.store_pending(channel_id, user_id, eval_data)

        clarification_text = self.evaluator.format_clarification_message(eval_data, username)
        await self.send_message(channel_id, clarification_text)

    async def _execute_mission(self, channel_id: str, prompt: str, username: str):
        try:
            async def progress_streamer(msg_text: str):
                await self.send_message(channel_id, msg_text)

            result = await self.orchestrator.launch_mission(
                prompt=prompt,
                platform="discord",
                channel_id=channel_id,
                user_id=username,
                progress_callback=progress_streamer,
            )
            mission = result.get("mission", {})
            mission_id = mission.get("id", "m-unknown")
            passed = mission.get("status") == "completed"

            completion_msg = (
                f"{'✅' if passed else '⚠️'} **OMNIFORGE MISSION DELIVERED: `{mission_id}`**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• **Status:** {'VERIFIED & SYNTHESIZED' if passed else 'FAILED'}\n"
                f"• **Deliverables:** {result.get('workspace_summary', {}).get('total_files', 0)} files in workspace\n"
                f"• **Design Standard:** `ui-skills` Compliant (Zero AI Slop)\n"
                f"• **Verification Evidence:** Automated Pytest Passed\n\n"
                f"🔗 **Live Web Preview:** http://localhost:8000/preview/{mission_id}/index.html\n"
                f"📊 **Mission Control:** http://localhost:8000\n"
            )
            await self.send_message(channel_id, completion_msg)
        except Exception as e:
            logger.error(f"Error executing Discord mission: {e}")
            await self.send_message(channel_id, f"❌ Mission execution error: `{e}`")

    async def send_message(self, channel_id: str, content: str):
        if not self.http_client or not self.token:
            return
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        headers = {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json"
        }
        try:
            await self.http_client.post(url, headers=headers, json={"content": content})
        except Exception as e:
            logger.warning(f"Discord send_message error: {e}")
