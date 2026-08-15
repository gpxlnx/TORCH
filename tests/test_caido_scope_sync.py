"""caido-scope-sync --dry-run: scope.md to precise Caido host globs."""
import json
import os
import pathlib
import subprocess

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "caido" / "caido-scope-sync.py"


def _mk(tmp, eng, in_lines, out_lines=()):
    directory = tmp / "targets" / eng
    directory.mkdir(parents=True)
    body = "## In scope\n" + "".join("- %s\n" % item for item in in_lines)
    body += "## Out of scope\n" + "".join("- %s\n" % item for item in out_lines)
    (directory / "scope.md").write_text(body)


def _run(tmp, *args):
    env = dict(os.environ, VAULT=str(tmp), CAIDO_SH="/bin/false")
    return subprocess.run(["python3", str(SCRIPT), *args], capture_output=True, text=True, env=env)


def test_dry_run_builds_precise_globs(tmp_path):
    _mk(tmp_path, "e1", ["10.0.0.5", "example.com", "10.112.0.0/16"], ["cdn.example.com"])
    result = _run(tmp_path, "--dry-run", "e1")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["name"] == "TORCH:e1"
    assert "10.0.0.5" in payload["allowlist"]
    assert "example.com" in payload["allowlist"]
    assert "*.example.com" in payload["allowlist"]
    assert "10.112.*" in payload["allowlist"]
    assert payload["denylist"] == ["cdn.example.com", "*.cdn.example.com"]


def test_non_octet_cidr_is_skipped_fail_closed(tmp_path):
    _mk(tmp_path, "e2", ["10.96.0.0/12", "1.2.3.4"])
    result = _run(tmp_path, "--dry-run", "e2")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["allowlist"] == ["1.2.3.4"]
    assert "skipped" in result.stderr and "10.96.0.0/12" in result.stderr


def test_empty_scope_errors(tmp_path):
    _mk(tmp_path, "e3", [])
    result = _run(tmp_path, "--dry-run", "e3")
    assert result.returncode == 3
    assert "no In-scope" in result.stderr
