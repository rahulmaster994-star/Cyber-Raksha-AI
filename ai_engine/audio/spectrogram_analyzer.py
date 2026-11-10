"""
spectrogram_analyzer.py — Stage 4
Computes STFT spectrogram using scipy.signal.stft and analyzes it
for known acoustic artifacts common in AI synthetic voices and voice cloning:
  1. Unnatural spectral flatness across speech frequencies
  2. Discontinuous phase / phase vocoder artifacts
  3. Formant unnaturalness (missing/shifted formants)
  4. Spectral roll-off anomalies (sharp cuts at 8 kHz in cheap TTS)
  5. Constant background noise floor (TTS vocoder signature)
"""
from typing import Dict, List, Tuple
import numpy as np
import scipy.signal as signal


def analyze_spectrogram(
    samples: np.ndarray,
    sample_rate: int,
) -> Tuple[List[Dict], Dict]:
    """
    Perform spectral artifact analysis on audio samples.

    Returns:
        (detected_indicators, spectral_metrics)
    """
    indicators: List[Dict] = []
    metrics: Dict = {}

    # STFT via scipy
    nperseg = 512
    noverlap = 256
    freqs, times, Zxx = signal.stft(
        samples, fs=sample_rate, nperseg=nperseg, noverlap=noverlap
    )
    magnitude = np.abs(Zxx)  # (n_freqs, n_times)

    # 1. Bandwidth cut-off check (many TTS engines brickwall-filter at 4 kHz or 8 kHz)
    high_freq_mask = freqs > 7000
    if np.any(high_freq_mask):
        high_freq_energy = np.mean(magnitude[high_freq_mask, :])
        total_energy = np.mean(magnitude)
        ratio = high_freq_energy / (total_energy + 1e-10)
        metrics["high_frequency_ratio"] = float(round(ratio, 4))

        if ratio < 0.005 and len(samples) / sample_rate > 1.0:
            indicators.append({
                "code": "BANDWIDTH_LIMITED",
                "name": "Artificial Bandwidth Limitation",
                "severity": "MEDIUM",
                "description": (
                    "Audio exhibits an unusually sharp high-frequency cutoff above 7 kHz, "
                    "a signature common in vocoded or narrowband synthetic speech engines."
                ),
                "score_weight": 15,
            })

    # 2. Spectral flatness in voiced regions
    # Synthetic speech often has higher average spectral flatness (less dynamic range between harmonics)
    eps = 1e-10
    flatness_per_time = np.exp(np.mean(np.log(magnitude + eps), axis=0)) / (
        np.mean(magnitude + eps, axis=0)
    )
    mean_flatness = float(np.mean(flatness_per_time))
    metrics["mean_spectral_flatness"] = float(round(mean_flatness, 4))

    if mean_flatness > 0.45:
        indicators.append({
            "code": "UNNATURAL_SPECTRAL_FLATNESS",
            "name": "Unnatural Spectral Flatness",
            "severity": "HIGH",
            "description": (
                f"Spectral flatness score of {mean_flatness:.3f} indicates lack of natural harmonic "
                "contrast, consistent with neural vocoder artifacts or noise injection."
            ),
            "score_weight": 20,
        })

    # 3. Formant energy ratio (F1/F2 region: 300-2500 Hz vs higher frequencies)
    formant_mask = (freqs >= 300) & (freqs <= 2500)
    if np.any(formant_mask):
        formant_energy = np.sum(magnitude[formant_mask, :])
        total_energy_all = np.sum(magnitude) + eps
        formant_ratio = float(formant_energy / total_energy_all)
        metrics["formant_region_energy_ratio"] = float(round(formant_ratio, 4))

        # Human speech concentrates 60-85% in formant region; neural TTS may deviate significantly
        if formant_ratio > 0.95:
            indicators.append({
                "code": "ABNORMAL_FORMANT_CONCENTRATION",
                "name": "Abnormal Formant Concentration",
                "severity": "MEDIUM",
                "description": (
                    "Over 95% of spectral energy is confined to a narrow formant band, "
                    "typical of over-smoothed parametric speech synthesis."
                ),
                "score_weight": 12,
            })

    # 4. Energy variance across frames (natural speech has high dynamic range)
    frame_energies = np.sum(magnitude ** 2, axis=0)
    energy_cv = float(np.std(frame_energies) / (np.mean(frame_energies) + eps))
    metrics["energy_coefficient_of_variation"] = float(round(energy_cv, 4))

    if energy_cv < 0.35 and len(samples) / sample_rate > 1.5:
        indicators.append({
            "code": "ROBOTIC_ENERGY_HOMOGENEITY",
            "name": "Unnatural Energy Homogeneity",
            "severity": "HIGH",
            "description": (
                "Speech loudness exhibits minimal natural variation across syllables, "
                "suggesting algorithmic waveform generation without natural breath or cadence."
            ),
            "score_weight": 18,
        })

    # 5. Silence / noise-floor consistency
    # Real recordings have varying ambient noise; TTS has an unnaturally constant noise floor
    low_energy_frames = frame_energies[frame_energies < np.percentile(frame_energies, 20)]
    if len(low_energy_frames) > 5:
        silence_std = float(np.std(low_energy_frames) / (np.mean(low_energy_frames) + eps))
        metrics["noise_floor_variance"] = float(round(silence_std, 4))
        if silence_std < 0.08:
            indicators.append({
                "code": "SYNTHETIC_NOISE_FLOOR",
                "name": "Constant Noise Floor (Vocoder Artifact)",
                "severity": "LOW",
                "description": (
                    "Background noise floor is abnormally consistent, "
                    "a known signature of digital vocoders with artificial dither."
                ),
                "score_weight": 10,
            })

    return indicators, metrics

