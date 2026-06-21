# Investigation Queries — AcmeCorp Intrusion

## Phase 1 — Initial Triage

```spl
index=main | stats count by sourcetype
```
**Resultado:** xmlwineventlog (Sysmon), XmlWinEventLog:Security — datos de ataque confirmados en el índice.

```spl
index=main | stats count by Computer
```
**Resultado:** Actividad en `win-dc-397.attackrange.local` y `win-dc-942.attackrange.local`.

---

## Phase 2 — PowerShell Execution (T1059.001)

**Sigma-cli detection query:**
```spl
index=main Image="*\\powershell.exe" CommandLine IN ("*-enc*", "*-WindowStyle Hidden*", "*-ExecutionPolicy Bypass*", "*-NoProfile*")
```
**Resultado:** 35 eventos. PowerShell con comandos codificados en Base64 y bypass de política de ejecución.

**Triage — ver comandos completos:**
```spl
index=main Image="*\\powershell.exe" CommandLine IN ("*-enc*", "*-WindowStyle Hidden*", "*-ExecutionPolicy Bypass*", "*-NoProfile*")
| table _time Computer CommandLine
| sort _time
```
**Hallazgo:** `powershell.exe -Exec bypass -enc VwByAGkAdABlAC0ASABvAHMAdAA...` en `win-dc-397` a las 08:54. Luego múltiples comandos codificados en `win-dc-942`.

---

## Phase 3 — Credential Dumping (T1003.001)

**Sigma-cli detection query:**
```spl
index=main TargetImage="*\\lsass.exe" GrantedAccess IN ("*0x1010*", "*0x1410*", "*0x1438*")
```
**Resultado:** 1 evento crítico.

**Triage:**
```spl
index=main TargetImage="*\\lsass.exe" GrantedAccess IN ("*0x1010*", "*0x1410*", "*0x1438*")
| table _time Computer SourceImage TargetImage GrantedAccess
```
**Hallazgo:** `powershell.exe` accedió a `lsass.exe` con `GrantedAccess=0x1410` (PROCESS_QUERY_INFORMATION + PROCESS_VM_READ) en `win-dc-942` a las 08:56. Dump de credenciales confirmado.

---

## Phase 4 — Persistence (T1547.001)

**Sigma-cli detection query:**
```spl
index=main EventType="SetValue" TargetObject IN ("*\\CurrentVersion\\Run*", "*\\CurrentVersion\\RunOnce*")
```
**Resultado:** 3 eventos de persistencia vía registry.

**Triage:**
```spl
index=main EventType="SetValue" TargetObject IN ("*\\CurrentVersion\\Run*", "*\\CurrentVersion\\RunOnce*")
| table _time Computer Image TargetObject Details
```
**Hallazgos:**
- `HKCU\...\Run\Atomic Red Team` → `C:\Path\AtomicRedTeam.exe`
- `HKLM\...\RunOnceEx\0001\Depend\1` → `C:\Path\AtomicRedTeam.dll`
- `HKLM\...\RunOnce\NextRun` → PowerShell web cradle descargando payload de GitHub

---

## Phase 5 — Lateral Movement (T1021.001)

**Sigma-cli detection query:**
```spl
index=main source="WinEventLog:Security" EventCode=4624 LogonType=10
```
**Resultado:** 17 eventos de logon RDP (LogonType=10).

**Triage:**
```spl
index=main source="WinEventLog:Security" EventCode=4624 LogonType=10
| table _time TargetUserName IpAddress WorkstationName
| sort _time
```
**Hallazgo:** Usuario `Administrator` conectándose por RDP desde `10.0.1.12` y `10.0.1.14` a las 09:15–09:17. Movimiento lateral post-dump de credenciales.

---

## Phase 6 — Timeline Correlation

```spl
index=main (
  (Image="*\\powershell.exe" CommandLine IN ("*-enc*","*-ExecutionPolicy Bypass*","*-NoProfile*")) OR
  (TargetImage="*\\lsass.exe" GrantedAccess IN ("*0x1010*","*0x1410*","*0x1438*")) OR
  (EventType="SetValue" TargetObject IN ("*\\CurrentVersion\\Run*","*\\CurrentVersion\\RunOnce*")) OR
  (source="WinEventLog:Security" EventCode=4624 LogonType=10)
)
| eval Technique=case(
    match(Image,"powershell") AND match(CommandLine,"-enc|-bypass|-NoProfile"), "T1059.001 PowerShell",
    isnotnull(TargetImage) AND match(TargetImage,"lsass"), "T1003.001 LSASS Dump",
    EventType="SetValue", "T1547.001 Registry Persistence",
    EventCode="4624" AND LogonType="10", "T1021.001 RDP Lateral Movement"
  )
| table _time Technique Computer TargetUserName IpAddress
| sort _time
```
