#!/usr/bin/env python3
"""Generate small GDB Python probes for Asterinas helper sessions."""

from __future__ import annotations

import argparse


def pid_snapshot(pid: int) -> str:
    return f"""python
import gdb

def run(command):
    try:
        gdb.write(f"{{command}}:\\n")
        gdb.write(gdb.execute(command, to_string=True))
    except gdb.error as error:
        gdb.write(f"{{command}}: ERROR: {{error}}\\n")

for command in [
    "ast-ps {pid}",
    "ast-fds {pid}",
    "p *$ast_process({pid})",
    "p *$ast_file_table({pid})",
]:
    run(command)
end
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate Asterinas GDB Python probe snippets.",
    )
    subparsers = parser.add_subparsers(dest="probe", required=True)

    pid_parser = subparsers.add_parser(
        "pid-snapshot",
        help="print process and fd helper state for one PID",
    )
    pid_parser.add_argument("--pid", type=int, required=True)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.probe == "pid-snapshot":
        print(pid_snapshot(args.pid), end="")
        return 0
    raise SystemExit(f"unsupported probe: {args.probe}")


if __name__ == "__main__":
    raise SystemExit(main())
