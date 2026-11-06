import os
import httpx
import logging
from collections import deque
from typing import Dict, Any, Optional

logger = logging.getLogger("omniforge.switch")


class SwitchGatewayAdapter:
    """Official Switch Integration Adapter.
    Bridges Discord, Telegram, and team communication platforms with OMNIFORGE.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        gateway_url: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("SWITCH_API_KEY", "")
        self.gateway_url = gateway_url or os.getenv("SWITCH_GATEWAY_URL", "https://api.switch.ai/v1")
        self.client = httpx.AsyncClient(timeout=15.0)
        self.message_history = deque(maxlen=200)

    def get_recent_messages(self, limit: int = 50):
        return list(self.message_history)[-limit:]

    def parse_incoming_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parses webhook payloads originating from Switch Discord/Slack bots."""
        # Handles standard Switch webhook payload structure
        event_type = payload.get("event", "message_created")
        msg_data = payload.get("data", payload)

        content = msg_data.get("content", "").strip()
        channel_id = msg_data.get("channel_id", "")
        user_id = msg_data.get("author", {}).get("id", msg_data.get("user_id", ""))
        platform = payload.get("platform", "discord")

        # Strip bot mention if present
        clean_prompt = content
        for mention in ["<@OMNIFORGE>", "@OMNIFORGE", "OMNIFORGE,"]:
            if clean_prompt.startswith(mention):
                clean_prompt = clean_prompt[len(mention):].strip()

        return {
            "event_type": event_type,
            "prompt": clean_prompt,
            "raw_content": content,
            "channel_id": str(channel_id),
            "user_id": str(user_id),
            "platform": platform,
            "metadata": msg_data,
        }

    async def send_message(
        self,
        channel_id: str,
        message: str,
        embed: Optional[Dict[str, Any]] = None,
        platform: str = "discord",
    ) -> bool:
        """Sends a notification or report back to the team chat via Switch Gateway."""
        import datetime
        self.message_history.append({
            "platform": platform,
            "channel_id": channel_id,
            "message": message,
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
            "embed": embed,
        })
        # Direct delivery to live Telegram bot if token and numeric chat_id present
        tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        if platform == "telegram" and tg_token and channel_id and (channel_id.isdigit() or (channel_id.startswith("-") and channel_id[1:].isdigit())):
            try:
                await self.client.post(
                    f"https://api.telegram.org/bot{tg_token}/sendMessage",
                    json={"chat_id": int(channel_id), "text": message}
                )
            except Exception as e:
                logger.debug(f"Direct Telegram send note: {e}")

        # Direct delivery to live Discord channel if token and numeric channel_id present
        discord_token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
        if platform == "discord" and discord_token and channel_id and channel_id.isdigit():
            try:
                headers = {"Authorization": f"Bot {discord_token}", "Content-Type": "application/json"}
                await self.client.post(
                    f"https://discord.com/api/v10/channels/{channel_id}/messages",
                    headers=headers,
                    json={"content": message}
                )
            except Exception as e:
                logger.debug(f"Direct Discord send note: {e}")

        if not self.api_key:
            # Running in local / simulated mode when offline
            logger.info(f"[SWITCH LOCAL SIMULATOR -> {platform}:{channel_id}]:\n{message}")
            return True

        endpoint = f"{self.gateway_url}/channels/{channel_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "content": message,
            "embed": embed,
            "platform": platform,
        }

        try:
            resp = await self.client.post(endpoint, json=body, headers=headers)
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to deliver message via Switch Gateway: {e}")
            return False

    async def send_mission_report(self, channel_id: str, report_markdown: str, platform: str = "discord") -> bool:
        """Publishes the finalized OMNIFORGE Mission Report to Discord."""
        return await self.send_message(channel_id, report_markdown, platform=platform)
