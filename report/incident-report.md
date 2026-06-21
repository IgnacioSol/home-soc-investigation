# Incident Report — AcmeCorp Windows Intrusion
**Case ID:** INC-2024-001 | **Analyst:** Ignacio Solano | **Severity:** Critical | **Status:** Contained (Lab)

---

## Executive Summary

A multi-stage intrusion was detected across AcmeCorp's Windows domain controllers (`win-dc-397` and `win-dc-942`). The attacker executed obfuscated PowerShell commands, dumped credentials from LSASS memory, established persistence via registry Run keys, and performed lateral movement via RDP using stolen Administrator credentials. All four attack phases were detected using Sigma rules (from [sigma-detection-rules](https://github.com/IgnacioSol/sigma-detection-rules)) converted to Splunk SPL via sigma-cli.

---

## Attack Timeline

| Timestamp (UTC) | Technique | Host | Evidence |
|---|---|---|---|
| 2021-01-19 08:54:43 | T1059.001 PowerShell | win-dc-397.attackrange.local | `powershell.exe -Exec bypass -enc VwByAGkAdABlAC0A...` |
| 2021-01-19 08:56:59 | T1059.001 PowerShell | win-dc-942.attackrange.local | Multiple `-EncodedCommand` + `-ExecutionPolicy Bypass` |
| 2021-01-19 08:56:59 | T1003.001 LSASS Dump | win-dc-942.attackrange.local | `powershell.exe` → `lsass.exe` GrantedAccess=0x1410 |
| 2021-01-19 08:56:59 | T1547.001 Persistence | win-dc-942.attackrange.local | `reg.exe` → `Run\Atomic Red Team` + `RunOnce\NextRun` |
| 2021-07-22 09:15:24 | T1021.001 RDP | ar-win-dc.attackrange.local | Administrator RDP from 10.0.1.12 (LogonType=10) |
| 2021-07-22 09:16:58 | T1021.001 RDP | ar-win-dc-2 | Administrator RDP from 10.0.1.12 / 10.0.1.14 |

---

## Indicators of Compromise (IOCs)

### IPs / Hostnames
| Indicator | Type | Context |
|---|---|---|
| win-dc-397.attackrange.local | Hostname | Initial PowerShell execution |
| win-dc-942.attackrange.local | Hostname | LSASS dump + persistence |
| 10.0.1.12 | IP | RDP lateral movement source |
| 10.0.1.14 | IP | RDP lateral movement source |

### Registry Keys
| Key | Value | Context |
|---|---|---|
| `HKCU\...\Run\Atomic Red Team` | `C:\Path\AtomicRedTeam.exe` | Persistence — executes on every login |
| `HKLM\...\RunOnceEx\0001\Depend\1` | `C:\Path\AtomicRedTeam.dll` | Persistence — executes on next boot |
| `HKLM\...\RunOnce\NextRun` | PowerShell web cradle | Persistence — re-downloads payload from GitHub |

### Malicious Files
| File | Context |
|---|---|
| `C:\Path\AtomicRedTeam.exe` | Persistence payload |
| `C:\Path\AtomicRedTeam.dll` | Persistence DLL |

---

## MITRE ATT&CK Mapping

| Tactic | Technique | ID | Detection Method |
|---|---|---|---|
| Execution | Command and Scripting Interpreter: PowerShell | T1059.001 | Sysmon EventID 1 — Image + CommandLine |
| Credential Access | OS Credential Dumping: LSASS Memory | T1003.001 | Sysmon EventID 10 — TargetImage + GrantedAccess |
| Persistence | Boot or Logon Autostart: Registry Run Keys | T1547.001 | Sysmon EventID 13 — EventType=SetValue |
| Lateral Movement | Remote Services: Remote Desktop Protocol | T1021.001 | Security EventID 4624 LogonType=10 |

---

## Findings by Phase

### Phase 1 — Initial Triage
Splunk index `main` contains Sysmon (xmlwineventlog) and Windows Security (XmlWinEventLog:Security) logs from two hosts. Anomalous activity detected on both `win-dc-397` and `win-dc-942`.

### Phase 2 — Execution (T1059.001)
35 PowerShell events detected. Attacker used `-EncodedCommand` (Base64 obfuscation) and `-ExecutionPolicy Bypass` to evade defenses. Initial execution on `win-dc-397` at 08:54, spreading to `win-dc-942` at 08:56. Sample decoded command: `Write-Host "Hello World"` — testing execution before deploying real payload.

### Phase 3 — Credential Access (T1003.001)
1 critical event: `powershell.exe` opened a handle to `lsass.exe` with `GrantedAccess=0x1410` (PROCESS_QUERY_INFORMATION + PROCESS_VM_READ). This access mask is sufficient to extract credential material from memory. Confirmed credential theft enabling subsequent lateral movement.

### Phase 4 — Persistence (T1547.001)
3 registry write events at 08:56:59 on `win-dc-942`. Attacker used `reg.exe` to establish persistence in three locations simultaneously: user Run key (survives every login), RunOnceEx (executes once at boot), and RunOnce with a PowerShell web cradle that re-downloads the payload from `raw.githubusercontent.com`.

### Phase 5 — Lateral Movement (T1021.001)
17 RDP logon events (EventCode=4624, LogonType=10). `Administrator` account used from `10.0.1.12` and `10.0.1.14` starting at 09:15 — 18 minutes after the LSASS dump. Confirms credential reuse from Phase 3.

---

## Remediation Recommendations

### Immediate Actions (0–24h)
1. Isolate `win-dc-397` and `win-dc-942` from the network
2. Reset all domain Administrator passwords — assume all cached credentials compromised
3. Delete persistence registry keys and remove `AtomicRedTeam.exe` / `.dll`
4. Block RDP access from `10.0.1.12` and `10.0.1.14`

### Short Term (1–7 days)
5. Block outbound HTTP to `raw.githubusercontent.com` at the firewall
6. Hunt for additional hosts with RDP logons from the same source IPs
7. Scan all domain hosts for `AtomicRedTeam.*` files

### Long Term (hardening)
8. Enable PowerShell Constrained Language Mode and script block logging (EventID 4104)
9. Deploy Credential Guard to protect LSASS
10. Restrict who can initiate RDP sessions and from which subnets
11. Alert on `GrantedAccess IN (0x1010, 0x1410, 0x1438)` against `lsass.exe`

---

## Appendix — SPL Queries Used

```spl
-- T1059.001 Detection
index=main Image="*\\powershell.exe" CommandLine IN ("*-enc*", "*-WindowStyle Hidden*", "*-ExecutionPolicy Bypass*", "*-NoProfile*")

-- T1003.001 Detection
index=main TargetImage="*\\lsass.exe" GrantedAccess IN ("*0x1010*", "*0x1410*", "*0x1438*")

-- T1547.001 Detection
index=main EventType="SetValue" TargetObject IN ("*\\CurrentVersion\\Run*", "*\\CurrentVersion\\RunOnce*")

-- T1021.001 Detection
index=main source="WinEventLog:Security" EventCode=4624 LogonType=10
```

*All detection queries generated by sigma-cli from Sigma rules in [sigma-detection-rules](https://github.com/IgnacioSol/sigma-detection-rules).*
