# -*- coding: utf-8 -*-
"""Pytest configuration for Vishap (# v6.0.2-fix-v2: pytest_configure).

Runs BEFORE collection (pytest_configure), so src.config picks up the tmp dir
when it is first imported. Fixes PermissionError on Windows for tests that
write audit files (previous fixture-based approach was too late).

v6.0.3-fallback: tempfile.mkdtemp() creates a 0o700 dir that some sandboxed
environments (DSH) cannot create subdirectories in; on failure we fall back to
a workspace-local .tmp_data dir instead.
"""
import os
import shutil
import tempfile
from pathlib import Path


_TMP_ROOT = None


def pytest_configure(config):
    """Set VISHAP_DATA_DIR before any test module is imported."""
    # v6.0.3-fallback: mkdtemp fails in DSH sandbox (0o700 ACL)
    global _TMP_ROOT
    if os.environ.get("VISHAP_DATA_DIR"):
        return  # respect explicit override
    try:
        _TMP_ROOT = Path(tempfile.mkdtemp(prefix="vishap-tests-"))
        data_dir = _TMP_ROOT / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError):
        # Sandboxed env (e.g. DSH): mkdtemp's 0o700 dir can't host subdirs.
        _TMP_ROOT = Path(__file__).parent.parent / ".tmp_data"
        _TMP_ROOT.mkdir(parents=True, exist_ok=True)
        data_dir = _TMP_ROOT / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
    os.environ["VISHAP_DATA_DIR"] = str(data_dir)


def pytest_unconfigure(config):
    """Cleanup tmp dir after session (best-effort)."""
    if _TMP_ROOT is not None:
        shutil.rmtree(_TMP_ROOT, ignore_errors=True)
