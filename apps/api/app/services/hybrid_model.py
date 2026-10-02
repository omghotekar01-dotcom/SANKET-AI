from __future__ import annotations

import json
from pathlib import Path

from .bootstrap_model import BootstrapKerasModel
from .temporal_model import TemporalTemplateModel


class HybridRecognitionModel:
    """Choose the strongest trustworthy recognizer available.

    Priority:
    1. A locally collected SANKET model only when its held-out report clears
       conservative minimum quality gates.
    2. The verified external 50-word BiLSTM bootstrap model.
    3. Any other readable SANKET temporal artifact as an emergency fallback.
    """

    MIN_LOCAL_TOP1 = 0.60
    MIN_LOCAL_ACCEPTED_ACCURACY = 0.70
    MIN_LOCAL_COVERAGE = 0.30
    MIN_LOCAL_TEST_SAMPLES = 3

    def __init__(self, local_dir: Path, bootstrap_dir: Path, enable_bootstrap: bool = True):
        self.local_dir = Path(local_dir)
        self.local = TemporalTemplateModel(local_dir)
        self.bootstrap = BootstrapKerasModel(bootstrap_dir) if enable_bootstrap else None
        self.active = None
        self.selection_reason = "not evaluated"
        self.reload()

    def _local_quality(self) -> tuple[bool, str]:
        manifest_path = self.local_dir / "manifest.json"
        evaluation_path = self.local_dir / "evaluation.json"
        if not manifest_path.exists() or not evaluation_path.exists():
            return False, "local model has no complete evaluation"

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            report = json.loads(evaluation_path.read_text(encoding="utf-8"))
            origin = str(manifest.get("training_origin", "unknown"))
            test = report.get("test") or {}
            top1 = float(test.get("top1_accuracy", 0.0))
            accepted = float(test.get("accepted_accuracy", 0.0))
            coverage = float(test.get("coverage", 0.0))
            samples = int(test.get("samples", 0))
        except Exception as exc:
            return False, f"local evaluation unreadable: {exc}"

        if origin != "local_consent_collection":
            return False, f"local artifact origin is {origin}, not team Training Studio data"
        if samples < self.MIN_LOCAL_TEST_SAMPLES:
            return False, f"local held-out set too small ({samples})"
        if top1 < self.MIN_LOCAL_TOP1:
            return False, f"local top-1 {top1:.2f} below {self.MIN_LOCAL_TOP1:.2f}"
        if accepted < self.MIN_LOCAL_ACCEPTED_ACCURACY:
            return False, (
                f"local accepted accuracy {accepted:.2f} below "
                f"{self.MIN_LOCAL_ACCEPTED_ACCURACY:.2f}"
            )
        if coverage < self.MIN_LOCAL_COVERAGE:
            return False, f"local coverage {coverage:.2f} below {self.MIN_LOCAL_COVERAGE:.2f}"

        return True, (
            f"local model passed gate: top1={top1:.2f}, "
            f"accepted={accepted:.2f}, coverage={coverage:.2f}, n={samples}"
        )

    def reload(self) -> bool:
        local_ok = self.local.reload()
        bootstrap_ok = False
        if self.bootstrap is not None:
            bootstrap_ok = self.bootstrap.reload()

        local_preferred = False
        local_reason = "local model unavailable"
        if local_ok:
            local_preferred, local_reason = self._local_quality()

        if local_ok and local_preferred:
            self.active = self.local
            self.selection_reason = local_reason
        elif bootstrap_ok and self.bootstrap is not None:
            self.active = self.bootstrap
            self.selection_reason = (
                "verified 50-word bootstrap selected; " + local_reason
                if local_ok else
                "verified 50-word bootstrap selected; no local model available"
            )
        elif local_ok:
            self.active = self.local
            self.selection_reason = (
                "bootstrap unavailable; using local artifact as fallback despite: "
                + local_reason
            )
        else:
            self.active = None
            self.selection_reason = "no usable recognizer available"

        return self.loaded

    @property
    def loaded(self) -> bool:
        return bool(self.active is not None and self.active.loaded)

    @property
    def is_bootstrap(self) -> bool:
        return bool(self.active is not None and getattr(self.active, "is_bootstrap", False))

    @property
    def backend(self) -> str:
        return getattr(self.active, "backend", "none") if self.active is not None else "none"

    @property
    def source(self) -> str:
        return getattr(self.active, "source", "SANKET local training") if self.active is not None else "none"

    @property
    def version(self):
        return self.active.version if self.active is not None else None

    @property
    def schema_version(self):
        return self.active.schema_version if self.active is not None else None

    @property
    def labels(self) -> list[str]:
        return list(self.active.labels) if self.active is not None else []

    @property
    def sequence_length(self) -> int:
        return int(self.active.sequence_length) if self.active is not None else 48

    @property
    def accept_threshold(self) -> float:
        return float(self.active.accept_threshold) if self.active is not None else 0.72

    @property
    def margin_threshold(self) -> float:
        return float(self.active.margin_threshold) if self.active is not None else 0.12

    @property
    def motion_threshold(self) -> float:
        return float(self.active.motion_threshold) if self.active is not None else 0.0015

    @property
    def tracking_threshold(self) -> float:
        return float(self.active.tracking_threshold) if self.active is not None else 0.48

    @property
    def load_error(self) -> str | None:
        if self.active is not None:
            return None
        errors = [self.local.load_error]
        if self.bootstrap is not None:
            errors.append(self.bootstrap.load_error)
        return " | ".join(e for e in errors if e) or "No recognition model available."

    @property
    def input_schema(self) -> str:
        return "bootstrap" if self.is_bootstrap else "native"

    def predict(self, sequence):
        if self.active is None:
            raise RuntimeError(self.load_error or "no recognition model")
        return self.active.predict(sequence)
