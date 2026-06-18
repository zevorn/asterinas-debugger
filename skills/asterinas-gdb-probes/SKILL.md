---
name: asterinas-gdb-probes
description: Use this primitive skill when Asterinas debugging needs repeatable GDB Python probes for object snapshots, helper command checks, conditional sampling, or comparisons that are too fragile to run manually at every stop.
---

# Asterinas GDB Probes

## Primitive Contract

Input: a repeated inspection need, the GDB expressions or helper commands to
run, and the stop where the probe should execute.

Output: a small GDB Python snippet or script that prints deterministic,
grep-friendly evidence.

## Probe Rules

1. Keep probes read-only unless the investigation explicitly requires state
   mutation.
2. Print labels before values so logs remain understandable after several
   stops.
3. Catch `gdb.error` around optional helper calls and report the failed command.
4. Prefer `gdb.execute(..., to_string=True)` for command output and
   `gdb.parse_and_eval()` for values.
5. Keep generated output short enough to compare across runs.
6. For repository-local scripts, write generated `.gdb`, `.py`, and log files
   under `build/agent/asterinas-debugger/`, not under Asterinas source
   directories.

## Helper Script

Use `scripts/make_probe.py` to generate a small GDB Python block:

```bash
python3 skills/asterinas-gdb-probes/scripts/make_probe.py pid-snapshot --pid 1
```

Paste the generated block at the GDB prompt or redirect it into a `.gdb` file.

For longer probes tied to one Asterinas checkout, generate or place them under:

```text
build/agent/asterinas-debugger/
```
