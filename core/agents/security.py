import re
from typing import Dict, Any, List
from core.agents.base import BaseAgent, AgentResult
from core.execution.sandbox import ExecutionSandbox
from core.events.publisher import EventPublisher


class SecurityGuardAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="SECURITY",
            role_description="Security gating, permission checks, secret leak detection, and command auditing.",
        )

    # Comprehensive patterns indicating leaked secrets, credentials, or dangerous patterns
    SECRET_PATTERNS = [
        (r"(?i)api[_-]?key\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]", "Exposed API Key"),
        (r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}", "Exposed Bearer Token"),
        (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
        (r"sk-[a-zA-Z0-9]{32,}", "OpenAI API Secret Key"),
        (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
        (r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----", "Raw Cryptographic Private Key"),
        (r"[0-9]{9,10}:[a-zA-Z0-9_-]{35}", "Telegram Bot Token"),
        (r"(?i)(?:password|passwd|secret_key)\s*[:=]\s*['\"][^'\"]{8,}['\"]", "Hardcoded Credentials/Password"),
    ]

    def scan_for_secrets(self, content: str) -> List[str]:
        findings = []
        for pattern, label in self.SECRET_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                findings.append(f"{label} detected (pattern: {pattern[:30]}...)")
        return findings

    async def execute(
        self,
        task_id: str,
        mission_title: str,
        task_title: str,
        task_context: Dict[str, Any],
        sandbox: ExecutionSandbox,
        publisher: EventPublisher,
    ) -> AgentResult:
        await publisher.task_started(task_id, self.name, "Running security audit on generated deliverables")

        findings: List[str] = []
        files = sandbox.list_files()

        for file_info in files:
            rel_path = file_info["rel_path"]
            if file_info["extension"] in [".html", ".js", ".css", ".py", ".md", ".json", ".env", ".yaml", ".yml"]:
                content = await sandbox.read_file(rel_path)
                leak_findings = self.scan_for_secrets(content)
                for f in leak_findings:
                    findings.append(f"{rel_path}: {f}")

        is_clean = len(findings) == 0

        audit_content = (
            f"# Security Audit Report: {mission_title}\n\n"
            f"- **Status**: {'PASSED (CLEAN)' if is_clean else 'FLAGGED (APPROVAL REQUIRED)'}\n"
            f"- **Files Audited**: {len(files)}\n"
            f"- **Vulnerabilities / Secret Leaks Detected**: {len(findings)}\n"
        )
        if findings:
            audit_content += "\n## Security Policy Violations:\n" + "\n".join(f"- ⚠️ {f}" for f in findings)
            audit_content += "\n\n> 🛑 **ACTION REQUIRED:** Automated delivery blocked until security issues are addressed."
        else:
            audit_content += "\nNo unencrypted secrets, leaked credentials, or policy violations identified."

        audit_file = await sandbox.write_file("SECURITY_AUDIT.md", audit_content)
        await publisher.file_created("SECURITY_AUDIT.md", self.name, task_id)

        await publisher.task_completed(
            task_id,
            self.name,
            f"Security scan finished: {'No vulnerabilities detected' if is_clean else f'{len(findings)} security findings flagged'}.",
            artifacts=[audit_file["rel_path"]],
        )

        return AgentResult(
            task_id=task_id,
            agent=self.name,
            status="completed" if is_clean else "needs_approval",
            output={
                "clean": is_clean,
                "findings_count": len(findings),
                "findings": findings,
                "report_file": audit_file["rel_path"],
            },
            artifacts=[audit_file["rel_path"]],
            error_message="Security audit flagged secret leaks or vulnerabilities" if not is_clean else None,
        )
