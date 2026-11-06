# OMNIFORGE — Autonomous AI Workforce
### Flip the Switch Hackathon | Powered by Switch AI

> **One Command. Infinite Execution.**
> *Your AI team. Your instructions. Work gets done.*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Switch](https://img.shields.io/badge/Platform-Switch%20AI-00f0ff.svg)](https://switch.ai)
[![Integration: Discord](https://img.shields.io/badge/Integration-Discord%20Bot-5865F2.svg)](https://discord.com)
[![Integration: Telegram](https://img.shields.io/badge/Integration-Telegram%20Bot-24A1DE.svg)](https://telegram.org)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)

---

## ⚡ Executive Summary

Modern AI chatbots generate text, but they don't take **ownership** of delivering real software. You still have to coordinate tools, write code, run tests, fix broken dependencies, and verify deliverables.

**OMNIFORGE** transforms your messaging channels (Discord, Slack, Telegram) into an autonomous software engineering workforce powered by **Switch AI**. When you assign a mission in Discord, OMNIFORGE doesn't just chat—it plans a dependency-aware Directed Acyclic Graph (DAG), delegates tasks to specialized agent roles, synthesizes code inside an isolated sandbox, runs automated unit tests, and delivers mathematically verifiable proof of completion back to your team.

---

## 🧠 The 6 Specialized Agent Roles

Instead of one generic AI model attempting everything, OMNIFORGE organizes work into a coordinated workforce:

| Agent | Responsibility | Output Artifact |
|---|---|---|
| **🧠 COMMANDER** | Chief orchestration, DAG planning, progress tracking, Discord delivery | `DAG Task Plan`, Final Report |
| **📐 ARCHITECT** | System architecture, tech stack selection, component mapping | `ARCHITECTURE.md` |
| **🎨 DESIGNER** | UI/UX visual design system, electric color tokens, responsive layout | `DESIGN_SYSTEM.md` |
| **💻 DEVELOPER** | Implementation via Hybrid Coding Adapter (OpenCode/Codex), code synthesis | Production Code (`.html`, `.css`, `.js`, etc.) |
| **🧪 TESTER** | Quality assurance, AST syntax validation, automated unit test suites | `test_suite.py`, `VERIFICATION_REPORT.md` |
| **🛡️ SECURITY** | Permission gate (Levels 0–7), secret leak detection, command audit | `SECURITY_AUDIT.md` |

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    User([Human Developer on Discord]) -->|@OMNIFORGE build landing page| Switch[Switch AI Gateway]
    Switch -->|Webhook Payload| API[OMNIFORGE FastAPI Gateway]
    
    subgraph Core Orchestration
        API --> Commander[Agent: COMMANDER]
        Commander --> Planner[DAG Mission Planner]
        Planner --> StateMgr[State Manager & Progress Tracker]
    end

    subgraph Autonomous Workforce
        StateMgr --> Architect[Agent: ARCHITECT]
        StateMgr --> Designer[Agent: DESIGNER]
        StateMgr --> Security[Agent: SECURITY GUARD]
        StateMgr --> Developer[Agent: DEVELOPER]
        StateMgr --> Tester[Agent: TESTER]
    end

    subgraph Sandboxed Execution
        Developer --> Sandbox[(Isolated Workspace Sandbox)]
        Tester --> Verification[Verification Engine: Build & Pytest]
        Verification --> Sandbox
    end

    subgraph Feedback & Mission Control
        Verification -->|Pass/Fail Evidence| Switch
        Switch -->|Final Mission Report| User
        StateMgr -.->|Live WebSocket Events| Dashboard[Mission Control UI]
    end
```

---

## 🔄 The 5-Stage Execution Lifecycle

1. **Stage 1: Understand** — COMMANDER parses the user's natural language objective, requirements, and constraints.
2. **Stage 2: Plan** — Decomposes the mission into an atomic Directed Acyclic Graph (DAG) with explicit task dependencies.
3. **Stage 3: Execute** — Specialized agents execute in order. Upstream design and architecture specs are automatically provided as context to the DEVELOPER agent.
4. **Stage 4: Verify & Self-Heal** — The TESTER executes automated unit tests and syntax validation in the isolated sandbox. If checks fail, errors are fed back for auto-correction.
5. **Stage 5: Deliver** — A verified execution evidence report returns directly to Discord via Switch with file statistics and pass/fail metrics.

---

## 🚀 Quickstart Guide (Run in 60 Seconds)

### 1. Clone & Setup Environment
```bash
git clone https://github.com/soojal-bhardwaj-27/omniforge.git
cd omniforge
cp .env.example .env
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch OMNIFORGE Engine & Mission Control
```bash
python -m uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser to access the live **Mission Control Dashboard**.

---

## 🎮 How to Test the Demo Mission

### Option A: From the Mission Control UI
1. Open `http://localhost:8000`.
2. Click **Dispatch Mission** with the default prompt:
   > *"Build a modern landing page for an AI startup with dark theme, pricing, and automated tests"*
3. Watch the 6 specialized agent cards activate in real time via WebSockets.
4. Inspect the generated deliverable artifacts in the workspace.
5. View the live web preview at `http://localhost:8000/preview/m-<id>/index.html`.

### Option B: Via Discord / Switch Webhook
Send an HTTP POST to `/api/switch/webhook`:
```bash
curl -X POST http://localhost:8000/api/switch/webhook \
  -H "Content-Type: application/json" \
  -d '{"content": "@OMNIFORGE Build a modern landing page for an AI startup", "channel_id": "discord-general", "platform": "discord"}'
```

### Option C: Run the Test Suite
```bash
pytest tests/ -v
```

---

## 🛡️ Security Architecture: 8 Permission Levels

| Level | Action | Permission Policy |
|---|---|---|
| **0** | Read project files | Automatic |
| **1** | Create or modify workspace files | Automatic inside sandbox jail |
| **2** | Run approved unit test suites | Automatic |
| **3** | Install approved dependencies | Restricted |
| **4** | Execute external shell commands | Approval required where risky |
| **5** | Delete files | Explicit human approval required |
| **6** | Deploy to production | Explicit human approval required |
| **7** | Access external credentials | Restricted and strictly audited |

---

## 🏆 Hackathon Alignment: Flip the Switch

- **Why Switch Matters**: Switch acts as the communication nervous system connecting our autonomous AI workforce directly to engineering teams inside Discord.
- **Measurable Accountability**: Zero hallucinated claims. Every mission requires test execution evidence, file verification, and security scanning before delivery.
- **Hybrid Architecture**: Swappable coding drivers (`OpenCode`, `Codex`, and local fallback) guarantee uninterrupted execution under any network condition.
