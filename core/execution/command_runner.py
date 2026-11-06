import asyncio
import os
import sys
import re
import subprocess
from dataclasses import dataclass
from typing import Dict, Any, Optional

# Allowlisted environment variables safe for child process execution
SAFE_ENV_VARS = {
    "PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "COMSPEC", "PATHEXT",
    "LANG", "LC_ALL", "PYTHONPATH", "NODE_PATH", "HOME", "USERPROFILE"
}

# Blocklist patterns for hazardous shell operations
BLOCKED_COMMAND_PATTERNS = [
    r"(?i)\brm\s+-rf\s+[/~]",
    r"(?i)\bdel\s+/[sfq]\s+[c-z]:",
    r"(?i)\bformat\s+[c-z]:",
    r"(?i)\bmkfs\.",
    r"(?i):(){ :|:& };:",
    r"(?i)\bcurl\b.*\|\s*(?:bash|sh|cmd|powershell)",
    r"(?i)\bwget\b.*\|\s*(?:bash|sh|cmd|powershell)",
    r"(?i)\bpowershell\b.*-enc",
]


@dataclass
class CommandResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


class CommandRunner:
    """Executes verified tool commands within an isolated workspace directory
    with environment variable sanitization and destructive command blocking.
    """

    def __init__(self, default_timeout_seconds: int = 120):
        self.default_timeout_seconds = default_timeout_seconds

    def _sanitize_environment(self, custom_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Creates an isolated, minimal environment preventing server secret leakage."""
        clean_env = {}
        # Keep only allowlisted system variables
        for key, val in os.environ.items():
            if key.upper() in SAFE_ENV_VARS:
                clean_env[key] = val

        # Explicitly ensure NO sensitive keys leak into child process
        for key in list(clean_env.keys()):
            k_upper = key.upper()
            if any(term in k_upper for term in ["TOKEN", "SECRET", "KEY", "PASS", "CRED", "AUTH", "DATABASE"]):
                del clean_env[key]

        if custom_env:
            for k, v in custom_env.items():
                if not any(term in k.upper() for term in ["TOKEN", "SECRET", "KEY", "PASS", "CRED", "AUTH", "DATABASE"]):
                    clean_env[k] = v

        return clean_env

    def _validate_command(self, command: str):
        """Rejects dangerous or destructive shell patterns."""
        for pattern in BLOCKED_COMMAND_PATTERNS:
            if re.search(pattern, command):
                raise PermissionError(f"Security Policy Violation: Command pattern '{pattern}' is blocked!")

    async def run(
        self,
        command: str,
        cwd: str,
        timeout: Optional[int] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> CommandResult:
        timeout = timeout or self.default_timeout_seconds
        start_time = asyncio.get_event_loop().time()

        try:
            self._validate_command(command)
        except PermissionError as pe:
            return CommandResult(
                command=command,
                exit_code=126,
                stdout="",
                stderr=str(pe),
                duration_seconds=0.0,
                timed_out=False,
            )

        run_env = self._sanitize_environment(env)
        is_windows = sys.platform.startswith("win")
        
        # Format command for execution
        if is_windows:
            shell_cmd = ["cmd.exe", "/c", command]
        else:
            shell_cmd = ["/bin/sh", "-c", command]

        try:
            proc = await asyncio.create_subprocess_exec(
                *shell_cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=run_env,
            )

            try:
                stdout_data, stderr_data = await asyncio.wait_for(proc.communicate(), timeout=timeout)
                duration = asyncio.get_event_loop().time() - start_time
                stdout_str = stdout_data.decode("utf-8", errors="replace")
                stderr_str = stderr_data.decode("utf-8", errors="replace")
                return CommandResult(
                    command=command,
                    exit_code=proc.returncode if proc.returncode is not None else -1,
                    stdout=stdout_str,
                    stderr=stderr_str,
                    duration_seconds=round(duration, 2),
                    timed_out=False,
                )
            except asyncio.TimeoutError:
                duration = asyncio.get_event_loop().time() - start_time
                try:
                    proc.kill()
                    await proc.wait()
                except Exception:
                    pass
                return CommandResult(
                    command=command,
                    exit_code=-1,
                    stdout="",
                    stderr=f"Command timed out after {timeout} seconds",
                    duration_seconds=round(duration, 2),
                    timed_out=True,
                )
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            return CommandResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"Failed to execute command: {str(e)}",
                duration_seconds=round(duration, 2),
                timed_out=False,
            )
