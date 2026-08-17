---
title: "DNS Dangling / NS Takeover"
type: technique
tags: [dns, ns-takeover, subdomain, takeover, bug-bounty]
date_created: 2026-08-17
date_updated: 2026-08-17
sources: []
related: ["[[subdomain-takeover]]"]
status: active
---

# DNS Dangling / NS Takeover

## Overview

NS Takeover (or DNS Dangling) occurs when a domain points to nameservers of an external service that is no longer registered or under the organization's control. The attacker can register that nameserver domain and control DNS resolution for the target subdomain/domain.

## Difference: CNAME vs NS Takeover

| Type | Scope | Impact |
|------|--------|---------|
| CNAME Takeover | 1 subdomain | Host content, phishing |
| NS Takeover | All records of the domain/subdomain | Full DNS control - MitM, phishing, token theft |

## How to identify

```bash
# 1. List all NS records of the target
dig target.com NS
dig +trace target.com NS
nslookup -type=NS sub.target.com

# 2. Check whether the nameservers respond
dig @ns1.dangling-ns.com target.com ANY
# NXDOMAIN or SERVFAIL -> the NS may be available!

# 3. Check registration availability
# Look up the NS domain at the registrar
whois dangling-ns.com
# Expired? -> register it!
```

## Methodology

```bash
# 1. Discover subdomains with NS records
# Via subfinder, amass, crt.sh

# 2. For each subdomain, check the NS records
for sub in $(cat subdomains.txt); do
    dig +short NS $sub
done

# 3. Check whether the NS does not resolve (dangling)
for ns in $(dig +short NS sub.target.com); do
    dig +short A $ns
    # If NXDOMAIN -> NS potentially available
done

# 4. Check whether the NS domain can be registered
# whois, registrars, namecheap, etc.

# 5. If registrable: register + configure a DNS server (bind9, AWS Route53)

# 6. Test control: create a verification TXT record
```

## Impact

NS Takeover grants full control over the subdomain's DNS:
- **Email MitM**: create an MX record, receive emails destined for the subdomain
- **HTTPS MitM**: obtain a TLS certificate via DNS challenge (Let's Encrypt) -> decrypt traffic
- **Token theft**: collect password-reset tokens, OAuth codes sent to the domain
- **Phishing**: host an identical site with a valid certificate
- **Cookie theft**: create a subdomain with cookie scope `*.target.com`

## Real-world case

Public research (2024): NS records of large companies pointing to nameservers of acquired/defunct DNS providers. Register the nameserver domain -> complete control.

## Tools
- dnsrecon : enumerate NS records
- subfinder : subdomain discovery
- dnsx : mass resolution
- can-i-take-over-xyz : reference for takeover-able platforms
