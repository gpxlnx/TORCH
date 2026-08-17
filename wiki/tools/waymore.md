---
title: "waymore"
type: tool
tags: [recon, osint, url-discovery, archive, bug-bounty, attack-surface]
date_created: 2026-08-17
date_updated: 2026-08-17
sources: []
phase: recon
---

## Purpose

**waymore** is a historical-URL and archived-response miner. It pulls URLs from the Wayback Machine, Common Crawl, AlienVault OTX, URLScan, and VirusTotal, then optionally downloads the archived response bodies so you can mine endpoints that no longer appear in the live app. Deeper than [[wiki/tools/gau]]: gau lists URLs, waymore can also fetch and grep the archived content.

## Install / setup

```bash
pip install waymore
waymore -h
```

## Two modes (the key distinction)

- **Mode U (URLs, fast):** collect the URL list only. The default first pass.
- **Mode R (responses, slow but deep):** download the archived response bodies. Run it after Mode U surfaces interesting paths worth pulling in full, then grep the downloaded bodies for hidden endpoints.

```bash
# Mode U: URLs only
waymore -i target.com -mode U -oU waymore_urls.txt

# Mode R: download archived responses
waymore -i target.com -mode R -oR waymore_responses/

# mine the archived bodies for endpoints the live app hides
grep -rEoh '"[/][a-zA-Z0-9_/?=&%-]{3,80}"' waymore_responses/ \
  | tr -d '"' | sort -u > waymore_paths.txt
```

## Usage

```bash
# full-history scrape (no result cap, from a start year)
waymore -i target.com -mode U -l 0 -from 2018 -oU waymore_full.txt

# feed a list of live hosts, filter noise (-f), append-dedupe
cat live_hosts.txt | unfurl -u domains > waymore_input.txt
waymore -i waymore_input.txt -mode U -f -oU waymore_urls.txt

# per-host over a scope file
xargs -a scope.txt -I@ sh -c 'waymore -mode U -i @ | anew waymore_all.txt'
```

## When to use

- Endpoint discovery for a POST-only / JSON API that directory scanners cannot see: the archive remembers routes the live app dropped.
- Feed the URL output into [[wiki/tools/httpx]] for liveness, or into a param/secret pass.
- Mode R when you suspect an old response embedded a key, an internal host, or a since-removed admin path.

## Notes

- Mode R is disk- and time-heavy: scope it to hosts Mode U already flagged, not the whole target.
- `-f` applies waymore's built-in filters (static assets, noise extensions); drop it when you want everything.
