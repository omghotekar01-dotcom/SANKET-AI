from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
report_path = ROOT / "ml" / "artifacts" / "isl500-specialist-v1" / "evaluation.json"
manifest_path = ROOT / "ml" / "artifacts" / "isl500-specialist-v1" / "manifest.json"

report = json.loads(report_path.read_text(encoding="utf-8"))
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
test = report["test"]

expected = {"hello","thank_you","yes","no","help","hospital","water","teacher","student","where"}
labels = set(manifest.get("labels", []))

assert labels == expected, labels
assert manifest["split"]["mode"] == "signer_disjoint", manifest["split"]
assert test["samples"] >= 10, test
assert test["top1_accuracy"] >= 0.70, test
assert test["macro_f1"] >= 0.65, test
assert test["accepted_accuracy"] >= 0.80, test
assert test["coverage"] >= 0.50, test

manifest["model_version"] = "sanket-isl500-specialist-v1"
manifest["training_origin"] = "public_isl500_signer_disjoint"
manifest["source"] = "ISL500/ISL-DATA research/academic-use subset"
manifest["usage"] = "research/academic prototype"
manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
report["manifest"] = manifest
report["claims_note"] = (
    "Metrics apply to the 10-class ISL500 specialist and one signer-disjoint "
    "holdout split. They are not unrestricted ISL accuracy."
)
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

print(json.dumps({
    "quality_gate": "passed",
    "test": test,
    "split": manifest["split"],
}, indent=2))
