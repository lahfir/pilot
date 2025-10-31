"""
Twilio tools for Browser-Use phone verification.
Provides custom actions for handling phone verification flows.
Also includes human-in-the-loop tools for manual intervention.
"""

from browser_use import Tools, ActionResult


def create_twilio_tools(twilio_service) -> Tools:
    """
    Create Browser-Use tools for Twilio phone verification.

    Args:
        twilio_service: TwilioService instance

    Returns:
        Tools instance with Twilio actions
    """
    tools = Tools()

    @tools.action(description="Get phone number for SMS verification")
    def get_verification_phone_number() -> ActionResult:
        """
        Get Twilio phone number to use for phone verification.
        Call this when you encounter a phone number input field.

        Returns:
            ActionResult with phone number or error
        """
        if not twilio_service.is_configured():
            return ActionResult(
                extracted_content="ERROR: Twilio not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER environment variables.",
                error="Twilio not configured",
            )

        phone = twilio_service.get_phone_number()
        if not phone:
            return ActionResult(
                extracted_content="ERROR: No Twilio phone number configured",
                error="No phone number",
            )

        return ActionResult(
            extracted_content=f"Use this phone number for verification: {phone}",
            long_term_memory=f"Twilio phone number: {phone}",
        )

    @tools.action(
        description="Wait for and retrieve SMS verification code (call after submitting phone number)"
    )
    async def get_verification_code(
        timeout: int = 60, poll_interval: float = 1.0
    ) -> ActionResult:
        """
        Wait for SMS verification code to arrive and return it.
        Call this AFTER you have submitted the phone number and the website has sent the SMS.

        Args:
            timeout: Maximum seconds to wait for SMS (default 60)
            poll_interval: Seconds between checks for new messages (default 1.0 for responsive polling)

        Returns:
            ActionResult with verification code or error
        """
        if not twilio_service.is_configured():
            return ActionResult(
                extracted_content="ERROR: Twilio not configured",
                error="Twilio not configured",
            )

        code = await twilio_service.get_verification_code(
            timeout=timeout, poll_interval=poll_interval
        )

        if not code:
            return ActionResult(
                extracted_content=f"ERROR: No verification code received within {timeout} seconds. The SMS may not have been sent yet, or there was a delivery issue.",
                error=f"No code received within {timeout}s",
            )

        return ActionResult(
            extracted_content=f"Verification code received: {code}",
            long_term_memory=f"Retrieved verification code: {code}",
        )

    @tools.action(description="Check if Twilio phone verification is available")
    def check_twilio_status() -> ActionResult:
        """
        Check if Twilio is properly configured and ready to use.

        Returns:
            ActionResult with configuration status
        """
        if twilio_service.is_configured():
            phone = twilio_service.get_phone_number()
            return ActionResult(
                extracted_content=f"Twilio is configured and ready. Phone number: {phone}"
            )

        return ActionResult(
            extracted_content="Twilio is NOT configured. Phone verification is not available.",
            error="Twilio not configured",
        )

    @tools.action(
        description="Request human help for CAPTCHA, visual verification, or other manual tasks"
    )
    def request_human_help(reason: str, instructions: str) -> ActionResult:
        """
        Request human intervention for tasks that require manual action.
        Use this when you encounter CAPTCHAs, visual verifications, or other challenges
        that cannot be automated.

        Args:
            reason: Why human help is needed (e.g., "Visual CAPTCHA detected")
            instructions: What the human needs to do (e.g., "Please solve the CAPTCHA showing traffic lights")

        Returns:
            ActionResult indicating the request was made
        """
        message = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                          🤝 HUMAN ASSISTANCE NEEDED                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

Reason: {reason}

Instructions:
{instructions}

The browser will remain open. Please complete the manual task, then press Enter
to allow the agent to continue.

Press [Enter] when ready to continue...
"""
        print(message)

        # Wait for user to press Enter
        try:
            input()
            return ActionResult(
                extracted_content="Human assistance completed. Continuing with the task...",
                long_term_memory=f"Human helped with: {reason}",
            )
        except (KeyboardInterrupt, EOFError):
            return ActionResult(
                extracted_content="User cancelled the task.",
                error="Task cancelled by user",
                is_done=True,
                success=False,
            )

    return tools
