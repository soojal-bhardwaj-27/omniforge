import os
import logging
from typing import Dict, Any, Optional
from core.execution.file_manager import WorkspaceFileManager
from core.execution.command_runner import CommandRunner, CommandResult

logger = logging.getLogger("omniforge.sandbox")


class ExecutionSandbox:
    """Unified sandbox environment for a mission.
    Provides isolated file system operations and command execution.
    """

    def __init__(self, workspace_root: str, mission_id: str, prefer_docker: bool = False):
        self.workspace_root = workspace_root
        self.mission_id = mission_id
        self.prefer_docker = prefer_docker
        self.file_manager = WorkspaceFileManager(workspace_root, mission_id)
        self.command_runner = CommandRunner()

    @property
    def workspace_path(self) -> str:
        return str(self.file_manager.workspace_dir)

    async def write_file(self, rel_path: str, content: str) -> Dict[str, Any]:
        return await self.file_manager.write_file(rel_path, content)

    async def read_file(self, rel_path: str) -> str:
        return await self.file_manager.read_file(rel_path)

    def file_exists(self, rel_path: str) -> bool:
        return self.file_manager.file_exists(rel_path)

    def list_files(self, rel_dir: str = "") -> list:
        return self.file_manager.list_files(rel_dir)

    async def execute_command(self, command: str, timeout: Optional[int] = None) -> CommandResult:
        # Executes within the mission's safe workspace directory
        logger.info(f"[{self.mission_id}] Executing: {command}")
        return await self.command_runner.run(command, cwd=self.workspace_path, timeout=timeout)

    def get_summary(self) -> Dict[str, Any]:
        return self.file_manager.get_summary()
