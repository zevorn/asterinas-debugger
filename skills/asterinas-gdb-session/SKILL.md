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

1. Check for a reusable running container before creating a new one.
2. If Docker is not reachable, start the Docker service first, then re-check
   the existing containers.
3. Build or locate the target kernel ELF through Asterinas tooling. Prefer
   `cargo osdk debug --remote <endpoint>` when the workspace supports helper
   auto-loading.
4. If auto-loading is not available, launch `rust-gdb` manually, attach with
   `target remote <endpoint>`, then source `scripts/gdb/asterinas-gdb.py`.
5. Confirm the helper banner or run `ast-version` before setting workflow
   breakpoints.
6. Keep QEMU, GDB, and log output in separate tmux panes when the investigation
   needs repeated boot or stop cycles.

## Command Shapes

```bash
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}'
cargo osdk debug --remote :1234
python3 skills/asterinas-debugger/scripts/asterinas_debugger.py doctor --repo .
```

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

## Architecture Notes

The GDB helper layer is mostly architecture-neutral because it reads DWARF
types, Rust symbols, and kernel object layouts. The session setup still depends
on the target ELF and QEMU endpoint selected by OSDK for `x86_64`, `riscv64`,
or `loongarch64`.
