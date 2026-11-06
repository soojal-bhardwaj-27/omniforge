from typing import List, Dict, Any
from database.models import AgentRole


class TaskPlanItem:
    def __init__(
        self,
        task_id: str,
        title: str,
        description: str,
        agent: AgentRole,
        dependencies: List[str] = None,
        priority: int = 1,
    ):
        self.task_id = task_id
        self.title = title
        self.description = description
        self.agent = agent
        self.dependencies = dependencies or []
        self.priority = priority

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.task_id,
            "title": self.title,
            "description": self.description,
            "agent": self.agent.value,
            "dependencies": self.dependencies,
            "priority": self.priority,
        }


class DAGMissionPlanner:
    """Decomposes a user mission into an executable Directed Acyclic Graph (DAG) of specialized agent tasks."""

    def plan_mission(self, mission_id: str, prompt: str) -> List[TaskPlanItem]:
        p_lower = prompt.lower()

        if any(w in p_lower for w in ["portfolio", "resume", "cv", "personal site", "showcase"]):
            t1_title = "System Architecture: Developer Portfolio & Case Studies"
            t1_desc = "Define semantic component hierarchy, case studies data schema, and accessible navigation."
            t2_title = "UI/UX Design System: Obsidian Zinc & ui-skills Tokens"
            t2_desc = "Formulate high-contrast zinc dark palette, emerald accent, and compositor-only micro-animations."
            t3_title = "Software Implementation: Interactive Showcase & Theme Engine"
            t3_desc = "Synthesize semantic HTML5, CSS3 grid, dark/light theme switch, and 1-click email copy."
            t4_title = "Automated Quality Assurance: Portfolio Structure & A11y"
            t4_desc = "Execute automated pytest verification of DOM structure, CSS tokens, and form handlers."
            t5_title = "Security Audit: Asset & Input Protection Gate"
            t5_desc = "Verify zero external credential leakage, sanitize input fields, and enforce permission gates."

        elif any(w in p_lower for w in ["store", "ecommerce", "sneaker", "shoes", "shop"]):
            t1_title = "System Architecture: E-Commerce Catalog & Cart Schema"
            t1_desc = "Architect product matrix, cart state manager, and checkout flow contracts."
            t2_title = "UI/UX Design System: 3D Product Visualizer Tokens"
            t2_desc = "Establish cybernetic dark store tokens, 3D card tilt physics, and badge tokens."
            t3_title = "Software Implementation: Product Grid, Cart Drawer & Checkout"
            t3_desc = "Synthesize product catalog, interactive cart drawer, size selector, and order checkout."
            t4_title = "Automated Quality Assurance: E-Commerce Core & Tests"
            t4_desc = "Run automated unit tests on cart state transitions, pricing calculations, and DOM nodes."
            t5_title = "Security Audit: Payment & Order Security Gate"
            t5_desc = "Scan for checkout injection vulnerabilities, validate data contracts, and enforce permissions."

        elif any(w in p_lower for w in ["dashboard", "analytics", "defi", "crypto", "telemetry"]):
            t1_title = "System Architecture: High-Density Telemetry & Stream Engine"
            t1_desc = "Define metric time-series schema, canvas chart pipeline, and query data flow."
            t2_title = "UI/UX Design System: Matrix Dark & Telemetry Tokens"
            t2_desc = "Establish high-density data tables, tabular-nums font tokens, and 60fps canvas palettes."
            t3_title = "Software Implementation: Telemetry Canvas & Live Feed"
            t3_desc = "Build interactive canvas graph, KPI stat cards, transaction table, and status indicators."
            t4_title = "Automated Quality Assurance: Chart Engine & Pipeline Tests"
            t4_desc = "Run verification suite testing canvas initializers, WebSocket listeners, and metrics."
            t5_title = "Security Audit: Stream Access & Permission Gate"
            t5_desc = "Audit real-time endpoints, verify data integrity, and enforce restricted command levels."

        else:
            t1_title = "System Architecture & Component Mapping"
            t1_desc = "Analyze requirements, select technology stack, define file structure and contracts."
            t2_title = "UI/UX Design System & Layout Tokens"
            t2_desc = "Establish visual identity, color tokens, responsive breakpoints, and accessibility standards."
            t3_title = "Software Implementation & Code Generation"
            t3_desc = "Synthesize production-ready codebase, styles, interactive scripts, and automated test suite."
            t4_title = "Automated Quality Assurance & Sandbox Testing"
            t4_desc = "Execute automated test suites, syntax linting, and build verification in isolated sandbox."
            t5_title = "Security Audit & Permission Gate Review"
            t5_desc = "Audit source files for exposed secrets, analyze package vulnerabilities and permissions."

        t1 = TaskPlanItem(task_id=f"{mission_id}-t1", title=t1_title, description=t1_desc, agent=AgentRole.ARCHITECT, dependencies=[], priority=1)
        t2 = TaskPlanItem(task_id=f"{mission_id}-t2", title=t2_title, description=t2_desc, agent=AgentRole.DESIGNER, dependencies=[t1.task_id], priority=2)
        t3 = TaskPlanItem(task_id=f"{mission_id}-t3", title=t3_title, description=t3_desc, agent=AgentRole.DEVELOPER, dependencies=[t1.task_id, t2.task_id], priority=3)
        t4 = TaskPlanItem(task_id=f"{mission_id}-t4", title=t4_title, description=t4_desc, agent=AgentRole.TESTER, dependencies=[t3.task_id], priority=4)
        t5 = TaskPlanItem(task_id=f"{mission_id}-t5", title=t5_title, description=t5_desc, agent=AgentRole.SECURITY, dependencies=[t3.task_id], priority=5)

        return [t1, t2, t3, t4, t5]
