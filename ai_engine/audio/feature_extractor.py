"""
feature_extractor.py — Stage 4
Extracts audio features using ONLY scipy + numpy (no librosa required).

Features extracted:
  - MFCCs (13 coefficients via manual mel filterbank + DCT)
  - Spectral centroid
  - Spectral bandwidth
  - Spectral rolloff (85%)
  - Zero-crossing rate
  - Spectral flatness
  - RMS energy
  - Pitch regularity (variance of autocorrelation peak lags)
  - Harmonic-to-noise ratio estimate
  - Short-time Fourier magnitude statistics (mean, std, max per frame)
"""
from typing import Dict, Tuple, List
import numpy as np
import scipy.signal as signal
import scipy.fft as fft_module

# STFT / frame parameters
FRAME_LENGTH = 512       # ~32 ms @ 16 kHz
HOP_LENGTH = 256         # 50% overlap
N_MFCC = 13
N_MELS = 40
F_MIN = 80.0             # Hz — lower mel filter edge
F_MAX = 7600.0           # Hz — upper mel filter edge (< Nyquist for 16 kHz)


def extract_features(
    samples: np.ndarray,
    sample_rate: int,
) -> Dict:
    """
    Extract all audio features from float32 mono samples.

    Returns a flat dict of scalar features plus arrays used by risk assessor.
    """
    frames = _frame_signal(samples, FRAME_LENGTH, HOP_LENGTH)

    # Windowed frames for spectral analysis
    window = np.hanning(FRAME_LENGTH)
    windowed = frames * window

    # Magnitude spectrum per frame  [n_frames, n_fft_bins]
    n_fft = FRAME_LENGTH
    magnitude = np.abs(fft_module.rfft(windowed, n=n_fft, axis=1))  # shape (n_frames, n_fft//2+1)
    freqs = np.fft.rfftfreq(n_fft, d=1.0 / sample_rate)             # shape (n_fft//2+1,)

    # --- Scalar features ---
    spectral_centroid_arr    = _spectral_centroid(magnitude, freqs)
    spectral_bandwidth_arr   = _spectral_bandwidth(magnitude, freqs, spectral_centroid_arr)
    spectral_rolloff_arr     = _spectral_rolloff(magnitude, freqs, roll_percent=0.85)
    zcr_arr                  = _zero_crossing_rate(frames)
    spectral_flatness_arr    = _spectral_flatness(magnitude)
    rms_arr                  = _rms_energy(frames)

    # MFCCs  [n_frames, N_MFCC]
    mfcc_matrix              = _mfcc(magnitude, sample_rate, N_MELS, N_MFCC)
    # Delta MFCCs
    delta_mfcc               = _delta(mfcc_matrix)

    # Pitch regularity using autocorrelation
    pitch_regularity, f0_arr = _pitch_regularity(samples, sample_rate)

    # Harmonic-to-noise ratio estimate
    hnr_estimate             = _hnr_estimate(samples, sample_rate)

    features: Dict = {
        # Spectral
        "spectral_centroid_mean":   float(np.mean(spectral_centroid_arr)),
        "spectral_centroid_std":    float(np.std(spectral_centroid_arr)),
        "spectral_bandwidth_mean":  float(np.mean(spectral_bandwidth_arr)),
        "spectral_bandwidth_std":   float(np.std(spectral_bandwidth_arr)),
        "spectral_rolloff_mean":    float(np.mean(spectral_rolloff_arr)),
        "spectral_rolloff_std":     float(np.std(spectral_rolloff_arr)),
        "spectral_flatness_mean":   float(np.mean(spectral_flatness_arr)),
        "spectral_flatness_std":    float(np.std(spectral_flatness_arr)),

        # Temporal
        "zcr_mean":                 float(np.mean(zcr_arr)),
        "zcr_std":                  float(np.std(zcr_arr)),
        "rms_mean":                 float(np.mean(rms_arr)),
        "rms_std":                  float(np.std(rms_arr)),

        # Pitch
        "pitch_regularity":         float(pitch_regularity),
        "f0_mean":                  float(np.mean(f0_arr)) if len(f0_arr) else 0.0,
        "f0_std":                   float(np.std(f0_arr)) if len(f0_arr) else 0.0,

        # Harmonics
        "hnr_estimate":             float(hnr_estimate),

        # MFCC means and stds (13 coefficients)
        **{f"mfcc_{i}_mean": float(np.mean(mfcc_matrix[:, i])) for i in range(N_MFCC)},
        **{f"mfcc_{i}_std":  float(np.std(mfcc_matrix[:, i]))  for i in range(N_MFCC)},

        # Delta MFCC means and stds
        **{f"delta_mfcc_{i}_mean": float(np.mean(delta_mfcc[:, i])) for i in range(N_MFCC)},
        **{f"delta_mfcc_{i}_std":  float(np.std(delta_mfcc[:, i]))  for i in range(N_MFCC)},
    }

    return features


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _frame_signal(samples: np.ndarray, frame_length: int, hop_length: int) -> np.ndarray:
    """Split signal into overlapping frames. Returns (n_frames, frame_length)."""
    n_frames = max(1, (len(samples) - frame_length) // hop_length + 1)
    frames = np.zeros((n_frames, frame_length), dtype=np.float32)
    for i in range(n_frames):
        start = i * hop_length
        end = start + frame_length
        chunk = samples[start:min(end, len(samples))]
        frames[i, :len(chunk)] = chunk
    return frames


def _spectral_centroid(magnitude: np.ndarray, freqs: np.ndarray) -> np.ndarray:
    mag_sum = np.sum(magnitude, axis=1, keepdims=True)
    mag_sum = np.where(mag_sum == 0, 1e-10, mag_sum)
    return np.sum(freqs * magnitude, axis=1) / mag_sum.squeeze()


def _spectral_bandwidth(
    magnitude: np.ndarray, freqs: np.ndarray, centroid: np.ndarray
) -> np.ndarray:
    mag_sum = np.sum(magnitude, axis=1, keepdims=True)
    mag_sum = np.where(mag_sum == 0, 1e-10, mag_sum)
    deviation = (freqs - centroid[:, np.newaxis]) ** 2
    return np.sqrt(np.sum(deviation * magnitude, axis=1) / mag_sum.squeeze())


def _spectral_rolloff(
    magnitude: np.ndarray, freqs: np.ndarray, roll_percent: float = 0.85
) -> np.ndarray:
    cumulative = np.cumsum(magnitude, axis=1)
    total = cumulative[:, -1:].copy()
    total = np.where(total == 0, 1e-10, total)
    threshold = roll_percent * total
    rolloff = np.zeros(len(magnitude))
    for i, (cum, thr) in enumerate(zip(cumulative, threshold)):
        idx = np.searchsorted(cum, thr[0])
        rolloff[i] = freqs[min(idx, len(freqs) - 1)]
    return rolloff


def _zero_crossing_rate(frames: np.ndarray) -> np.ndarray:
    signs = np.sign(frames)
    crossings = np.sum(np.abs(np.diff(signs, axis=1)), axis=1)
    return crossings / (2 * (frames.shape[1] - 1))


def _spectral_flatness(magnitude: np.ndarray) -> np.ndarray:
    eps = 1e-10
    geo_mean = np.exp(np.mean(np.log(magnitude + eps), axis=1))
    arith_mean = np.mean(magnitude + eps, axis=1)
    return geo_mean / arith_mean


def _rms_energy(frames: np.ndarray) -> np.ndarray:
    return np.sqrt(np.mean(frames ** 2, axis=1))


def _hz_to_mel(hz: float) -> float:
    return 2595.0 * np.log10(1.0 + hz / 700.0)


def _mel_to_hz(mel: float) -> float:
    return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)


def _mel_filterbank(n_mels: int, n_fft: int, sample_rate: int) -> np.ndarray:
    """Triangular mel filterbank. Returns (n_mels, n_fft//2+1)."""
    low_mel = _hz_to_mel(F_MIN)
    high_mel = _hz_to_mel(min(F_MAX, sample_rate / 2))
    mel_points = np.linspace(low_mel, high_mel, n_mels + 2)
    hz_points = np.array([_mel_to_hz(m) for m in mel_points])
    bin_points = np.floor((n_fft + 1) * hz_points / sample_rate).astype(int)

    n_bins = n_fft // 2 + 1
    filterbank = np.zeros((n_mels, n_bins))
    for m in range(1, n_mels + 1):
        f_left = bin_points[m - 1]
        f_center = bin_points[m]
        f_right = bin_points[m + 1]
        for k in range(f_left, f_center):
            if f_center != f_left:
                filterbank[m - 1, k] = (k - f_left) / (f_center - f_left)
        for k in range(f_center, f_right):
            if f_right != f_center:
                filterbank[m - 1, k] = (f_right - k) / (f_right - f_center)
    return filterbank


def _mfcc(
    magnitude: np.ndarray,
    sample_rate: int,
    n_mels: int,
    n_mfcc: int,
) -> np.ndarray:
    """
    Compute MFCCs via manual mel filterbank + log + DCT.
    Returns (n_frames, n_mfcc).
    """
    n_fft = (magnitude.shape[1] - 1) * 2
    filterbank = _mel_filterbank(n_mels, n_fft, sample_rate)

    # Power spectrum
    power = magnitude ** 2

    # Apply mel filterbank
    mel_energy = power @ filterbank.T  # (n_frames, n_mels)
    log_mel = np.log(mel_energy + 1e-10)

    # DCT-II  (scipy.fft.dct)
    from scipy.fft import dct
    mfcc_all = dct(log_mel, type=2, axis=1, norm="ortho")
    return mfcc_all[:, :n_mfcc].astype(np.float32)


def _delta(mfcc: np.ndarray, width: int = 9) -> np.ndarray:
    """Compute first-order delta (temporal derivative) of MFCC matrix."""
    n_frames, n_coef = mfcc.shape
    half = width // 2
    padded = np.pad(mfcc, ((half, half), (0, 0)), mode="edge")
    weights = np.arange(-half, half + 1, dtype=np.float32)
    denom = 2 * np.sum(weights ** 2)
    if denom == 0:
        denom = 1.0
    delta = np.zeros_like(mfcc)
    for t in range(n_frames):
        delta[t] = np.sum(weights[:, np.newaxis] * padded[t:t + width], axis=0)
    return delta / denom


def _pitch_regularity(
    samples: np.ndarray,
    sample_rate: int,
    min_f0: float = 60.0,
    max_f0: float = 400.0,
) -> Tuple[float, np.ndarray]:
    """
    Estimate pitch regularity using autocorrelation on short frames.
    Returns (pitch_regularity_score, f0_per_frame_array).
    Lower regularity variance → more machine-like; natural speech has
    higher pitch variance.
    """
    frame_ms = 30
    hop_ms = 10
    frame_len = int(sample_rate * frame_ms / 1000)
    hop_len = int(sample_rate * hop_ms / 1000)

    min_lag = int(sample_rate / max_f0)
    max_lag = int(sample_rate / min_f0)

    if min_lag >= max_lag or frame_len < max_lag:
        return 0.0, np.array([])

    f0_list = []
    n_frames = (len(samples) - frame_len) // hop_len + 1
    for i in range(min(n_frames, 200)):  # cap at 200 frames for speed
        start = i * hop_len
        frame = samples[start:start + frame_len].astype(np.float64)

        # Autocorrelation via FFT
        n = len(frame)
        f_fft = fft_module.rfft(frame, n=2 * n)
        acf = fft_module.irfft(np.abs(f_fft) ** 2)[:n]

        # Find peak in valid lag range
        segment = acf[min_lag:max_lag]
        if len(segment) == 0:
            continue
        peak_lag = np.argmax(segment) + min_lag
        if acf[0] > 0:
            confidence = acf[peak_lag] / acf[0]
            if confidence > 0.3:  # voiced threshold
                f0 = sample_rate / peak_lag
                f0_list.append(f0)

    if len(f0_list) < 3:
        return 0.0, np.array(f0_list)

    f0_arr = np.array(f0_list)
    # Coefficient of variation — lower = more regular = more machine-like
    cv = float(np.std(f0_arr) / (np.mean(f0_arr) + 1e-10))
    return cv, f0_arr


def _hnr_estimate(samples: np.ndarray, sample_rate: int) -> float:
    """
    Harmonic-to-noise ratio estimate using cepstral analysis.
    Higher HNR → more harmonic (natural voice); lower → noisier or synthetic flat spectrum.
    Returns dB estimate in [0, 40].
    """
    n = min(len(samples), 4096)
    frame = samples[:n]
    if np.max(np.abs(frame)) < 1e-6:
        return 0.0
    power_spectrum = np.abs(fft_module.rfft(frame)) ** 2
    log_power = np.log(power_spectrum + 1e-10)
    cepstrum = np.abs(fft_module.irfft(log_power))

    min_lag = max(1, int(sample_rate / 400))
    max_lag = min(len(cepstrum) - 1, int(sample_rate / 60))

    if min_lag >= max_lag:
        return 0.0

    peak_power = np.max(cepstrum[min_lag:max_lag])
    noise_floor = np.mean(cepstrum[max_lag:])

    if noise_floor < 1e-10:
        return 40.0  # very high HNR — clamp

    hnr_db = 10.0 * np.log10(peak_power / noise_floor)
    return float(np.clip(hnr_db, 0.0, 40.0))

