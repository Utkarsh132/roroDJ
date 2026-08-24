import re

from app.services.memory import Session


GENRES = {
    "afrobeats", "amapiano", "ambient", "classical", "country", "drill", "drum and bass",
    "dubstep", "edm", "folk", "funk", "hip hop", "house", "jazz", "metal", "pop", "r&b",
    "reggae", "rock", "soul", "techno", "trance", "trap",
}


def adapt_profile(session: Session, message: str) -> None:
    text = message.lower()
    found = [genre for genre in GENRES if genre in text]
    for genre in found:
        if genre not in session.profile.genres:
            session.profile.genres.append(genre)

    goal_patterns = {
        "write lyrics": r"\b(write|draft|create).{0,20}\b(lyrics?|verse|hook|chorus)\b",
        "make a beat": r"\b(make|create|build).{0,20}\b(beat|instrumental|groove)\b",
        "improve vocals": r"\b(vocal|sing|voice|mic|recording)\b",
        "mix or master": r"\b(mix|master|eq|compress|loudness)\b",
        "prepare a DJ set": r"\b(dj set|transition|mix tracks|setlist|cue point)\b",
    }
    for goal, pattern in goal_patterns.items():
        if re.search(pattern, text) and goal not in session.profile.goals:
            session.profile.goals.append(goal)

    bpm = re.search(r"\b(\d{2,3})\s*bpm\b", text)
    if bpm:
        session.profile.preferences["bpm"] = bpm.group(1)

    key = re.search(r"\b([a-g](?:#|b)?\s*(?:major|minor|min|maj))\b", text)
    if key:
        session.profile.preferences["key"] = key.group(1).title()

