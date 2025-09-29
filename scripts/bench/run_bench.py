from __future__ import annotations

import argparse
import csv
import subprocess
from pathlib import Path
from typing import List

BENCH_SCRIPTS = [
    Path(__file__).with_name("win") / "fg_burst.ps1",
    Path(__file__).with_name("win") / "bg_disk.ps1",
    Path(__file__).with_name("win") / "bg_net.ps1",
]


def run_powershell(script: Path, collect: bool) -> subprocess.CompletedProcess[str]:
    cmd: List[str] = [
        "powershell",
        "-NoLogo",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
    ]
    if collect:
        cmd.append("-CollectCsv")
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run optional Windows load generation scripts.")
    parser.add_argument(
        "--collect",
        action="store_true",
        help="Write PowerShell CSV outputs (if emitted) to reports/bench_summary.csv",
    )
    args = parser.parse_args()

    reports = Path("reports")
    reports.mkdir(parents=True, exist_ok=True)
    summary_rows = []

    for script in BENCH_SCRIPTS:
        if not script.exists():
            print(f"[bench] Missing script {script}")
            continue
        print(f"[bench] Running {script.name} ...")
        proc = run_powershell(script, collect=args.collect)
        if proc.returncode != 0:
            print(f"[bench] {script.name} exited with {proc.returncode}")
            if proc.stderr:
                print(proc.stderr)
        if args.collect and proc.stdout:
            summary_rows.append([script.name, proc.stdout.strip()])

    if args.collect and summary_rows:
        out_csv = reports / "bench_summary.csv"
        with out_csv.open("w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["script", "output"]) 
            writer.writerows(summary_rows)
        print(f"[bench] Wrote {out_csv}")


if __name__ == "__main__":
    main()
