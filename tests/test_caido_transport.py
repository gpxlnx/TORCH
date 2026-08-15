"""caido-transport.sh: native, SDK fallback, and down branches."""
import os
import pathlib
import subprocess

RESOLVER = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "caido" / "caido-transport.sh"


def _run(env_extra=None, args=()):
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(["bash", str(RESOLVER), *args], capture_output=True, text=True, env=env)


def test_native_when_flagged():
    result = _run({"CAIDO_NATIVE": "1"})
    assert result.returncode == 0
    assert result.stdout.strip() == "native"
    assert "mcp__caido__" in result.stderr


def test_sdk_when_client_is_healthy(tmp_path):
    stub = tmp_path / "caido-client.sh"
    stub.write_text("#!/usr/bin/env bash\n[ \"$1\" = health ] && echo '{\"ready\":true}'\n")
    stub.chmod(0o755)
    result = _run({"CAIDO_SH": str(stub)})
    assert result.returncode == 0
    assert result.stdout.strip() == "sdk"


def test_down_when_client_fails(tmp_path):
    stub = tmp_path / "caido-client.sh"
    stub.write_text("#!/usr/bin/env bash\nexit 1\n")
    stub.chmod(0o755)
    result = _run({"CAIDO_SH": str(stub)})
    assert result.returncode == 3
    assert result.stdout.strip() == "down"
    assert "ssh local-forward" in result.stderr.lower()


def test_dry_run_never_probes_sdk(tmp_path):
    stub = tmp_path / "caido-client.sh"
    stub.write_text("#!/usr/bin/env bash\necho SHOULD_NOT_RUN >&2\nexit 1\n")
    stub.chmod(0o755)
    result = _run({"CAIDO_SH": str(stub)}, args=("--dry-run",))
    assert "SHOULD_NOT_RUN" not in result.stderr
    assert result.stdout.strip() == "down"
    assert result.returncode == 3
