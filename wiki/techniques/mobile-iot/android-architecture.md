---
title: Android Architecture for Pentest
type: technique
tags: [android, mobile, architecture, pentest]
phase: recon
date_created: 2026-08-17
date_updated: 2026-08-17
sources: []
related: ["[[android-application]]", "[[android-security-model]]", "[[android-permissions-model]]"]
---

# Android Architecture for Pentest

## What it is

Understanding the Android platform architecture is the foundation for mobile testing. Android is built in layers, and each layer exposes a distinct attack surface. This page maps those layers to where an attacker looks.

## Android system layers

The APK lifecycle runs code through compilation to the DEX format, DEX is built into an APK, the APK is signed, and the signed APK is distributed (Play Store or sideload) and installed.

| Layer | Components |
|-------|-----------|
| Applications | User apps + system apps |
| Application Framework | Activity Manager, Package Manager, Content Providers, View System |
| Libraries + Android Runtime | SQLite, SSL, OpenGL, ART/Dalvik VM |
| Hardware Abstraction Layer | Hardware drivers |
| Linux Kernel | Security, memory management, drivers |

### Modern app architecture (Clean Architecture)

Most apps split into three layers, which tells you where secrets and business logic live:

```
+-----------------------------+
|          UI Layer           |  <- Activities, Fragments, ViewModels
+-----------------------------+
|         Domain Layer        |  <- Use Cases, Business Logic
+-----------------------------+
|          Data Layer         |  <- Repositories, Data Sources
|    (Data Sources + Repos)   |  <- APIs, Databases, Cache
+-----------------------------+
```

## Android Framework security components

- **Activity Manager**: manages the Activity lifecycle. Exported activities are an attack surface.
- **Package Manager**: manages APK installation and permission verification.
- **Content Provider**: the standard mechanism for sharing data between apps. Sink for SQL injection and path traversal.
- **Binder IPC**: inter-process communication. A path to privilege escalation when a privileged service trusts caller input.

## Pentest impact

- **Exported components**: activities, services, and receivers exported without protection are reachable via ADB or a malicious app.
- **IPC via Intents**: data passed through implicit intents can be intercepted by a co-installed app.
- **Exposed data layer**: the app's APIs and databases can leak data when misconfigured.

## Tools for architecture analysis

| Tool | Use |
|------|-----|
| `adb shell dumpsys activity` | Inspect running activities |
| Jadx / Apktool | Decompile for per-layer analysis |
| Drozer | Audit exported components |
| MobSF | Automated architecture analysis |

## Related

- [[android-application]] - full Android testing methodology, tooling, and exploitation
- [[android-security-model]] - the security model (DAC/SELinux/sandbox)
- [[android-permissions-model]] - the permission system

## Sources

- Imported from an external notes vault (copy-adapted).
