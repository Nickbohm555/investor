from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_executable(path: Path, contents: str) -> None:
    path.write_text(contents)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def test_execute_phase_prompt_tells_codex_to_decide_without_asking(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    output_file = tmp_path / "prompt.txt"

    _write_executable(
        bin_dir / "codex",
        """#!/usr/bin/env bash
set -euo pipefail
cat > "${GSD_ALL_TEST_PROMPT_FILE:?}"
""",
    )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["GSD_ALL_TEST_PROMPT_FILE"] = str(output_file)

    result = subprocess.run(
        ["bash", str(REPO_ROOT / "gsd-all.sh"), "execute", "7:7", "--repo", str(REPO_ROOT), "--no-push"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    prompt = output_file.read_text()
    assert "Use $gsd-execute-phase 7" in prompt
    assert "Make all reasonable decisions yourself." in prompt
    assert "Do not ask me for input, approval, or clarification." in prompt


def test_execute_uses_caffeinate_when_available(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    output_file = tmp_path / "argv.txt"

    _write_executable(
        bin_dir / "caffeinate",
        """#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$@" > "${GSD_ALL_TEST_ARGV_FILE:?}"
while [[ $# -gt 0 && "$1" == -* ]]; do
  shift
done
"$@"
""",
    )
    _write_executable(
        bin_dir / "codex",
        """#!/usr/bin/env bash
set -euo pipefail
cat >/dev/null
""",
    )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["GSD_ALL_TEST_ARGV_FILE"] = str(output_file)

    result = subprocess.run(
        ["bash", str(REPO_ROOT / "gsd-all.sh"), "execute", "7:7", "--repo", str(REPO_ROOT), "--no-push"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    argv = output_file.read_text().splitlines()
    assert argv[:2] == ["-dimsu", "codex"]
