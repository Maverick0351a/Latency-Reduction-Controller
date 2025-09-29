from __future__ import annotations

import argparse

from .agent import Agent, AgentOptions
from .config import ControllerConfig


def main() -> None:
    parser = argparse.ArgumentParser("lrc")
    parser.add_argument("--mode", choices=["shadow", "active"], default="shadow")
    parser.add_argument("--interval", type=float, default=0.5)
    args = parser.parse_args()

    cfg = ControllerConfig()
    Agent(cfg, AgentOptions(interval_s=args.interval, mode=args.mode)).run()


if __name__ == "__main__":
    main()
