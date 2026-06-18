---
name: asterinas-gdb-session
description: "Use this primitive skill when an Asterinas debugging task needs a reproducible GDB session: find or reuse the project Docker container, start Docker service if needed, run QEMU with a remote GDB stub, attach rust-gdb to the kernel ELF, source scripts/gdb/asterinas-gdb.py, and keep tmux panes organized."
---

# Asterinas GDB Session

## Primitive Contract

Input: Asterinas workspace, target architecture, build profile, remote GDB
endpoint, and optional running Docker container.

Output: a live `rust-gdb` prompt attached to the target, with Asterinas helpers
loaded and the exact setup commands recorded.

## Procedure

1. Check for reusable Asterinas containers before creating a new one. Include
   both running and stopped containers.
2. Prefer a running container with the target checkout mounted. If none is
   running, start a stopped warm container for the same checkout before trying
   a fresh container.
3. If Docker is not reachable, start the Docker service first, then re-check
   the existing containers.
4. Inspect the selected container without triggering rustup. Check toolchain
   target directories directly under `/root/.rustup/toolchains/.../lib/rustlib`
   instead of running `rustc`, `cargo`, or `cargo osdk`.
5. Build or locate the target kernel ELF through Asterinas tooling. Prefer
   `cargo osdk debug --remote <endpoint>` when the workspace supports helper
   auto-loading.
6. If auto-loading is not available, launch `rust-gdb` manually, attach with
   `target remote <endpoint>`, then source `scripts/gdb/asterinas-gdb.py`.
7. Confirm the helper banner or run `ast-version` before setting workflow
   breakpoints.
8. Keep QEMU, GDB, and log output in separate tmux panes when the investigation
   needs repeated boot or stop cycles.
9. Store agent-generated logs, `.gdb` scripts, and Python probes under
   `build/agent/asterinas-debugger/` in the Asterinas repository.
10. After interrupted QEMU or smoke runs, check for `defunct` QEMU processes.
    If zombies are parented by container PID 1, restart the test container
    instead of trying to `kill` the zombie process.

## Command Shapes

```bash
docker ps -a --format '{{.Names}}\t{{.Image}}\t{{.Status}}'
cargo osdk debug --remote :1234
python3 skills/asterinas-debugger/scripts/asterinas_debugger.py doctor --repo .
```

No-rustup preflight inside a candidate container:

```bash
find /root/.rustup/toolchains -maxdepth 4 -type d \
    \( -name x86_64-unknown-none \
    -o -name riscv64imac-unknown-none-elf \
    -o -name loongarch64-unknown-none-softfloat \) -print
test -f /root/asterinas/target/x86_64-unknown-none/debug/aster-kernel-osdk-bin
test -f /root/asterinas/test/initramfs/build/initramfs.cpio.gz
```

If the selected container lacks required Rust targets, report that it is a
fresh or incomplete container. Do not run `rustup target add` unless the user
explicitly asks to warm that container.

Interrupted QEMU cleanup:

```bash
ps -eo pid,ppid,stat,cmd | grep -E 'defunct|qemu|rust-gdb|cargo osdk'
docker restart <warm-container>
```

Use container restart only for zombie cleanup or when no live debugging session
needs to be preserved.

Manual fallback inside GDB:

```gdb
target remote :1234
source scripts/gdb/asterinas-gdb.py
ast-version
info pretty-printer
```

When the command is launched outside the Asterinas tree, pass `--repo` to the
workflow script or export `ASTERINAS_REPO` so helper paths resolve to the
current PR checkout instead of an unrelated directory.

## Temporary Artifacts

Use `build/agent/asterinas-debugger/` for session-specific files:

```text
build/agent/asterinas-debugger/qemu.log
build/agent/asterinas-debugger/process_lifecycle.gdb
build/agent/asterinas-debugger/process_lifecycle.py
```

These files are not part of the Asterinas source tree. Do not add them under
`scripts/gdb/`, `kernel/`, `ostd/`, or `test/`.

## Architecture Notes

The GDB helper layer is mostly architecture-neutral because it reads DWARF
types, Rust symbols, and kernel object layouts. The session setup still depends
on the target ELF and QEMU endpoint selected by OSDK for `x86_64`, `riscv64`,
or `loongarch64`.
