# Evidence Rules

Use one evidence block per hypothesis. Keep it short enough to paste into an
issue, PR comment, or debugging note.

## Block Format

```text
Hypothesis:
Stop or command:
Observed:
Raw fallback:
Conclusion:
Next step:
```

`Stop or command` must include the exact GDB command, helper command, or Python
probe that produced the observation. `Raw fallback` is optional, but should be
filled when pretty-printer output, helper output, or object navigation is under
review.

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
