"""Pre-episode raw-capture path helpers (no downloads)."""

from __future__ import annotations

import os
from pathlib import Path


class CapturePathError(ValueError):
    """Invalid capture path arguments."""


def data_root(explicit: Path | str | None = None) -> Path:
    """Resolve GRAIN_DATA_ROOT or an explicit root. Does not create directories."""
    if explicit is not None:
        return Path(explicit)
    env = os.environ.get("GRAIN_DATA_ROOT")
    if not env:
        raise CapturePathError(
            "GRAIN_DATA_ROOT is unset and no explicit root was provided. "
            "Refuse to invent a data root."
        )
    return Path(env)


def sweeps_root(
    *,
    data_root_path: Path | str | None = None,
    sweeps_subdir: str,
) -> Path:
    """Root for Phase 1 hits before any episode_id exists."""
    if not sweeps_subdir:
        raise CapturePathError("sweeps_subdir is required (from prereg capture config).")
    return data_root(data_root_path) / sweeps_subdir


def candidate_capture_dir(
    *,
    sweep_id: str,
    candidate_id: str,
    data_root_path: Path | str | None = None,
    sweeps_subdir: str,
) -> Path:
    """Directory for one pre-episode sweep hit.

    Layout: ``$GRAIN_DATA_ROOT/<sweeps_subdir>/<sweep_id>/<candidate_id>/``

    Does not create directories or download documents.
    """
    if not sweep_id:
        raise CapturePathError("sweep_id is required")
    if not candidate_id:
        raise CapturePathError("candidate_id is required")
    return sweeps_root(data_root_path=data_root_path, sweeps_subdir=sweeps_subdir) / sweep_id / candidate_id
