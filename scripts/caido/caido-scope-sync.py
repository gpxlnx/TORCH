#!/usr/bin/env python3
"""Synchronize targets/<eng>/scope.md with a named Caido scope.

Usage:
  caido-scope-sync.py [<eng>]
  caido-scope-sync.py --dry-run [<eng>]

Env: VAULT, CAIDO_SH. CIDRs that cannot be expressed safely as host globs are
skipped instead of widened.
"""
import ipaddress
import json
import os
import re
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(SCRIPT_DIR))
VAULT = os.environ.get("VAULT") or REPO
CAIDO_SH = os.environ.get("CAIDO_SH") or os.path.join(SCRIPT_DIR, "caido-client.sh")
sys.path.insert(0, os.path.join(REPO, "skills", "hooks"))
import _engagement


def entry_to_globs(entry):
    """Return precise Caido host globs for one scope entry, or [] if unsafe."""
    entry = entry.strip()
    if not entry or entry == "-":
        return []
    if "/" in entry and not entry.startswith(("http://", "https://")):
        try:
            net = ipaddress.ip_network(entry, strict=False)
        except ValueError:
            return []
        if net.version != 4 or net.prefixlen not in (8, 16, 24, 32):
            return []
        if net.prefixlen == 32:
            return [str(net.network_address)]
        octets = str(net.network_address).split(".")[: net.prefixlen // 8]
        return [".".join(octets) + ".*"]

    host = re.sub(r"^https?://", "", entry, flags=re.I).split("/")[0]
    if host.startswith("[") and "]" in host:
        host = host[1:host.index("]")]
    elif host.count(":") == 1:
        host = host.split(":", 1)[0]
    host = host.strip().lower().rstrip(".")
    if not host:
        return []
    try:
        ipaddress.ip_address(host)
        return [host]
    except ValueError:
        return [host, "*." + host]


def _patterns(entries):
    out = []
    for entry in entries:
        for pattern in entry_to_globs(entry):
            if pattern not in out:
                out.append(pattern)
    return out


def scope_payload(eng, in_scope, out_scope):
    return {
        "name": "TORCH:" + eng,
        "allowlist": _patterns(in_scope),
        "denylist": _patterns(out_scope),
    }


def _call(*args):
    return subprocess.run(
        ["bash", CAIDO_SH, *args], capture_output=True, text=True, timeout=90
    )


def _scope_rows(value):
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("scopes", "results", "items"):
            if isinstance(value.get(key), list):
                return value[key]
    return []


def _push(payload):
    listed = _call("scopes")
    if listed.returncode:
        return False, (listed.stderr or listed.stdout).strip()
    try:
        rows = _scope_rows(json.loads(listed.stdout))
    except json.JSONDecodeError:
        return False, "invalid JSON from `caido-client scopes`"

    existing = next((row for row in rows if row.get("name") == payload["name"]), None)
    common = [
        "--allow", ",".join(payload["allowlist"]),
        "--deny", ",".join(payload["denylist"]),
    ]
    if existing and existing.get("id"):
        result = _call("update-scope", str(existing["id"]), "--name", payload["name"], *common)
        action = "updated"
    else:
        result = _call("create-scope", payload["name"], *common)
        action = "created"
    return result.returncode == 0, action if result.returncode == 0 else (result.stderr or result.stdout).strip()


def main():
    argv = sys.argv[1:]
    dry = "--dry-run" in argv
    rest = [arg for arg in argv if arg != "--dry-run"]
    eng = rest[0] if rest else None
    directory = os.path.join(VAULT, "targets", eng) if eng else _engagement.active_dir()
    if not directory or not os.path.isdir(directory):
        print("caido-scope-sync: no engagement (pass <eng> or set targets/active.md)", file=sys.stderr)
        return 2
    eng = os.path.basename(directory.rstrip(os.sep))
    scope = _engagement.scope(directory)
    if not scope["in_scope"]:
        print("caido-scope-sync: scope.md has no In-scope entries; nothing to sync", file=sys.stderr)
        return 3

    skipped = [entry for entry in scope["in_scope"] if not entry_to_globs(entry)]
    if skipped:
        print(
            "caido-scope-sync: skipped unsupported or unsafe entries: " + ", ".join(skipped),
            file=sys.stderr,
        )
    payload = scope_payload(eng, scope["in_scope"], scope["out_of_scope"])
    if dry:
        print(json.dumps(payload, indent=2))
        print(
            "# dry-run: %d allow pattern(s) would be synced to Caido"
            % len(payload["allowlist"]),
            file=sys.stderr,
        )
        return 0

    ok, detail = _push(payload)
    if ok:
        print(
            "caido-scope-sync: %s %s with %d allow pattern(s)"
            % (detail, payload["name"], len(payload["allowlist"]))
        )
        return 0
    print("caido-scope-sync: push failed -> " + detail, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
