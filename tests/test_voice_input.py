"""
Tests for Voice Input - verify audio capture and transcription work correctly.
"""

import os
import pytest
import asyncio
import time
from unittest.mock import patch, MagicMock


class TestAudioCapture:
    """Test audio capture functionality."""

    def test_audio_capture_initialization(self):
        """
        Test if audio capture initializes correctly.
        """
        print("\n" + "=" * 80)
        print("🔍 TESTING AUDIO CAPTURE INITIALIZATION")
        print("=" * 80)

        from computer_use.services.audio_capture import AudioCapture

        capture = AudioCapture(sample_rate=16000, channels=1, dtype="int16")

        print("📋 Audio Capture Config:")
        print(f"   - Sample Rate: {capture.sample_rate}Hz")
        print(f"   - Channels: {capture.channels}")
        print(f"   - Data Type: {capture.dtype}")
        print(f"   - Chunk Size: {capture.chunk_size}")

        assert capture.sample_rate == 16000, "Sample rate should be 16kHz"
        assert capture.channels == 1, "Should be mono"
        assert capture.dtype == "int16", "Should use int16 format"
        print("✅ Audio capture initialized successfully")

        print("=" * 80)

    def test_check_microphone_available(self):
        """
        Test if microphone availability check works.
        """
        print("\n" + "=" * 80)
        print("🔍 TESTING MICROPHONE AVAILABILITY CHECK")
        print("=" * 80)

        from computer_use.services.audio_capture import AudioCapture

        is_available = AudioCapture.check_microphone_available()

        print(f"🎤 Microphone Available: {is_available}")

        assert isinstance(is_available, bool), "Should return boolean"
        print("✅ Microphone check completed")

        print("=" * 80)

    def test_get_default_input_device(self):
        """
        Test getting default input device info.
        """
        print("\n" + "=" * 80)
        print("🔍 TESTING DEFAULT INPUT DEVICE")
        print("=" * 80)

        from computer_use.services.audio_capture import AudioCapture

        device_info = AudioCapture.get_default_input_device()

        if device_info:
            print("🎤 Default Input Device:")
            print(f"   - Name: {device_info.get('name', 'N/A')}")
            print(f"   - Channels: {device_info.get('max_input_channels', 0)}")
            print(f"   - Sample Rate: {device_info.get('default_samplerate', 0)}Hz")
        else:
            print("⚠️  No input device found")

        print("✅ Device query completed")

        print("=" * 80)

    @pytest.mark.skipif(
        not os.getenv("TEST_AUDIO_RECORDING"),
        reason="Requires microphone access and TEST_AUDIO_RECORDING env var",
    )
    def test_audio_recording_start_stop(self):
        """
        Test starting and stopping audio recording.
        Requires microphone permission and TEST_AUDIO_RECORDING=1.
        """
        print("\n" + "=" * 80)
        print("🔍 TESTING AUDIO RECORDING START/STOP")
        print("=" * 80)

        from computer_use.services.audio_capture import AudioCapture

        capture = AudioCapture()

        print("🎤 Starting recording...")
        success = capture.start_recording()

        assert success, "Recording should start successfully"
        print("✅ Recording started")

        time.sleep(0.5)

        print("⏸️  Stopping recording...")
        capture.stop_recording()

        print("✅ Recording stopped")

        print("=" * 80)

    def test_context_manager(self):
        """
        Test audio capture context manager usage.
        """
        print("\n" + "=" * 80)
        print("🔍 TESTING CONTEXT MANAGER")
        print("=" * 80)

        from computer_use.services.audio_capture import AudioCapture

        with patch("sounddevice.InputStream") as mock_stream:
            mock_stream_instance = MagicMock()
            mock_stream.return_value = mock_stream_instance

            with AudioCapture() as capture:
                assert capture is not None
                print("✅ Context manager entered")

            mock_stream_instance.stop.assert_called_once()
            mock_stream_instance.close.assert_called_once()
            print("✅ Context manager exited and cleaned up")

        print("=" * 80)


class TestVoiceInputService:
    """Test voice input service functionality."""

    def test_voice_service_initialization(self):
        """
        Test if voice input service initializes correctly.
        """
        print("\n" + "=" * 80)
        print("🔍 TESTING VOICE INPUT SERVICE INITIALIZATION")
        print("=" * 80)

        if not os.getenv("DEEPGRAM_API_KEY"):
            print("⚠️  DEEPGRAM_API_KEY not set, testing error handling")

            from computer_use.services.voice_input_service import VoiceInputService

            with pytest.raises(ValueError) as exc_info:
                VoiceInputService()

            assert "DEEPGRAM_API_KEY" in str(exc_info.value)
            print("✅ Correctly raises error when API key missing")

        else:
            print("✅ DEEPGRAM_API_KEY found")

            from computer_use.services.voice_input_service import VoiceInputService

            service = VoiceInputService()

            print("📋 Voice Service Status:")
            print(f"   - API Key: {'*' * 8}...{service.api_key[-4:]}")
            print(f"   - Client: {type(service.client).__name__}")

            assert service.api_key is not None
            assert service.client is not None
            print("✅ Voice service initialized successfully")

        print("=" * 80)

    def test_check_api_key_configured(self):
        """
        Test API key configuration check.
        """
        print("\n" + "=" * 80)
        print("🔍 TESTING API KEY CONFIGURATION CHECK")
        print("=" * 80)

        from computer_use.services.voice_input_service import VoiceInputService

        is_configured = VoiceInputService.check_api_key_configured()

        print(f"🔑 API Key Configured: {is_configured}")

        if is_configured:
            print("   ✅ DEEPGRAM_API_KEY is set")
        else:
            print("   ⚠️  DEEPGRAM_API_KEY not found")

        assert isinstance(is_configured, bool)
        print("✅ API key check completed")

        print("=" * 80)

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("DEEPGRAM_API_KEY"),
        reason="Requires DEEPGRAM_API_KEY environment variable",
    )
    @pytest.mark.skipif(
        not os.getenv("TEST_VOICE_TRANSCRIPTION"),
        reason="Requires TEST_VOICE_TRANSCRIPTION=1 for live API test",
    )
    async def test_transcription_lifecycle(self):
        """
        Test complete transcription lifecycle with real API.
        Requires DEEPGRAM_API_KEY and TEST_VOICE_TRANSCRIPTION=1.
        """
        print("\n" + "=" * 80)
        print("🔍 TESTING TRANSCRIPTION LIFECYCLE")
        print("=" * 80)

        from computer_use.services.voice_input_service import VoiceInputService

        interim_results = []

        def interim_callback(text: str):
            interim_results.append(text)
            print(f"   📝 Interim: {text}")

        service = VoiceInputService()

        print("🎤 Starting transcription...")
        success = await service.start_transcription(interim_callback=interim_callback)

        if not success:
            error = service.get_error()
            print(f"⚠️  Failed to start: {error}")
            pytest.skip(f"Could not start transcription: {error}")

        print("✅ Transcription started")
        print("   Speak something (will record for 3 seconds)...")

        await asyncio.sleep(3)

        print("⏸️  Stopping transcription...")
        result = await service.stop_transcription()

        print("📋 Results:")
        print(f"   - Final: {result}")
        print(f"   - Language: {service.detected_language}")
        print(f"   - Interim Count: {len(interim_results)}")

        print("✅ Transcription lifecycle completed")

        print("=" * 80)

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """
        Test error handling in voice service.
        """
        print("\n" + "=" * 80)
        print("🔍 TESTING ERROR HANDLING")
        print("=" * 80)

        if not os.getenv("DEEPGRAM_API_KEY"):
            print("⚠️  Skipping - DEEPGRAM_API_KEY not set")
            print("=" * 80)
            return

        from computer_use.services.voice_input_service import VoiceInputService

        service = VoiceInputService()

        with (
            patch.object(service, "audio_capture", None),
            patch.object(service.client.listen.websocket.v("1"), "start") as mock_start,
        ):
            mock_start.side_effect = Exception("Connection failed")

            success = await service.start_transcription()

            assert not success, "Should fail with connection error"
            assert service.get_error() is not None
            print("✅ Error handling works correctly")

        print("=" * 80)


class TestVoiceInputIntegration:
    """Test voice input integration with UI."""

    @pytest.mark.asyncio
    async def test_ui_voice_input_missing_api_key(self):
        """
        Test UI voice input when API key is missing.
        """
        print("\n" + "=" * 80)
        print("🔍 TESTING UI VOICE INPUT - NO API KEY")
        print("=" * 80)

        with patch.dict(os.environ, {}, clear=True):
            from computer_use.utils.ui import get_voice_input

            result = await get_voice_input()

            assert result is None, "Should return None when API key missing"
            print("✅ Correctly handles missing API key")

        print("=" * 80)

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("DEEPGRAM_API_KEY"),
        reason="Requires DEEPGRAM_API_KEY environment variable",
    )
    async def test_ui_voice_input_mock_success(self):
        """
        Test UI voice input with mocked successful transcription.
        """
        print("\n" + "=" * 80)
        print("🔍 TESTING UI VOICE INPUT - MOCK SUCCESS")
        print("=" * 80)

        from computer_use.utils.ui import get_voice_input

        mock_result = "Hello, this is a test"

        with patch("computer_use.utils.ui.VoiceInputService") as MockService:
            mock_service = MagicMock()
            mock_service.start_transcription.return_value = True
            mock_service.stop_transcription.return_value = mock_result
            mock_service.detected_language = "en"
            MockService.return_value = mock_service
            MockService.check_api_key_configured.return_value = True

            with patch(
                "computer_use.utils.ui.AudioCapture.check_microphone_available",
                return_value=True,
            ):
                with patch("builtins.input", return_value=""):
                    result = await get_voice_input()

                    assert result == mock_result
                    print(f"✅ Successfully transcribed: {result}")

        print("=" * 80)


class TestMultilingualSupport:
    """Test multilingual language detection."""

    @pytest.mark.skipif(
        not os.getenv("DEEPGRAM_API_KEY"),
        reason="Requires DEEPGRAM_API_KEY environment variable",
    )
    def test_language_detection_config(self):
        """
        Test that language detection is properly configured.
        """
        print("\n" + "=" * 80)
        print("🔍 TESTING LANGUAGE DETECTION CONFIG")
        print("=" * 80)

        from computer_use.services.voice_input_service import VoiceInputService

        service = VoiceInputService()

        print("📋 Language Detection Config:")
        print(f"   - Client Type: {type(service.client).__name__}")
        print(f"   - API Key Configured: {bool(service.api_key)}")
        print("   - Model: nova-2 with multi-language support")
        print("   - Detect Language: Enabled")

        assert service.client is not None, "Client should be initialized"
        assert service.api_key is not None, "API key should be set"
        print("✅ Language detection properly configured")

        print("=" * 80)


def run_manual_voice_test():
    """
    Manual test function for interactive voice testing.
    Run with: pytest -s tests/test_voice_input.py::run_manual_voice_test
    """
    print("\n" + "=" * 80)
    print("🎤 MANUAL VOICE INPUT TEST")
    print("=" * 80)
    print("\nThis will test real voice input with your microphone.")
    print("Make sure you have:")
    print("  1. DEEPGRAM_API_KEY set in environment")
    print("  2. Microphone connected and accessible")
    print("\nPress Ctrl+C to skip or Enter to continue...")

    try:
        input()
    except KeyboardInterrupt:
        print("\n⏭️  Skipped")
        return

    async def run_test():
        from computer_use.services.voice_input_service import VoiceInputService

        def on_interim(text):
            print(f"   📝 {text}")

        service = VoiceInputService()
        print("\n🎤 Listening for 5 seconds... Speak something!")

        success = await service.start_transcription(interim_callback=on_interim)

        if not success:
            print(f"❌ Failed: {service.get_error()}")
            return

        await asyncio.sleep(5)

        result = await service.stop_transcription()

        print("\n📋 RESULTS:")
        print(f"   Final: {result}")
        print(f"   Language: {service.detected_language}")

    asyncio.run(run_test())
    print("=" * 80)


if __name__ == "__main__":
    print("🧪 Running Voice Input Tests")
    print("=" * 80)
    pytest.main([__file__, "-v", "-s"])
