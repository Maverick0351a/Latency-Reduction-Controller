from __future__ import annotations

import psutil

try:
    import win32api  # type: ignore
    import win32con  # type: ignore
    import win32process  # type: ignore

    _HAS_WIN32 = True
except Exception:  # pragma: no cover - optional dependency
    _HAS_WIN32 = False

_PRIO: dict[str, int] = {}
if _HAS_WIN32:
    _PRIO = {
        "bg": win32process.BELOW_NORMAL_PRIORITY_CLASS,
        "normal": win32process.NORMAL_PRIORITY_CLASS,
        "fg": win32process.ABOVE_NORMAL_PRIORITY_CLASS,
        "high": win32process.HIGH_PRIORITY_CLASS,
    }


def set_cpu_priority(pid: int, level: str) -> bool:
    if not _HAS_WIN32:
        return False
    try:
        ph = win32api.OpenProcess(
            win32con.PROCESS_SET_INFORMATION | win32con.PROCESS_QUERY_INFORMATION,
            False,
            pid,
        )
        cls = _PRIO.get(level, win32process.NORMAL_PRIORITY_CLASS)
        win32process.SetPriorityClass(ph, cls)
        return True
    except Exception:
        return False


def set_io_priority(pid: int, level: int) -> bool:
    """Configure process I/O priority using psutil if available."""

    try:
        proc = psutil.Process(pid)
        if hasattr(proc, "ionice"):
            proc.ionice(level)
            return True
    except Exception:
        return False
    return False
