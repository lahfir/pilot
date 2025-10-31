# Twilio Phone Verification

Complete guide for SMS verification with Browser-Use agent.

---

## Quick Start (5 Minutes)

### 1. Get Twilio Credentials

1. Sign up: [twilio.com/try-twilio](https://www.twilio.com/try-twilio)
2. Get from [Console](https://www.twilio.com/console):
   - Account SID
   - Auth Token
3. Buy phone number: [Phone Numbers → Buy](https://www.twilio.com/console/phone-numbers/search)

### 2. Configure Environment

```bash
# .env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
```

### 3. Install & Setup Webhook

```bash
# Install dependencies
pip install twilio flask pyngrok

# Terminal 1: Start app (webhook runs on port 5001)
python -m computer_use.main

# Terminal 2: Expose webhook
ngrok http 5001
```

### 4. Configure Twilio Webhook

1. Go to [Phone Numbers](https://www.twilio.com/console/phone-numbers/incoming)
2. Click your number → **Messaging** section
3. **A MESSAGE COMES IN:**
   - Webhook: `https://YOUR-NGROK-URL.ngrok.io/sms`
   - Method: POST
4. Go to [Messaging Integrations](https://console.twilio.com/us1/service/sms/MG2effad77189c6f8c1249be6f5de612a0/sms-service-instance-configure?frameUrl=%2Fconsole%2Fsms%2Fservices%2FMG2effad77189c6f8c1249be6f5de612a0%3Fx-target-region%3Dus1) and select **Send a webhook**
5. Paste the webhook URL (e.g., `https://YOUR-NGROK-URL.ngrok.io/sms`) and click **Save**

### 5. Use It

```python
# Agent automatically handles phone verification
task = "Sign up for an account on example.com"
```

---

## How It Works

### Architecture

```
Website sends SMS → Twilio → Webhook (POST /sms) → TwilioService stores message
                                                              ↓
Browser Agent requests code ← LLM extracts code ← TwilioService polls for message
```

### Components

1. **TwilioService** - Stores SMS, extracts codes with LLM
2. **WebhookServer** - Flask server receives Twilio POST requests
3. **TwilioController** - Browser-Use actions for agent

### Verification Flow

```
1. Agent detects phone field
2. Calls get_verification_phone_number() → "+16267023124"
3. Enters number, submits form
4. Website sends SMS to Twilio number
5. Twilio forwards to webhook → stores in TwilioService
6. Agent calls get_verification_code(timeout=60)
7. TwilioService polls (every 1s), finds message
8. LLM extracts code: "123456"
9. Agent enters code, continues signup
```

### Code Extraction

The LLM extracts codes from various SMS formats:

- "Your verification code is 123456"
- "123456 is your code"
- "Use code 123456 to verify"
- "Your OTP: 123456"

Polling: **1 second intervals** for responsive detection.

---

## Available Actions

The Browser agent can call:

- `get_verification_phone_number()` - Get Twilio number
- `get_verification_code(timeout=60, poll_interval=1.0)` - Wait for SMS
- `check_twilio_status()` - Verify configuration
- `request_human_help(reason, instructions)` - For CAPTCHAs

---

## Troubleshooting

### No SMS Received

```bash
# 1. Check webhook is running
curl http://localhost:5001/health
# Should return: {"status": "ok"}

# 2. Verify ngrok is running
ngrok http 5001

# 3. Check Twilio logs
# Go to: Console → Monitor → Logs → Messaging
```

### Code Extraction Fails

Check logs for:

- `❌ LLM extraction error` - LLM client issue
- `⚠️ Code confidence too low` - Unclear SMS format

### Webhook Not Receiving

```bash
# Test manually
curl -X POST http://localhost:5001/sms \
  -d "From=+1234567890" \
  -d "To=+1987654321" \
  -d "Body=Your verification code is 123456"
```

---

## Configuration

### Environment Variables

```bash
# Required
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1234567890

# Optional
WEBHOOK_PORT=5001  # Default: 5000, auto-increments if taken
NGROK_AUTH_TOKEN=your_ngrok_token  # For persistent URLs
```

### Custom Timeout

```python
# Agent can adjust wait time
get_verification_code(timeout=120, poll_interval=0.5)
```

---

## Technical Details

### Thread Safety

- **Message Storage**: Thread-safe with `threading.Lock`
- **Webhook Server**: Runs in daemon thread
- **Message Expiry**: Auto-cleanup after 5 minutes

### Performance

- **Polling Interval**: 1 second (configurable)
- **Default Timeout**: 60 seconds
- **Webhook Response**: < 100ms
- **LLM Extraction**: 1-3 seconds
- **Total Time**: 10-30 seconds typical

### Security

- **HTTPS Required**: Production must use HTTPS
- **Memory Storage**: Messages stored in-memory only
- **Auto-Expiry**: Messages cleared after 5 minutes
- **No Persistence**: Cleared on restart

---

## Production Deployment

1. Deploy app to server with public domain
2. Use HTTPS (Twilio requires it)
3. Update webhook URL in Twilio Console
4. Consider adding webhook signature validation
5. Implement rate limiting

---

## Limitations

- Single verification at a time
- In-memory storage (not distributed)
- Webhook must be publicly accessible
- SMS may take 10-30 seconds to arrive

---

## Files Changed

- `src/computer_use/services/twilio_service.py` - Core service
- `src/computer_use/services/webhook_server.py` - Flask webhook
- `src/computer_use/tools/twilio_controller.py` - Browser actions
- `src/computer_use/tools/browser_tool.py` - Integration
- `pyproject.toml` - Dependencies

---

## References

- [Twilio SMS Docs](https://www.twilio.com/docs/sms)
- [Twilio Webhooks](https://www.twilio.com/docs/usage/webhooks)
- [Browser-Use](https://github.com/browser-use/browser-use)
- [ngrok Docs](https://ngrok.com/docs)
