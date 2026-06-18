# Asterinas Debugger Workflows

Each workflow composes the primitive skills in this order:

1. `$asterinas-gdb-session`
2. `$asterinas-gdb-inspect`
3. `$asterinas-gdb-breakpoints`
4. `$asterinas-gdb-probes`, only if repeated sampling is needed

Generated workflow artifacts should live under
`build/agent/asterinas-debugger/` in the Asterinas repository.

## Boot

Use for early traps, missing helper attachment, failed kernel entry, or hangs
before PID 1 is visible.

- Confirm helper loading with `ast-version`.
- If normal breakpoints fail, try `hbreak` on the early symbol.
- Capture `bt`, registers, and the first successful helper baseline.
- Do not assume process helpers work until `ast-ps` can list PID 1.

## Process Loading

Use for ELF loading, dynamic library mapping, user image setup, argv/envp
layout, or a process that starts but fails before the expected user code.

- Start with `ast-ps`, `ast-threads`, and `ast-fds <pid>`.
- Inspect `$ast_process(pid)` and `$ast_thread(tid)` before adding stops.
- Break on loader, ELF, VMA, page-fault, or file-open symbols that match the
  current source tree.
- Watch the process file table or VM mapping only after the target object
  address is known.
- If dynamic library state is unclear, write a probe that prints process,
  thread, fd, and mapping summaries at the same stop.

## Scheduling

Use for stuck tasks, wrong runnable state, unexpected exit, or wakeup problems.

- Capture `ast-threads` and the target `$ast_thread(tid)`.
- Compare friendly and raw output for atomic and lock fields.
- Break on scheduler enqueue, dequeue, wake, block, and exit paths.
- Watch only stable task or thread fields.

## Filesystem

Use for path lookup, fd table, VFS, mount, cache, or file operation bugs.

- Capture `ast-fds <pid>` and `$ast_file_table(pid)`.
- Break on path lookup and concrete file operation functions.
- Compare helper fd summaries with raw file table entries.
- Add GDB Python probes when the same fd table must be sampled across several
  opens, closes, or exec transitions.

## Driver

Use for block, console, PCI, virtio, interrupt, or device initialization bugs.

- Confirm the boot stage and first failing device operation.
- Prefer symbol breakpoints near the concrete driver path.
- Capture registers and backtraces at interrupt or MMIO boundaries.
- Use watchpoints sparingly because device paths can execute frequently.

## Network Or Peripheral Stack

Use for network stack, socket, virtio-net, interrupt, queue, or packet-flow
bugs.

- Start from process and fd state when the symptom is user-visible.
- Move down to socket, queue, driver, and interrupt state only as needed.
- Use command lists or probes for packet counters and queue state.
- Keep each sampling point labeled with the direction: syscall, stack, driver,
  interrupt, or completion.

## Framekernel Boundary

Use when the failure crosses kernel and OSTD responsibilities, such as memory,
timer, task, interrupt, or architecture setup.

- Confirm whether the affected code is in `kernel/` or `ostd/`.
- Preserve the safe/unsafe boundary in notes and proposed fixes.
- Use raw output for layout-sensitive OSTD structures.
- Escalate to source breakpoints only after helper and convenience function
  output identifies the object being crossed.
