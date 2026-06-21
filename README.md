# Home SOC Investigation Lab

A simulated SOC Tier 1/2 incident investigation using Splunk, real attack data, and custom Sigma detection rules.

This project is the applied layer of my [sigma-detection-rules](https://github.com/IgnacioSol/sigma-detection-rules) repository — the rules defined there are converted to SPL and executed here against real attack data.

---

## Scenario

**Target organization:** AcmeCorp (fictional)  
**Incident type:** Multi-stage APT intrusion  
**Analyst role:** SOC Tier 2 (escalated case)

A Windows endpoint in AcmeCorp's corporate network triggered several alerts. Investigation revealed a full attack chain:

| Phase | Technique | ATT&CK ID |
|---|---|---|
| Execution | Malicious PowerShell | T1059.001 |
| Credential Access | LSASS Memory Dump | T1003.001 |
| Persistence | Registry Run Keys | T1547.001 |
| Lateral Movement | RDP to internal host | T1021.001 |

---

## Stack

| Component | Purpose |
|---|---|
| Splunk 9.2.1 (Docker) | SIEM — log ingestion, indexing, search |
| splunk/attack_data | Simulated attack logs per ATT&CK technique |
| sigma-cli | Converts Sigma YAML rules to SPL queries |
| Python 3 | Dataset download and ingestion scripts |

---

## Repository Structure

```
home-soc-investigation/
├── docker/
│   └── docker-compose.yml       # Splunk instance
├── datasets/                    # Downloaded attack_data logs (gitignored)
├── sigma-to-spl/
│   └── converted/               # SPL output from sigma-cli
├── investigation/
│   └── queries.md               # SPL queries built during investigation
└── report/
    └── incident-report.md       # Final incident report
```

---

## How to Run

### 1. Start Splunk

```bash
cd docker
docker compose up -d
```

Splunk UI → http://localhost:8000  
Username: `admin` / Password: `AcmeCorp2024!`

Wait ~60 seconds for Splunk to initialize on first run.

### 2. Download datasets

```bash
python3 datasets/download_datasets.py
```

### 3. Ingest data into Splunk

```bash
python3 datasets/ingest.py
```

### 4. Convert Sigma rules to SPL

```bash
cd sigma-to-spl
pip install sigma-cli
sigma convert -t splunk -p splunk_windows ../path/to/sigma-rules/ -o converted/
```

### 5. Run the investigation

Open `investigation/queries.md` and follow the phases.

---

## Detection Rules

All detection logic originates from [sigma-detection-rules](https://github.com/IgnacioSol/sigma-detection-rules):

- `rules/T1003.001_lsass_memory_access.yml`
- `rules/T1059.001_malicious_powershell.yml`
- `rules/T1547.001_registry_run_keys.yml`
- `rules/T1021.001_rdp_lateral_movement.yml`

---

## Final Report

See [`report/incident-report.md`](report/incident-report.md) for the complete incident report including executive summary, timeline, IOCs, ATT&CK mapping, and remediation recommendations.

---

## Learning Objectives

- Operate Splunk as a SIEM for real incident investigation
- Translate Sigma detection rules to SPL using sigma-cli
- Build an attack timeline by correlating Windows Event Logs
- Produce a professional SOC Tier 2 incident report
