"""
Cross-platform audio capture service for voice input.
"""

import sounddevice as sd
import numpy as np
import queue
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class AudioCapture:
    """
    Handles real-time microphone audio capture with cross-platform support.
    Streams audio chunks for processing by voice recognition services.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        dtype: str = "int16",
        chunk_size: int = 1024,
    ):
        """
        Initialize audio capture configuration.

        Args:
            sample_rate: Audio sample rate in Hz (default 16kHz for speech)
            channels: Number of audio channels (1=mono, 2=stereo)
            dtype: Audio data type (int16 for PCM)
            chunk_size: Number of frames per buffer
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = dtype
        self.chunk_size = chunk_size
        self.audio_queue: queue.Queue = queue.Queue()
        self.stream: Optional[sd.InputStream] = None
        self.is_recording = False
        self._error: Optional[Exception] = None

    def _audio_callback(
        self, indata: np.ndarray, frames: int, time_info, status
    ) -> None:
        """
        Callback function called by sounddevice for each audio chunk.

        Args:
            indata: Audio data as numpy array
            frames: Number of frames
            time_info: Time information
            status: Stream status flags
        """
        if status:
            logger.warning(f"Audio callback status: {status}")

        if self.is_recording:
            self.audio_queue.put(indata.copy())

    def start_recording(self) -> bool:
        """
        Start capturing audio from the default microphone.

        Returns:
            True if recording started successfully, False otherwise
        """
        try:
            self.is_recording = True
            self._error = None

            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=self.dtype,
                blocksize=self.chunk_size,
                callback=self._audio_callback,
            )
            self.stream.start()
            logger.info(
                f"Audio recording started: {self.sample_rate}Hz, {self.channels}ch"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to start audio recording: {e}")
            self._error = e
            self.is_recording = False
            return False

    def stop_recording(self) -> None:
        """
        Stop capturing audio and cleanup resources.
        """
        self.is_recording = False

        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
                logger.info("Audio recording stopped")
            except Exception as e:
                logger.error(f"Error stopping audio stream: {e}")
            finally:
                self.stream = None

        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

    def get_audio_chunk(self, timeout: float = 1.0) -> Optional[bytes]:
        """
        Get next audio chunk from the queue.

        Args:
            timeout: Maximum time to wait for audio data in seconds

        Returns:
            Audio data as bytes, or None if timeout or error
        """
        try:
            audio_data = self.audio_queue.get(timeout=timeout)
            return audio_data.tobytes()
        except queue.Empty:
            return None

    def get_error(self) -> Optional[Exception]:
        """
        Get any error that occurred during recording.

        Returns:
            Exception if error occurred, None otherwise
        """
        return self._error

    @staticmethod
    def check_microphone_available() -> bool:
        """
        Check if microphone is available on the system.

        Returns:
            True if microphone is available, False otherwise
        """
        try:
            devices = sd.query_devices()
            for device in devices:
                if device["max_input_channels"] > 0:
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking microphone availability: {e}")
            return False

    @staticmethod
    def get_default_input_device() -> Optional[dict]:
        """
        Get information about the default input device.

        Returns:
            Device info dictionary or None if not available
        """
        try:
            return sd.query_devices(kind="input")
        except Exception as e:
            logger.error(f"Error querying default input device: {e}")
            return None

    def __enter__(self):
        """Context manager entry."""
        self.start_recording()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_recording()
