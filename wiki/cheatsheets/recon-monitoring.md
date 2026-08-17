---
title: "Recon Monitoring (Continuous Discovery)"
type: cheatsheet
tags: [cheatsheet, recon, monitoring, ct-logs, bug-bounty, attack-surface]
date_created: 2026-08-17
date_updated: 2026-08-17
sources: []
---

Continuous / passive discovery: watch Certificate Transparency logs and archives for new assets as they appear, instead of a one-shot enum. Complements the one-shot flow in [[recon]]. Pipe new hits into `notify` so a fresh subdomain pings you the moment it is issued a cert.

## gungnir (real-time CT log monitor)

Streams newly issued certificates for a wildcard/root list and prints matching hostnames as they appear.

```bash
# monitor a wildcard/root list, tee results
gungnir -r roots.txt | tee -a gungnir_out.txt

# build the wildcard list from a public scope repo, normalize the *. prefixes
curl -s "https://raw.githubusercontent.com/<scope-repo>/inscope_wildcards.txt" \
  | sed 's/\*\.//; s/\*//' | grep -v '\*' \
  | tldnfo --silent --extract domain,suffix | grep -a '.' \
  | anew -q wildcards.txt

# alert on every new subdomain via notify
gungnir -r roots.txt | notify -silent -id newsubs

# only alert on high-value hostnames
gungnir -r roots.txt | grep -E 'jenkins|grafana|symfony|gitlab|IIS' \
  | notify -silent -id newsubs
```

## Wayback / CDX continuous scrape

Re-run a full-history URL scrape on a schedule to catch newly archived endpoints. See [[wiki/tools/waymore]] for Mode U vs Mode R.

```bash
# full-history URL scrape from a start year, deduped
waymore -i target.com -mode U -l 0 -from 2018 -oU waymore_full.txt

# CDX API direct (Wayback), collapse duplicates
curl -s "http://web.archive.org/cdx/search/cdx?url=*.target.com/*&output=text&fl=original&collapse=urlkey" \
  | anew waybackcdx.txt
```

## Favicon-hash pivoting (favirecon)

Cluster hosts by favicon hash to find related infrastructure and shadow assets that share a favicon.

```bash
pip install favirecon
favirecon -l subdomains.txt -s -o favicons.txt

# hash each favicon, group the common ones
for s in $(cat subdomains.txt); do
  curl -s "https://$s/favicon.ico" | md5sum | awk -v h="$s" '{print $1" "h}'
done | sort | uniq -c -w32 | sort -nr > favicon_clusters.txt

# pivot a favicon hash to more hosts via Shodan
shodan search "http.favicon.hash:<hash>" --fields ip_str,port,hostnames
```

## Cloud SNI ranges (cloudrecon / kaeferjaeger)

Public daily dumps of CN/SAN values per cloud IP range let you find origins and subdomains behind a CDN without touching the target.

```bash
# pull a provider's merged SNI list, grep your apex, extract the SANs
wget https://kaeferjaeger.gay/sni-ip-ranges/amazon/ipv4_merged_sni.txt
grep -F "target.com" ipv4_merged_sni.txt | grep -oP '\[\K[^\]]+' | tr ' ' '\n' | sort -u
```

## Notes

- CT monitoring finds an asset at issuance, often before DNS or the app is live: first-mover advantage on new attack surface.
- Route `notify` to a private channel; never post client hostnames to a shared/public sink (see the client-data boundary).
