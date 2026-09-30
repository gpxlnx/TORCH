"""vm.sh static source assertions (no VM; never opens a live SSH connection)."""
import os
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "setup", "vm.sh")


def read_source():
    with open(SCRIPT) as f:
        return f.read()


def test_ssh_invocation_has_control_multiplexing():
    src = read_source()
    assert "ControlMaster=auto" in src
    assert "ControlPath=" in src
    assert "ControlPersist=" in src


def test_ssh_invocation_regression_guard():
    src = read_source()
    assert "sshpass -p" in src
    assert "ConnectTimeout=8" in src


def test_fails_fast_with_clear_message_when_sshpass_missing():
    # a fresh machine without sshpass must not die on a bare "command not found" --
    # PATH="" makes `command -v sshpass` find nothing; invoke bash by absolute path
    # since PATH is empty. The guard must fire before anything else needs PATH.
    r = subprocess.run(["/bin/bash", SCRIPT, "echo hi"], capture_output=True, text=True,
                       env={"PATH": ""}, timeout=10)
    assert r.returncode == 3
    assert "sshpass missing" in r.stderr
