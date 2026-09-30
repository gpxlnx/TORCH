import os, subprocess
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SH = os.path.join(REPO, "scripts", "vm-bg.sh")

def test_dry_run_prints_devshm_plan():
    p = subprocess.run(["bash", SH, "--dry-run", "eng1", "pspy", "/opt/pspy/pspy64 -pf"],
                       capture_output=True, text=True, timeout=20)
    assert p.returncode == 0
    out = p.stdout
    assert "/dev/shm/pspy.log" in out and "tmux" in out and "stdbuf" in out


def test_redirect_wraps_whole_multi_statement_command():
    # regression: redirect must cover the ENTIRE command, not just the last ';'-segment,
    # or output from earlier statements silently goes to the tmux pane instead of the log.
    p = subprocess.run(["bash", SH, "--dry-run", "eng1", "multi", "echo a; echo b"],
                       capture_output=True, text=True, timeout=20)
    assert p.returncode == 0
    assert "( stdbuf -oL -eL echo a; echo b ) > /dev/shm/multi.log" in p.stdout
