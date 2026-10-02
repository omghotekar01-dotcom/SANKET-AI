from __future__ import annotations

import json
from pathlib import Path

from .temporal_model import TemporalTemplateModel

CORE_EXTENSION_TARGETS = {"yes", "no", "help", "water", "where"}


class CoreExtensionModel:
    """Quality-gated SANKET model for high-value core signs absent from bootstrap."""

    MIN_TOP1 = 0.45
    MIN_MACRO_F1 = 0.35
    MIN_ACCEPTED_ACCURACY = 0.60
    MIN_COVERAGE = 0.30
    MIN_TEST_SAMPLES = 6

    is_bootstrap = False
    input_schema = "native"

    def __init__(self, model_dir: Path):
        self.model_dir = Path(model_dir)
        self.model = TemporalTemplateModel(self.model_dir)
        self.loaded = False
        self.load_error: str | None = None
        self.quality_reason = "not evaluated"
        self.reload()

    def reload(self) -> bool:
        self.model.reload()
        self.loaded = False
        self.load_error = self.model.load_error
        if not self.model.loaded:
            self.quality_reason = self.model.load_error or "artifact unavailable"
            return False

        manifest_path = self.model_dir / "manifest.json"
        report_path = self.model_dir / "evaluation.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            report = json.loads(report_path.read_text(encoding="utf-8"))
            origin = str(manifest.get("training_origin", ""))
            labels = {str(x) for x in manifest.get("labels", [])}
            test = report.get("test") or {}
            top1 = float(test.get("top1_accuracy", 0.0))
            macro_f1 = float(test.get("macro_f1", 0.0))
            accepted = float(test.get("accepted_accuracy", 0.0))
            coverage = float(test.get("coverage", 0.0))
            samples = int(test.get("samples", 0))
        except Exception as exc:
            self.load_error = f"Core extension evaluation unreadable: {exc}"
            self.quality_reason = self.load_error
            return False

        problems: list[str] = []
        if origin != "public_core_extension":
            problems.append(f"unexpected origin {origin!r}")
        if not labels or not labels.issubset(CORE_EXTENSION_TARGETS):
            problems.append(f"unexpected labels {sorted(labels)}")
        if samples < self.MIN_TEST_SAMPLES:
            problems.append(f"test samples {samples} < {self.MIN_TEST_SAMPLES}")
        if top1 < self.MIN_TOP1:
            problems.append(f"top1 {top1:.2f} < {self.MIN_TOP1:.2f}")
        if macro_f1 < self.MIN_MACRO_F1:
            problems.append(f"macro F1 {macro_f1:.2f} < {self.MIN_MACRO_F1:.2f}")
        if accepted < self.MIN_ACCEPTED_ACCURACY:
            problems.append(
                f"accepted accuracy {accepted:.2f} < {self.MIN_ACCEPTED_ACCURACY:.2f}"
            )
        if coverage < self.MIN_COVERAGE:
            problems.append(f"coverage {coverage:.2f} < {self.MIN_COVERAGE:.2f}")

        if problems:
            self.load_error = "Core extension quality gate failed: " + "; ".join(problems)
            self.quality_reason = self.load_error
            return False

        self.loaded = True
        self.load_error = None
        self.quality_reason = (
            f"passed: top1={top1:.2f}, macroF1={macro_f1:.2f}, "
            f"accepted={accepted:.2f}, coverage={coverage:.2f}, n={samples}"
        )
        return True

    @property
    def labels(self) -> list[str]:
        return list(self.model.labels) if self.loaded else []

    @property
    def version(self):
        return self.model.version if self.loaded else None

    @property
    def backend(self) -> str:
        return f"core_extension:{self.model.backend}" if self.loaded else "core_extension:none"

    @property
    def source(self) -> str:
        return self.model.source if self.loaded else "SANKET public core extension"

    @property
    def schema_version(self):
        return self.model.schema_version

    @property
    def sequence_length(self) -> int:
        return self.model.sequence_length

    @property
    def accept_threshold(self) -> float:
        return self.model.accept_threshold

    @property
    def margin_threshold(self) -> float:
        return self.model.margin_threshold

    @property
    def motion_threshold(self) -> float:
        return self.model.motion_threshold

    @property
    def tracking_threshold(self) -> float:
        return self.model.tracking_threshold

    def predict(self, sequence):
        if not self.loaded:
            raise RuntimeError(self.load_error or "core extension is unavailable")
        return self.model.predict(sequence)
