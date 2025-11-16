import os
import re
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .logging_conf import configure_logging
from .models import ThoughtData, ThoughtStage
from .storage_utils import (
    load_thoughts_from_file,
    prepare_thoughts_for_serialization,
    save_thoughts_to_file,
)

logger = configure_logging("sequential-thinking.storage")


class ThoughtStorage:
    """Storage manager for thought data."""

    def __init__(self, storage_dir: Optional[str] = None, default_project_id: Optional[str] = None):
        """Initialize the storage manager.

        Args:
            storage_dir: Directory to store thought data files. If None, uses a default directory.
            default_project_id: Project identifier to scope sessions.
        """
        if storage_dir is None:
            home_dir = Path.home()
            self.storage_dir = home_dir / ".mcp_sequential_thinking"
        else:
            self.storage_dir = Path(storage_dir)

        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self._lock = threading.RLock()
        env_project = os.environ.get("MCP_PROJECT_ID")
        self.default_project_id = self._sanitize_project_id(default_project_id or env_project or "default")
        self._project_histories: Dict[str, List[ThoughtData]] = {}
        self.thought_history: List[ThoughtData] = []

        self._ensure_history(self.default_project_id)
        logger.debug("Initialized ThoughtStorage at %s (project=%s)", self.storage_dir, self.default_project_id)

    def set_default_project(self, project_id: str) -> None:
        """Set the default project context for future operations."""
        resolved = self._sanitize_project_id(project_id)
        with self._lock:
            self.default_project_id = resolved
            self._ensure_history(resolved)
            self.thought_history = self._project_histories[resolved]
            logger.debug("Switched default project to %s", resolved)

    def _sanitize_project_id(self, project_id: str) -> str:
        """Convert arbitrary project identifiers into filesystem-safe names."""
        if not project_id:
            return "default"
        cleaned = re.sub(r"[^a-zA-Z0-9._-]", "_", project_id.strip())
        return cleaned or "default"

    def _session_file_for(self, project_id: str) -> Path:
        return self.storage_dir / f"{project_id}_session.json"

    def _lock_file_for(self, project_id: str) -> Path:
        return self.storage_dir / f"{project_id}_session.lock"

    def _ensure_history(self, project_id: str) -> List[ThoughtData]:
        """Load a project's thoughts into memory if needed."""
        if project_id not in self._project_histories:
            session_file = self._session_file_for(project_id)
            lock_file = self._lock_file_for(project_id)
            self._project_histories[project_id] = load_thoughts_from_file(session_file, lock_file)
        if project_id == self.default_project_id:
            self.thought_history = self._project_histories[project_id]
        return self._project_histories[project_id]

    def _resolve_project_id(self, project_id: Optional[str]) -> str:
        return self._sanitize_project_id(project_id or self.default_project_id)

    def _save_session(self, project_id: str) -> None:
        """Persist a single project's history to disk."""
        history = self._project_histories.get(project_id, [])
        thoughts_with_ids = prepare_thoughts_for_serialization(history)
        session_file = self._session_file_for(project_id)
        lock_file = self._lock_file_for(project_id)
        save_thoughts_to_file(session_file, thoughts_with_ids, lock_file)
        logger.debug("Saved %s thoughts for project %s", len(history), project_id)

    def add_thought(self, thought: ThoughtData, project_id: Optional[str] = None) -> None:
        """Add a thought to the history for the requested project."""
        with self._lock:
            pid = self._resolve_project_id(project_id)
            history = self._ensure_history(pid)
            history.append(thought)
            if pid == self.default_project_id:
                self.thought_history = history
            self._save_session(pid)

    def get_all_thoughts(self, project_id: Optional[str] = None) -> List[ThoughtData]:
        """Get all thoughts for the requested project."""
        with self._lock:
            pid = self._resolve_project_id(project_id)
            history = list(self._ensure_history(pid))
        return history

    def get_thoughts_by_stage(self, stage: ThoughtStage, project_id: Optional[str] = None) -> List[ThoughtData]:
        """Get all thoughts in a specific stage."""
        with self._lock:
            pid = self._resolve_project_id(project_id)
            history = self._ensure_history(pid)
            return [t for t in history if t.stage == stage]

    def clear_history(self, project_id: Optional[str] = None) -> None:
        """Clear the thought history for a project."""
        with self._lock:
            pid = self._resolve_project_id(project_id)
            history = self._ensure_history(pid)
            history.clear()
            if pid == self.default_project_id:
                self.thought_history = history
            self._save_session(pid)

    def export_session(self, file_path: str, project_id: Optional[str] = None) -> None:
        """Export the requested project session to a file."""
        pid = self._resolve_project_id(project_id)
        with self._lock:
            history = list(self._ensure_history(pid))
            thoughts_with_ids = prepare_thoughts_for_serialization(history)
            metadata = {
                "exportedAt": datetime.now().isoformat(),
                "metadata": {
                    "project": pid,
                    "totalThoughts": len(history),
                    "stages": {
                        stage.value: len([t for t in history if t.stage == stage])
                        for stage in ThoughtStage
                    },
                },
            }

        file_path_obj = Path(file_path)
        lock_file = file_path_obj.with_suffix(".lock")
        save_thoughts_to_file(file_path_obj, thoughts_with_ids, lock_file, metadata)

    def import_session(self, file_path: str, project_id: Optional[str] = None) -> None:
        """Import a session into the requested project."""
        file_path_obj = Path(file_path)
        lock_file = file_path_obj.with_suffix(".lock")
        thoughts = load_thoughts_from_file(file_path_obj, lock_file)

        with self._lock:
            pid = self._resolve_project_id(project_id)
            self._project_histories[pid] = thoughts
            if pid == self.default_project_id:
                self.thought_history = thoughts
            self._save_session(pid)
