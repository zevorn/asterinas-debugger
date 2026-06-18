---
name: asterinas-gdb-inspect
description: Use this primitive skill when an Asterinas debugging task needs to inspect helper commands, convenience functions, process and thread objects, file descriptors, kernel symbols, atomics, locks, or Rust pretty-printer output in GDB.
---

# Asterinas GDB Inspect

## Primitive Contract

Input: a live Asterinas GDB session and the object or subsystem to inspect.

Output: a compact state snapshot with helper output, raw fallback output when
needed, and the next object to inspect.

## Baseline Snapshot

Run these first when the helper is expected to be loaded:

```gdb
ast-version
info pretty-printer
ast-ps
ast-threads
ast-pstree
```

For a specific process:

```gdb
ast-ps 1
ast-fds 1
p *$ast_process(1)
p *$ast_thread(1)
p *$ast_pid_table()
p *$ast_file_table(1)
```

The expected helper implementation is the current Asterinas GDB helper under
`scripts/gdb/asterinas-gdb.py`. If these commands are missing, inspect the
session setup before debugging kernel state.

## Wrapper-Type Checks

Pretty-printer checks should cover both friendly and raw output:

```gdb
p (*$ast_thread(1)).is_exited
p/r (*$ast_thread(1)).is_exited
```

Use friendly output to understand state quickly. Use raw output when checking
layout compatibility, field offsets, or whether a printer is hiding the value
that matters.

## Escalation

Escalate from helper commands to raw GDB when:

- a helper cannot find an expected object;
- a command prints a summary but not the field needed for the hypothesis;
- pretty-printer output differs from raw layout output;
- a kernel symbol lookup works but object navigation does not.

Record both the helper command and the raw expression so the discrepancy can be
reproduced.
