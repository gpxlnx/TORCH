---
title: "Secrets Regex Catalog"
type: cheatsheet
tags: [cheatsheet, secrets, recon, bug-bounty, source-code-analysis, api-keys]
date_created: 2026-08-17
date_updated: 2026-08-17
sources: []
---

Regex catalog for grepping API keys, tokens, and credentials out of JS bundles, source maps, git history, archived responses, and config files. Pair with [[hardcoded-secrets-enumeration]], [[javascript-source-map-exploitation]], and the [[recon-dorks]] GitHub/Shodan dorks. After a match, **always live-validate** the credential (a matched pattern is not a confirmed secret) before reporting.

## Usage

```bash
# grep a single provider pattern across collected JS
grep -REoh 'AKIA[0-9A-Z]{16}' js_files/ | sort -u

# run the whole catalog against a directory (build a patterns file from the table below)
grep -REohf secrets-patterns.txt ./target_source/ | sort -u

# feed archived bodies (waymore Mode R) through it
grep -REohf secrets-patterns.txt waymore_responses/ | sort -u
```

Prefer purpose-built scanners ([[wiki/tools/trufflehog]], gitleaks, [[wiki/tools/semgrep]]) for scale and entropy checks; this catalog is for targeted greps and for understanding what a match means.

## Cloud / AWS

| Secret | Regex |
|---|---|
| AWS Access Key ID | `(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}` |
| AWS Secret Key | `(?i)aws(.{0,20})?(?-i)['\"][0-9a-zA-Z\/+]{40}['\"]` |
| AWS MWS Key | `amzn\.mws\.[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}` |
| Amazon SNS topic | `arn:aws:sns:[a-z0-9\-]+:[0-9]+:[A-Za-z0-9\-_]+` |
| AWS Cognito pool | `(us-east-1|us-east-2|us-west-1|us-west-2|sa-east-1):[0-9A-Za-z]{8}-[0-9A-Za-z]{4}-[0-9A-Za-z]{4}-[0-9A-Za-z]{4}-[0-9A-Za-z]{12}` |
| Google API key | `AIza[0-9A-Za-z\-_]{35}` |
| Firebase Web API key | `AIza[0-9A-Za-z\-_]{35}` |
| Firebase Database | `([a-z0-9.-]+\.firebaseio\.com|[a-z0-9.-]+\.firebaseapp\.com)` |
| GCP Service Account | `"type": "service_account"` |
| Heroku API key | `(?i)heroku(.{0,20})?[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}` |
| DigitalOcean PAT | `dop_v1_[0-9a-f]{64}` |

## Source control / CI

| Secret | Regex |
|---|---|
| GitHub Personal Access Token | `ghp_[0-9a-zA-Z]{36}` |
| GitHub OAuth Access Token | `gho_[0-9a-zA-Z]{36}` |
| GitHub App Token | `(ghu|ghs)_[0-9a-zA-Z]{36}` |
| GitHub Refresh Token | `ghr_[0-9a-zA-Z]{76}` |
| GitLab Personal Access Token | `glpat-[0-9a-zA-Z-_]{20}` |
| GitLab Runner Token | `GR1348941[a-zA-Z0-9\-=_]{20,40}` |
| PyPI upload token | `pypi-AgEIcHlwaS5vcmc[A-Za-z0-9-_]{50,1000}` |

## Payments

| Secret | Regex |
|---|---|
| Stripe API key | `(?i)stripe(.{0,20})?[sr]k_live_[0-9a-zA-Z]{24}` |
| PayPal Braintree access token | `access_token\$production\$[0-9a-z]{16}\$[0-9a-f]{32}` |
| Square access token | `sq0atp-[0-9A-Za-z\-_]{22}` |
| Square OAuth secret | `sq0csp-[0-9A-Za-z\-_]{43}` |
| Picatic API Key | `sk_live_[0-9a-z]{32}` |
| Shopify shared secret | `shpss_[a-fA-F0-9]{32}` |
| Shopify access token | `shpat_[a-fA-F0-9]{32}` |
| Shopify custom app token | `shpca_[a-fA-F0-9]{32}` |
| Shopify private app token | `shppa_[a-fA-F0-9]{32}` |

## Messaging / email / SaaS

| Secret | Regex |
|---|---|
| Slack token | `xox[baprs]-([0-9a-zA-Z]{10,48})?` |
| Slack Webhook | `https://hooks\.slack\.com/services/T[a-zA-Z0-9_]{8}/B[a-zA-Z0-9_]{8,12}/[a-zA-Z0-9_]{24}` |
| Telegram Bot Token | `[0-9]{8,10}:AA[0-9A-Za-z_-]{35}` |
| Twilio API key | `(?i)twilio(.{0,20})?SK[0-9a-f]{32}` |
| SendGrid API Key | `SG\.[\w_]{16,32}\.[\w_]{16,64}` |
| MailChimp API key | `[0-9a-f]{32}-us[0-9]{1,2}` |
| Mailgun API key | `key-[0-9a-zA-Z]{32}` |
| Zoom JWT Token | `(?i)zoom(.{0,20})?['\"][0-9a-zA-Z-_\.]{36,160}['\"]` |
| Cloudinary Basic Auth | `cloudinary://[0-9]{15}:[0-9A-Za-z\-_]+@[0-9A-Za-z\-_]+` |

## Identity / social

| Secret | Regex |
|---|---|
| Okta Token | `00[0-9a-zA-Z]{20}\$[0-9a-zA-Z]{6,}` |
| Facebook Secret Key | `(?i)(facebook|fb)(.{0,20})?(?-i)['\"][0-9a-f]{32}['\"]` |
| Facebook Client ID | `(?i)(facebook|fb)(.{0,20})?['\"][0-9]{13,17}['\"]` |
| Twitter Secret Key | `(?i)twitter(.{0,20})?[0-9a-z]{35,44}` |
| Twitter Client ID | `(?i)twitter(.{0,20})?[0-9a-z]{18,25}` |
| LinkedIn Client ID | `(?i)linkedin(.{0,20})?(?-i)[0-9a-z]{12}` |
| LinkedIn Secret Key | `(?i)linkedin(.{0,20})?[0-9a-z]{16}` |

## Observability / other

| Secret | Regex |
|---|---|
| Sentry Auth Token | `sentry_auth_token_[0-9a-zA-Z]{70}` |
| Dynatrace token | `dt0[a-zA-Z]{1}[0-9]{2}\.[A-Z0-9]{24}\.[A-Z0-9]{64}` |
| Bugsnag API Key | `(?i)(bs|bugsnag)(.{0,20})?[0-9a-f]{32}` |
| Netlify Token | `(?i)netlify(.{0,20})?['\"][0-9a-zA-Z]{40}['\"]` |
| Adobe Client Credentials | `(?i)adobe(.{0,20})?['\"][a-zA-Z0-9]{32,56}['\"]` |
| Asymmetric Private Key | `-----BEGIN ((EC|PGP|DSA|RSA|OPENSSH) )?PRIVATE KEY( BLOCK)?-----` |

## After a match

1. **Validate live** before reporting (a regex hit is a candidate, not a finding). AWS: `aws sts get-caller-identity`. Slack: post to a test method. GitHub: `curl -H "Authorization: Bearer <tok>" https://api.github.com/rate_limit`.
2. Scope the impact: what does the key reach, and is that host in scope.
3. Report with the redacted key + the validation evidence, never the live secret in the clear. See [[bug-bounty-reporting]].
