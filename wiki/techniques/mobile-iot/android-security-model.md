---
title: "Android Security Model: DAC, SELinux, Sandboxing"
type: technique
tags: [android, mobile, security-model, selinux, sandbox]
phase: recon
date_created: 2026-08-17
date_updated: 2026-08-17
sources: []
related: ["[[android-architecture]]", "[[android-application]]", "[[android-permissions-model]]"]
---

# Android Security Model: DAC, SELinux, Sandboxing

## What it is

Android layers several security mechanisms: DAC (inherited from Linux), SELinux (MAC), the per-app sandbox, and the permission system. Understanding this model is what lets you reason about where a bypass is possible.

## Layer 1: Linux DAC (Discretionary Access Control)

- Every app is assigned a **unique UID** by the system.
- Files owned by one app are inaccessible to others by default.
- Processes run under the app's UID.
- **Weakness**: if two apps share the same UID (`sharedUserId`), each can read the other's data.

```xml
<!-- AndroidManifest.xml: use of sharedUserId (deprecated API 29+) -->
<manifest android:sharedUserId="com.example.shared">
```

## Layer 2: SELinux (Mandatory Access Control)

- **MAC**: policies are defined by the system, not by the file owner.
- Each process runs in a **SELinux context** (for example `u:r:untrusted_app:s0`).
- `allow` rules define what each domain may do.
- **audit2allow** shows what SELinux blocked, useful to understand denials during a bypass attempt.

### Permission protection levels

| Level | Description |
|-------|-------------|
| `normal` | Granted automatically at install |
| `dangerous` | Requires explicit user approval |
| `signature` | Only apps sharing the same signing certificate |
| `signatureOrSystem` | System apps or the same signature |

## Layer 3: App sandbox

- Each app runs in its **own Linux process** under a unique UID.
- It **cannot access another app's data** without an explicit grant.
- Private storage lives in `/data/data/<package>/`.
- Content Providers are the standard mechanism for cross-app data sharing.

### Sandbox bypass attack surfaces

```
1. Exported Content Providers with no read permission
2. Backup over ADB (android:allowBackup="true")
3. Exported Activities reachable without authentication
4. Interceptable implicit Intents
5. Files on External Storage (shared across apps)
```

## Protecting components in AndroidManifest.xml

```xml
<!-- Declaring a custom permission -->
<permission
    android:name="com.example.MY_PERMISSION"
    android:protectionLevel="signature"/>

<!-- Using the permission to protect a component -->
<activity
    android:name=".AdminActivity"
    android:permission="com.example.MY_PERMISSION"/>
```

## Primary attack vectors

| Vector | Test technique |
|--------|----------------|
| Exported activities | `adb shell am start -n com.app/.Activity` |
| Exported services | `adb shell am startservice` |
| Content Providers | `adb shell content query --uri content://...` |
| Broadcast Receivers | `adb shell am broadcast -a ACTION` |
| Backup | `adb backup -apk -f backup.ab com.app` |

## Impact

- **Classes**: Broken Access Control, Information Disclosure, Privilege Escalation.
- Severity depends on the data or functionality exposed by the misconfigured component.

## Related

- [[android-application]] - full testing methodology
- [[android-permissions-model]] - the permission system in detail
- [[android-architecture]] - platform layers

## Sources

- Imported from an external notes vault (copy-adapted).
