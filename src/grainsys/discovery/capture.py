"""Pre-episode raw-capture path helpers (no downloads)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from grainsys.discovery.config import (
    DiscoveryConfigError,
    require_safe_path_component,
    require_safe_relative_path,
)


class CapturePathError(ValueError):
    """Invalid capture path arguments."""


def _as_capture_error(exc: DiscoveryConfigError) -> CapturePathError:
    return CapturePathError(str(exc))


def _require_component(value: Any, *, field: str) -> str:
    try:
        return require_safe_path_component(value, field=field)
    except DiscoveryConfigError as exc:
        raise _as_capture_error(exc) from exc


def _require_subdir(value: Any, *, field: str) -> str:
    try:
        return require_safe_relative_path(value, field=field)
    except DiscoveryConfigError as exc:
        raise _as_capture_error(exc) from exc


def _assert_contained(*, path: Path, root: Path, field: str) -> Path:
    """Resolve ``path`` and require it stays under ``root``."""
    try:
        root_resolved = root.resolve()
        path_resolved = path.resolve()
    except OSError as exc:
        raise CapturePathError(f"{field} could not be resolved: {exc}") from exc
    try:
        path_resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise CapturePathError(
            f"{field} resolves outside data root ({path_resolved} not under "
            f"{root_resolved}); refuse"
        ) from exc
    return path_resolved


def data_root(explicit: Path | str | None = None) -> Path:
    """Resolve GRAIN_DATA_ROOT or an explicit root. Does not create directories.

    Explicit roots may be absolute. Environment / explicit values are not
    invented; absence fails closed.
    """
    if explicit is not None:
        if isinstance(explicit, bool) or not isinstance(explicit, (Path, str)):
            raise CapturePathError(
                f"data_root must be a path or string (got {type(explicit).__name__})"
            )
        if isinstance(explicit, str) and ("\x00" in explicit or not explicit.strip()):
            raise CapturePathError("data_root string must be nonempty without NUL")
        return Path(explicit)
    env = os.environ.get("GRAIN_DATA_ROOT")
    if not env:
        raise CapturePathError(
            "GRAIN_DATA_ROOT is unset and no explicit root was provided. "
            "Refuse to invent a data root."
        )
    if "\x00" in env:
        raise CapturePathError("GRAIN_DATA_ROOT contains NUL; refuse")
    return Path(env)


def sweeps_root(
    *,
    data_root_path: Path | str | None = None,
    sweeps_subdir: str,
) -> Path:
    """Root for Phase 1 hits before any episode_id exists."""
    subdir = _require_subdir(sweeps_subdir, field="sweeps_subdir")
    root = data_root(data_root_path)
    joined = root.joinpath(*subdir.split("/"))
    _assert_contained(path=joined, root=root, field="sweeps_root")
    return joined


def candidate_capture_dir(
    *,
    sweep_id: str,
    candidate_id: str,
    data_root_path: Path | str | None = None,
    sweeps_subdir: str,
) -> Path:
    """Directory for one pre-episode sweep hit.

    Layout: ``$GRAIN_DATA_ROOT/<sweeps_subdir>/<sweep_id>/<candidate_id>/``

    Does not create directories or download documents. Rejects non-string/bool,
    absolute/rooted, dot/dot-dot, separators, NUL, and traversal.
    """
    sid = _require_component(sweep_id, field="sweep_id")
    cid = _require_component(candidate_id, field="candidate_id")
    base = sweeps_root(data_root_path=data_root_path, sweeps_subdir=sweeps_subdir)
    root = data_root(data_root_path)
    joined = base / sid / cid
    _assert_contained(path=joined, root=root, field="candidate_capture_dir")
    return joined
