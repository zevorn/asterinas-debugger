---
name: asterinas-debugger
description: Use this workflow skill when debugging Asterinas kernel issues with rust-gdb, QEMU, Docker, and the Asterinas GDB helpers. It classifies boot, process loading, scheduling, filesystem, driver, network or peripheral, and framekernel problems, then composes the asterinas-gdb-session, asterinas-gdb-breakpoints, asterinas-gdb-inspect, and asterinas-gdb-probes primitive skills into an evidence-driven flow.
---

# Asterinas Debugger

## Overview

This is the workflow skill for Asterinas debugging. It selects a scenario,
loads the relevant primitive skills, and drives GDB work in short evidence
loops.

## Included Primitive Skills

Use these skills as flow primitives:

- `$asterinas-gdb-session`: prepare or reuse Docker, QEMU, rust-gdb, tmux, and
  helper loading.
- `$asterinas-gdb-breakpoints`: choose breakpoints, hardware breakpoints,
  conditional breakpoints, watchpoints, and command lists.
- `$asterinas-gdb-inspect`: inspect Asterinas helper commands, convenience
  functions, kernel symbols, wrapper printers, processes, threads, and file
  descriptors.
- `$asterinas-gdb-probes`: write repeatable GDB Python probes when a manual
  command sequence becomes fragile or needs repeated sampling.

Do not inline all primitive details into this workflow. Load only the primitive
skill needed for the current step, then return to this workflow for scenario
control.

## Workflow

1. Classify the symptom into one scenario in `references/workflows.md`.
2. Use `$asterinas-gdb-session` to confirm the target ELF, remote endpoint, and
   helper loading path. Reuse an already warmed Asterinas container whenever
   one exists.
3. Use `$asterinas-gdb-inspect` to take a baseline snapshot before changing
   execution state.
4. Use `$asterinas-gdb-breakpoints` to place the smallest useful stop or
   watchpoint for the current hypothesis.
5. Use `$asterinas-gdb-probes` only after the same inspection needs to be run
   more than once or across several stops.
6. After each stop, record the exact command, output summary, and next
   hypothesis using `references/evidence.md`.

## Asterinas Repository Binding

Run this skill from the Asterinas source tree whenever possible. The workflow
expects the current PR's GDB helper files to exist under:

- `scripts/gdb/asterinas-gdb.py`
- `scripts/gdb/helper/`
- `scripts/gdb/test/`

If the working directory is not the Asterinas tree, pass the repository path to
the utility script with `--repo <path>` or set `ASTERINAS_REPO=<path>`. The
script searches upward from the current directory before using the environment
variable.

## Agent Output Directory

Put agent-generated debugging artifacts under:

```text
build/agent/asterinas-debugger/
```

This includes temporary `.gdb` files, GDB Python probes, QEMU logs, trace
outputs, and scratch notes created for one debugging session. Do not write these
files into Asterinas source directories such as `scripts/`, `kernel/`, `ostd/`,
or `test/`.

## Container Rule

Do not create a fresh Asterinas Docker container until reusable containers have
been checked. Prefer, in order:

1. a running Asterinas container with the target checkout mounted;
2. a stopped Asterinas container that was previously used for this checkout and
   can be started again;
3. a new container, only when no reusable container exists.

For preflight checks, inspect files and directories directly. Avoid commands
that can trigger rustup updates, such as `rustc`, `cargo`, or `cargo osdk`,
until the intended container has been selected and its toolchain targets have
been checked.

Prefer helper commands first. Fall back to raw GDB expressions or GDB Python
when helper output is missing, too broad, or not close enough to the object
under investigation.

## Scenario References

- `references/workflows.md`: boot, process loading, scheduling, filesystem,
  driver, network or peripheral, and framekernel workflows.
- `references/evidence.md`: evidence format, stop summaries, and escalation
  rules.

## Utility Script

The workflow script prints deterministic plans and `.gdb` skeletons:

```bash
python3 skills/asterinas-debugger/scripts/asterinas_debugger.py list
python3 skills/asterinas-debugger/scripts/asterinas_debugger.py doctor --repo .
python3 skills/asterinas-debugger/scripts/asterinas_debugger.py plan \
    process-loading --repo .
python3 skills/asterinas-debugger/scripts/asterinas_debugger.py gdbinit process-loading \
    --repo . \
    --remote :1234
python3 skills/asterinas-debugger/scripts/asterinas_debugger.py lifecycle-gdb \
    --repo . \
    --remote .osdk-gdb-socket
```

Generated `.gdb` files are starting points. Review the symbol names against the
current build before relying on them.

Lifecycle trace files are written under `build/agent/asterinas-debugger/` by
default. They are temporary debugging artifacts and should not be committed to
the Asterinas source tree.
