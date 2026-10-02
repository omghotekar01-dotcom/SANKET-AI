from __future__ import annotations

from pathlib import Path

from .bootstrap_model import BootstrapKerasModel
from .temporal_model import TemporalTemplateModel


class HybridRecognitionModel:
    """Prefer a locally trained SANKET model; fall back to verified bootstrap weights."""

    def __init__(self, local_dir: Path, bootstrap_dir: Path, enable_bootstrap: bool = True):
        self.local = TemporalTemplateModel(local_dir)
        self.bootstrap = BootstrapKerasModel(bootstrap_dir) if enable_bootstrap else None
        self.active = None
        self.reload()

    def reload(self) -> bool:
        local_ok = self.local.reload()
        bootstrap_ok = False
        if self.bootstrap is not None:
            bootstrap_ok = self.bootstrap.reload()

        if local_ok:
            self.active = self.local
        elif bootstrap_ok and self.bootstrap is not None:
            self.active = self.bootstrap
        else:
            self.active = None
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
