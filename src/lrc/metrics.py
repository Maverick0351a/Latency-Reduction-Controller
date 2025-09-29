from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Tuple

import psutil

try:
    import pynvml  # type: ignore

    _HAS_NVML = True
except Exception:  # pragma: no cover - optional dependency
    _HAS_NVML = False


@dataclass
class ResourceSnapshot:
    util: Dict[str, float]
    per_proc_cpu: Dict[int, float]
    per_proc_io_bps: Dict[int, Tuple[int, int]]
    ts: float


class MetricReader:
    """Collect system- and process-level metrics with smoothing baselines."""

    def __init__(self) -> None:
        self._net_prev = psutil.net_io_counters(pernic=False)
        self._disk_prev = psutil.disk_io_counters()
        self._ts_prev = time.time()
        self._per_proc_prev: Dict[int, Tuple[int, int]] = {}
        if _HAS_NVML:
            try:
                pynvml.nvmlInit()
            except Exception:
                pass

    def close(self) -> None:
        if _HAS_NVML:
            try:
                pynvml.nvmlShutdown()
            except Exception:
                pass

    def read(self, interval_s: float = 0.5) -> ResourceSnapshot:
        time.sleep(interval_s)
        now = time.time()
        dt = max(1e-3, now - self._ts_prev)

        cpu_util = psutil.cpu_percent(None) / 100.0
        ram_util = psutil.virtual_memory().percent / 100.0

        disk_now = psutil.disk_io_counters()
        dr = max(0, disk_now.read_bytes - self._disk_prev.read_bytes)
        dw = max(0, disk_now.write_bytes - self._disk_prev.write_bytes)
        disk_bps = (dr + dw) / dt
        disk_util = min(1.0, disk_bps / (500 * 1024 * 1024))
        self._disk_prev = disk_now

        net_now = psutil.net_io_counters(pernic=False)
        nr = max(0, net_now.bytes_recv - self._net_prev.bytes_recv)
        ns = max(0, net_now.bytes_sent - self._net_prev.bytes_sent)
        net_bps = (nr + ns) / dt
        link_mbps = 100.0
        try:
            stats = psutil.net_if_stats()
            link_mbps = max(
                [s.speed for s in stats.values() if s.isup] + [link_mbps]
            ) or link_mbps
        except Exception:
            pass
        net_util = min(1.0, net_bps / (link_mbps * 1024 * 1024 / 8.0))
        self._net_prev = net_now

        gpu_util = 0.0
        if _HAS_NVML:
            try:
                count = pynvml.nvmlDeviceGetCount()
                vals = []
                for idx in range(count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(idx)
                    rates = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    vals.append(rates.gpu / 100.0)
                gpu_util = max(vals) if vals else 0.0
            except Exception:
                gpu_util = 0.0

        util = {
            "CPU": cpu_util,
            "GPU": gpu_util,
            "RAM": ram_util,
            "DISK": disk_util,
            "NET": net_util,
        }

        procs = {
            p.pid: p
            for p in psutil.process_iter(attrs=["name", "cpu_percent"])
        }
        total_pct = sum((p.info["cpu_percent"] or 0.0) for p in procs.values()) or 1e-3
        per_proc_cpu = {
            pid: max(0.0, min(1.0, (p.info["cpu_percent"] or 0.0) / total_pct))
            for pid, p in procs.items()
        }

        per_proc_io_bps: Dict[int, Tuple[int, int]] = {}
        for pid, proc in procs.items():
            try:
                io = proc.io_counters()
                pr0, pw0 = self._per_proc_prev.get(pid, (io.read_bytes, io.write_bytes))
                per_proc_io_bps[pid] = (
                    int(max(0, (io.read_bytes - pr0) / dt)),
                    int(max(0, (io.write_bytes - pw0) / dt)),
                )
                self._per_proc_prev[pid] = (io.read_bytes, io.write_bytes)
            except Exception:
                pass

        self._ts_prev = now
        return ResourceSnapshot(
            util=util,
            per_proc_cpu=per_proc_cpu,
            per_proc_io_bps=per_proc_io_bps,
            ts=now,
        )
