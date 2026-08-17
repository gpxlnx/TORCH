# Design: Import recon/tooling/exploration knowledge from external Obsidian bugbounty vault

**Date:** 2026-08-17
**Source vault:** `/home/gxavier/repos/obsidian/bugbounty` (628 md, 18MB, PT-BR)
**Goal:** Grow TORCH's recon breadth/depth, secret-detection, dorks, and Caido exploitation
recipes by synthesizing the genuinely net-new knowledge from the external vault, scrubbed of all
client data and secrets, in TORCH voice (English, image-free, generic).

## Non-goals

- No verbatim copy of any source file. Every command is rewritten with generic placeholders
  (`target.com`, `$DOMAIN`), never a real host from the source.
- Training notes (`99. VER - 07. Treinamentos`, ~390 files) excluded by operator decision.
- ShadowClone note excluded (contains a live AWS key pair; skip entirely, operator decision).
- No new standalone micro tool-pages for one-liner tools; those fold into cheatsheets.

## Hard constraints (gating)

1. **Leak gate.** Source contains live secrets (AWS `AKIA...` key pair + account id in ShadowClone)
   and real target names (webmotors, warren.com.br, hilton, redbull, DoD) plus personal paths
   (`/root/nina/`, `/root/tools/`). Nothing carrying a secret or client marker is imported as-is.
   `scripts/check-leaks.sh` MUST pass before completion. All wiki pages stay client-free per the
   CLAUDE.md client-data boundary.
2. **Format.** Source is fragmentary PT-BR with `>` blockquote noise and `![[image]]` embeds.
   Output is clean English TORCH pages, image-free (image handling rule), with `## sources:`
   frontmatter noting the import provenance generically (not a per-file source list).
3. **Convention.** Recon tools land in cheatsheets (TORCH indexes recon this way), not 14 tiny pages.

## Baseline (already in TORCH, do NOT duplicate)

68 tool pages, 30 cheatsheets, 42 payloads, 369 techniques. Core PTES recon already covered:
puredns, shuffledns, alterx, amass, naabu, dnsx, gowitness, httpx, feroxbuster, ffuf, arjun,
paramspider, gospider, linkfinder, katana, gau, crt.sh.

## What enters (net-new, synthesized)

### A. Recon breadth -> `wiki/cheatsheets/recon.md` (+ new `recon-monitoring.md`)
Add tuned command blocks (when-to-use + generic flags) for tools TORCH lacks:
bbot, waymore, gotator, dnsgen, findomain, assetfinder, tlsx, asnmap, favirecon, cloudrecon,
xnlinkfinder, hakrawler, dirsearch, shosubgo, github-subdomains, gitlab-subdomains, revwhoix,
sameowner, fierce, altdns, pugdns.
CT/passive **monitoring** (gungnir, cdx/wayback continuous) -> new `recon-monitoring.md`.

### B. Own tool pages (only the two deep, multi-mode tools)
- `wiki/tools/bbot.md` - recursive module-graph subdomain enum (passive/active presets).
- `wiki/tools/waymore.md` - mode U (URLs) vs mode R (archived-response mining) + path extraction.

### D. Secret detection -> new `wiki/cheatsheets/secrets-regex.md`
The ~50-entry regex catalog (AWS/GCP/Firebase/Slack/Stripe/GitHub/GitLab/Twilio/SendGrid/Okta/
Telegram/... tokens + private-key + cognito-pool patterns). Wire into `hunt-secrets` skill `## Wiki`
+ `playbook.json`.

## Scope decision (operator, 2026-08-17): only A, B, D

Areas C, E, F, G are DEFERRED (leave TORCH as-is). This pass imports ONLY:
- **A** recon breadth -> `recon.md` + new `recon-monitoring.md`
- **B** two tool pages -> `bbot.md`, `waymore.md`
- **D** secret-regex catalog -> new `secrets-regex.md` + hunt-secrets/playbook wiring

## Wiring / index updates

- `scripts/playbook.json`: add `secrets-regex` ref to the secret/exposure fingerprint rows.
- `skills/hunt/hunt-secrets/SKILL.md`: reference `[[secrets-regex]]` in its Wiki section.
- `wiki/index.md` + qmd re-index after pages land.

## Execution order (leak-safe)

1. Build the import blocklist (files with secret/client markers) - done in analysis.
2. Synthesize each target page from the source content, rewriting to generic English.
3. `scripts/check-leaks.sh` gate. If it flags anything, fix before continuing.
4. Lint (`lint-wiki.py`, `lint-md-tables.py`), re-index, update index/MOC.
5. Report the delta (pages added/updated) + re-flag the leaked AWS key for rotation.

## Testing / verification

- `scripts/check-leaks.sh` passes (no client marker / secret in any new wiki page).
- `python3 scripts/lint-wiki.py` + `lint-md-tables.py` pass on new/edited pages.
- qmd re-index succeeds; spot-query 3 new topics (bbot, secrets-regex, waymore) return the new pages.
- No `![[` image embed and no `>` blockquote-dump artifact in any new page.

## Out of scope / deferred

- 390 training notes.
- ShadowClone (live-key infra note).
- Converting recon one-liners into standalone tool pages (folded into cheatsheets instead).
