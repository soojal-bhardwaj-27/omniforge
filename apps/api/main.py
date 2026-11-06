import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database.session import init_db
from apps.api.routes import missions, events, switch, connectors

import asyncio
from apps.api.dependencies import get_orchestrator, set_live_bridge
from integrations.live_bridges.telegram_bridge import TelegramLiveBridge
from integrations.live_bridges.discord_bridge import DiscordLiveBridge

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite/PostgreSQL schema on application start
    await init_db()
    os.makedirs("./workspaces", exist_ok=True)

    orchestrator = get_orchestrator()
    # Hydrate state from persistent database
    await orchestrator.state_manager.hydrate_from_db()

    tg_bridge = TelegramLiveBridge(orchestrator)
    discord_bridge = DiscordLiveBridge(orchestrator)
    
    # Register live bridges for genuine health status reporting
    set_live_bridge("telegram", tg_bridge)
    set_live_bridge("discord", discord_bridge)

    tg_task = asyncio.create_task(tg_bridge.start())
    discord_task = asyncio.create_task(discord_bridge.start())

    yield

    await tg_bridge.stop()
    await discord_bridge.stop()
    set_live_bridge("telegram", None)
    set_live_bridge("discord", None)
    tg_task.cancel()
    discord_task.cancel()


app = FastAPI(
    title="OMNIFORGE API Gateway",
    description="Autonomous AI Workforce Orchestration Platform · Powered by Switch",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration: strict explicit origins
allowed_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000")
allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Security headers middleware for preview and API
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/preview"):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self' 'unsafe-inline' 'unsafe-eval' https: data:; "
            "img-src 'self' data: https:; "
            "style-src 'self' 'unsafe-inline' https:; "
            "font-src 'self' data: https:; "
            "frame-ancestors 'self';"
        )
    return response

# Register endpoints
app.include_router(missions.router)
app.include_router(events.router)
app.include_router(switch.router)
app.include_router(connectors.router)

# Health Check Endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "OMNIFORGE Core Engine",
        "version": "1.0.0",
        "switch_gateway": "connected",
    }


# Glowing Forge Favicon Endpoint
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
      <defs>
        <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#5865F2"/>
          <stop offset="100%" stop-color="#00F0FF"/>
        </linearGradient>
      </defs>
      <rect width="100" height="100" rx="24" fill="#0e101c"/>
      <path d="M50 18 L76 33 L76 67 L50 82 L24 67 L24 33 Z" fill="none" stroke="url(#g)" stroke-width="6"/>
      <circle cx="50" cy="50" r="14" fill="url(#g)"/>
    </svg>"""
    return Response(content=svg, media_type="image/svg+xml")

# Mount workspaces for direct browser preview of generated apps
if os.path.exists("./workspaces"):
    app.mount("/preview", StaticFiles(directory="./workspaces", html=True), name="preview")

# Mount Planet sneaker landing page at /planet
planet_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "planet"))
if os.path.exists(planet_dir):
    app.mount("/planet", StaticFiles(directory=planet_dir, html=True), name="planet")

# Mount Mission Control dashboard at root /
dashboard_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dashboard"))
if os.path.exists(dashboard_dir):
    app.mount("/", StaticFiles(directory=dashboard_dir, html=True), name="dashboard")



