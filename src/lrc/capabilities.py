from __future__ import annotations

import importlib
import platform
import sys
from dataclasses import dataclass


@dataclass
class WinCaps:
    os_version: str
    build: int
    has_pywin32: bool
    has_nvml: bool
    can_set_priority: bool
    can_set_io_priority: bool


def detect_caps() -> WinCaps:
    """Probe runtime capabilities to stay resilient to Windows updates."""

    build = 0
    try:
        build = getattr(sys.getwindowsversion(), "build", 0) or 0
    except Exception:
        build = 0

    has_pywin32 = False
    can_set_prio = False
    try:
        importlib.import_module("win32api")
        importlib.import_module("win32con")
        importlib.import_module("win32process")
        has_pywin32 = True
        can_set_prio = True
    except Exception:
        has_pywin32 = False
        can_set_prio = False

    has_nvml = False
    try:
        importlib.import_module("pynvml")
        has_nvml = True
    except Exception:
        has_nvml = False

    can_set_io_prio = False
    try:
        import psutil  # type: ignore

        proc = psutil.Process()
        can_set_io_prio = hasattr(proc, "ionice")
    except Exception:
        can_set_io_prio = False

    return WinCaps(
        os_version=platform.version(),
        build=build,
        has_pywin32=has_pywin32,
        has_nvml=has_nvml,
        can_set_priority=can_set_prio,
        can_set_io_priority=can_set_io_prio,
    )
