import pytest
import pytest_asyncio
from core.execution.sandbox import ExecutionSandbox
from core.execution.verification import VerificationEngine


@pytest.mark.asyncio
async def test_verification_engine():
    sandbox = ExecutionSandbox("./workspaces", "test-verification-mission")
    engine = VerificationEngine(sandbox)

    # Write sample files
    await sandbox.write_file("index.html", "<!DOCTYPE html><html><body><h1>Test</h1></body></html>")
    await sandbox.write_file("app.py", "def add(a, b):\n    return a + b\n")

    report = await engine.verify_mission(
        mission_id="test-verification-mission",
        expected_files=["index.html", "app.py"],
    )

    assert report.passed is True
    assert report.total_checks >= 2
    assert report.failed_checks == 0
    assert len(report.errors) == 0

    # Markdown export test
    discord_md = report.to_discord_markdown("Test Mission")
    assert "OMNIFORGE MISSION REPORT" in discord_md
    assert "Execution Evidence" in discord_md
