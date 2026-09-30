# New machine checklist (new PC, new Kali VM)

Reproducible steps to stand up TORCH on a machine that was never bootstrapped, pointed at a
Kali VM with its own IP/user/password. Nothing here is tied to any specific host -- validated
live twice in one session against two different real Kali VMs. Detail lives in `docs/setup.md`
(general bootstrap) and `docs/virtual-machine.md` (VM bridge reference); this is the condensed
run-once checklist.

## 1. Clone the repo

```bash
git clone git@github.com:gpxlnx/TORCH.git ~/tstsh/TORCH   # or wherever you keep it
cd ~/tstsh/TORCH
```

## 2. Bootstrap (once per machine)

```bash
bash setup/bootstrap.sh
```

Creates the `~/.claude/CLAUDE.md` include, registers hooks, installs qmd + the official Claude
plugins + caveman + ponytail, registers the `wiki-search`/`caveman-shrink` MCP servers,
installs `sshpass`, and copies `setup/vm.sh` -> `~/.torch/vm.sh` (no secrets in that copy).

## 3. Configure the new Kali VM

```bash
mkdir -p ~/.torch
cat > ~/.torch/creds.txt <<'EOF'
# IP
<NEW-VM-IP>
# Username
<user>
# Password
<password>
EOF
chmod 600 ~/.torch/creds.txt
```

Flexible format (label or header form), optional `tailnet ip:` line for off-LAN access -- see
`docs/virtual-machine.md`.

## 4. Provision the toolchain on the VM

```bash
bash scripts/vm-provision.sh
```

`bootstrap.sh` only runs this automatically when `creds.txt` already existed before step 2;
since you create it after, run it manually here.

## 5. VM-side prerequisites

- sshd needs `PasswordAuthentication yes` (default on official Kali images; `vm.sh`
  authenticates with `sshpass -p`, not a key).
- sudo needs `NOPASSWD` for the configured user, or `vm-provision.sh` reports `MISS` for every
  package that needs root (it degrades gracefully, never hangs). To grant it:

```bash
bash ~/.torch/vm.sh 'echo "<password>" | sudo -S sh -c "echo \"<user> ALL=(ALL) NOPASSWD: ALL\" > /etc/sudoers.d/99-nopasswd && chmod 0440 /etc/sudoers.d/99-nopasswd && visudo -cf /etc/sudoers.d/99-nopasswd"'
```

## 6. Verify

```bash
bash ~/.torch/vm.sh 'whoami; hostname; uname -a'
python3 scripts/campaign-doctor.py --verbose
```

`campaign-doctor.py` should report `ALL GREEN` (or only machine-wiring `WARN`s it names how to
fix).

## 7. Finish

Restart Claude Code, then run `qmd update` to build the local wiki search index.
