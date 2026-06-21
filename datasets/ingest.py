#!/usr/bin/env python3
"""
Ingests downloaded log files into Splunk via HTTP Event Collector (HEC).
Run after download_datasets.py and after Splunk is up (docker compose up -d).
"""

import urllib.request
import urllib.error
import json
import os
import time

SPLUNK_HEC_URL = "http://localhost:8088/services/collector/raw"
# HEC token is created automatically via Splunk API on first run
SPLUNK_HEC_SETUP_URL = "http://localhost:8089/services/data/inputs/http"
SPLUNK_USER = "admin"
SPLUNK_PASS = "AcmeCorp2024!"

DATASETS = [
    {"filename": "T1059.001_powershell.log",  "index": "attack_data", "sourcetype": "WinEventLog:Microsoft-Windows-PowerShell/Operational"},
    {"filename": "T1003.001_lsass.log",       "index": "attack_data", "sourcetype": "WinEventLog:Security"},
    {"filename": "T1547.001_registry.log",    "index": "attack_data", "sourcetype": "XmlWinEventLog:Microsoft-Windows-Sysmon/Operational"},
    {"filename": "T1021.001_rdp.log",         "index": "attack_data", "sourcetype": "WinEventLog:Security"},
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def get_hec_token():
    """Creates a HEC token via Splunk REST API and returns it."""
    import base64
    credentials = base64.b64encode(f"{SPLUNK_USER}:{SPLUNK_PASS}".encode()).decode()
    data = urllib.parse.urlencode({
        "name": "attack_data_ingest",
        "index": "attack_data",
        "disabled": "0",
    }).encode()
    req = urllib.request.Request(
        SPLUNK_HEC_SETUP_URL,
        data=data,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
    )
    # Disable SSL verification for local Docker instance
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            body = json.loads(resp.read())
            return body.get("entry", [{}])[0].get("content", {}).get("token")
    except Exception as e:
        print(f"[warn] Could not auto-create HEC token: {e}")
        return None


def ingest_file(filepath, sourcetype, index, token):
    if not os.path.exists(filepath):
        print(f"[skip] {os.path.basename(filepath)} not found — run download_datasets.py first")
        return

    print(f"[ingest] {os.path.basename(filepath)} → index={index} sourcetype={sourcetype}")
    with open(filepath, "rb") as f:
        data = f.read()

    req = urllib.request.Request(
        f"{SPLUNK_HEC_URL}?sourcetype={sourcetype}&index={index}",
        data=data,
        headers={
            "Authorization": f"Splunk {token}",
            "Content-Type": "text/plain",
        }
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            if result.get("text") == "Success":
                print(f"[ok] {os.path.basename(filepath)}")
            else:
                print(f"[warn] {result}")
    except urllib.error.HTTPError as e:
        print(f"[error] HTTP {e.code}: {e.read().decode()}")


if __name__ == "__main__":
    import urllib.parse

    print("Waiting for Splunk to be ready...")
    time.sleep(5)

    token = get_hec_token()
    if not token:
        print("\n[manual step needed]")
        print("Go to: http://localhost:8000 → Settings → Data Inputs → HTTP Event Collector")
        print("Create a token, then set HEC_TOKEN env variable and re-run:")
        print("  HEC_TOKEN=your-token python3 ingest.py")
        token = os.environ.get("HEC_TOKEN")
        if not token:
            exit(1)

    print(f"\nUsing HEC token: {token[:8]}...\n")

    for ds in DATASETS:
        filepath = os.path.join(SCRIPT_DIR, ds["filename"])
        ingest_file(filepath, ds["sourcetype"], ds["index"], token)

    print("\nIngestion complete. Search in Splunk: index=attack_data")
