from __future__ import annotations

from enum import StrEnum
from typing import Any
from pydantic import BaseModel, Field


class RecognitionState(StrEnum):
    ACCEPTED = "ACCEPTED"
    NEED_REPEAT = "NEED_REPEAT"
    NO_SIGN = "NO_SIGN"
    TRACKING_LOST = "TRACKING_LOST"
    UNSUPPORTED = "UNSUPPORTED"


class TrackingInfo(BaseModel):
    left_hand: bool = False
    right_hand: bool = False
    pose: bool = False
    face: bool = False
    quality: float = Field(0.0, ge=0.0, le=1.0)


class Alternative(BaseModel):
    label: str
    confidence: float = Field(ge=0.0, le=1.0)


class PredictionEvent(BaseModel):
    type: str = "prediction"
    state: RecognitionState
    label: str | None = None
    display_text: str | None = None
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    alternatives: list[Alternative] = []
    tracking: TrackingInfo
    domain: str = "general"
    reason: str | None = None
    latency_ms: float | None = None
    model_version: str | None = None
    feature_schema: str = "holistic-v1"
    demo: bool = False


class TextToISLRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)


class ISLClipItem(BaseModel):
    phrase: str
    mode: str
    file: str | None = None
    source: str | None = None
    license_note: str | None = None


class TextToISLResponse(BaseModel):
    normalized_text: str
    mode: str
    items: list[ISLClipItem]
    message: str | None = None


class FeedbackRequest(BaseModel):
    utterance_id: str | None = None
    raw_label: str | None = None
    accepted: bool
    corrected_label: str | None = None
    note: str | None = Field(default=None, max_length=1000)


class CollectorStartRequest(BaseModel):
    label: str = Field(pattern=r"^[a-z0-9_-]{1,64}$")
    signer_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    consent: bool
    environment_tag: str | None = Field(default=None, max_length=100)
    save_raw_video: bool = False


class CollectorStopRequest(BaseModel):
    collector_id: str


class SignalingEnvelope(BaseModel):
    type: str
    payload: dict[str, Any] = {}
