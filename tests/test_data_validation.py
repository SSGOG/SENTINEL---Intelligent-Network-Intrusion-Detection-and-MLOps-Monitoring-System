"""Unit test for CIC-IDS2017 schema validation and audit rules."""

from pathlib import Path
import json
import pytest

MANIFEST_PATH = Path("reports/data_quality/dataset_manifest.json")

def test_manifest_exists():
    assert MANIFEST_PATH.exists(), "Dataset manifest must be generated before testing."

def test_primary_dataset_integrity():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    primary_files = manifest["primary_machine_learning_csv"]
    assert len(primary_files) == 8, f"Expected exactly 8 primary CSV files, found {len(primary_files)}"
    
    total_rows = 0
    for item in primary_files:
        assert item["blank_labels"] == 0, f"File {item['filename']} has {item['blank_labels']} blank labels!"
        assert item["validation_status"] == "VALID"
        total_rows += item["row_count"]
    
    assert total_rows > 2_500_000, f"Expected over 2.5 million rows across 8 files, found {total_rows}"

def test_secondary_thursday_quarantine_evidence():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    thursday = manifest["thursday_investigation"]
    sec_web = thursday["secondary_webattacks_audit"]
    assert sec_web is not None
    # Verify the known historical flaw: exactly 288,602 blank labels corresponding to concatenated infiltration rows
    assert sec_web["blank_labels"] == 288602, f"Expected 288,602 blank labels in GeneratedLabelledFlows, got {sec_web['blank_labels']}"
