"""
audio_preprocessor.py — Stage 4
Loads, decodes, normalises and resamples WAV audio into a consistent
numpy float32 array suitable for feature extraction.

Requires: scipy, numpy (both available in venv).
pydub/ffmpeg are NOT required; only WAV is handled here.
"""
import io
import wave
import struct
from typing import Dict, Tuple

import numpy as np
import scipy.io.wavfile as wav
import scipy.signal as signal

TARGET_SAMPLE_RATE = 16000  # 16 kHz standard for speech analysis


class AudioPreprocessingError(Exception):
    """Raised when audio preprocessing fails."""


def load_and_preprocess(
    file_bytes: bytes,
) -> Tuple[np.ndarray, int, float, Dict]:
    """
    Load WAV bytes, convert to mono float32, resample to TARGET_SAMPLE_RATE.

    Returns:
        samples   : np.ndarray float32, shape (n_samples,), range [-1.0, 1.0]
        sample_rate: int — always TARGET_SAMPLE_RATE after resampling
        duration  : float — duration in seconds
        metadata  : dict  — original file metadata
    """
    buf = io.BytesIO(file_bytes)

    # Read WAV using scipy (handles 8/16/24/32-bit PCM and float)
    try:
        original_sr, samples_raw = wav.read(buf)
    except Exception as e:
        raise AudioPreprocessingError(f"Failed to read WAV data: {e}") from e

    # --- Convert to float32 in [-1.0, 1.0] ---
    samples = _to_float32(samples_raw)

    # --- Stereo → mono ---
    if samples.ndim == 2:
        samples = samples.mean(axis=1)

    n_channels_original = samples_raw.shape[1] if samples_raw.ndim == 2 else 1

    # --- Metadata (before resampling) ---
    original_duration = len(samples) / original_sr
    metadata: Dict = {
        "original_sample_rate": original_sr,
        "original_channels": n_channels_original,
        "original_n_samples": len(samples),
        "original_duration_seconds": round(original_duration, 4),
        "dtype": str(samples_raw.dtype),
        "target_sample_rate": TARGET_SAMPLE_RATE,
    }

    # --- Resample to 16 kHz if needed ---
    if original_sr != TARGET_SAMPLE_RATE:
        num_target_samples = int(len(samples) * TARGET_SAMPLE_RATE / original_sr)
        samples = signal.resample(samples, num_target_samples).astype(np.float32)

    # --- Normalise amplitude ---
    peak = np.max(np.abs(samples))
    if peak > 0:
        samples = samples / peak

    duration = len(samples) / TARGET_SAMPLE_RATE

    return samples, TARGET_SAMPLE_RATE, duration, metadata


def _to_float32(samples_raw: np.ndarray) -> np.ndarray:
    """Convert integer PCM or float PCM array to float32 in [-1, 1]."""
    dtype = samples_raw.dtype

    if dtype == np.float32 or dtype == np.float64:
        return samples_raw.astype(np.float32)
    elif dtype == np.int16:
        return samples_raw.astype(np.float32) / 32768.0
    elif dtype == np.int32:
        return samples_raw.astype(np.float32) / 2_147_483_648.0
    elif dtype == np.uint8:
        return (samples_raw.astype(np.float32) - 128.0) / 128.0
    else:
        # Fallback: attempt normalisation by max possible value
        info = np.iinfo(dtype) if np.issubdtype(dtype, np.integer) else None
        if info:
            return samples_raw.astype(np.float32) / max(abs(info.min), info.max)
        return samples_raw.astype(np.float32)


def get_audio_metadata_from_bytes(file_bytes: bytes, filename: str, file_size: int) -> Dict:
    """
    Extract lightweight metadata from WAV bytes for API response.
    Does NOT do full preprocessing.
    """
    buf = io.BytesIO(file_bytes)
    try:
        with wave.open(buf, "rb") as wf:
            sr = wf.getframerate()
            n_frames = wf.getnframes()
            channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            duration = n_frames / sr if sr > 0 else 0.0
        return {
            "filename": filename,
            "file_size_bytes": file_size,
            "duration_seconds": round(duration, 3),
            "sample_rate": sr,
            "channels": channels,
            "bit_depth": sampwidth * 8,
            "format": "WAV",
        }
    except Exception:
        return {
            "filename": filename,
            "file_size_bytes": file_size,
            "format": "WAV",
        }

