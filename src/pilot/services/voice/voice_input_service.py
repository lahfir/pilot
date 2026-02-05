"""
Voice input service using Deepgram streaming API with language detection.
"""

import os
import asyncio
import logging
from typing import Optional, Callable, Any
from deepgram import DeepgramClient
from deepgram.core.events import EventType
from .audio_capture import AudioCapture

logger = logging.getLogger(__name__)


class VoiceInputService:
    """
    Provides voice-to-text transcription using Deepgram streaming API.
    Supports automatic language detection and real-time transcription feedback.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Deepgram voice input service.

        Args:
            api_key: Deepgram API key (uses DEEPGRAM_API_KEY env var if not provided)
        """
        self.api_key = api_key or os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPGRAM_API_KEY not found in environment variables")

        self.client = DeepgramClient(api_key=self.api_key)
        self.audio_capture: Optional[AudioCapture] = None
        self.connection = None
        self.connection_manager = None
        self.transcription_result = ""
        self.detected_language = None
        self.is_listening = False
        self._interim_callback: Optional[Callable[[str], None]] = None
        self._error: Optional[Exception] = None

    async def start_transcription(
        self,
        interim_callback: Optional[Callable[[str], None]] = None,
        sample_rate: int = 16000,
        language: str = "multi",
    ) -> bool:
        """
        Start real-time voice transcription with multilingual support.
        Note: Language detection is NOT supported for streaming. Instead, use
        Nova-2/Nova-3 multilingual models with language='multi' for automatic
        multi-language transcription.

        Args:
            interim_callback: Optional callback for interim transcription results
            sample_rate: Audio sample rate in Hz
            language: Language code (e.g., 'en', 'es', 'fr', 'hi', 'ja') or 'multi'
                     for automatic multilingual support with Nova-2/3 models.
                     Default is 'multi'.

        Returns:
            True if started successfully, False otherwise
        """
        try:
            self._interim_callback = interim_callback
            self._error = None
            self.transcription_result = ""
            self.detected_language = language

            self.connection_manager = self.client.listen.v1.connect(
                model="nova-3",
                language=language,
                smart_format=True,
                interim_results=True,
                utterance_end_ms=1500,
                vad_events=True,
                encoding="linear16",
                channels=1,
                sample_rate=sample_rate,
            )

            self.audio_capture = AudioCapture(
                sample_rate=sample_rate, channels=1, dtype="int16"
            )

            if not self.audio_capture.start_recording():
                raise Exception("Failed to start audio recording")

            logger.info("Audio capture started, connecting to Deepgram...")

            self.connection = self.connection_manager.__enter__()

            self.connection.on(EventType.OPEN, self._on_open)
            self.connection.on(EventType.MESSAGE, self._on_message)
            self.connection.on(EventType.ERROR, self._on_error)
            self.connection.on(EventType.CLOSE, self._on_close)

            logger.info("🔌 Event handlers registered, starting connection...")

            self.is_listening = True

            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, self.connection.start_listening)

            logger.info("⏳ Waiting for connection to establish...")
            await asyncio.sleep(0.5)

            asyncio.create_task(self._stream_audio())

            logger.info("✅ Voice transcription started, audio streaming active")
            return True

        except Exception as e:
            logger.error(f"Failed to start transcription: {e}")
            self._error = e
            await self.stop_transcription()
            return False

    async def stop_transcription(self) -> str:
        """
        Stop transcription and return final result.

        Returns:
            Final transcription text
        """
        self.is_listening = False

        if self.audio_capture:
            self.audio_capture.stop_recording()
            self.audio_capture = None

        if self.connection_manager:
            try:
                self.connection_manager.__exit__(None, None, None)
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
            finally:
                self.connection = None
                self.connection_manager = None

        logger.info("Voice transcription stopped")
        return self.transcription_result

    async def _stream_audio(self) -> None:
        """
        Stream audio chunks from microphone to Deepgram.
        """
        try:
            chunk_count = 0
            while self.is_listening and self.audio_capture:
                audio_chunk = self.audio_capture.get_audio_chunk(timeout=0.1)

                if audio_chunk and self.connection:
                    self.connection.send_media(audio_chunk)
                    chunk_count += 1
                    if chunk_count % 50 == 0:
                        logger.debug(f"Sent {chunk_count} audio chunks to Deepgram")
                    await asyncio.sleep(0.01)

            logger.info(f"Audio streaming stopped. Sent {chunk_count} total chunks")

        except Exception as e:
            logger.error(f"Error streaming audio: {e}")
            self._error = e

    def _on_open(self, *args, **kwargs) -> None:
        """Handle connection open event."""
        logger.info(
            "🟢 Deepgram WebSocket connection OPENED - ready to receive transcripts"
        )

    def _on_message(self, result: Any, **kwargs) -> None:
        """
        Handle transcription message from Deepgram.

        For live streaming, Deepgram sends ListenV1ResultsEvent with:
        - result.channel.alternatives[0].transcript
        - result.is_final

        Args:
            result: Deepgram event (ListenV1ResultsEvent, ListenV1SpeechStartedEvent, etc.)
        """
        try:
            event_type = type(result).__name__

            if event_type != "ListenV1ResultsEvent":
                logger.debug(f"📨 Skipping non-transcript event: {event_type}")
                return

            if not hasattr(result, "channel"):
                logger.warning(f"⚠️  No channel in {event_type}")
                return

            channel = result.channel

            if not hasattr(channel, "alternatives") or not channel.alternatives:
                logger.warning("⚠️  No alternatives in channel")
                return

            alternative = channel.alternatives[0]
            sentence = alternative.transcript

            if not sentence or len(sentence) == 0:
                return

            is_final = getattr(result, "is_final", False)
            logger.debug(f"🎤 Transcript: '{sentence}' (final={is_final})")

            if is_final:
                self.transcription_result = sentence
                logger.info(f"✅ Final transcript: {sentence}")

            if self._interim_callback and sentence:
                self._interim_callback(sentence)

        except Exception as e:
            logger.error(f"❌ Error processing transcription: {e}", exc_info=True)

    def _on_error(self, error, **kwargs) -> None:
        """
        Handle error from Deepgram.

        Args:
            error: Error object
        """
        logger.error(f"Deepgram error: {error}", exc_info=True)
        self._error = Exception(str(error))

    def _on_close(self, *args, **kwargs) -> None:
        """Handle connection close event."""
        logger.info("🔴 Deepgram WebSocket connection CLOSED")

    def get_error(self) -> Optional[Exception]:
        """
        Get any error that occurred during transcription.

        Returns:
            Exception if error occurred, None otherwise
        """
        return self._error

    @staticmethod
    def check_api_key_configured() -> bool:
        """
        Check if Deepgram API key is configured.

        Returns:
            True if API key is available, False otherwise
        """
        return bool(os.getenv("DEEPGRAM_API_KEY"))
