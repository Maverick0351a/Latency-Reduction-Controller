# Latency Reduction Controller (LRC)

Windows-first foreground **latency & jitter** optimizer with a transparent control law:

- **Shadow mode**: observe decisions safely
- **Active mode**: adjust per-process priorities (CPU, I/O) with guardrails
- **Adaptive to Windows updates** via runtime capability detection & safe fallbacks
- **MSIX** packaging for easy install; PyInstaller-built Win32 payload

**Dual-licensed**: GPLv3 (public) or Commercial (proprietary use). See `DUAL-LICENSING.md`.

---

## How it works

LRC samples system load (CPU/GPU/RAM/DISK/NET), computes a bounded **contention signal** per resource,
and aggregates a **Prioritized Resource Contention Index (PRCI)** that emphasizes the foreground task.
When PRCI crosses a threshold (with hysteresis), LRC:

- **Boosts** likely-foreground processes (CPU priority up)
- **Throttles** heavy background contributors (CPU priority down, I/O priority lower)

All changes use documented, user-space Windows APIs and enforce minimum shares and recovery to avoid starvation.

---

## Quickstart (development)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -e ".[dev]"
```

### Run shadow mode (observe only)

```powershell
python -m lrc.cli --mode shadow
```

### Run active mode (apply safe adjustments)

```powershell
python -m lrc.cli --mode active
```

By default, LRC avoids system processes and only changes priorities for apps owned by your user session.

### Benchmark helpers (optional)

Install external tools for richer load gen (e.g. diskspd, iperf3, ffmpeg), then:

```powershell
python .\scripts\bench\run_bench.py --collect
```

Outputs summary CSV to `reports/bench_summary.csv` when `--collect` is provided.

### Build Win32 binary & MSIX

Build the payload (Win32 exe via PyInstaller):

```powershell
pip install pyinstaller
pyinstaller --onefile --name lrc.exe src\lrc\cli.py
mkdir dist\lrc-win
move .\dist\lrc.exe dist\lrc-win\lrc.exe
```

Pack an unsigned MSIX (requires Windows 10/11 SDK `makeappx`):

```powershell
.\packaging\msix\make_msix.ps1 -BuildDir "dist\lrc-win" -Out "LRC-App.msix"
```

Sign & install for dev sideloading:

```powershell
.\packaging\msix\sign_msix.ps1 -Msix "LRC-App.msix" -Pfx "dev_signing.pfx" -Password "Passw0rd!"
.\packaging\msix\install_msix.ps1 -Msix "LRC-App.msix" -Pfx "dev_signing.pfx" -Password "Passw0rd!"
```

For production, sign with a trusted code-signing certificate; end users must trust the cert to install MSIX packages.

---

## Adaptive to Windows updates

LRC probes capabilities at runtime:

- Windows build version (to gate features if APIs change)
- Presence of `pywin32` (CPU priority), `psutil.ionice` (I/O priority), `pynvml` (GPU telemetry)
- Safe fallbacks if a capability is missing (observe-only, or CPU-only adjustments)

This capability-first approach reduces breakage risk across Windows updates. When a capability degrades, LRC
drops to a less-invasive behavior rather than failing.

---

## Safety model

- No kernel hooks, no process injection—only documented user-space APIs (`SetPriorityClass`, `ionice`).
- System allowlist prevents touching critical OS/AV/EDR processes.
- Hysteresis & rate limits avoid oscillations.
- Recovery raises background shares when the system is calm.

---

## Licensing

- **GPLv3 (public)**: strong copyleft. Great for community users and academic settings.
- **Commercial license**: proprietary terms for closed-source integration or OEM bundling. See `LICENSE-COMMERCIAL.md` and contact `sales@worlddatafilter.com`.

Refer to `DUAL-LICENSING.md` for a summary of the two-track model.

---

## Roadmap

- Real foreground detection (active window → owning process tree)
- Per-process GPU & Disk attribution (where available)
- Profiles (Gaming/Creator/Enterprise) and UI panel
- WinGet/Chocolatey manifests; Microsoft Store submission
- Signed MSIX & MSI (optional admin service build)

---

## Contributing

Planned contributions require a CLA or Developer Certificate of Origin (DCO). Details to come in future updates.
