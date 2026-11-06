import pytest
import pytest_asyncio
from database.session import init_db
from core.orchestrator.commander import CommanderOrchestrator


@pytest.mark.asyncio
async def test_full_mission_flow():
    await init_db()
    commander = CommanderOrchestrator(workspace_root="./workspaces")

    result = await commander.launch_mission(
        prompt="Build a modern landing page for an AI startup with pricing and tests",
        mission_title="AI Startup Portal",
        platform="discord",
        channel_id="test-channel-99",
    )

    assert result["mission"]["status"] == "completed"
    assert result["mission"]["progress"] == 100
    assert result["workspace_summary"]["total_files"] >= 4

    # Verify generated files
    files = result["workspace_summary"]["files"]
    assert "index.html" in files
    assert "styles.css" in files
    assert "app.js" in files
    assert "ARCHITECTURE.md" in files
    assert "DESIGN_SYSTEM.md" in files
    assert "VERIFICATION_REPORT.md" in files
    assert "SECURITY_AUDIT.md" in files

    # Verify verification report details
    verification = result["verification"]
    assert verification["passed"] is True
    assert "OMNIFORGE MISSION REPORT" in verification["report_markdown"]
