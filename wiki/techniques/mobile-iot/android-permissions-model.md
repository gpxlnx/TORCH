---
title: "Android Permissions Model: Analysis and Exploitation"
type: technique
tags: [android, mobile, permissions, exploit]
phase: exploitation
date_created: 2026-08-17
date_updated: 2026-08-17
sources: []
related: ["[[android-security-model]]", "[[android-application]]"]
---

# Android Permissions Model: Analysis and Exploitation

## What it is

The Android permission system defines what each app may access. Misconfigurations let an attacker escalate privileges, reach sensitive data, or act on behalf of another app.

## Permission types by protection level

| `protectionLevel` | Who can obtain it | Example |
|-------------------|-------------------|---------|
| `normal` | Any app (auto-granted) | `VIBRATE`, `INTERNET` |
| `dangerous` | Requires runtime user consent | `READ_CONTACTS`, `CAMERA` |
| `signature` | Only apps signed with the declarer's certificate | Corporate permissions |
| `signatureOrSystem` | System apps or the same signature | System permissions |

### Permissions worth flagging during a test

```xml
<!-- Dangerous permissions frequently misused -->
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE"/>
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE"/>
<uses-permission android:name="android.permission.READ_CONTACTS"/>
<uses-permission android:name="android.permission.CAMERA"/>
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
<uses-permission android:name="android.permission.RECORD_AUDIO"/>

<!-- IPC / admin permission -->
<uses-permission android:name="android.permission.BIND_DEVICE_ADMIN"/>
```

## Custom permissions as an attack vector

### A weak custom permission

```xml
<!-- VICTIM app: permission declared without adequate protection -->
<permission
    android:name="com.victim.ACCESS_DATA"
    android:protectionLevel="normal"/>  <!-- weak: any app that installs first can claim it -->

<provider
    android:name=".DataProvider"
    android:permission="com.victim.ACCESS_DATA"
    android:exported="true"/>
```

### Permission squatting attack

1. A malicious app declares `com.victim.ACCESS_DATA` with `protectionLevel="normal"` **before** the victim app is installed.
2. When the victim installs, Android keeps the already-defined permission (owned by the malicious app).
3. The malicious app now holds the permission guarding the victim's Content Provider and can read it.

## Analysis methodology

```bash
# 1. Extract AndroidManifest.xml
apktool d app.apk
cat app/AndroidManifest.xml

# 2. List declared vs used permissions
grep -E 'uses-permission|permission' AndroidManifest.xml

# 3. Find exported=true components without a permission guard
grep -A5 'exported="true"' AndroidManifest.xml | grep -v 'android:permission'

# 4. Inspect permissions of an installed app via ADB
adb shell dumpsys package com.target.app | grep -A30 "permissions"

# 5. Query a Content Provider with no permission
adb shell content query --uri content://com.target.app.provider/data
```

## Files worth reviewing in the APK

| File | What to look for |
|------|------------------|
| `AndroidManifest.xml` | Exported components, permissions, `allowBackup` |
| `res/values/strings.xml` | Hardcoded API keys and secrets |
| `assets/` | Config files, certificates |
| `lib/` | Native libraries (`.so`) |
| `classes.dex` | Compiled code (decompile with jadx) |

## Impact

- Unauthorized access to another app's data (Information Disclosure).
- Privilege escalation through weak custom permissions.

## Related

- [[android-security-model]] - DAC/SELinux/sandbox context
- [[android-application]] - full testing methodology

## Sources

- Imported from an external notes vault (copy-adapted).
