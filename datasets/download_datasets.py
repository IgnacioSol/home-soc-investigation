#!/usr/bin/env python3
"""
Downloads attack simulation datasets from splunk/attack_data for the 4 ATT&CK
techniques used in this investigation.
"""

import urllib.request
import os
import gzip
import shutil

BASE_URL = "https://media.githubusercontent.com/media/splunk/attack_data/master/datasets/attack_techniques"

DATASETS = [
    {
        "technique": "T1059.001",
        "name": "powershell_malicious",
        "url": f"{BASE_URL}/T1059.001/atomic_red_team/windows-powershell.log",
        "filename": "T1059.001_powershell.log",
    },
    {
        "technique": "T1003.001",
        "name": "lsass_memory_dump",
        "url": f"{BASE_URL}/T1003.001/atomic_red_team/windows-security.log",
        "filename": "T1003.001_lsass.log",
    },
    {
        "technique": "T1547.001",
        "name": "registry_run_keys",
        "url": f"{BASE_URL}/T1547.001/atomic_red_team/windows-sysmon.log",
        "filename": "T1547.001_registry.log",
    },
    {
        "technique": "T1021.001",
        "name": "rdp_lateral_movement",
        "url": f"{BASE_URL}/T1021.001/atomic_red_team/windows-security.log",
        "filename": "T1021.001_rdp.log",
    },
]

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def download(dataset):
    dest = os.path.join(OUTPUT_DIR, dataset["filename"])
    if os.path.exists(dest):
        print(f"[skip] {dataset['filename']} already exists")
        return
    print(f"[download] {dataset['technique']} → {dataset['filename']}")
    try:
        urllib.request.urlretrieve(dataset["url"], dest)
        print(f"[ok] saved to {dest}")
    except Exception as e:
        print(f"[error] {dataset['technique']}: {e}")
        print(f"        URL tried: {dataset['url']}")


if __name__ == "__main__":
    print("Downloading attack_data datasets...\n")
    for ds in DATASETS:
        download(ds)
    print("\nDone. Run ingest.py next to load into Splunk.")
