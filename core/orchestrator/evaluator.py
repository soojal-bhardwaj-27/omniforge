"""OMNIFORGE Mission Evaluator & Clarification Engine.
Analyzes user intent from Telegram/Discord/Slack, detects ambiguities,
asks clarifying questions before execution, and formats tailored mission specs.
Scoped strictly by sender ID with TTL expiration to prevent session takeover.
"""

import time
from typing import Dict, Any, Optional, Tuple, List
import re


class MissionEvaluator:
    """Evaluates inbound mission requests, detects domain/scope,
    and manages clarification dialogs before coding commences.
    Strictly scoped per (channel_id, user_id) with 10-minute TTL.
    """

    def __init__(self, ttl_seconds: int = 600):
        # Maps f"{channel_id}:{user_id}" -> PendingEvaluation
        self.pending_evaluations: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = ttl_seconds

    def _get_key(self, channel_id: str, user_id: str = "") -> str:
        # If user_id is provided, scope to that user in that channel
        uid = str(user_id).strip()
        cid = str(channel_id).strip()
        return f"{cid}:{uid}" if uid else cid

    def get_pending(self, channel_id: str, user_id: str = "") -> Optional[Dict[str, Any]]:
        key = self._get_key(channel_id, user_id)
        pending = self.pending_evaluations.get(key)
        if not pending:
            # Fallback to channel-only key for legacy or single-user room if exact match not found
            pending = self.pending_evaluations.get(str(channel_id).strip())

        if pending:
            # Verify TTL
            created_at = pending.get("_created_at", 0)
            if time.time() - created_at > self.ttl_seconds:
                self.clear_pending(channel_id, user_id)
                return None
            return pending
        return None

    def store_pending(self, channel_id: str, user_id: str, eval_data: Dict[str, Any]):
        key = self._get_key(channel_id, user_id)
        eval_data["_created_at"] = time.time()
        eval_data["_user_id"] = str(user_id)
        self.pending_evaluations[key] = eval_data

    def clear_pending(self, channel_id: str, user_id: str = ""):
        key = self._get_key(channel_id, user_id)
        if key in self.pending_evaluations:
            del self.pending_evaluations[key]
        cid = str(channel_id).strip()
        if cid in self.pending_evaluations:
            del self.pending_evaluations[cid]

    def evaluate_intent(self, prompt: str) -> Dict[str, Any]:
        """Deeply inspects the user prompt to classify domain, detect preferences,
        and generate smart clarifying questions.
        """
        p_lower = prompt.lower()

        # Classify Domain
        if any(w in p_lower for w in ["portfolio", "resume", "cv", "personal site", "developer site", "showcase"]):
            domain = "portfolio"
            display_domain = "Developer & Design Engineer Portfolio"
        elif any(w in p_lower for w in ["store", "ecommerce", "sneaker", "shoes", "shop", "checkout", "cart", "product"]):
            domain = "ecommerce"
            display_domain = "Interactive E-Commerce / Product Showcase"
        elif any(w in p_lower for w in ["dashboard", "analytics", "defi", "crypto", "telemetry", "metrics", "chart"]):
            domain = "dashboard"
            display_domain = "Real-Time Telemetry & Analytics Dashboard"
        else:
            domain = "saas"
            display_domain = "Modern SaaS / Web Application Platform"

        # Detect features requested
        features_detected = []
        if "dark" in p_lower:
            features_detected.append("Obsidian Dark Theme")
        if "light" in p_lower:
            features_detected.append("Clean Minimal Light Theme")
        if any(w in p_lower for w in ["pricing", "cost", "plan", "rate"]):
            features_detected.append("Tiered Rates & Pricing Section")
        if any(w in p_lower for w in ["test", "automated", "pytest"]):
            features_detected.append("Automated Verification Test Suite")
        if any(w in p_lower for w in ["3d", "tilt", "animation", "motion"]):
            features_detected.append("Interactive 3D / Micro-Interaction Effects")
        if any(w in p_lower for w in ["contact", "form", "reach"]):
            features_detected.append("Interactive Consultation & Contact Form")
        if any(w in p_lower for w in ["skill", "project", "work"]):
            features_detected.append("Selected Case Studies & Stack Chips")

        if not features_detected:
            features_detected = ["Modern Responsive Layout", "Interactive Micro-Interactions", "Automated QA Suite"]

        if domain == "portfolio":
            questions = [
                "1️⃣ **Theme Style:** Obsidian Zinc Dark (Recommended) or Clean Paper Light?",
                "2️⃣ **Primary Accent:** Emerald Green (Default) or Electric Cyan or Warm Amber?",
                "3️⃣ **Key Focus:** Design Engineering (UI/UX + Code) or Full-Stack Backend Architecture?"
            ]
            default_summary = "Obsidian Dark theme, Emerald accents, Design Engineering focus with live metrics & project filters."
        elif domain == "ecommerce":
            questions = [
                "1️⃣ **Visual Style:** Cybernetic Dark with 3D Tilt (Recommended) or Minimalist Modern?",
                "2️⃣ **Currency & Pricing:** USD ($) or EUR (€) or Crypto/Solana?",
                "3️⃣ **Interactive Features:** Include interactive 3D shoe card, size selector, and cart drawer?"
            ]
            default_summary = "Cybernetic Dark store, 3D card tilt physics, interactive cart drawer, and review matrix."
        elif domain == "dashboard":
            questions = [
                "1️⃣ **Data Density:** High-Density Telemetry (Recommended) or Clean Minimalist Cards?",
                "2️⃣ **Color Palette:** Matrix Emerald / Cyan on Black or Deep Midnight Indigo?",
                "3️⃣ **Interactivity:** Real-time simulated WebSockets feed and live chart canvas?"
            ]
            default_summary = "High-density dark telemetry dashboard, 60fps canvas chart, and real-time transaction feed."
        else:
            questions = [
                "1️⃣ **Color Palette:** Electric Cyan / Violet (Cyberpunk) or Monochromatic Zinc?",
                "2️⃣ **Conversion Elements:** Include Interactive Pricing Calculator and Live App Demo modal?",
                "3️⃣ **Engineering Rigor:** Enforce strict AST validation and pytest verification suite?"
            ]
            default_summary = "Modern dark SaaS landing page, interactive pricing tabs, feature matrix, and automated test suite."

        return {
            "domain": domain,
            "display_domain": display_domain,
            "features_detected": features_detected,
            "questions": questions,
            "default_summary": default_summary,
            "original_prompt": prompt,
        }

    def format_clarification_message(self, eval_data: Dict[str, Any], user_name: str) -> str:
        features_list = "\n".join(f"  • {f}" for f in eval_data["features_detected"])
        questions_list = "\n".join(eval_data["questions"])

        return (
            f"🧠 **OMNIFORGE Evaluation & Understanding**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Hello @{user_name}! I have parsed and evaluated your command:\n"
            f"> *\"{eval_data['original_prompt'][:100]}\"*\n\n"
            f"📋 **Target Domain:** `{eval_data['display_domain']}`\n"
            f"🎯 **Identified Requirements:**\n"
            f"{features_list}\n\n"
            f"⚙️ **Proposed Architecture Plan:**\n"
            f"• Follows strict `ui-skills` (no AI slop, compositor-only motion, tabular numbers)\n"
            f"• Default configuration: *{eval_data['default_summary']}*\n\n"
            f"❓ **Clarifying Decisions Before We Build:**\n"
            f"{questions_list}\n\n"
            f"👉 *Reply with your preferences (e.g. `dark, emerald, design`), or simply reply **`CONFIRM`** / **`GO`** to execute with optimal defaults!*"
        )

    def is_confirmation(self, text: str) -> bool:
        cleaned = text.strip().lower()
        confirm_keywords = [
            "confirm", "go", "yes", "proceed", "build", "build it", "do it",
            "ok", "okay", "approved", "start", "run", "sure", "yep", "1", "default", "defaults"
        ]
        return cleaned in confirm_keywords or cleaned.startswith("confirm") or cleaned.startswith("go")
