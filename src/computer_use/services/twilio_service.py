"""
Twilio service for managing SMS verification codes.
Handles Twilio API interactions, message storage, and code extraction.
"""

import os
import threading
import time
from typing import Optional, Any
from pydantic import BaseModel, Field


class VerificationCode(BaseModel):
    """
    Represents an extracted verification code from SMS.
    """

    code: str = Field(description="The extracted verification code")
    confidence: float = Field(description="Confidence level of extraction (0.0 to 1.0)")


class SMSMessage:
    """
    Represents an SMS message received from Twilio.
    """

    def __init__(self, from_number: str, to_number: str, body: str, timestamp: float):
        """
        Initialize SMS message.

        Args:
            from_number: Sender phone number
            to_number: Recipient phone number (Twilio number)
            body: Message body text
            timestamp: Unix timestamp when message was received
        """
        self.from_number = from_number
        self.to_number = to_number
        self.body = body
        self.timestamp = timestamp


class TwilioService:
    """
    Manages Twilio SMS interactions and verification code extraction.
    Thread-safe singleton service for storing and retrieving SMS messages.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """
        Singleton pattern to ensure only one instance exists.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Initialize Twilio service with credentials from environment.
        """
        if hasattr(self, "_initialized"):
            return

        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.phone_number = os.getenv("TWILIO_PHONE_NUMBER")

        self.messages: list[SMSMessage] = []
        self.messages_lock = threading.Lock()
        self.llm_client = None

        self.message_expiry_seconds = 300

        self._initialized = True

    def set_llm_client(self, llm_client: Any):
        """
        Set LLM client for code extraction.

        Args:
            llm_client: LLM client instance (Langchain compatible)
        """
        self.llm_client = llm_client

    def is_configured(self) -> bool:
        """
        Check if Twilio is properly configured.

        Returns:
            True if all required credentials are set
        """
        return bool(self.account_sid and self.auth_token and self.phone_number)

    def get_phone_number(self) -> Optional[str]:
        """
        Get the configured Twilio phone number.

        Returns:
            Twilio phone number or None if not configured
        """
        return self.phone_number

    def store_message(self, from_number: str, to_number: str, body: str):
        """
        Store incoming SMS message with thread safety.

        Args:
            from_number: Sender phone number
            to_number: Recipient phone number
            body: Message body text
        """
        message = SMSMessage(
            from_number=from_number,
            to_number=to_number,
            body=body,
            timestamp=time.time(),
        )

        with self.messages_lock:
            self.messages.append(message)
            self._cleanup_old_messages()
            print(
                f"📨 SMS stored: {body[:50]}... (Total messages: {len(self.messages)})"
            )

    def _cleanup_old_messages(self):
        """
        Remove messages older than expiry time.
        Must be called with messages_lock held.
        """
        current_time = time.time()
        self.messages = [
            msg
            for msg in self.messages
            if current_time - msg.timestamp < self.message_expiry_seconds
        ]

    def get_latest_message(self, max_age_seconds: int = 120) -> Optional[SMSMessage]:
        """
        Get the most recent SMS message.

        Args:
            max_age_seconds: Maximum age of message to retrieve

        Returns:
            Latest SMSMessage or None if no recent messages
        """
        with self.messages_lock:
            self._cleanup_old_messages()

            if not self.messages:
                return None

            latest = self.messages[-1]
            if time.time() - latest.timestamp <= max_age_seconds:
                return latest

            return None

    async def extract_verification_code(
        self, message_body: str
    ) -> Optional[VerificationCode]:
        """
        Extract verification code from SMS message using LLM.

        Args:
            message_body: SMS message text

        Returns:
            VerificationCode with extracted code and confidence, or None if extraction fails
        """
        if not self.llm_client:
            print("⚠️  LLM client not set, cannot extract verification code")
            return None

        try:
            prompt = f"""Extract the verification code from this SMS message.
The code is typically a 4-8 digit number or alphanumeric string.

SMS Message: "{message_body}"

Return ONLY the verification code itself, nothing else.
If you cannot find a verification code, return "NONE".
"""

            print("🤖 Extracting code using LLM...")
            structured_llm = self.llm_client.with_structured_output(VerificationCode)
            result: VerificationCode = await structured_llm.ainvoke(prompt)

            if result and result.code and result.code != "NONE":
                print(
                    f"✅ LLM extracted: {result.code} (confidence: {result.confidence})"
                )
                return result
            else:
                print(f"❌ LLM could not extract code (result: {result})")

            return None

        except Exception as e:
            print(f"❌ LLM extraction error: {str(e)}")
            return None

    async def get_verification_code(
        self, timeout: int = 60, poll_interval: float = 1.0
    ) -> Optional[str]:
        """
        Wait for and retrieve verification code from latest SMS.
        Polls for new messages until timeout.

        Args:
            timeout: Maximum seconds to wait for code
            poll_interval: Seconds between polling attempts (default 1.0s for responsive checking)

        Returns:
            Verification code string or None if timeout/failure
        """
        start_time = time.time()
        poll_count = 0

        print(
            f"🔍 Polling for verification code (timeout: {timeout}s, interval: {poll_interval}s)..."
        )

        while time.time() - start_time < timeout:
            poll_count += 1
            latest_message = self.get_latest_message(max_age_seconds=timeout)

            if latest_message:
                print(
                    f"📬 Found message (poll #{poll_count}): {latest_message.body[:50]}..."
                )
                code_result = await self.extract_verification_code(latest_message.body)

                if code_result:
                    print(
                        f"🔑 Extracted code: {code_result.code} (confidence: {code_result.confidence:.2f})"
                    )
                    if code_result.confidence > 0.5:
                        return code_result.code
                    else:
                        print(
                            f"⚠️  Code confidence too low ({code_result.confidence:.2f}), continuing to poll..."
                        )
                else:
                    print("❌ Failed to extract code from message")
            else:
                if poll_count % 10 == 0:  # Log every 10 polls to avoid spam
                    print(
                        f"⏳ No message yet (poll #{poll_count}, elapsed: {time.time() - start_time:.1f}s)"
                    )

            await self._async_sleep(poll_interval)

        print(f"⏱️  Timeout reached after {poll_count} polls, no valid code found")
        return None

    async def _async_sleep(self, seconds: float):
        """
        Async sleep helper.

        Args:
            seconds: Seconds to sleep
        """
        import asyncio

        await asyncio.sleep(seconds)

    def clear_messages(self):
        """
        Clear all stored messages.
        """
        with self.messages_lock:
            self.messages.clear()
