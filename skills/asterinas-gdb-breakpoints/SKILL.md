---
name: asterinas-gdb-breakpoints
description: Use this primitive skill when an Asterinas investigation needs breakpoints, hardware breakpoints, conditional breakpoints, watchpoints, or command lists that turn a debugging hypothesis into concrete GDB stops and evidence.
---

# Asterinas GDB Breakpoints

## Primitive Contract

Input: a hypothesis, a target symbol or expression, and the state that must be
captured when the program stops.

Output: a minimal GDB stop plan with commands to capture evidence and either
continue or hand control back to the user.

## Procedure

1. State the invariant being checked before placing the stop.
2. Prefer one precise symbol breakpoint over broad `rbreak` patterns.
3. Use `hbreak` for early boot code or ROM/identity-mapped code when normal
   software breakpoints fail.
4. Use conditions only when the expression is cheap and stable at the stop.
5. Use watchpoints after the watched object address is known and expected to
   remain valid.
6. Add a short `commands` block when repeated manual inspection would be
   error-prone.

## Command Shapes

```gdb
info address SYMBOL
break SYMBOL
break SYMBOL if CONDITION
hbreak SYMBOL
watch -location EXPRESSION
```

Evidence command block:

```gdb
commands
  silent
  printf "hit: SYMBOL\n"
  bt 12
  info registers
  continue
end
```

Do not leave broad tracing enabled after it has answered the question. Disable
or delete stops that no longer serve the active hypothesis.
