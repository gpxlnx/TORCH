---
title: "bbot"
type: tool
tags: [recon, osint, subdomain-enumeration, bug-bounty, attack-surface]
date_created: 2026-08-17
date_updated: 2026-08-17
sources: []
phase: recon
---

## Purpose

**bbot** (BigBadOWASP OSINT Tool) is a recursive, modular recon framework. Its distinguishing trait is the **recursive event graph**: each discovered asset (subdomain, URL, cloud bucket, secret) is fed back through every applicable module, so one seed domain cascades into a full attack surface. Use it as a broad first pass that other tools ([[wiki/tools/subfinder]], [[wiki/tools/dnsx]], [[wiki/tools/httpx]]) then refine.

## Install / setup

```bash
pipx install bbot
# or: pip install bbot
bbot --help
```

## Presets and flags

bbot groups modules into **presets** (`-p`) and filters them by **flags** (`-rf` require, `-ef` exclude):

```bash
# list what a module accepts
bbot --list-module-options | grep -i shodan

# passive subdomain enum only (no traffic to target)
bbot -t target.com -p subdomain-enum -rf passive

# active subdomain enum (DNS brute, HTTP)
bbot -t target.com -p subdomain-enum
```

## Usage

```bash
# passive pass, capture just the subdomains.txt artifact
domain="target.com"; out=$(mktemp -d)
bbot -t "$domain" -p subdomain-enum -rf passive -o "$out" >/dev/null 2>&1
cp "$(find "$out" -type f -name subdomains.txt | head -n1)" "bbot_${domain}.txt"

# multiple targets from a scope file
bbot -t scope.txt -p subdomain-enum -rf passive -o bbot_out/

# chain into the pipeline
cat bbot_target.com.txt | dnsx -silent | httpx -silent | anew live.txt
```

## When to use

- First broad sweep on a new root domain: the recursive graph surfaces assets single-source tools miss.
- Passive preset (`-rf passive`) when the RoE forbids touching the target.
- Cross-check against [[wiki/tools/subfinder]] output with `anew` to find the delta each tool contributes.

## Notes

- Passive vs active matters for scope: `-rf passive` only queries third-party sources; the default `subdomain-enum` preset also brute-forces DNS and probes HTTP (active, counts against rate limits).
- Feed API keys (Shodan, GitHub, etc.) in the bbot config for far deeper passive results.
