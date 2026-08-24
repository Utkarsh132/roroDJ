import math
import os
import tempfile
from pathlib import Path

import numpy as np

from app.schemas import AudioAnalysisResponse, AudioMetrics


NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _db(value: float) -> float:
    return round(20 * math.log10(max(value, 1e-9)), 2)


def analyze_audio_bytes(data: bytes, filename: str) -> AudioAnalysisResponse:
    try:
        import librosa
    except ImportError as exc:
        raise RuntimeError('Audio dependencies missing. Run: pip install -e ".[audio]"') from exc

    suffix = Path(filename).suffix or ".wav"
    temp_path = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
            handle.write(data)
            temp_path = handle.name

        signal, sample_rate = librosa.load(temp_path, sr=None, mono=True)
        if signal.size == 0:
            raise ValueError("The audio file contains no samples.")

        duration = float(librosa.get_duration(y=signal, sr=sample_rate))
        rms = float(np.sqrt(np.mean(np.square(signal))))
        peak = float(np.max(np.abs(signal)))
        clipping = float(np.mean(np.abs(signal) >= 0.999) * 100)
        silence = float(np.mean(np.abs(signal) < 10 ** (-60 / 20)) * 100)

        tempo, _ = librosa.beat.beat_track(y=signal, sr=sample_rate)
        bpm = float(np.asarray(tempo).reshape(-1)[0]) if np.size(tempo) else None

        chroma = librosa.feature.chroma_cqt(y=signal, sr=sample_rate)
        key_index = int(np.argmax(np.mean(chroma, axis=1))) if chroma.size else None
        key_estimate = NOTE_NAMES[key_index] if key_index is not None else None

        centroid = librosa.feature.spectral_centroid(y=signal, sr=sample_rate)
        centroid_hz = float(np.mean(centroid)) if centroid.size else None

        metrics = AudioMetrics(
            duration_seconds=round(duration, 2),
            sample_rate_hz=int(sample_rate),
            bpm=round(bpm, 1) if bpm and np.isfinite(bpm) else None,
            key_estimate=key_estimate,
            rms_dbfs=_db(rms),
            peak_dbfs=_db(peak),
            clipping_percent=round(clipping, 3),
            silence_percent=round(silence, 2),
            spectral_centroid_hz=round(centroid_hz, 1) if centroid_hz else None,
        )
        warnings, suggestions = assess_recording(metrics)
        return AudioAnalysisResponse(
            filename=filename,
            metrics=metrics,
            warnings=warnings,
            suggestions=suggestions,
        )
    finally:
        if temp_path:
            os.unlink(temp_path)


def assess_recording(metrics: AudioMetrics) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    suggestions: list[str] = []

    if metrics.clipping_percent > 0.1 or metrics.peak_dbfs > -0.3:
        warnings.append("Clipping or near-clipping detected.")
        suggestions.append("Lower the microphone or interface gain and target peaks around -12 to -6 dBFS.")
    if metrics.rms_dbfs < -35:
        warnings.append("The recording level is very low.")
        suggestions.append("Move closer to the microphone or raise clean preamp gain before recording.")
    if metrics.sample_rate_hz < 44100:
        warnings.append("Sample rate is below the usual music-production baseline.")
        suggestions.append("Record at 44.1 kHz or 48 kHz with 24-bit depth when your interface supports it.")
    if metrics.silence_percent > 35:
        warnings.append("A large portion of the file is effectively silent.")
        suggestions.append("Trim unused regions or check the selected microphone and input channel.")
    if metrics.spectral_centroid_hz and metrics.spectral_centroid_hz < 700:
        suggestions.append("The recording is dark; check mic angle, distance, room absorption, and low-pass filtering.")
    elif metrics.spectral_centroid_hz and metrics.spectral_centroid_hz > 5000:
        suggestions.append("The recording is very bright; check sibilance, mic axis, and reflective surfaces.")
    if not warnings:
        suggestions.append("Technical capture looks usable. Judge room tone, plosives, and tonal balance by ear.")
    suggestions.append("Microphone model alone does not determine quality; placement, room, gain, and performance matter.")
    return warnings, suggestions

