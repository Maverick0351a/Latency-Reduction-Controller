from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .config import ControllerConfig, RESOURCES


def smoothstep(x: float) -> float:
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    return 3 * x * x - 2 * x * x * x


@dataclass
class ProcView:
    pid: int
    name: str
    is_fg: bool
    cpu_frac: float
    io_r_bps: int
    io_w_bps: int


@dataclass
class Decision:
    boost: Dict[int, Dict[str, float]]
    throttle: Dict[int, Dict[str, float]]
    acting: bool
    telemetry: Dict[str, float]


@dataclass
class ControllerState:
    cbar: Dict[str, float] = field(default_factory=lambda: {r: 0.0 for r in RESOURCES})
    prci_sys_bar: float = 0.0
    prci_fg_bar: float = 0.0
    prci_bg_bar: float = 0.0
    acting: bool = False
    idle_ctr: int = 0
    s: Dict[int, Dict[str, float]] = field(default_factory=dict)


class LRCController:
    def __init__(self, cfg: ControllerConfig):
        self.cfg = cfg
        self.st = ControllerState()

    def step(self, util: Dict[str, float], procs: List[ProcView]) -> Decision:
        for r in RESOURCES:
            x = (util[r] - self.cfg.theta[r]) / max(1e-9, 1.0 - self.cfg.theta[r])
            self.st.cbar[r] = self.cfg.alpha * smoothstep(x) + (1 - self.cfg.alpha) * self.st.cbar[r]

        for pv in procs:
            self.st.s.setdefault(
                pv.pid,
                {r: 1.0 / max(1, len(procs)) for r in RESOURCES},
            )

        cproc: Dict[int, float] = {}
        for pv in procs:
            pprio = 1.0 if pv.is_fg else 0.3
            score = 0.0
            score += pprio * self.cfg.eta["CPU"] * self.st.cbar["CPU"] * pv.cpu_frac
            io_mag = min(1.0, (pv.io_r_bps + pv.io_w_bps) / (50 * 1024 * 1024))
            score += pprio * self.cfg.eta["DISK"] * self.st.cbar["DISK"] * io_mag
            cproc[pv.pid] = score

        prci_sys = sum(cproc.values())
        prci_fg = sum(cproc[pv.pid] for pv in procs if pv.is_fg)
        prci_bg = prci_sys - prci_fg

        self.st.prci_sys_bar = self.cfg.alpha * prci_sys + (1 - self.cfg.alpha) * self.st.prci_sys_bar
        self.st.prci_fg_bar = self.cfg.alpha * prci_fg + (1 - self.cfg.alpha) * self.st.prci_fg_bar
        self.st.prci_bg_bar = self.cfg.alpha * prci_bg + (1 - self.cfg.alpha) * self.st.prci_bg_bar

        if not self.st.acting and (
            self.st.prci_fg_bar > self.cfg.prci_up or self.st.prci_bg_bar > self.cfg.prci_up
        ):
            self.st.acting = True
        elif self.st.acting and (
            self.st.prci_fg_bar < self.cfg.prci_down and self.st.prci_bg_bar < self.cfg.prci_down
        ):
            self.st.acting = False

        boost: Dict[int, Dict[str, float]] = {}
        throttle: Dict[int, Dict[str, float]] = {}
        if self.st.acting:
            for pv in procs:
                if not pv.is_fg:
                    continue
                deltas: Dict[str, float] = {}
                for r in RESOURCES:
                    d = min(self.cfg.delta_max[r], self.cfg.beta_fg[r] * self.st.cbar[r])
                    cur = self.st.s[pv.pid][r]
                    new = min(self.cfg.s_max[r], cur + d)
                    deltas[r] = new - cur
                    self.st.s[pv.pid][r] = new
                boost[pv.pid] = deltas

            for pv in sorted(
                [p for p in procs if not p.is_fg],
                key=lambda x: cproc[x.pid],
                reverse=True,
            ):
                deltas = {}
                for r in RESOURCES:
                    d = min(self.cfg.delta_max[r], self.cfg.beta_bg[r] * self.st.cbar[r])
                    cur = self.st.s[pv.pid][r]
                    new = max(self.cfg.s_min[r], cur - d)
                    deltas[r] = new - cur
                    self.st.s[pv.pid][r] = new
                throttle[pv.pid] = deltas
        else:
            if self.st.prci_sys_bar < self.cfg.prci_idle:
                self.st.idle_ctr += 1
                if self.st.idle_ctr >= self.cfg.recovery_hold:
                    for pid in list(self.st.s.keys()):
                        for r in RESOURCES:
                            self.st.s[pid][r] = min(
                                self.cfg.s_max[r],
                                self.st.s[pid][r] + self.cfg.recovery_gamma,
                            )
            else:
                self.st.idle_ctr = 0

        telemetry = {
            "prci_sys": self.st.prci_sys_bar,
            "prci_fg": self.st.prci_fg_bar,
            "prci_bg": self.st.prci_bg_bar,
            "c_cpu": self.st.cbar["CPU"],
            "c_disk": self.st.cbar["DISK"],
            "c_net": self.st.cbar["NET"],
            "acting": 1.0 if self.st.acting else 0.0,
        }
        return Decision(boost=boost, throttle=throttle, acting=self.st.acting, telemetry=telemetry)
