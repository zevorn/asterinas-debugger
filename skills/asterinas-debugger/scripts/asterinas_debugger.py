#!/usr/bin/env python3
"""Plan Asterinas GDB helper workflows."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path


HELPER_REL = Path("scripts/gdb/asterinas-gdb.py")
HELPER_DIR_REL = Path("scripts/gdb/helper")
SMOKE_REL = Path("scripts/gdb/test/smoke.py")
SMOKE_RUNNER_REL = Path("scripts/gdb/test/run_smoke.sh")


WORKFLOWS = {
    "boot": {
        "purpose": "early boot, entry, and helper attachment failures",
        "primitives": [
            "asterinas-gdb-session",
            "asterinas-gdb-inspect",
            "asterinas-gdb-breakpoints",
        ],
        "baseline": ["ast-version", "info pretty-printer"],
        "stops": ["hbreak aster_kernel::__ostd_main"],
        "checks": ["bt 12", "info registers"],
    },
    "process-loading": {
        "purpose": "ELF loading, dynamic libraries, VMAs, and exec setup",
        "primitives": [
            "asterinas-gdb-session",
            "asterinas-gdb-inspect",
            "asterinas-gdb-breakpoints",
            "asterinas-gdb-probes",
        ],
        "baseline": [
            "ast-ps",
            "ast-threads",
            "ast-fds 1",
            "p *$ast_process(1)",
            "p *$ast_thread(1)",
        ],
        "stops": [
            "# break on the loader, ELF, VMA, or page-fault symbol",
            "# that matches the current source tree",
        ],
        "checks": [
            "bt 16",
            "p *$ast_file_table(1)",
            "p/r (*$ast_thread(1)).is_exited",
        ],
    },
    "scheduling": {
        "purpose": "task state, wakeup, blocking, and exit bugs",
        "primitives": [
            "asterinas-gdb-session",
            "asterinas-gdb-inspect",
            "asterinas-gdb-breakpoints",
        ],
        "baseline": ["ast-threads", "p *$ast_thread(1)"],
        "stops": ["# break on scheduler enqueue, wake, block, or exit path"],
        "checks": ["bt 16", "p (*$ast_thread(1)).is_exited"],
    },
    "filesystem": {
        "purpose": "path lookup, fd table, VFS, mount, and file operation bugs",
        "primitives": [
            "asterinas-gdb-session",
            "asterinas-gdb-inspect",
            "asterinas-gdb-breakpoints",
            "asterinas-gdb-probes",
        ],
        "baseline": ["ast-ps", "ast-fds 1", "p *$ast_file_table(1)"],
        "stops": ["# break on lookup, open, close, read, write, or mount path"],
        "checks": ["bt 16", "p *$ast_process(1)"],
    },
    "driver": {
        "purpose": "device init, interrupt, MMIO, PCI, virtio, or block bugs",
        "primitives": [
            "asterinas-gdb-session",
            "asterinas-gdb-inspect",
            "asterinas-gdb-breakpoints",
        ],
        "baseline": ["ast-version", "ast-threads"],
        "stops": ["# break on the concrete driver function under review"],
        "checks": ["bt 16", "info registers"],
    },
    "network": {
        "purpose": "socket, queue, packet-flow, virtio-net, and IRQ bugs",
        "primitives": [
            "asterinas-gdb-session",
            "asterinas-gdb-inspect",
            "asterinas-gdb-breakpoints",
            "asterinas-gdb-probes",
        ],
        "baseline": ["ast-ps", "ast-fds 1", "ast-threads"],
        "stops": ["# break on syscall, stack, driver, IRQ, or completion path"],
        "checks": ["bt 16", "# print queue and socket state"],
    },
    "framekernel": {
        "purpose": "kernel/OSTD boundary, timer, memory, task, or arch issues",
        "primitives": [
            "asterinas-gdb-session",
            "asterinas-gdb-inspect",
            "asterinas-gdb-breakpoints",
        ],
        "baseline": ["ast-version", "ast-threads"],
        "stops": ["# break on the boundary symbol that owns the transition"],
        "checks": ["bt 16", "p/r OBJECT"],
    },
}


def find_repo(explicit: str | None) -> Path | None:
    """Find the Asterinas repository that contains the GDB helper."""
    candidates = []
    if explicit:
        candidates.append(Path(explicit))

    env_repo = os.environ.get("ASTERINAS_REPO")
    if env_repo:
        candidates.append(Path(env_repo))

    current = Path.cwd()
    candidates.extend([current, *current.parents])

    for candidate in candidates:
        repo = candidate.expanduser().resolve()
        if (repo / HELPER_REL).is_file():
            return repo

    return None


def require_workflow(name: str) -> dict[str, object]:
    try:
        return WORKFLOWS[name]
    except KeyError:
        choices = ", ".join(sorted(WORKFLOWS))
        raise SystemExit(f"unknown workflow '{name}'; expected one of: {choices}")


def print_list() -> None:
    for name in sorted(WORKFLOWS):
        workflow = WORKFLOWS[name]
        print(f"{name}: {workflow['purpose']}")


def print_repo_check(repo: Path | None) -> int:
    if repo is None:
        print("Asterinas repo: not found")
        print("Pass --repo <path> or set ASTERINAS_REPO.")
        return 1

    checks = [
        ("helper entry", repo / HELPER_REL),
        ("helper package", repo / HELPER_DIR_REL),
        ("smoke test", repo / SMOKE_REL),
        ("smoke runner", repo / SMOKE_RUNNER_REL),
    ]

    print(f"Asterinas repo: {repo}")
    status = 0
    for label, path in checks:
        exists = path.exists()
        state = "ok" if exists else "missing"
        print(f"{label}: {state} ({path})")
        status |= 0 if exists else 1

    for binary in ["docker", "tmux", "rust-gdb"]:
        path = shutil.which(binary)
        state = path if path else "missing"
        print(f"{binary}: {state}")

    if (repo / "Makefile").is_file():
        print("full smoke command: make gdb-smoke-test")

    return status


def print_plan(name: str, repo: Path | None) -> None:
    workflow = require_workflow(name)
    print(f"Workflow: {name}")
    print(f"Purpose: {workflow['purpose']}")
    if repo:
        print(f"Asterinas repo: {repo}")
        print(f"Helper: {repo / HELPER_REL}")
    else:
        print("Asterinas repo: not resolved")
    print()
    print("Primitive skills:")
    for primitive in workflow["primitives"]:
        print(f"- ${primitive}")
    print()
    print("Baseline commands:")
    for command in workflow["baseline"]:
        print(f"- {command}")
    print()
    print("Stop plan:")
    for command in workflow["stops"]:
        print(f"- {command}")
    print()
    print("Evidence checks:")
    for command in workflow["checks"]:
        print(f"- {command}")


def print_gdbinit(name: str, repo: Path | None, remote: str | None) -> int:
    workflow = require_workflow(name)
    if repo is None:
        print("error: Asterinas repo not found", file=sys.stderr)
        print("pass --repo <path> or set ASTERINAS_REPO", file=sys.stderr)
        return 1

    print("set pagination off")
    print("set confirm off")
    if remote:
        print(f"target remote {remote}")
    print(f"source {repo / HELPER_REL}")
    print("ast-version")
    print("info pretty-printer")
    print()
    print(f"# Baseline for {name}")
    for command in workflow["baseline"]:
        print(command)
    print()
    print(f"# Stops for {name}")
    for command in workflow["stops"]:
        print(command)
    print()
    print(f"# Evidence checks for {name}")
    for command in workflow["checks"]:
        print(command)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate Asterinas GDB helper workflow plans.",
    )
    parser.add_argument(
        "--repo",
        help="Asterinas source tree; defaults to ASTERINAS_REPO or cwd parents",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list", help="list known workflows")
    subparsers.add_parser("doctor", help="check helper and tool availability")

    plan_parser = subparsers.add_parser("plan", help="print a workflow plan")
    plan_parser.add_argument("workflow", choices=sorted(WORKFLOWS))

    gdbinit_parser = subparsers.add_parser(
        "gdbinit",
        help="print a .gdb skeleton for a workflow",
    )
    gdbinit_parser.add_argument("workflow", choices=sorted(WORKFLOWS))
    gdbinit_parser.add_argument("--remote", help="GDB remote endpoint")

    return parser


def normalize_argv(argv: list[str] | None) -> list[str] | None:
    """Allow --repo before or after the subcommand."""
    if argv is None:
        argv = sys.argv[1:]

    repo_args: list[str] = []
    remaining: list[str] = []
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--repo":
            if index + 1 >= len(argv):
                raise SystemExit("--repo requires a path")
            repo_args = [arg, argv[index + 1]]
            index += 2
        elif arg.startswith("--repo="):
            repo_args = [arg]
            index += 1
        else:
            remaining.append(arg)
            index += 1

    return [*repo_args, *remaining]


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(normalize_argv(argv))

    if args.command == "list":
        print_list()
        return 0

    repo = find_repo(args.repo)
    if args.command == "doctor":
        return print_repo_check(repo)
    if args.command == "plan":
        print_plan(args.workflow, repo)
        return 0
    if args.command == "gdbinit":
        return print_gdbinit(args.workflow, repo, args.remote)

    parser.error(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
