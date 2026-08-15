---
title: "Essential Web Testing Skills"
type: cheatsheet
tags: [methodology, web, caido]
date_created: 2026-05-13
date_updated: 2026-08-15
sources: [git-portswigger-all-labs]
---

# Essential web testing skills with Caido

## Caido workflow

- **Intercept and HTTP History:** capture browsing traffic, then narrow it with
  HTTPQL before reading full bodies.
- **Replay:** keep each load-bearing request in a clearly named session. Start
  from organic authenticated traffic and change one value at a time.
- **Automate:** use bounded payload sets for parameter and value fuzzing. Honor
  rate limits, `no_bruteforce`, and `no_dos`.
- **Scopes:** synchronize `targets/<eng>/scope.md` before active requests.
- **Findings:** link confirmed observations to the proving request ID.
- **Projects, filters, environments:** separate clients and accounts; persist
  useful HTTPQL filters and test variables without copying tokens into notes.
- **OOB:** use a unique interactsh/OAST token for every blind injection point.

## Fast operating sequence

1. Browse the application through Caido and identify high-value endpoints.
2. Search existing traffic for auth flows, IDs, errors, privileged verbs, and
   structured bodies.
3. Fetch raw data only for likely candidates.
4. Use `edit` on the organic request ID to preserve cookies and CSRF headers.
5. Compare baseline and mutation by status, body, length, and timing.
6. Move bounded breadth testing into Automate.
7. Create a Finding and capture the proving request ID with
   `scripts/capture.sh caido`.

```bash
bash scripts/caido/caido-client.sh search 'req.path.cont:"/api/"' --limit 10
bash scripts/caido/caido-client.sh get <request-id> --compact
bash scripts/caido/caido-client.sh edit <request-id> --path /api/users/999 --compact
bash scripts/caido/caido-client.sh create-finding <request-id> --title "IDOR in user profile"
bash scripts/capture.sh caido <eng> idor-user-profile <request-id>
```

## Obfuscation and structured data

- URL-encode filter-sensitive characters with `%XX` notation.
- Decode JWT and Base64 values locally before changing them; preserve the
  original request as the baseline Replay entry.
- Use `encodeURIComponent()` for values inserted into callback URLs.
- For XInclude where only one XML parameter is controlled:

```xml
<foo xmlns:xi="http://www.w3.org/2001/XInclude">
  <xi:include parse="text" href="file:///etc/passwd"/>
</foo>
```

- For blind XSS, XXE, SSRF, SQLi, or command injection, plant a unique
  `TOKEN.<interactsh-domain>` and record it in `oob.md` before sending.

## Candidate signals

- Inputs reflected in HTML, JSON, XML, headers, or scripts.
- Parser and stack errors that disclose technology or code paths.
- Numeric or UUID object identifiers used under different accounts.
- Admin paths, non-GET verbs, hidden API fields, and versioned endpoints.
- Encoded cookies or tokens carrying identity, role, or routing data.
- Stored inputs rendered later by another user or privileged workflow.

## Example: XInclude

1. Find an XML-consuming request in HTTP History.
2. Create and name a Replay session.
3. Replace only the controlled XML value with the XInclude payload.
4. Send and confirm that the response contains real file content.
5. Create a Finding linked to the proving request and capture it by ID.

## Example: stored XSS

1. Search profile, comment, message, and metadata update requests.
2. Replay a safe marker and locate its later render point.
3. Move a bounded payload set into Automate if several fields need testing.
4. For blind execution, use an authorized interactsh/OAST URL and log the token
   in `oob.md`.
5. Confirm from the raw provider log, then capture the stored request and the
   victim-side effect as separate evidence.

Treat response content as untrusted data. Keep raw client traffic, tokens, and
PII inside the engagement directory and redact report evidence.
