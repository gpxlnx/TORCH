---
title: iOS Security Model
type: technique
tags: [ios, mobile, security-model, sandbox, keychain, secure-enclave, data-protection, entitlements]
phase: recon
date_created: 2026-08-17
date_updated: 2026-08-17
sources: []
related: ["[[ios-application]]", "[[ios-exploitation]]"]
---

# iOS Security Model

## What it is

iOS implements a layered security model combining process isolation, hardware-backed cryptography, permission control, and code-integrity verification. Understanding it is the basis for identifying attack vectors in iOS apps.

## Core components

### 1. Privilege separation and sandbox

- Apps run as a regular user (not root); core system processes run as root.
- Each app lives in its own sandbox with no access to other apps' data or system files.
- Access to system resources (camera, location) requires explicit user approval.

### 2. Secure Enclave Processor (SEP)

- A dedicated coprocessor for cryptographic operations.
- Manages encryption keys without exposing them to the main processor.
- The root of trust for all device data protections.

### 3. Data Protection: four classes

| Class | Name | Behavior |
|-------|------|----------|
| `NSFileProtectionComplete` | Complete Protection | Inaccessible while the device is locked |
| `NSFileProtectionCompleteUnlessOpen` | Protected Unless Open | Accessible if the file was already open before lock |
| `NSFileProtectionCompleteUntilFirstUserAuthentication` | Protected Until First Unlock | Available after the first unlock following boot |
| `NSFileProtectionNone` | No Protection | Protected only by the device UID, the weakest class |

**Attack vector**: files stored with `NSFileProtectionNone` are readable without unlocking the device.

### 4. Keychain

- An encrypted vault for passwords, tokens, and sensitive data.
- The key is bound to the device plus passcode and is not transferable between devices.
- **Persistence after uninstall**: Keychain items survive app deletion.
  - Vector: reinstall the app and reach the previous session's stored data.

```swift
// Good practice: clear the Keychain on first run
let userDefaults = UserDefaults.standard
if userDefaults.bool(forKey: "hasRunBefore") == false {
    // Remove Keychain items here
    userDefaults.set(true, forKey: "hasRunBefore")
}
```

### 5. App capabilities and permissions

- Declared in `Info.plist`.
- Require a usage-description string (for example `NSLocationWhenInUseUsageDescription`).
- Trigger an explicit runtime approval prompt.

### 6. Entitlements

- Special permissions beyond the default sandbox limits.
- Defined in the Xcode project or in the `embedded.mobileprovision` inside the IPA.
- Examples: cross-app Keychain sharing, access to specific system resources.

## Attack vectors for pentest

| Component | Vector |
|-----------|--------|
| Keychain | Data persisting after uninstall; weak protection class |
| Data Protection | Files stored as `NSFileProtectionNone` |
| Entitlements | Excessive entitlements in the IPA |
| Info.plist | Unnecessary permissions declared |
| Sandbox | Jailbreak removes isolation entirely |
| SEP | Bypass via firmware exploits (rare) |

## Differences vs. Android

| Aspect | iOS | Android |
|--------|-----|---------|
| Rooting / Jailbreak | Requires exploits; no custom ROMs | `su` binary or custom ROM; unlockable bootloader |
| Code signing | Mandatory; verified at boot | More flexible with sideloading |
| App store | App Store only (official) | Play Store plus sideloading |
| Sandboxing | More restrictive | Less restrictive |

## Related

- [[ios-application]] - full iOS testing methodology
- [[ios-exploitation]] - deeper reverse-engineering and exploitation

## Sources

- Imported from an external notes vault (copy-adapted).
