from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.schemas import AudioAnalysisResponse, ChatRequest, ChatResponse
from app.services.audio import analyze_audio_bytes
from app.services.chat import get_provider
from app.services.memory import session_store
from app.services.profile import adapt_profile
from app.services.roles import ROLE_ACTIONS

settings = get_settings()
app = FastAPI(title="roroDJ API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "provider": settings.model_provider, "model": settings.model_name}


@app.get("/api/v1/capabilities")
async def capabilities() -> dict:
    return {
        "roles": ["dj", "singer", "producer", "musician", "general"],
        "available": ["adaptive_chat", "audio_analysis", "microphone_guidance", "browser_equalizer"],
        "planned": ["transcription", "stem_separation", "music_embeddings", "beat_generation", "audio_generation"],
    }


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    session = session_store.get_or_create(request.session_id, request.role)
    adapt_profile(session, request.message)
    session_store.add_message(request.session_id, "user", request.message)
    provider = get_provider(settings)
    try:
        reply = await provider.complete(session, request.message)
    except Exception as exc:
        if settings.model_provider != "fallback":
            raise HTTPException(status_code=422, detail=f"Model provider failed: {exc}") from exc
        raise
    session_store.add_message(request.session_id, "assistant", reply)
    return ChatResponse(
        session_id=request.session_id,
        reply=reply,
        role=request.role,
        profile=session.profile,
        provider=provider.name,
        suggested_actions=ROLE_ACTIONS[request.role],
    )


@app.get("/api/v1/sessions/{session_id}")
async def get_session(session_id: str) -> dict:
    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"profile": session.profile, "messages": session.messages}


@app.delete("/api/v1/sessions/{session_id}")
async def delete_session(session_id: str) -> dict[str, bool]:
    return {"deleted": session_store.delete(session_id)}


@app.post("/api/v1/audio/analyze", response_model=AudioAnalysisResponse)
async def analyze_audio(file: UploadFile = File(...)) -> AudioAnalysisResponse:
    if not file.content_type or not (
        file.content_type.startswith("audio/") or file.filename.lower().endswith((".wav", ".mp3", ".flac", ".m4a", ".ogg"))
    ):
        raise HTTPException(status_code=400, detail="Upload a WAV, MP3, FLAC, M4A, or OGG audio file.")
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_mb} MB.")
    try:
        return analyze_audio_bytes(data, file.filename or "audio")
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

