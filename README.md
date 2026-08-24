# roroDJ

roroDJ is a role-aware music copilot for DJs, singers, producers, and musicians. This starter is a runnable foundation, not a pretend fully trained foundation model.

## What works now

- Adaptive chat with DJ, singer, producer, musician, and general modes
- Per-session creative profile and conversation memory
- Optional Ollama LLM integration with an offline fallback coach
- Audio upload analysis: duration, sample rate, BPM, chroma-based key estimate, RMS, peak, clipping, silence, spectral centroid, and microphone warnings
- Browser studio with a live 8-band Web Audio equalizer
- Lyrics and creative-direction prompts through the same role-aware orchestration layer
- Health, capabilities, chat, session, and audio-analysis APIs

## Architecture

```text
frontend (React + Vite)
        |
        v
FastAPI orchestration API
  |-- role router and adaptive profile
  |-- conversation memory
  |-- audio/MIR analyzer
  |-- fallback coach
  `-- Ollama model adapter
```

Production music generation, source separation, transcription, embeddings, and a vector database belong behind new adapters. Do not train a single giant model from scratch.

## Quick start

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,audio]"
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Connect a real local language model

Install Ollama, pull a model, and change the provider:

```bash
ollama pull qwen3:8b
export RORODJ_MODEL_PROVIDER=ollama
export RORODJ_MODEL_NAME=qwen3:8b
uvicorn app.main:app --reload --port 8000
```

For a larger machine, replace `qwen3:8b` with a stronger instruction model supported by Ollama.

## Docker

```bash
docker compose up --build
```

The frontend runs at `http://localhost:5173` and the API at `http://localhost:8000`.

## API

- `GET /health`
- `GET /api/v1/capabilities`
- `POST /api/v1/chat`
- `GET /api/v1/sessions/{session_id}`
- `DELETE /api/v1/sessions/{session_id}`
- `POST /api/v1/audio/analyze`

Interactive API docs are at `http://localhost:8000/docs`.

## Next model adapters

Implement these as isolated services rather than mixing them into chat:

1. Speech-to-text service
2. Stem separation service
3. Music/audio embedding and retrieval service
4. MIDI/beat generation service
5. Full audio generation service
6. Rights-cleared dataset ingestion and evaluation pipeline
7. PostgreSQL/pgvector session and knowledge storage
8. GPU worker queue

