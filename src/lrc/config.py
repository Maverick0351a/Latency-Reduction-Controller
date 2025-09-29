from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Set

RESOURCES = ("CPU", "GPU", "RAM", "DISK", "NET")


@dataclass
class ControllerConfig:
    """Control parameters for the latency reduction controller."""

    # contention thresholds (theta) and per-resource weights (eta)
    theta: Dict[str, float] = field(
        default_factory=lambda: {
            "CPU": 0.75,
            "GPU": 0.75,
            "RAM": 0.85,
            "DISK": 0.70,
            "NET": 0.70,
        }
    )
    eta: Dict[str, float] = field(
        default_factory=lambda: {
            "CPU": 1.00,
            "GPU": 0.80,
            "RAM": 0.60,
            "DISK": 0.75,
            "NET": 0.70,
        }
    )
    # smoothing factor (EWMA)
    alpha: float = 0.20
    # per-resource step bounds & gains
    delta_max: Dict[str, float] = field(
        default_factory=lambda: {
            "CPU": 0.05,
            "GPU": 0.05,
            "RAM": 0.03,
            "DISK": 0.05,
            "NET": 0.05,
        }
    )
    beta_fg: Dict[str, float] = field(
        default_factory=lambda: {
            "CPU": 0.60,
            "GPU": 0.50,
            "RAM": 0.30,
            "DISK": 0.50,
            "NET": 0.50,
        }
    )
    beta_bg: Dict[str, float] = field(
        default_factory=lambda: {
            "CPU": 0.60,
            "GPU": 0.50,
            "RAM": 0.30,
            "DISK": 0.50,
            "NET": 0.50,
        }
    )
    s_min: Dict[str, float] = field(
        default_factory=lambda: {
            "CPU": 0.05,
            "GPU": 0.05,
            "RAM": 0.05,
            "DISK": 0.05,
            "NET": 0.05,
        }
    )
    s_max: Dict[str, float] = field(
        default_factory=lambda: {
            "CPU": 0.95,
            "GPU": 0.95,
            "RAM": 0.95,
            "DISK": 0.95,
            "NET": 0.95,
        }
    )
    # hysteresis & recovery
    prci_up: float = 0.10
    prci_down: float = 0.05
    prci_idle: float = 0.02
    recovery_gamma: float = 0.01
    recovery_hold: int = 20
    # policy & safety
    latency_critical: Set[str] = field(default_factory=set)
    allowlist_system: Set[str] = field(
        default_factory=lambda: {
            "System",
            "Registry",
            "MsMpEng.exe",
            "wininit.exe",
            "winlogon.exe",
            "csrss.exe",
            "services.exe",
            "lsass.exe",
            "smss.exe",
            "svchost.exe",
        }
    )
