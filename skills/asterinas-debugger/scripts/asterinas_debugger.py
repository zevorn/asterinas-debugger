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
DEFAULT_AGENT_DIR = Path("build/agent/asterinas-debugger")

LOOP_TEMPLATE = [
    "Goal:",
    "Iteration:",
    "Hypothesis:",
    "Stop or command:",
    "Observed:",
    "Raw fallback:",
    "Verdict: supported | rejected | inconclusive | complete",
    "Next step:",
]


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
    print()
    print("Goal loop record:")
    for line in LOOP_TEMPLATE:
        print(f"- {line}")


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


def lifecycle_python() -> str:
    return r'''"""Trace an Asterinas process lifecycle through GDB helpers."""

import gdb


EVENTS = []
MAX_COMMAND_LINES = 10
TARGET_PID = None


def _run(command):
    try:
        output = gdb.execute(command, to_string=True)
    except gdb.error as error:
        gdb.write(f"TRACE-CMD {command}: ERROR: {error}\n")
        return

    gdb.write(f"TRACE-CMD {command}:\n")
    for line in output.rstrip().splitlines()[:MAX_COMMAND_LINES]:
        gdb.write(f"TRACE-OUT {line}\n")


def _field_int(value, field):
    try:
        return int(value[field])
    except (gdb.error, TypeError, ValueError):
        return None


def _context_pid_tid():
    try:
        ctx = gdb.parse_and_eval("ctx")
        pid = _field_int(ctx["process"], "pid")
        tid = _field_int(ctx["posix_thread"], "tid")
        return pid, tid
    except gdb.error:
        return None, None


def _exit_process_pid():
    try:
        process = gdb.parse_and_eval("current_process")
        return _field_int(process, "pid")
    except gdb.error:
        return None


def _snapshot(label):
    pid, tid = _context_pid_tid()
    if pid is None and label == "exit_process":
        pid = _exit_process_pid()

    EVENTS.append((label, pid, tid))
    event_no = len(EVENTS)
    gdb.write(f"\nTRACE-EVENT {event_no}: {label}")
    if pid is not None:
        gdb.write(f" pid={pid}")
    if tid is not None:
        gdb.write(f" tid={tid}")
    gdb.write("\n")

    _run("bt 6")
    _run("ast-ps")
    _run("ast-threads")

    sample_pid = pid if pid is not None else TARGET_PID
    if sample_pid is not None:
        _run(f"ast-ps {sample_pid}")
        _run(f"ast-fds {sample_pid}")

    if TARGET_PID is not None and TARGET_PID != sample_pid:
        _run(f"ast-ps {TARGET_PID}")
        _run(f"ast-fds {TARGET_PID}")

    _run("p (*$ast_thread(1)).is_exited")
    _run("p/r (*$ast_thread(1)).is_exited")


class LifecycleBreakpoint(gdb.Breakpoint):
    def __init__(self, spec, label, final=False):
        super().__init__(spec)
        self.silent = True
        self.label = label
        self.final = final

    def stop(self):
        _snapshot(self.label)
        if not self.final:
            return False
        if TARGET_PID is None:
            return True

        pid = _exit_process_pid()
        return pid == TARGET_PID


def _try_break(spec, label, final=False):
    try:
        LifecycleBreakpoint(spec, label, final)
        gdb.write(f"TRACE-INSTALL {label}: {spec}\n")
    except gdb.error as error:
        gdb.write(f"TRACE-INSTALL {label}: ERROR: {error}\n")


def install(target_pid=None):
    global TARGET_PID
    TARGET_PID = target_pid

    _run("ast-version")
    _try_break(
        "aster_kernel::process::process::init_proc::spawn_init_process",
        "spawn_init_process",
    )
    _try_break("aster_kernel::process::clone::clone_child", "clone_child")
    _try_break("aster_kernel::syscall::execve::sys_execve", "sys_execve")
    _try_break("aster_kernel::process::execve::do_execve", "do_execve")
    _try_break("aster_kernel::syscall::exit::sys_exit", "sys_exit")
    _try_break(
        "aster_kernel::syscall::exit_group::sys_exit_group",
        "sys_exit_group",
    )
    _try_break("aster_kernel::process::posix_thread::exit::do_exit", "do_exit")
    _try_break(
        "aster_kernel::process::posix_thread::exit::do_exit_group",
        "do_exit_group",
    )
    _try_break(
        "aster_kernel::process::exit::exit_process",
        "exit_process",
        final=True,
    )


def finalize():
    gdb.write("\nTRACE-SUMMARY:\n")
    for index, (label, pid, tid) in enumerate(EVENTS, start=1):
        gdb.write(f"TRACE-SUMMARY {index}: {label}")
        if pid is not None:
            gdb.write(f" pid={pid}")
        if tid is not None:
            gdb.write(f" tid={tid}")
        gdb.write("\n")

    if not EVENTS:
        raise gdb.GdbError("no lifecycle events were observed")
    if not any(label == "exit_process" for label, _, _ in EVENTS):
        raise gdb.GdbError("process exit was not observed")

    gdb.write("TRACE: lifecycle ok\n")
'''


def _gdb_path(path: Path, repo: Path) -> str:
    try:
        return str(path.relative_to(repo))
    except ValueError:
        return str(path)


def lifecycle_gdb(repo: Path, output_dir: Path, remote: str, pid: int | None) -> str:
    helper_path = _gdb_path(repo / HELPER_REL, repo)
    python_dir = _gdb_path(output_dir, repo)
    pid_arg = "None" if pid is None else str(pid)
    return f"""# Generated by asterinas-debugger. Do not commit this file.
set pagination off
set confirm off

target remote {remote}
source {helper_path}

hbreak __ostd_main
continue
delete

python
import sys
sys.path.insert(0, {python_dir!r})
import process_lifecycle
process_lifecycle.install(target_pid={pid_arg})
end

continue

python
process_lifecycle.finalize()
end

quit
"""


def write_lifecycle_files(
    repo: Path | None,
    output_dir_arg: str | None,
    remote: str,
    pid: int | None,
) -> int:
    if repo is None:
        print("error: Asterinas repo not found", file=sys.stderr)
        print("pass --repo <path> or set ASTERINAS_REPO", file=sys.stderr)
        return 1

    if output_dir_arg:
        output_dir = Path(output_dir_arg).expanduser()
        if not output_dir.is_absolute():
            output_dir = repo / output_dir
    else:
        output_dir = repo / DEFAULT_AGENT_DIR

    output_dir.mkdir(parents=True, exist_ok=True)

    python_path = output_dir / "process_lifecycle.py"
    gdb_path = output_dir / "process_lifecycle.gdb"
    python_path.write_text(lifecycle_python())
    gdb_path.write_text(lifecycle_gdb(repo, output_dir, remote, pid))

    print(f"wrote {gdb_path}")
    print(f"wrote {python_path}")
    print(f"run: rust-gdb --batch --command={gdb_path} <kernel-elf>")
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

    lifecycle_parser = subparsers.add_parser(
        "lifecycle-gdb",
        help="write process lifecycle GDB scripts under build/agent",
    )
    lifecycle_parser.add_argument(
        "--output-dir",
        help="output directory; defaults to build/agent/asterinas-debugger",
    )
    lifecycle_parser.add_argument(
        "--pid",
        type=int,
        help="stop only when this PID exits; default stops on first process exit",
    )
    lifecycle_parser.add_argument(
        "--remote",
        default=".osdk-gdb-socket",
        help="GDB remote endpoint; default is .osdk-gdb-socket",
    )

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
    if args.command == "lifecycle-gdb":
        return write_lifecycle_files(repo, args.output_dir, args.remote, args.pid)

    parser.error(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
