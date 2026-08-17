---
title: "API Key Exposure"
type: technique
tags: [api-key, secrets, config-files, javascript, git-history, android, recon, financial-impact]
created: 2026-08-17
updated: 2026-08-17
sources: []
related: ["[[secrets-exposure]]", "[[api-key-management]]", "[[s3-misconfiguration]]", "[[firebase-security]]"]
status: active
---

# API Key Exposure

## Overview

API key exposure occurs when API keys (secrets that authenticate access to external services) become publicly reachable, in config files, JavaScript code, Git repositories, or unauthenticated endpoints. It is one of the most common and impactful vulnerabilities, especially when the keys have no restrictions configured.

**Key insight**: an API key in JavaScript is usually Low/Medium; the same key in a public production endpoint with no auth can be Critical.

## Impact

| Key type | Potential impact | Severity |
|----------|------------------|----------|
| Maps key (no restrictions) | Financial abuse (high monthly billing possible) | Critical |
| Cloud access keys | Access to the entire cloud infrastructure | Critical |
| Source-host token | Access to repositories, actions, secrets | High/Critical |
| Payment provider keys | Fraudulent transactions | Critical |
| Email-service keys | Spam, phishing using a legitimate domain | High |
| BaaS keys | Access to database, auth, storage | Medium/High |
| Maps key (with restrictions) | Limited by referrer/IP | Low/Medium |
| Read-only keys with limited scope | Public information via the API | Low |

## Where to look

### 1. Exposed config files (highest impact)

```bash
# Config paths - test during recon
/env.json           /envs/env.json      /config.json
/.env               /app.config.js      /settings.json
/api/config         /conf/config.php    /web.config
/.env.production    /.env.local         /secrets.json
```

### 2. JavaScript files (in browser/proxy)

```javascript
// DevTools -> Sources -> search for:
apiKey, api_key, API_KEY, SECRET, TOKEN, CLIENT_ID
"AIza"     // Google API key prefix
"sk-"      // Stripe/OpenAI secret prefix
"ghp_"     // GitHub Personal Access Token
"AKIA"     // AWS Access Key
"SG."      // SendGrid API key
```

### 3. APK / mobile app analysis

```bash
# Extract and grep URLs and secrets from an APK
unzip -d extracted target.apk
grep -rE "https?://[a-zA-Z0-9._/-]+" extracted/ | grep -v ".png|.jpg" | sort -u
grep -r "api_key\|apiKey\|secret\|SECRET\|token\|TOKEN" extracted/
grep -r "AIza\|AKIA\|ghp_\|sk-\|SG\." extracted/
```

### 4. Git history

```bash
# Search for secrets in Git history
git log --all --oneline --diff-filter=D -- "*.env" "*.json"
git log -p --all | grep -E "api_key|apiKey|SECRET|TOKEN|AIza|AKIA|ghp_"

# Tools
trufflehog git https://github.com/target/repo
gitleaks detect --source .
```

### 5. Internal browser extensions

```bash
# Google dork to find exposed internal extensions
site:chrome.google.com/webstore "target company"
# Download and analyze the .crx content
```

### 6. Public Postman collections

```bash
# Search Postman/SwaggerHub by organization name
site:postman.com/apis "target"
# Analyze collection variables for API keys
```

## Test methodology

### Phase 1: Discovery

```bash
# 1. Recon config files
for path in "/.env" "/config.json" "/envs/env.json" "/api/config" "/app.config.js"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "https://target.com$path")
  echo "$code $path"
done

# 2. Automated JS analysis
katana -u https://target.com -jc -o js_files.txt
cat js_files.txt | xargs -I{} curl -s {} | grep -E "AIza|AKIA|ghp_|sk-|SG\."

# 3. Source maps for minified JS
curl "https://target.com/main.bundle.js.map" 2>/dev/null | jq '.sources'
```

### Phase 2: Validation (keyhacks methodology)

```bash
# Maps API key
curl "https://maps.googleapis.com/maps/api/geocode/json?address=test&key=KEY"
curl "https://maps.googleapis.com/maps/api/directions/json?origin=London&destination=Paris&key=KEY"
curl "https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=51.5,-0.1&radius=1000&key=KEY"

# Source-host token
curl -H "Authorization: token TOKEN" https://api.github.com/user
curl -H "Authorization: token TOKEN" https://api.github.com/user/repos

# Cloud keys (authorized environment only)
aws sts get-caller-identity --access-key-id AKID --secret-access-key SECRET

# BaaS
curl "https://identitytoolkit.googleapis.com/v1/accounts:signInAnonymously?key=KEY" \
  -H "Content-Type: application/json" -d '{}'
```

### Phase 3: Calculate financial impact (when applicable)

For unrestricted Maps API keys:

```
1. Identify which APIs are enabled (test each one)
2. Check pricing for the provider
3. Calculate: cost per request x maximum possible volume
4. Apply a distribution multiplier (multiple IPs = 3x)
5. Calculate total monthly cost
```

## Restriction types (Maps as an example)

```
- No HTTP referrer restrictions
- No IP address restrictions
- No API-level restrictions
- No daily quota limits
= Critical severity

- Restricted to a specific HTTP referrer
- Restricted to the specific APIs used
- With budget alerts configured
= Low/Medium severity
```

## Tools

| Tool | Use |
|------|-----|
| **trufflehog** | Scanning secrets in Git/JS/filesystem |
| **gitleaks** | Scanning secrets in Git repositories |
| **secretfinder** | Search for secrets in JavaScript |
| **jsluice** | Endpoints + secrets from JS in one step |
| **nuclei** | Templates for API key exposure |
| **keyhacks** | Repository of commands to validate different key types |
| **katana** | Crawler for JS-file discovery |

## Real examples

### Maps key in /envs/env.json - high monthly potential

APK analysis revealed an `/envs/env.json` endpoint reachable without authentication. The JSON contained a Maps API key with no restrictions. 10 Maps APIs responded 200 OK. A large monthly financial impact was calculated.

### Secrets in public Postman

Organizations expose API keys in public Postman collections. Monitoring surfaced dozens of secrets across many orgs.

## Report tips

- **Never abuse the key**: only validate that it works, do not make bulk calls.
- **Quantify financial damage** where possible (APIs with billing such as Maps).
- **Test all APIs/permissions**: do not stop at the first one that responds.
- **Demonstrate the discovery route**: how you found it (APK -> endpoint -> JSON).
- **Include evidence of the absence of restrictions**: show no HTTP referrer, IP, or API restrictions.
- **Recommend remediation**: revoke immediately + Secret Manager + restrictions.

## Recommended remediation

1. Revoke and rotate exposed keys immediately.
2. Audit cloud billing for unauthorized use.
3. Migrate to a Secret Manager (Google, AWS, HashiCorp Vault).
4. Configure restrictions: HTTP referrer (web) or IP (server-side).
5. Enable only the necessary APIs.
6. Configure budget alerts.
7. Implement authentication on config endpoints.
8. Add key-exposure detection to the CI/CD pipeline (trufflehog/gitleaks).

## GitHub dorks for API keys

```
# Generic vendor keys
"GEMINI_API_KEY"
org:company /AIza[0-9A-Za-z_-]{35}/

# AWS
org:company "aws_access_key"
org:company "AKIA[0-9A-Z]{16}"

# Generic
org:company "api_key" OR "apiKey" OR "API_KEY"
```

## Additional tools

- leakprowl - scan keys across a subdomain list: `python leakprowl.py file subdomains.txt --check-content`
- trivy - `trivy repo https://github.com/username/repo`
- badsecrets - .NET/ViewState keys, machineKey: `python badsecrets.py -d /path/to/target`

## References

- [[secrets-exposure]] - the broader secrets-exposure technique
- [keyhacks](https://github.com/streaak/keyhacks) - validating different key types
