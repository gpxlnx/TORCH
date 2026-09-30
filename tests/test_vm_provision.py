import os
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "scripts", "vm-provision.sh")


def test_list_has_required_packages():
    p = subprocess.run(["bash", SCRIPT, "--list"], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    pkgs = set(p.stdout.split())
    # capture deps (original purpose)
    for need in ("tmux", "scrot", "xdotool", "imagemagick", "x11-utils", "xauth"):
        assert need in pkgs, "missing capture dep %s in provision list" % need
    # recon/test toolchain the nudges depend on (httpx-toolkit = ProjectDiscovery httpx)
    for need in ("httpx-toolkit", "subfinder", "naabu", "katana", "dalfox", "sqlmap",
                 "swaks", "trufflehog", "seclists"):
        assert need in pkgs, "missing recon tool %s in provision list" % need


def test_pwncat_cs_symlinked_into_path_visible_to_noninteractive_ssh():
    # regression: pipx/pip --user install pwncat-cs into ~/.local/bin, which is NOT on
    # vm.sh's non-interactive, non-login ssh PATH -- so it silently stayed invisible/unusable.
    src = open(SCRIPT, encoding="utf-8").read()
    assert "ln -sf" in src and "/usr/local/bin/pwncat-cs" in src


def test_gau_builds_from_source_when_not_apt_packaged():
    # gau (getallurls) is not in Kali's apt repo -- must fall back to git clone + go build,
    # with VCS stamping disabled (root-cloned repo, user-built -- git blocks that otherwise).
    src = open(SCRIPT, encoding="utf-8").read()
    assert "github.com/lc/gau" in src
    assert "-buildvcs=false" in src
