from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (
    REPO_ROOT
    / "skills"
    / "asterinas-debugger"
    / "scripts"
    / "asterinas_debugger.py"
)
PROBE = (
    REPO_ROOT
    / "skills"
    / "asterinas-gdb-probes"
    / "scripts"
    / "make_probe.py"
)


def run_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def make_fake_asterinas_repo(root: Path) -> Path:
    repo = root / "asterinas"
    (repo / "scripts/gdb/helper").mkdir(parents=True)
    (repo / "scripts/gdb/test").mkdir(parents=True)
    (repo / "scripts/gdb/asterinas-gdb.py").write_text("# helper\n")
    (repo / "scripts/gdb/test/smoke.py").write_text("# smoke\n")
    (repo / "scripts/gdb/test/run_smoke.sh").write_text("#!/bin/sh\n")
    (repo / "Makefile").write_text("gdb-smoke-test:\n\t@true\n")
    return repo


class AsterinasDebuggerTest(unittest.TestCase):
    def test_lists_workflows(self) -> None:
        result = run_command("python3", str(WORKFLOW), "list")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("process-loading", result.stdout)
        self.assertIn("framekernel", result.stdout)

    def test_doctor_checks_current_helper_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_fake_asterinas_repo(Path(tmpdir))
            result = run_command(
                "python3",
                str(WORKFLOW),
                "--repo",
                str(repo),
                "doctor",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("helper entry: ok", result.stdout)
        self.assertIn("smoke runner: ok", result.stdout)
        self.assertIn("full smoke command: make gdb-smoke-test", result.stdout)

    def test_gdbinit_sources_repo_helper(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_fake_asterinas_repo(Path(tmpdir))
            result = run_command(
                "python3",
                str(WORKFLOW),
                "--repo",
                str(repo),
                "gdbinit",
                "process-loading",
                "--remote",
                ":1234",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("target remote :1234", result.stdout)
        self.assertIn("source ", result.stdout)
        self.assertIn("scripts/gdb/asterinas-gdb.py", result.stdout)
        self.assertIn("ast-fds 1", result.stdout)
        self.assertIn("p *$ast_process(1)", result.stdout)

    def test_plan_includes_goal_loop_record(self) -> None:
        result = run_command(
            "python3",
            str(WORKFLOW),
            "plan",
            "process-loading",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Goal loop record:", result.stdout)
        self.assertIn("Verdict: supported | rejected", result.stdout)
        self.assertIn("Next step:", result.stdout)

    def test_lifecycle_gdb_writes_under_build_agent_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = make_fake_asterinas_repo(Path(tmpdir))
            result = run_command(
                "python3",
                str(WORKFLOW),
                "--repo",
                str(repo),
                "lifecycle-gdb",
                "--remote",
                ".osdk-gdb-socket",
            )

            gdb_path = (
                repo
                / "build/agent/asterinas-debugger/process_lifecycle.gdb"
            )
            python_path = (
                repo
                / "build/agent/asterinas-debugger/process_lifecycle.py"
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("build/agent/asterinas-debugger", result.stdout)
            self.assertTrue(gdb_path.exists())
            self.assertTrue(python_path.exists())
            gdb_text = gdb_path.read_text()
            self.assertIn("source scripts/gdb/asterinas-gdb.py", gdb_text)
            self.assertIn(
                "sys.path.insert(0, 'build/agent/asterinas-debugger')",
                gdb_text,
            )
            self.assertIn("TRACE-EVENT", python_path.read_text())

    def test_probe_has_gdb_python_block_without_indent_prefix(self) -> None:
        result = run_command(
            "python3",
            str(PROBE),
            "pid-snapshot",
            "--pid",
            "1",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith("python\n"))
        self.assertIn("ast-ps 1", result.stdout)
        self.assertIn("p *$ast_file_table(1)", result.stdout)
        self.assertTrue(result.stdout.rstrip().endswith("end"))


if __name__ == "__main__":
    unittest.main()
