from __future__ import annotations

import os
import subprocess
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content)
    path.chmod(0o755)


def _build_env(tmp_path: Path) -> dict[str, str]:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    crontab_file = tmp_path / "crontab.txt"
    curl_log = tmp_path / "curl.log"

    _write_executable(
        fake_bin / "crontab",
        f"""#!/bin/sh
set -eu
FILE="{crontab_file}"
cmd="${{1:-}}"
case "$cmd" in
  -l)
    if [ -f "$FILE" ]; then
      cat "$FILE"
    else
      exit 1
    fi
    ;;
  -)
    cat > "$FILE"
    ;;
  -r)
    rm -f "$FILE"
    ;;
  *)
    echo "unsupported crontab args: $*" >&2
    exit 1
    ;;
esac
""",
    )
    _write_executable(
        fake_bin / "curl",
        f"""#!/bin/sh
set -eu
printf '%s\n' "$*" >> "{curl_log}"
if [ "${{CURL_SHOULD_FAIL:-0}}" = "1" ]; then
  exit 1
fi
printf '%s' "${{CURL_RESPONSE:-{{\"status\":\"started\"}}}}"
""",
    )

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["HOME"] = str(tmp_path)
    env["INVESTOR_REPO_ROOT"] = str(tmp_path)
    env["INVESTOR_SCHEDULE_TRIGGER_URL"] = "http://127.0.0.1:8000/runs/trigger/scheduled"
    env["INVESTOR_SCHEDULED_TRIGGER_TOKEN"] = "scheduled-test-token"
    env["INVESTOR_CRON_LOG_PATH"] = "logs/cron/daily-trigger.log"
    env["INVESTOR_CURL_BIN"] = str(fake_bin / "curl")
    env["CRONTAB_FILE"] = str(crontab_file)
    env["CURL_LOG"] = str(curl_log)
    return env


def test_cron_install_is_idempotent_and_status_reports_log_path(tmp_path: Path):
    env = _build_env(tmp_path)

    subprocess.run([str(SCRIPTS_DIR / "cron-install.sh")], cwd=tmp_path, env=env, check=True)
    subprocess.run([str(SCRIPTS_DIR / "cron-install.sh")], cwd=tmp_path, env=env, check=True)

    crontab_text = (tmp_path / "crontab.txt").read_text()
    assert crontab_text.count("# >>> investor daily schedule >>>") == 1
    assert crontab_text.count("# <<< investor daily schedule <<<") == 1
    assert "./scripts/cron-trigger.sh >> ./logs/cron/daily-trigger.log 2>&1" in crontab_text

    status = subprocess.run(
        [str(SCRIPTS_DIR / "cron-status.sh")],
        cwd=tmp_path,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "managed=present" in status.stdout
    assert "log_path=logs/cron/daily-trigger.log" in status.stdout


def test_cron_remove_clears_only_managed_block(tmp_path: Path):
    env = _build_env(tmp_path)

    subprocess.run([str(SCRIPTS_DIR / "cron-install.sh")], cwd=tmp_path, env=env, check=True)
    subprocess.run([str(SCRIPTS_DIR / "cron-remove.sh")], cwd=tmp_path, env=env, check=True)

    status = subprocess.run(
        [str(SCRIPTS_DIR / "cron-status.sh")],
        cwd=tmp_path,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "managed=absent" in status.stdout
    assert "log_path=logs/cron/daily-trigger.log" in status.stdout


def test_cron_trigger_loads_env_posts_and_logs_success_and_failure(tmp_path: Path):
    env = _build_env(tmp_path)
    (tmp_path / ".env").write_text(
        "INVESTOR_SCHEDULE_TRIGGER_URL=http://127.0.0.1:8000/runs/trigger/scheduled\n"
        "INVESTOR_SCHEDULED_TRIGGER_TOKEN=scheduled-test-token\n"
    )

    success = subprocess.run(
        [str(SCRIPTS_DIR / "cron-trigger.sh")],
        cwd=tmp_path,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    assert success.returncode == 0
    log_text = (tmp_path / "logs/cron/daily-trigger.log").read_text()
    assert "scheduled_trigger result=started" in log_text
    curl_args = (tmp_path / "curl.log").read_text()
    assert "/runs/trigger/scheduled" in curl_args
    assert "X-Investor-Scheduled-Trigger: scheduled-test-token" in curl_args

    duplicate_env = env.copy()
    duplicate_env["CURL_RESPONSE"] = '{"status":"duplicate"}'
    duplicate = subprocess.run(
        [str(SCRIPTS_DIR / "cron-trigger.sh")],
        cwd=tmp_path,
        env=duplicate_env,
        check=True,
        capture_output=True,
        text=True,
    )

    assert duplicate.returncode == 0
    log_text = (tmp_path / "logs/cron/daily-trigger.log").read_text()
    assert "scheduled_trigger result=duplicate" in log_text

    failure_env = env.copy()
    failure_env["CURL_SHOULD_FAIL"] = "1"
    failure = subprocess.run(
        [str(SCRIPTS_DIR / "cron-trigger.sh")],
        cwd=tmp_path,
        env=failure_env,
        capture_output=True,
        text=True,
    )

    assert failure.returncode != 0
    log_text = (tmp_path / "logs/cron/daily-trigger.log").read_text()
    assert "scheduled_trigger result=failure" in log_text
