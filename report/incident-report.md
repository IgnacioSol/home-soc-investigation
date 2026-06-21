# Incident Report — AcmeCorp Intrusion
**Case ID:** INC-2024-001 | **Analyst:** Ignacio Solano | **Severity:** Critical | **Status:** Contained (Lab)

---

## Executive Summary

Se detectó una intrusión multi-etapa en win-dc-942.attackrange.local. El atacante ejecutó PowerShell con comandos codificados en Base64 para simultáneamente robar credenciales de LSASS y establecer persistencia via Registry Run Keys. 17 minutos después usó las credenciales del usuario Administrator para moverse lateralmente por RDP desde 10.0.1.12.

---

## Attack Timeline

| Timestamp (UTC) | Technique | Host | Evidence |
|---|---|---|---|
| 2020-11-27 08:56:59 | T1059.001 PowerShell | win-dc-942.attackrange.local | powershell.exe -EncodedCommand + -ExecutionPolicy Bypass |
| 2020-11-27 08:56:59 | T1003.001 LSASS Dump | win-dc-942.attackrange.local | powershell.exe → lsass.exe GrantedAccess=0x1410 |
| 2020-11-27 08:56:59 | T1547.001 Persistence | win-dc-942.attackrange.local | reg.exe → Run/RunOnce keys + web cradle |
| 2020-11-27 09:15:24 | T1021.001 RDP | ar-win-dc.attackrange.local | Administrator RDP desde 10.0.1.12 (LogonType=10) |

---

## Indicators of Compromise (IOCs)

### IPs / Hostnames
| Indicator | Type | Context |
|---|---|---|
| win-dc-942.attackrange.local | Hostname | Host comprometido — ejecución del ataque |
| 10.0.1.12 | IP | Máquina del atacante — origen del RDP |

### Registry Keys
| Key | Value | Context |
|---|---|---|
| HKCU\...\Run\Atomic Red Team | C:\Path\AtomicRedTeam.exe | Ejecuta en cada login |
| HKLM\...\RunOnceEx\0001\Depend\1 | C:\Path\AtomicRedTeam.dll | Ejecuta en próximo boot |
| HKLM\...\RunOnce\NextRun | powershell.exe IEX DownloadString(...) | Descarga payload desde GitHub en cada arranque |

---

## MITRE ATT&CK Mapping

| Tactic | Technique | ID | Detection Method |
|---|---|---|---|
| Execution | PowerShell | T1059.001 | Sysmon EventID 1 — Image + CommandLine |
| Credential Access | LSASS Memory | T1003.001 | Sysmon EventID 10 — TargetImage + GrantedAccess |
| Persistence | Registry Run Keys | T1547.001 | Sysmon EventID 13 — EventType=SetValue |
| Lateral Movement | RDP | T1021.001 | Security EventID 4624 LogonType=10 |

---

## Findings by Phase

### Phase 1 — Initial Triage
7000 eventos de Sysmon y 34 de Windows Security en dos domain controllers: win-dc-397 (929 eventos) y win-dc-942 (6031 eventos). El volumen anómalo en win-dc-942 indicó que era el foco de la actividad maliciosa.

### Phase 2 — Execution (T1059.001)
35 eventos de PowerShell con flags maliciosos detectados. El atacante usó `-EncodedCommand` para ocultar el payload en Base64 y `-ExecutionPolicy Bypass` para ignorar las políticas de seguridad. El comando decodificado reveló un execution wrapper que ejecuta código en memoria sin tocar el disco — técnica de evasión anti-antivirus.

### Phase 3 — Credential Access (T1003.001)
1 evento crítico: `powershell.exe` abrió un handle a `lsass.exe` con `GrantedAccess=0x1410` (permiso de lectura de memoria). LSASS es el proceso de Windows que guarda las contraseñas en memoria. Este acceso fue suficiente para extraer las credenciales del usuario Administrator del dominio.

### Phase 4 — Persistence (T1547.001)
3 claves de registry escritas en el mismo segundo que las fases 2 y 3 — parte del mismo script. El atacante dejó tres mecanismos de persistencia: un ejecutable en Run (activo en cada login), una DLL en RunOnceEx (activa en el próximo boot), y un web cradle en RunOnce que re-descarga el payload desde GitHub en cada arranque.

### Phase 5 — Lateral Movement (T1021.001)
17 eventos de RDP (LogonType=10) con el usuario Administrator conectándose desde 10.0.1.12, exactamente 17 minutos después del dump de LSASS. Confirma que las credenciales robadas en Fase 3 fueron usadas inmediatamente para expandirse por la red.

---

## Remediation Recommendations

1. **Aislar** win-dc-942 y bloquear RDP desde 10.0.1.12 inmediatamente
2. **Resetear** todas las contraseñas del dominio — las credenciales de Administrator están comprometidas
3. **Eliminar** las claves de registry maliciosas y los archivos AtomicRedTeam.exe / .dll
4. **Bloquear** conexiones salientes a raw.githubusercontent.com en el firewall
5. **Habilitar** PowerShell Constrained Language Mode y script block logging (EventID 4104)
6. **Desplegar** Credential Guard para proteger LSASS de accesos externos

---

## Appendix — SPL Queries Used

```
-- T1059.001
index=main Image="*\\powershell.exe" CommandLine IN ("*-enc*", "*-WindowStyle Hidden*", "*-ExecutionPolicy Bypass*", "*-NoProfile*")

-- T1003.001
index=main TargetImage="*\\lsass.exe" GrantedAccess IN ("*0x1010*", "*0x1410*", "*0x1438*")

-- T1547.001
index=main EventType="SetValue" TargetObject IN ("*\\CurrentVersion\\Run*", "*\\CurrentVersion\\RunOnce*")

-- T1021.001
index=main source="WinEventLog:Security" EventCode=4624 LogonType=10
```

*Todas las queries generadas por sigma-cli desde las reglas Sigma en [sigma-detection-rules](https://github.com/IgnacioSol/sigma-detection-rules).*
