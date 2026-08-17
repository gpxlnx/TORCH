---
title: "Client-Side Path Traversal (CSPT)"
type: technique
tags: [cspt, client-side-path-traversal, cspt2csrf, path-traversal]
date_created: 2026-08-17
date_updated: 2026-08-17
sources: []
related: ["[[cross-site-path-traversal]]", "[[csrf]]"]
status: active
---

# Client-Side Path Traversal (CSPT)

> Canonical alias: see [[cross-site-path-traversal]] for the full technique.

CSPT = the attacker controls part of a path used by client-side JS to build a request, redirecting it to a different endpoint on the same origin. Chains to CSRF (CSPT2CSRF), data leaks, or XSS.

- [[cross-site-path-traversal]] : detailed technique, payloads, polyglots
