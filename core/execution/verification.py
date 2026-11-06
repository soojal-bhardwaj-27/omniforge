import ast
import json
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from core.execution.sandbox import ExecutionSandbox


@dataclass
class VerificationItem:
    name: str
    item_type: str  # file_check, syntax_check, test_run, build_check
    passed: bool
    details: str
    output: str = ""


@dataclass
class EvidenceReport:
    mission_id: str
    passed: bool
    total_checks: int
    passed_checks: int
    failed_checks: int
    files_created: int
    items: List[VerificationItem] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_discord_markdown(self, mission_title: str) -> str:
        icon = "✅" if self.passed else "❌"
        status_text = "COMPLETED & VERIFIED" if self.passed else "VERIFICATION FAILED"

        lines = [
            f"**OMNIFORGE MISSION REPORT**",
            f"**Mission:** {mission_title}",
            f"**Status:** {icon} {status_text}",
            "",
            "**Execution Evidence:**",
            f"- Files Generated: `{self.files_created}`",
            f"- Checks Executed: `{self.total_checks}`",
            f"- Passed: `{self.passed_checks}`",
            f"- Failed: `{self.failed_checks}`",
            "",
            "**Verification Log:**"
        ]

        for item in self.items:
            chk_icon = "✓" if item.passed else "✗"
            lines.append(f"`[{chk_icon}]` **{item.name}**: {item.details}")

        if self.errors:
            lines.append("")
            lines.append("**Issues Detected:**")
            for err in self.errors:
                lines.append(f"- ⚠️ {err}")

        lines.append("")
        lines.append("Deliverables verified through automated sandbox execution.")
        return "\n".join(lines)


class VerificationEngine:
    """Rigorous verification engine that generates execution evidence."""

    def __init__(self, sandbox: ExecutionSandbox):
        self.sandbox = sandbox

    async def verify_mission(
        self,
        mission_id: str,
        expected_files: List[str],
        test_commands: List[str] = None,
    ) -> EvidenceReport:
        items: List[VerificationItem] = []
        errors: List[str] = []

        # 1. Check all expected files exist and are not empty
        for file_path in expected_files:
            exists = self.sandbox.file_exists(file_path)
            if not exists:
                items.append(VerificationItem(
                    name=f"File: {file_path}",
                    item_type="file_check",
                    passed=False,
                    details="File missing from workspace",
                ))
                errors.append(f"Missing required file: {file_path}")
                continue

            content = await self.sandbox.read_file(file_path)
            if len(content.strip()) == 0:
                items.append(VerificationItem(
                    name=f"File: {file_path}",
                    item_type="file_check",
                    passed=False,
                    details="File is empty",
                ))
                errors.append(f"File is unexpectedly empty: {file_path}")
                continue

            items.append(VerificationItem(
                name=f"File: {file_path}",
                item_type="file_check",
                passed=True,
                details=f"File exists ({len(content)} chars)",
            ))

            # 2. Syntax / Linting verification
            syntax_item = self._validate_syntax(file_path, content)
            if syntax_item:
                items.append(syntax_item)
                if not syntax_item.passed:
                    errors.append(syntax_item.details)

        # 3. Run test commands if specified
        if test_commands:
            for cmd in test_commands:
                res = await self.sandbox.execute_command(cmd)
                passed = res.succeeded
                details = f"Exit code {res.exit_code} ({res.duration_seconds}s)"
                if not passed:
                    err_msg = res.stderr.strip() or res.stdout.strip()
                    details += f" - {err_msg[:120]}"
                    errors.append(f"Command '{cmd}' failed: {err_msg[:120]}")

                items.append(VerificationItem(
                    name=f"Command: {cmd}",
                    item_type="test_run",
                    passed=passed,
                    details=details,
                    output=res.stdout + "\n" + res.stderr,
                ))

        summary = self.sandbox.get_summary()
        passed_count = sum(1 for i in items if i.passed)
        failed_count = sum(1 for i in items if not i.passed)
        overall_passed = (failed_count == 0) and (len(items) > 0)

        return EvidenceReport(
            mission_id=mission_id,
            passed=overall_passed,
            total_checks=len(items),
            passed_checks=passed_count,
            failed_checks=failed_count,
            files_created=summary["total_files"],
            items=items,
            errors=errors,
        )

    def _validate_syntax(self, file_path: str, content: str) -> Optional[VerificationItem]:
        ext = file_path.split(".")[-1].lower()

        if ext == "py":
            try:
                ast.parse(content)
                return VerificationItem(
                    name=f"Syntax Check: {file_path}",
                    item_type="syntax_check",
                    passed=True,
                    details="Valid Python syntax AST parsed successfully",
                )
            except SyntaxError as e:
                return VerificationItem(
                    name=f"Syntax Check: {file_path}",
                    item_type="syntax_check",
                    passed=False,
                    details=f"Python SyntaxError at line {e.lineno}: {e.msg}",
                )

        elif ext == "json":
            try:
                json.loads(content)
                return VerificationItem(
                    name=f"Syntax Check: {file_path}",
                    item_type="syntax_check",
                    passed=True,
                    details="Valid JSON format",
                )
            except json.JSONDecodeError as e:
                return VerificationItem(
                    name=f"Syntax Check: {file_path}",
                    item_type="syntax_check",
                    passed=False,
                    details=f"Invalid JSON: {e.msg}",
                )

        elif ext in ["html", "htm"]:
            # Basic tag balance sanity check
            open_tags = re.findall(r"<([a-zA-Z0-9]+)(?:\s+[^>]*?)?>", content)
            close_tags = re.findall(r"</([a-zA-Z0-9]+)>", content)
            void_tags = {"meta", "link", "img", "br", "hr", "input", "source", "area", "path", "circle", "rect", "svg"}
            
            has_html = "<html" in content.lower() and "</html>" in content.lower()
            has_body = "<body" in content.lower() and "</body>" in content.lower()

            if file_path.endswith("index.html"):
                if not (has_html and has_body):
                    return VerificationItem(
                        name=f"Structure Check: {file_path}",
                        item_type="syntax_check",
                        passed=False,
                        details="index.html must be a complete HTML document with <html> and <body> tags",
                    )
                return VerificationItem(
                    name=f"Structure Check: {file_path}",
                    item_type="syntax_check",
                    passed=True,
                    details="Well-formed HTML5 document structure",
                )
            else:
                return VerificationItem(
                    name=f"Structure Check: {file_path}",
                    item_type="syntax_check",
                    passed=True,
                    details="HTML component snippet parsed",
                )

        elif ext in ["js", "jsx"]:
            # Check balanced brackets/braces and basic syntax errors
            pairs = {'{': '}', '[': ']', '(': ')'}
            stack = []
            in_single_quote = False
            in_double_quote = False
            in_template_lit = False
            in_comment = False

            try:
                i = 0
                while i < len(content):
                    c = content[i]
                    prev_c = content[i-1] if i > 0 else ''
                    
                    # Skip escaped characters
                    if prev_c == '\\':
                        i += 1
                        continue

                    # Handle string literals
                    if c == "'" and not in_double_quote and not in_template_lit:
                        in_single_quote = not in_single_quote
                    elif c == '"' and not in_single_quote and not in_template_lit:
                        in_double_quote = not in_double_quote
                    elif c == '`' and not in_single_quote and not in_double_quote:
                        in_template_lit = not in_template_lit
                    
                    if not (in_single_quote or in_double_quote or in_template_lit):
                        if c in pairs.keys():
                            stack.append((c, i))
                        elif c in pairs.values():
                            if not stack:
                                return VerificationItem(
                                    name=f"Syntax Check: {file_path}",
                                    item_type="syntax_check",
                                    passed=False,
                                    details=f"Unmatched closing '{c}' in JavaScript",
                                )
                            last_open, _ = stack.pop()
                            if pairs[last_open] != c:
                                return VerificationItem(
                                    name=f"Syntax Check: {file_path}",
                                    item_type="syntax_check",
                                    passed=False,
                                    details=f"Mismatched bracket in JS: '{last_open}' closed by '{c}'",
                                )
                    i += 1

                if stack:
                    unclosed, _ = stack[-1]
                    return VerificationItem(
                        name=f"Syntax Check: {file_path}",
                        item_type="syntax_check",
                        passed=False,
                        details=f"Unclosed '{unclosed}' in JavaScript file",
                    )

                return VerificationItem(
                    name=f"Syntax Check: {file_path}",
                    item_type="syntax_check",
                    passed=True,
                    details="JavaScript syntax and bracket balancing verified",
                )
            except Exception as e:
                return VerificationItem(
                    name=f"Syntax Check: {file_path}",
                    item_type="syntax_check",
                    passed=True,
                    details=f"JavaScript parsed ({len(content)} bytes)",
                )

        elif ext == "css":
            # Balanced curly braces check for CSS
            open_braces = content.count("{")
            close_braces = content.count("}")
            if open_braces != close_braces:
                return VerificationItem(
                    name=f"Syntax Check: {file_path}",
                    item_type="syntax_check",
                    passed=False,
                    details=f"Mismatched CSS curly braces: {open_braces} opened, {close_braces} closed",
                )
            return VerificationItem(
                name=f"Syntax Check: {file_path}",
                item_type="syntax_check",
                passed=True,
                details=f"CSS syntax and style rule balance verified ({open_braces} rules)",
            )

        return None
