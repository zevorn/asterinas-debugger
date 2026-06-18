# Asterinas Debugger Skills

This repository provides a small set of Codex skills for debugging
[Asterinas](https://github.com/asterinas/asterinas) with `rust-gdb`, QEMU,
Docker, and the Asterinas GDB helpers.

The skills are a companion to the upstream GDB helper work:

- PR: <https://github.com/asterinas/asterinas/pull/3412>
- RFC issue: <https://github.com/asterinas/asterinas/issues/3094>

The goal is to make kernel debugging less repetitive. The skills do not replace
GDB or the helper scripts. They organize common debugging work into repeatable
steps and reuse the helper commands when they are available.

## Design

The design follows a simple Loop Engineering and Humanize style:

1. collect a small baseline snapshot;
2. form one concrete hypothesis;
3. place the smallest useful breakpoint, watchpoint, or probe;
4. record the evidence;
5. decide the next step with human review.

The repository separates stable flow primitives from higher-level workflows.
Primitive skills handle one debugging capability well. The workflow skill
combines them for common Asterinas scenarios.

## Skills

| Skill | Purpose |
|-------|---------|
| `asterinas-debugger` | Main workflow router for Asterinas debugging |
| `asterinas-gdb-session` | Reuse Docker, start QEMU, attach GDB, load helpers |
| `asterinas-gdb-breakpoints` | Turn a hypothesis into concrete GDB stops |
| `asterinas-gdb-inspect` | Inspect helper commands, objects, printers, and symbols |
| `asterinas-gdb-probes` | Generate repeatable GDB Python probes |

The main workflow currently covers boot, process loading, scheduling,
filesystem, driver, network, and framekernel investigations.

## Requirements

Use these skills from an Asterinas source tree whenever possible. The expected
Asterinas checkout should contain the upstream GDB helper files:

```text
scripts/gdb/asterinas-gdb.py
scripts/gdb/helper/
scripts/gdb/test/
```

The local environment should provide the normal Asterinas development tools:

- Docker and a reusable Asterinas development container;
- QEMU from the Asterinas image;
- `rust-gdb`;
- `tmux` for multi-pane debugging sessions when useful.

The skills prefer reusing a warm container. They avoid running `rustc`,
`cargo`, or `cargo osdk` during preflight checks until the intended container
has been selected, because those commands may trigger Rust toolchain updates.

## Installation

Install the skills into Codex:

```bash
./scripts/install-skills-codex.sh
```

Install to a custom skills directory:

```bash
./scripts/install-skills-codex.sh \
    --codex-skills-dir "$HOME/.codex/skills"
```

Preview the install without writing files:

```bash
./scripts/install-skills-codex.sh --dry-run
```

## Utility Script

The main skill includes a helper script that prints workflow plans and GDB
skeletons. Run it from the Asterinas repository, or pass `--repo` explicitly.

```bash
python3 skills/asterinas-debugger/scripts/asterinas_debugger.py list
python3 skills/asterinas-debugger/scripts/asterinas_debugger.py doctor --repo .
python3 skills/asterinas-debugger/scripts/asterinas_debugger.py plan \
    process-loading --repo .
python3 skills/asterinas-debugger/scripts/asterinas_debugger.py gdbinit \
    process-loading --repo . --remote :1234
```

For process lifecycle tracing, generate temporary files under the Asterinas
build directory:

```bash
python3 skills/asterinas-debugger/scripts/asterinas_debugger.py lifecycle-gdb \
    --repo . \
    --remote .osdk-gdb-socket
```

Generated lifecycle files are written under:

```text
build/agent/asterinas-debugger/
```

Do not commit those generated debugging artifacts to the Asterinas source tree.

## Example Workflow

A typical process-loading investigation looks like this:

1. Start or reuse the Asterinas development container.
2. Boot the kernel with a QEMU GDB stub.
3. Attach `rust-gdb` and source `scripts/gdb/asterinas-gdb.py`.
4. Run a baseline snapshot:

```gdb
ast-version
info pretty-printer
ast-ps
ast-threads
ast-fds 1
p *$ast_process(1)
```

5. Add the smallest breakpoint or probe for the active hypothesis.
6. Record the command, output summary, and next hypothesis.

## Validation

Run the repository test suite:

```bash
./scripts/run-tests.sh
```

This validates the skill metadata and runs the Python unit tests for the
workflow utility script.

The Asterinas-side helper behavior is tested in the Asterinas repository by
the GDB smoke test:

```bash
make gdb-smoke-test
```

## Notes

- The GDB helper layer is mostly architecture-neutral because it reads DWARF
  types, Rust symbols, and kernel object layouts.
- Full runtime debugging still depends on the target architecture, QEMU, and
  the GDB available in the selected container.
- Use `gdb-multiarch` for non-x86 remote targets when the container's
  `rust-gdb` is built only for `x86_64-linux-gnu`.

## License

This repository is licensed under the MIT License. See [LICENSE](LICENSE).
