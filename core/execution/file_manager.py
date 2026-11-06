import os
import re
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional

SAFE_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-]+$")


class WorkspaceFileManager:
    """Manages files within an isolated mission workspace with strict containment
    and path traversal protections against sibling-prefix bypasses.
    """

    def __init__(self, workspace_root: str, mission_id: str):
        if not SAFE_ID_REGEX.match(mission_id) or ".." in mission_id:
            raise ValueError(f"Invalid or unsafe mission_id: '{mission_id}'")

        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_dir = (self.workspace_root / mission_id).resolve()

        # Verify the workspace directory is strictly a descendant of workspace_root
        try:
            self.workspace_dir.relative_to(self.workspace_root)
        except ValueError:
            raise PermissionError(f"Workspace directory escapes workspace root boundary: '{mission_id}'")

        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_safe(self, rel_path: str) -> Path:
        """Resolves target path and strictly verifies path-aware descendant containment.
        Rejects traversal attempts and sibling-prefix path escapes.
        """
        # Block raw directory traversal patterns upfront
        cleaned = rel_path.replace("\\", "/").strip()
        if ".." in cleaned.split("/") or cleaned.startswith("/"):
            raise PermissionError(f"Directory traversal detected: '{rel_path}'")

        target = (self.workspace_dir / rel_path).resolve()
        
        # Strict path containment check using relative_to (cannot be fooled by sibling prefix)
        try:
            target.relative_to(self.workspace_dir)
        except ValueError:
            raise PermissionError(f"Access denied: Path '{rel_path}' escapes workspace boundary!")

        return target

    async def write_file(self, rel_path: str, content: str) -> Dict[str, Any]:
        target = self._resolve_safe(rel_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        def _sync_write():
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)

        await asyncio.to_thread(_sync_write)

        stat = target.stat()
        return {
            "rel_path": str(target.relative_to(self.workspace_dir)).replace("\\", "/"),
            "full_path": str(target),
            "size_bytes": stat.st_size,
        }

    async def read_file(self, rel_path: str) -> str:
        target = self._resolve_safe(rel_path)
        if not target.exists():
            raise FileNotFoundError(f"File not found: {rel_path}")

        def _sync_read():
            with open(target, "r", encoding="utf-8") as f:
                return f.read()

        return await asyncio.to_thread(_sync_read)

    def file_exists(self, rel_path: str) -> bool:
        try:
            target = self._resolve_safe(rel_path)
            return target.is_file()
        except PermissionError:
            return False

    def list_files(self, rel_dir: str = "") -> List[Dict[str, Any]]:
        target_dir = self._resolve_safe(rel_dir) if rel_dir else self.workspace_dir
        if not target_dir.exists():
            return []

        results = []
        for p in target_dir.rglob("*"):
            if p.is_file():
                results.append({
                    "rel_path": str(p.relative_to(self.workspace_dir)).replace("\\", "/"),
                    "size_bytes": p.stat().st_size,
                    "extension": p.suffix,
                })
        return results

    def get_summary(self) -> Dict[str, Any]:
        files = self.list_files()
        total_size = sum(f["size_bytes"] for f in files)
        return {
            "workspace_path": str(self.workspace_dir),
            "total_files": len(files),
            "total_size_bytes": total_size,
            "files": [f["rel_path"] for f in files],
        }
