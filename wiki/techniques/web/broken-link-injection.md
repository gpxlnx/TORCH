---
title: "Broken Link Injection"
type: technique
tags: [broken-link, injection, subdomain-takeover, open-redirect, bug-bounty, socialhunter]
date_created: 2026-08-17
date_updated: 2026-08-17
sources: []
related: ["[[subdomain-takeover]]", "[[open-redirect]]", "[[dns-ns-takeover]]"]
status: active
---

# Broken Link Injection

## Overview

Broken Link Injection abuses broken links on a site (for CSS, JS, images, social media) that point to unregistered or expired domains. The attacker registers those domains to serve malicious content.

## Vectors

```html
<!-- Links to unregistered social media handles -->
<a href="https://twitter.com/nonexistent_handle">Follow us</a>

<!-- Expired CDN scripts -->
<script src="https://old-cdn.com/library.js"></script>

<!-- Favicon from an expired domain -->
<link rel="icon" href="https://expired-host.com/favicon.ico">

<!-- CSS from an expired domain -->
<link rel="stylesheet" href="https://old-brand.com/styles.css">
```

## Methodology

```bash
# 1. Extract all external links from the target
# With GoSpider or Hakrawler
gospider -s https://target.com --include-subs -o output/
cat output/*.txt | grep "https://" | grep -v "target.com" | sort -u > external-links.txt

# 2. Check which external domains do not resolve
cat external-links.txt | xargs -I{} bash -c 'domain=$(echo {} | cut -d/ -f3); if ! dig +short $domain | grep -q "."; then echo "BROKEN: {}"; fi'

# 3. Check registration availability
# whois or an availability-checking tool
```

## Exploitation

```
Register the expired domain -> host:
- Malicious JavaScript (XSS/content hijacking)
- Malicious CSS (UI redressing, data theft via CSS selectors)
- Favicon with tracking
- Social engineering (for social media handles)
```

## Real-world cases

```
# Non-existent Twitter handle on a contact page
# Register @handle -> post phishing "as the company"

# CDN of an acquired company
# Register the old CDN domain -> serve malicious JS
# -> XSS for every visitor of the target site
```

## Impact
- **Critical**: external JS -> stored XSS on every page
- **High**: external CSS -> data theft via CSS, UI redressing
- **Medium**: social media handle -> phishing/impersonation
- **Low**: image/favicon -> tracking, minor defacement

## Tools
- GoSpider, Hakrawler : crawling
- gau, waybackurls : historical links
- nuclei : broken-links template
- **socialhunter** : checks broken social media handles at scale

```bash
go install github.com/utkusen/socialhunter@latest
socialhunter -f domains.txt  # file with a list of domains
```

### socialhunter via Python (alternative mode)

```bash
python social_hunter.py -f /path/to/subdomains.txt --depth 5 --all-formats
```
