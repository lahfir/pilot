# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Cross-platform AI agent system for autonomous desktop and web automation. Uses CrewAI framework with multiple specialist agents (Browser, GUI, System, Coding) orchestrated by a Manager Agent.

## Strict Guidelines (CRITICAL)

This is a **multi-purpose, platform-agnostic, task-agnostic** autonomous agent system. All development must adhere to these principles:

### No Task-Specific Code or Instructions

- **NEVER** add code, prompts, or logic designed for a specific task (e.g., "how to send an email", "how to book a flight")
- **NEVER** include task-specific workflows, checklists, or step-by-step guides for particular use cases
- Agent instructions and system prompts must remain **general-purpose** - they describe capabilities, not specific tasks
- The agent learns task execution dynamically from user requests, not from hardcoded instructions

### No Platform-Specific Assumptions

- **NEVER** write code that only works on one platform (macOS, Windows, or Linux)
- All functionality must use platform abstraction layers (`platform_registry.py`, `platform_detector.py`)
- Platform-specific implementations belong **only** in dedicated platform modules (`accessibility/macos_accessibility.py`, etc.)
- System prompts and agent instructions must **never** reference platform-specific behaviors or paths

### General Methodology Over Specific Solutions

- Code should implement **general patterns** that apply to any task
- Example: Implement "click element by text" not "click the Submit button on login forms"
- Example: Implement "type text into focused field" not "enter email address"
- The agent's strength is **reasoning and planning**, not memorized procedures

### What IS Allowed

- General-purpose tools (screenshot, click, type, scroll, read screen)
- Abstract capability descriptions ("can interact with UI elements", "can execute shell commands")
- Platform detection and routing logic
- Error handling and recovery patterns that apply broadly
- Performance optimizations that benefit all tasks equally

### What is NOT Allowed

- Task-specific prompts or examples in agent configurations
- Hardcoded element selectors for specific applications
- Workflow templates for particular use cases
- Platform-specific code outside of platform abstraction modules
- Instructions that would make the agent better at one task at the expense of generality

### CRITICAL: Bug Fixes Must Be General

**When a bug is discovered (e.g., agent hallucinated a result, action failed, etc.):**

1. **NEVER** propose a task-specific workaround (e.g., "clear the calculator before calculations")
2. **ALWAYS** fix the underlying general issue (e.g., "add result validation against observed values")
3. The agent must learn to handle edge cases through **reasoning**, not hardcoded instructions
4. If the agent failed to read the actual result, fix the **observation/validation framework** - don't add app-specific logic

**Examples of WRONG fixes:**
- "Add code to press AC before entering calculations" ❌
- "Check if email was sent by looking for 'Message Sent' text" ❌
- "Wait 2 seconds after opening Calculator" ❌

**Examples of CORRECT fixes:**
- "Validate reported results against ObservationRegistry" ✓
- "Add general UI state change detection" ✓
- "Improve observation recording for all tools" ✓

### Review Checklist (Before Any Change)

1. Does this change work on all platforms (macOS, Windows, Linux)?
2. Does this change apply to ALL possible tasks, not just one?
3. Would this change still be useful if the user's task is completely different?
4. Is this a general capability or a specific solution?
5. **NEW**: If fixing a bug, am I fixing the general framework or adding a task-specific hack?

## Tech Stack

- **Python 3.11+** with uv package manager
- **CrewAI** - Multi-agent orchestration
- **Browser-Use** - Web automation engine
- **LangChain** - LLM integration (Google, OpenAI, Anthropic)
- **Platform APIs**: atomacos (macOS), pywinauto (Windows), pyatspi (Linux)
- **Vision**: EasyOCR, PaddleOCR, macOS Vision API, OpenCV

## Commands

```bash
# Install dependencies (pick your platform)
uv sync --extra macos
uv sync --extra windows
uv sync --extra linux
uv sync --dev --extra macos          # With dev dependencies

# Run the agent
uv run python -m pilot.main
uv run python -m pilot.main --voice-input  # With voice

# Testing
uv run pytest                         # All tests
uv run pytest -v                      # Verbose
uv run pytest -m "not slow"          # Skip slow tests
uv run pytest tests/test_crew_tools.py  # Single file
uv run pytest -k "test_name"         # Single test by name

# Linting (required before committing)
uv run ruff check .                   # Check issues
uv run ruff check --fix .             # Auto-fix
uv run ruff format .                  # Format code
```

## Architecture

### Multi-Agent System

```
User Request → Manager Agent → [Browser|GUI|System|Coding] Agent → Result
```

- **Manager Agent** (`src/pilot/crew.py`) - Analyzes requests, decomposes into subtasks, delegates
- **Browser Agent** - Web automation via Browser-Use framework
- **GUI Agent** - Desktop app control via accessibility APIs
- **System Agent** - Shell command execution (platform-aware)
- **Coding Agent** - Code writing via Cline AI

### Multi-Tier Detection (for UI element location)

1. Accessibility APIs (fastest, most reliable)
2. OCR with EasyOCR/PaddleOCR (fallback)
3. Vision AI - LLM-based screen analysis
4. Template matching (final fallback)

### Directory Structure

```
src/pilot/
├── main.py                    # CLI entry point
├── crew.py                    # Main orchestrator (core file)
├── agents/                    # Specialist agent implementations
├── config/
│   ├── agents.yaml           # Agent role definitions
│   ├── tasks.yaml            # Task templates
│   ├── llm_config.py         # LLM provider setup
│   └── timing_config.py      # Performance tuning
├── tools/
│   ├── accessibility/        # Platform-specific accessibility APIs
│   ├── browser/              # Browser-specific tools
│   ├── vision/               # OCR engines and vision detection
│   └── fallback/             # Fallback detection methods
├── services/                  # Business logic services
├── schemas/                   # Pydantic data models
├── prompts/                   # Agent prompt templates
└── utils/                     # Platform detection, safety, logging
```

## Environment Variables

```bash
# LLM Provider (required - pick one)
LLM_PROVIDER=google           # or openai, anthropic
LLM_MODEL=gemini-3-flash-preview
GOOGLE_API_KEY=...            # Or OPENAI_API_KEY / ANTHROPIC_API_KEY

# Vision and Browser LLM (same provider options)
VISION_LLM_PROVIDER=google
VISION_LLM_MODEL=gemini-3-flash-preview
BROWSER_LLM_PROVIDER=google
BROWSER_LLM_MODEL=gemini-3-flash-preview

# Optional - SMS verification
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...

# Optional - Voice input
DEEPGRAM_API_KEY=...
```

## Platform Permissions

| Platform | Requirement                                          |
| -------- | ---------------------------------------------------- |
| macOS    | System Settings → Privacy & Security → Accessibility |
| Windows  | Run as Administrator for some apps                   |
| Linux    | AT-SPI enabled (usually default)                     |

## Code Standards

From `.cursor/rules/`:

- **400 LOC max** per file
- **Docstrings only**, no inline comments (Google-style)
- **Type hints required** on all function parameters and returns
- **Run ruff** before any commit: `ruff check --fix . && ruff format .`

## Testing

Pytest markers for platform-specific tests:

- `@pytest.mark.macos` / `@pytest.mark.windows` / `@pytest.mark.linux`
- `@pytest.mark.slow` - Long-running tests
- `@pytest.mark.asyncio` - Async tests

Key test files:

- `tests/test_crew_tools.py` - Tool functionality
- `tests/test_accessibility_cross_platform.py` - Platform API testing
- `tests/test_end_to_end.py` - Full workflow tests
- `tests/test_hierarchical_delegation.py` - Agent coordination

## Key Files

- `src/pilot/crew.py` - Main orchestrator, start here for understanding flow
- `src/pilot/config/agents.yaml` - Agent roles and anti-hallucination rules
- `src/pilot/tools/vision/ocr_factory.py` - OCR engine selection logic
- `src/pilot/utils/safety_checker.py` - Operation validation
