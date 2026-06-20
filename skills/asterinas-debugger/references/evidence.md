# Evidence Rules

Use one evidence block per loop iteration. Keep it short enough to paste into
an issue, PR comment, Goal update, or debugging note.

The loop shape is:

```text
Goal -> baseline -> hypothesis -> stop/probe -> evidence -> verdict -> next step
```

## Block Format

```text
Goal:
Iteration:
Hypothesis:
Stop or command:
Observed:
Raw fallback:
Verdict:
Next step:
```

`Stop or command` must include the exact GDB command, helper command, or Python
probe that produced the observation. `Raw fallback` is optional, but should be
filled when pretty-printer output, helper output, or object navigation is under
review. `Verdict` should be one of: `supported`, `rejected`, `inconclusive`,
or `complete`.

Use `complete` only when the evidence answers the active Goal. Use
`inconclusive` when the next iteration needs a narrower hypothesis, a different
stop, or a probe.

## Minimum Baseline

Before placing scenario breakpoints, capture:

```gdb
ast-version
info pretty-printer
ast-ps
ast-threads
```

For process or file investigations, add:

```gdb
ast-ps 1
ast-fds 1
p *$ast_process(1)
p *$ast_file_table(1)
```

## Artifact Location

Store session logs, generated `.gdb` files, generated GDB Python probes, and
trace output in:

```text
build/agent/asterinas-debugger/
```

These files are agent scratch artifacts. They should not be added to Asterinas
source directories or included in the Asterinas PR.

## Container Evidence

When a debugging session uses Docker, record which container was selected and
why:

```text
Container:
Image:
State before use:
Mounted checkout:
Rust targets present:
Kernel ELF:
Initramfs:
```

Use direct file checks for this preflight. Avoid `rustc`, `cargo`, or
`cargo osdk` until the selected container is confirmed, because those commands
may trigger rustup target installation in a fresh container.

## Escalation Rule

Move one level lower only when the current level cannot answer the question:

1. Asterinas helper command.
2. Asterinas convenience function.
3. Raw GDB expression.
4. GDB Python probe.
5. Manual source-level breakpoint or watchpoint.

Record the failed or incomplete higher-level command before using the lower
level. That keeps helper gaps visible instead of hiding them inside raw GDB
work.

## Goal Updates

When the investigation is running under Codex Goal or Oh-My-Pi Goal, include a
short loop update after every stop:

```text
Goal state:
Latest evidence:
Verdict:
Next iteration:
```

Keep the Goal thread focused on the current hypothesis and evidence. Do not
store raw logs in the Goal; put full logs and probes under
`build/agent/asterinas-debugger/` and reference the filename.
