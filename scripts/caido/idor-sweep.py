#!/usr/bin/env python3
"""Caido-driven two-account and bounded numeric-ID authorization check.

Usage:
  idor-sweep.py [--dry-run] <eng> <reqfile> [--attacker-auth "Cookie: session=B"]
                [--id-regex '/orders/(\\d+)'] [--range N] [--port P]
                [--https|--no-https]

Env: VAULT, CAIDO_SH. Live requests are created as named Caido Replay sessions.
"""
import argparse
import hashlib
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

DEFAULT_ID_RES = [r"/(\d+)(?:/|\?|$)", r"[?&]id=(\d+)"]
AUTH_HEADERS = ("cookie", "authorization", "x-api-key", "x-auth-token")


def parse_request(text):
    text = text.replace("\r\n", "\n")
    head, _, body = text.partition("\n\n")
    lines = head.split("\n")
    parts = lines[0].split()
    method, path = (parts + ["", ""])[0], (parts + ["", ""])[1]
    headers, host = [], ""
    for line in lines[1:]:
        if ":" in line:
            key, value = line.split(":", 1)
            headers.append((key.strip(), value.strip()))
            if key.strip().lower() == "host":
                host = value.strip()
    return {
        "method": method,
        "path": path,
        "host": host.split(":")[0],
        "headers": headers,
        "body": body,
    }


def find_id(path, id_regex=None):
    for pattern in ([id_regex] if id_regex else DEFAULT_ID_RES):
        match = re.search(pattern, path)
        if match:
            return int(match.group(1)), match.span(1)
    return None


def sub_id(path, span, new_id):
    return path[: span[0]] + str(new_id) + path[span[1] :]


def swap_auth(headers, attacker_auth):
    out = [(key, value) for key, value in headers if key.lower() not in AUTH_HEADERS]
    if attacker_auth:
        name, value = attacker_auth.split(":", 1)
        name, value = name.strip(), value.strip()
        out = [(key, val) for key, val in out if key.lower() != name.lower()]
        out.append((name, value))
    return out


def build_set(req, idinfo, attacker_auth, rng):
    current, span = idinfo
    attacker_headers = swap_auth(req["headers"], attacker_auth)
    out = [
        {"label": "owner-baseline", "id": current, "path": req["path"], "headers": req["headers"]},
        {"label": "idor-test", "id": current, "path": req["path"], "headers": attacker_headers},
    ]
    for distance in range(1, rng + 1):
        for candidate in (current - distance, current + distance):
            if candidate < 0 or candidate == current:
                continue
            out.append(
                {
                    "label": "enum",
                    "id": candidate,
                    "path": sub_id(req["path"], span, candidate),
                    "headers": attacker_headers,
                }
            )
    return out


def host_in_scope(host, in_scope):
    host = (host or "").lower().strip()
    return any(
        _engagement._scope_entry_match(host, (entry or "").lower().strip(), strict=True)
        for entry in in_scope
    )


def _die(message, code=2):
    print("idor-sweep: " + message, file=sys.stderr)
    raise SystemExit(code)


def verdict(responses):
    owner = next(row for row in responses if row["label"] == "owner-baseline")
    attacker = next(row for row in responses if row["label"] == "idor-test")
    enum = [row for row in responses if row["label"] == "enum"]
    out = {"owner_status": owner["status"]}
    if not 200 <= owner["status"] < 300:
        out["idor"] = "WARN: baseline not 2xx (stale session / wrong request?)"
    elif 200 <= attacker["status"] < 300 and (
        attacker["hash"] == owner["hash"]
        or abs(attacker["length"] - owner["length"]) <= 0.05 * max(owner["length"], 1)
    ):
        out["idor"] = "LIKELY IDOR"
    elif attacker["status"] in (401, 403, 404) or attacker["length"] == 0:
        out["idor"] = "authorization enforced"
    else:
        out["idor"] = "inconclusive (status %d)" % attacker["status"]
    out["enum_accessible"] = sum(1 for row in enum if 200 <= row["status"] < 300)
    out["enum_total"] = len(enum)
    return out


def _raw(request, meta):
    lines = ["%s %s HTTP/1.1" % (meta["method"], request["path"])]
    lines += ["%s: %s" % (key, value) for key, value in request["headers"]]
    return "\r\n".join(lines) + "\r\n\r\n" + meta.get("body", "")


def session_specs(meta):
    names = {"owner-baseline": "idor-owner", "idor-test": "idor-attacker"}
    return [
        {"name": names[row["label"]], "raw": _raw(row, meta)}
        for row in meta["requests"]
        if row["label"] in names
    ]


def parse_caido_response(output):
    """Return status, body length, hash, request id, and session id from SDK JSON."""
    try:
        payload = json.loads(output)
    except (TypeError, json.JSONDecodeError):
        return 0, 0, "", "", ""
    response = payload.get("response") or {}
    status = int(response.get("statusCode") or 0)
    raw = response.get("raw") or ""
    normalized = raw.replace("\r\n", "\n")
    body = normalized.split("\n\n", 1)[1] if "\n\n" in normalized else ""
    length = int(response.get("length") or len(body))
    digest = hashlib.sha256(body.encode("utf-8", "ignore")).hexdigest()[:16] if status else ""
    return status, length, digest, str(payload.get("requestId") or ""), str(payload.get("sessionId") or "")


def _send(meta, request):
    name = "idor-%s-%s" % (request["label"], request["id"])
    args = [
        "bash", CAIDO_SH, "send-raw",
        "--host", meta["host"], "--port", str(meta["port"]),
        "--tls" if meta["https"] else "--no-tls",
        "--raw", "-", "--name", name,
        "--max-body", "0", "--max-body-chars", "0",
    ]
    try:
        result = subprocess.run(
            args, input=_raw(request, meta), capture_output=True, text=True, timeout=60
        )
    except subprocess.TimeoutExpired:
        return 0, 0, "", "", ""
    if result.returncode:
        return 0, 0, "", "", ""
    return parse_caido_response(result.stdout)


def run_live(meta):
    responses = []
    for request in meta["requests"]:
        status, length, digest, request_id, session_id = _send(meta, request)
        responses.append(
            {
                "label": request["label"], "id": request["id"], "status": status,
                "length": length, "hash": digest, "request_id": request_id,
                "session_id": session_id,
            }
        )
    if any(row["status"] == 0 for row in responses):
        print("idor-sweep: one or more Caido Replay sends failed", file=sys.stderr)
        return 1

    result = verdict(responses)
    print("id | label | status | len | caido_request")
    for row in responses:
        print("%s | %s | %s | %s | %s" % (
            row["id"], row["label"], row["status"], row["length"], row["request_id"]
        ))
    print("\nVERDICT: %s  (baseline %s; %d/%d enum neighbors accessible)" % (
        result["idor"], result["owner_status"], result["enum_accessible"], result["enum_total"]
    ))
    if result["idor"] == "LIKELY IDOR":
        attacker = next(row for row in responses if row["label"] == "idor-test")
        print("Caido Replay sessions are named idor-owner-* and idor-attacker-* for A/B review.")
        print("PoC it: scripts/capture.sh caido %s idor-%s %s" % (
            meta["eng"], meta["host"], attacker["request_id"]
        ))
        print("Then scaffold a FIND per hunt-idor (never auto-written).")
    return 0


def main():
    parser = argparse.ArgumentParser(prog="idor-sweep.py")
    parser.add_argument("eng")
    parser.add_argument("reqfile")
    parser.add_argument("--attacker-auth")
    parser.add_argument("--id-regex")
    parser.add_argument("--range", type=int, default=3)
    parser.add_argument("--port", type=int)
    parser.add_argument("--https", action="store_true", default=None)
    parser.add_argument("--no-https", dest="https", action="store_false")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.attacker_auth and ":" not in args.attacker_auth:
        _die("--attacker-auth must be 'Name: value' (got %r)" % args.attacker_auth)

    directory = os.path.join(VAULT, "targets", args.eng)
    if not os.path.isdir(directory):
        _die("no engagement dir %s" % directory)
    scope = _engagement.scope(directory)
    if scope.get("passive_only"):
        _die("passive_only is set in scope.md; idor-sweep is an ACTIVE test, refusing")
    if not scope["in_scope"]:
        _die("scope.md has no in_scope entries; add the target before running idor-sweep")
    try:
        with open(args.reqfile, encoding="utf-8", errors="ignore") as request_file:
            request = parse_request(request_file.read())
    except OSError as error:
        _die("cannot read reqfile: %s" % error)
    if not host_in_scope(request["host"], scope["in_scope"]):
        _die("target host %r not in scope.md in_scope; refusing" % request["host"])
    idinfo = find_id(request["path"], args.id_regex)
    if not idinfo:
        _die("no numeric id found in path %r (use --id-regex)" % request["path"])

    rng = 0 if scope.get("no_bruteforce") else max(0, args.range)
    request_set = build_set(request, idinfo, args.attacker_auth, rng)
    https = args.https if args.https is not None else True
    port = args.port if args.port else (443 if https else 80)
    meta = {
        "host": request["host"], "port": port, "https": https,
        "method": request["method"], "body": request["body"],
        "no_bruteforce": bool(scope.get("no_bruteforce")),
        "requests": request_set, "eng": args.eng,
    }
    if args.dry_run:
        print(json.dumps(meta, indent=2))
        return 0
    return run_live(meta)


if __name__ == "__main__":
    sys.exit(main())
