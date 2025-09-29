from __future__ import annotations

from dataclasses import dataclass
from typing import List, Set, Tuple

import psutil

from .capabilities import detect_caps
from .config import ControllerConfig
from .controller import LRCController, ProcView
from .metrics import MetricReader
from .os_win import set_cpu_priority, set_io_priority
from .safety import is_system_critical


@dataclass
class AgentOptions:
    interval_s: float = 0.5
    mode: str = "shadow"  # "shadow" or "active"


class Agent:
    def __init__(self, cfg: ControllerConfig, opts: AgentOptions):
        self.cfg = cfg
        self.opts = opts
        self.caps = detect_caps()
        self.reader = MetricReader()
        self.ctrl = LRCController(cfg)

    def _pick_foreground_pids(self, top: List[Tuple[int, float]]) -> Set[int]:
        return {top[0][0]} if top else set()

    def run(self) -> None:
        print(
            f"[LRC] Windows build={self.caps.build} pywin32={self.caps.has_pywin32} nvml={self.caps.has_nvml}"
        )
        print(f"[LRC] mode={self.opts.mode}")
        try:
            while True:
                snap = self.reader.read(self.opts.interval_s)
                top = sorted(snap.per_proc_cpu.items(), key=lambda kv: kv[1], reverse=True)[:50]
                fg_pids = self._pick_foreground_pids(top)

                procs: List[ProcView] = []
                for pid, frac in top:
                    try:
                        proc = psutil.Process(pid)
                        name = proc.name()
                        if is_system_critical(name, self.cfg.allowlist_system):
                            continue
                        io = snap.per_proc_io_bps.get(pid, (0, 0))
                        procs.append(
                            ProcView(
                                pid=pid,
                                name=name,
                                is_fg=pid in fg_pids,
                                cpu_frac=frac,
                                io_r_bps=io[0],
                                io_w_bps=io[1],
                            )
                        )
                    except Exception:
                        pass

                decision = self.ctrl.step(snap.util, procs)
                tel = decision.telemetry
                print(
                    "PRCI(sys/fg/bg)="
                    f"{tel['prci_sys']:.3f}/{tel['prci_fg']:.3f}/{tel['prci_bg']:.3f} "
                    "C(cpu/disk/net)="
                    f"{tel['c_cpu']:.2f}/{tel['c_disk']:.2f}/{tel['c_net']:.2f} "
                    f"act={bool(decision.acting)} procs={len(procs)}"
                )

                if self.opts.mode == "active":
                    if self.caps.can_set_priority:
                        for pid in decision.boost.keys():
                            set_cpu_priority(pid, "fg")
                        for pid in decision.throttle.keys():
                            set_cpu_priority(pid, "bg")
                    else:
                        print("[LRC] pywin32 not available -> CPU priority untouched")

                    if self.caps.can_set_io_priority:
                        for pid in decision.throttle.keys():
                            set_io_priority(pid, 3)
                    else:
                        print("[LRC] psutil ionice missing -> IO priority untouched")
        finally:
            self.reader.close()
