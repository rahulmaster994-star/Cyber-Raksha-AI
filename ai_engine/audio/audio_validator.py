"""
audio_validator.py — Stage 4
Validates uploaded audio files before processing.
Checks extension, size, and WAV header integrity.
"""
import io
import struct
import wave
from pathlib import Path
from typing import Tuple

# Supported formats (WAV only without pydub/ffmpeg)
SUPPORTED_EXTENSIONS = {".wav"}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
MIN_DURATION_SECONDS = 0.5
MAX_DURATION_SECONDS = 300.0


class AudioValidationError(Exception):
    """Raised when audio file fails validation."""
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(message)
        self.error_code = error_code


def validate_audio_file(
    file_bytes: bytes,
    filename: str,
) -> Tuple[str, int]:
    """
    Validate audio file bytes.

    Returns:
        (extension, file_size_bytes) on success.

    Raises:
        AudioValidationError on failure.
    """
    if not file_bytes:
        raise AudioValidationError("Uploaded file is empty.", "EMPTY_FILE")

    file_size = len(file_bytes)
    if file_size > MAX_FILE_SIZE_BYTES:
        raise AudioValidationError(
            f"File size {file_size / (1024*1024):.1f} MB exceeds the 25 MB limit.",
            "FILE_TOO_LARGE",
        )

    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise AudioValidationError(
            f"Unsupported format '{ext}'. Only WAV files are supported. "
            "MP3/FLAC support requires optional dependencies (pydub + ffmpeg) "
            "which are not currently installed.",
            "UNSUPPORTED_FORMAT",
        )

    # Validate WAV header
    _validate_wav_header(file_bytes)

    return ext, file_size


def _validate_wav_header(file_bytes: bytes) -> None:
    """Check RIFF/WAVE magic bytes and confirm wave module can open it."""
    if len(file_bytes) < 12:
        raise AudioValidationError(
            "File is too small to be a valid WAV file.", "CORRUPT_HEADER"
        )

    # Check RIFF and WAVE signatures
    if file_bytes[:4] != b"RIFF":
        raise AudioValidationError(
            "File does not have a valid WAV (RIFF) header.", "CORRUPT_HEADER"
        )
    if file_bytes[8:12] != b"WAVE":
        raise AudioValidationError(
            "File RIFF header does not identify as WAVE format.", "CORRUPT_HEADER"
        )

    # Try opening with wave module to catch deeper format errors
    try:
        buf = io.BytesIO(file_bytes)
        with wave.open(buf, "rb") as wf:
            n_frames = wf.getnframes()
            framerate = wf.getframerate()
            if framerate <= 0:
                raise AudioValidationError(
                    "Invalid sample rate in WAV header.", "CORRUPT_HEADER"
                )
            duration = n_frames / framerate
            if duration < MIN_DURATION_SECONDS:
                raise AudioValidationError(
                    f"Audio duration {duration:.2f}s is below the minimum "
                    f"{MIN_DURATION_SECONDS}s required for analysis.",
                    "TOO_SHORT",
                )
            if duration > MAX_DURATION_SECONDS:
                raise AudioValidationError(
                    f"Audio duration {duration:.1f}s exceeds the maximum "
                    f"{MAX_DURATION_SECONDS}s allowed.",
                    "TOO_LONG",
                )
    except AudioValidationError:
        raise
    except Exception as e:
        raise AudioValidationError(
            f"Could not parse WAV file: {e}", "CORRUPT_FILE"
        ) from e

