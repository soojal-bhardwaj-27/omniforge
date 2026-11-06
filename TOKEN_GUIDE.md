# 🚀 OMNIFORGE / RIO DevTeam — Multi-Platform Setup Guide
### Telegram + Discord + Slack + Switch AI Integration

---

## ⚡ Zero-Token Mode (Ready Out-of-the-Box!)
You **do not need any bot tokens** to run, demo, or grade this hackathon project.

OMNIFORGE is equipped with a **Zero-Token Multi-Platform Simulator**:
- **Simulate Telegram:** Sends commands through the `@RIO_DevTeam_bot` bridge into the `#rio-devteam` shared room.
- **Simulate Discord:** Triggers the Discord bot bridge and echoes back planning, code, and verification reports.
- **Simulate Slack:** Simulates inbound slash commands and Slack app events.
- **3D Mission Control (`http://localhost:8000`):** Features one-click buttons to trigger any platform, switch themes, watch live agent telemetry, and view generated deliverables.

---

## 🔑 How to Add Real Live Bot Tokens (Optional)

Whenever you are ready to connect real bots, simply open `.env` and fill in:

### 1. Telegram Bot Token (30 seconds)
1. Open Telegram and search for [`@BotFather`](https://t.me/BotFather).
2. Send `/newbot`.
3. Give your bot a name (e.g., `OMNIFORGE Bot`) and a username (e.g., `omniforge_dev_bot`).
4. Copy the API token provided and paste it in `.env`:
   ```env
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
   ```

### 2. Discord Bot Token (1 minute)
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click **New Application** $\rightarrow$ Name it `OMNIFORGE`.
3. Go to the **Bot** tab on the left $\rightarrow$ Click **Reset Token** $\rightarrow$ Copy the token.
4. Enable **Message Content Intent** under Privileged Gateway Intents.
5. Paste into `.env`:
   ```env
   DISCORD_BOT_TOKEN=MTAyND...
   ```
6. To invite the bot to your server: Go to **OAuth2 $\rightarrow$ URL Generator**, select `bot` + `Send Messages`, and open the generated link in your browser.

### 3. Slack App Token (1 minute)
1. Go to [Slack API Apps](https://api.slack.com/apps) $\rightarrow$ Click **Create New App** $\rightarrow$ **From scratch**.
2. Go to **Incoming Webhooks** $\rightarrow$ Toggle **Activate Incoming Webhooks** to **On**.
3. Click **Add New Webhook to Workspace** $\rightarrow$ Choose a channel (e.g., `#devteam`).
4. Copy the Webhook URL or Bot Token and paste into `.env`:
   ```env
   SLACK_BOT_TOKEN=xoxb-...
   ```

---

## 🐳 Running with Docker Desktop

With Docker Desktop installed and running:
```bash
# Start full OMNIFORGE stack with Postgres & Redis
docker compose up -d

# Check running containers
docker compose ps

# View live logs
docker compose logs -f omniforge
```

Access:
- **Mission Control Dashboard:** `http://localhost:8000`
- **3D Sneaker Visualizer [Planet]:** `http://localhost:8000/planet`
- **Workspace Deliverables Preview:** `http://localhost:8000/preview`
- **Interactive REST API Docs:** `http://localhost:8000/docs`
