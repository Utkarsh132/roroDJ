from dataclasses import dataclass, field
from threading import Lock

from app.schemas import CreativeProfile, CreativeRole


@dataclass
class Session:
    profile: CreativeProfile
    messages: list[dict[str, str]] = field(default_factory=list)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._lock = Lock()

    def get_or_create(self, session_id: str, role: CreativeRole) -> Session:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                session = Session(profile=CreativeProfile(role=role))
                self._sessions[session_id] = session
            session.profile.role = role
            return session

    def add_message(self, session_id: str, role: str, content: str) -> None:
        with self._lock:
            session = self._sessions[session_id]
            session.messages.append({"role": role, "content": content})
            session.messages = session.messages[-20:]

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def delete(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None


session_store = SessionStore()

