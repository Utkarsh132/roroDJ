from enum import StrEnum

from pydantic import BaseModel, Field


class CreativeRole(StrEnum):
    DJ = "dj"
    SINGER = "singer"
    PRODUCER = "producer"
    MUSICIAN = "musician"
    GENERAL = "general"


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=3, max_length=100)
    message: str = Field(min_length=1, max_length=8000)
    role: CreativeRole = CreativeRole.GENERAL


class CreativeProfile(BaseModel):
    role: CreativeRole
    genres: list[str] = []
    goals: list[str] = []
    preferences: dict[str, str] = {}


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    role: CreativeRole
    profile: CreativeProfile
    provider: str
    suggested_actions: list[str]


class AudioMetrics(BaseModel):
    duration_seconds: float
    sample_rate_hz: int
    bpm: float | None
    key_estimate: str | None
    rms_dbfs: float
    peak_dbfs: float
    clipping_percent: float
    silence_percent: float
    spectral_centroid_hz: float | None


class AudioAnalysisResponse(BaseModel):
    filename: str
    metrics: AudioMetrics
    warnings: list[str]
    suggestions: list[str]

