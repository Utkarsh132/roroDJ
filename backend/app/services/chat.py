from abc import ABC, abstractmethod

import httpx

from app.config import Settings
from app.schemas import CreativeRole
from app.services.memory import Session
from app.services.roles import ROLE_PROMPTS


class ChatProvider(ABC):
    name: str

    @abstractmethod
    async def complete(self, session: Session, message: str) -> str:
        raise NotImplementedError


class OllamaProvider(ChatProvider):
    name = "ollama"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def complete(self, session: Session, message: str) -> str:
        system = build_system_prompt(session)
        messages = [{"role": "system", "content": system}, *session.messages[-12:]]
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.settings.ollama_url.rstrip('/')}/api/chat",
                json={
                    "model": self.settings.model_name,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": 0.75},
                },
            )
            response.raise_for_status()
            return response.json()["message"]["content"].strip()


class FallbackProvider(ChatProvider):
    name = "fallback"

    async def complete(self, session: Session, message: str) -> str:
        role = session.profile.role
        genres = ", ".join(session.profile.genres) or "your chosen genre"
        bpm = session.profile.preferences.get("bpm", "a tempo that fits the reference")
        lower = message.lower()

        if any(word in lower for word in ("lyric", "verse", "hook", "chorus")):
            return (
                f"Let’s shape this for {genres}. Start with a one-line emotional thesis, then write a "
                "4-line hook where lines 1 and 3 share an image and lines 2 and 4 land the title. "
                "Keep stressed syllables on strong beats. Send me the theme, point of view, and one phrase "
                "you want preserved, and I’ll draft a version without copying an existing song."
            )
        if role == CreativeRole.DJ:
            return (
                f"Build around {bpm} BPM. Mark 16- or 32-bar phrase boundaries, introduce the incoming "
                "track with lows cut, swap basslines at a phrase boundary, then release the outgoing track "
                "over 8 bars. Upload both tracks and I can compare tempo, tonal center, loudness, and likely "
                "transition pressure points."
            )
        if role == CreativeRole.SINGER:
            return (
                "Record one dry take 15–20 cm from the microphone with peaks near -12 dBFS. Then make three "
                "passes: lead, tight double, and a quieter harmony. Tell me your comfortable lowest and "
                "highest notes plus the song key, and I’ll propose a melody and harmony map."
            )
        if role == CreativeRole.PRODUCER:
            return (
                f"Use an 8-bar constraint at {bpm} BPM: drums and bass first, one harmonic anchor, then one "
                "contrast element. Duplicate it into intro, A, lift, and drop sections before adding sounds. "
                "Upload the bounce so I can check tempo, key estimate, headroom, brightness, clipping, and silence."
            )
        if role == CreativeRole.MUSICIAN:
            return (
                "Turn the idea into a motif of 3–5 notes, repeat it once, then change only the ending. Test it "
                "over tonic, predominant, and dominant harmony. Tell me your instrument, level, and key for "
                "specific voicings or tablature-style note names."
            )
        return (
            "I can help turn that into a concrete music task. Choose DJ, singer, producer, or musician mode, "
            "then give me a reference mood, target genre, and desired outcome. You can also upload audio for "
            "tempo, key, loudness, clipping, silence, and microphone-quality analysis."
        )


def build_system_prompt(session: Session) -> str:
    profile = session.profile
    context = (
        f"Known genres: {', '.join(profile.genres) or 'unknown'}. "
        f"Known goals: {', '.join(profile.goals) or 'unknown'}. "
        f"Preferences: {profile.preferences or 'none'}."
    )
    return (
        f"{ROLE_PROMPTS[profile.role]}\n{context}\n"
        "Never claim to hear audio that has not been analyzed. Avoid imitating living artists exactly; "
        "translate references into musical attributes. Give prioritized, testable steps. Keep answers concise "
        "unless the user asks for depth."
    )


def get_provider(settings: Settings) -> ChatProvider:
    if settings.model_provider.lower() == "ollama":
        return OllamaProvider(settings)
    return FallbackProvider()

