from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
manifest=json.loads((ROOT/"ml/artifacts/isl500-specialist-v1/manifest.json").read_text(encoding="utf-8"))
report=json.loads((ROOT/"ml/artifacts/isl500-specialist-v1/evaluation.json").read_text(encoding="utf-8"))
test=report["test"]
expected={"hello","thank_you","yes","no","help","water","teacher","student","where"}

assert set(manifest["labels"])==expected, manifest["labels"]
assert manifest["split"]["mode"]=="signer_disjoint_10_2_3", manifest["split"]
assert len(manifest["split"]["test_signers"])==3
assert test["samples"]>=27, test
assert test["top1_accuracy"]>=0.70, test
assert test["macro_f1"]>=0.65, test
assert test["accepted_accuracy"]>=0.80, test
assert test["coverage"]>=0.50, test
print(json.dumps({"quality_gate":"passed","test":test,"backend":manifest["backend"]},indent=2))
