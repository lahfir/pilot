# OSWorld Benchmark Integration

This guide explains how to evaluate PILOT against the [OSWorld benchmark](https://os-world.github.io/), a comprehensive benchmark for testing multimodal agents on real computer tasks.

## Overview

OSWorld provides:
- **369 real computer tasks** across Ubuntu, Windows, and macOS
- **Execution-based evaluation** in actual virtual machines
- **Diverse domains**: OS operations, office apps, daily tasks, professional tools
- **Reproducible setup** with VM snapshots and evaluation scripts

## Quick Start

### 1. Clone OSWorld

```bash
git clone https://github.com/xlang-ai/OSWorld.git
cd OSWorld
pip install -r requirements.txt
```

### 2. Set Up VM Environment

Choose one of these providers:

#### Option A: Docker (Easiest)

```bash
# Pull the Ubuntu image
docker pull showlab/osworld:ubuntu

# Start container
docker run -d --name osworld-ubuntu \
    -p 5900:5900 \
    showlab/osworld:ubuntu
```

#### Option B: VMware (Best compatibility)

1. Download Ubuntu 22.04 VMware image from OSWorld releases
2. Import into VMware Workstation/Fusion
3. Configure network to bridge mode

#### Option C: AWS (Fastest evaluation)

```bash
# Configure AWS credentials
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-west-2

# OSWorld will automatically provision EC2 instances
```

### 3. Run PILOT Against OSWorld

```bash
# From pilot directory
cd /path/to/pilot

# Basic run with Docker
python -m pilot.benchmarks.osworld_runner \
    --osworld-path /path/to/OSWorld \
    --provider docker

# Quick test (5 tasks)
python -m pilot.benchmarks.osworld_runner \
    --osworld-path /path/to/OSWorld \
    --max-tasks 5

# Run specific domain
python -m pilot.benchmarks.osworld_runner \
    --osworld-path /path/to/OSWorld \
    --domain os
```

## Detailed Setup

### Environment Variables

Ensure these are set before running:

```bash
# LLM Configuration (required)
export LLM_PROVIDER=google
export LLM_MODEL=gemini-2.0-flash
export GOOGLE_API_KEY=your_api_key

# Vision LLM (for screenshot analysis)
export VISION_LLM_PROVIDER=google
export VISION_LLM_MODEL=gemini-2.0-flash
```

### OSWorld Configuration

The OSWorld environment expects certain configurations:

| Setting | Default | Description |
|---------|---------|-------------|
| `provider_name` | `docker` | VM provider |
| `action_space` | `pyautogui` | Action format |
| `screen_size` | `1920x1080` | VM screen resolution |
| `client_password` | `password` | VM sudo password |
| `headless` | `False` | Run without display |

### VM Credentials

| Provider | Username | Password |
|----------|----------|----------|
| Docker/VMware | `user` | `password` |
| AWS | `ubuntu` | `osworld-public-evaluation` |

## Architecture

### How the Adapter Works

```
┌─────────────────────────────────────────────────────────────┐
│                      OSWorld Framework                       │
├─────────────────────────────────────────────────────────────┤
│  DesktopEnv                                                  │
│  ├── reset(task_config) → obs                               │
│  ├── step(action) → obs, reward, done, info                 │
│  └── evaluate() → score                                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  OSWorldAgentAdapter                         │
├─────────────────────────────────────────────────────────────┤
│  Implements OSWorld Interface:                               │
│  ├── reset(vm_ip) - Clear state for new task                │
│  └── predict(instruction, obs) → (response, actions)        │
│                                                              │
│  Translates:                                                 │
│  ├── OSWorld obs → PILOT context                            │
│  └── PILOT results → pyautogui actions                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    PILOT (ComputerUseCrew)                   │
├─────────────────────────────────────────────────────────────┤
│  Multi-agent system:                                         │
│  ├── Manager Agent (orchestration)                          │
│  ├── Browser Agent (web tasks)                              │
│  ├── GUI Agent (desktop automation)                         │
│  └── System Agent (shell commands)                          │
└─────────────────────────────────────────────────────────────┘
```

### Action Flow

1. **OSWorld** provides observation (screenshot + a11y tree)
2. **Adapter** formats observation for PILOT
3. **PILOT** executes task using its multi-agent system
4. **Adapter** converts PILOT's actions to pyautogui format
5. **OSWorld** executes pyautogui code in VM

### Supported Actions

| pyautogui Action | Description | Example |
|-----------------|-------------|---------|
| `click(x, y)` | Left click at coordinates | `pyautogui.click(100, 200)` |
| `doubleClick(x, y)` | Double click | `pyautogui.doubleClick(100, 200)` |
| `rightClick(x, y)` | Right click | `pyautogui.rightClick(100, 200)` |
| `typewrite(text)` | Type text | `pyautogui.typewrite('hello')` |
| `hotkey(*keys)` | Key combination | `pyautogui.hotkey('ctrl', 'c')` |
| `scroll(clicks)` | Scroll wheel | `pyautogui.scroll(-3)` |
| `WAIT` | Wait for UI update | Special control action |
| `DONE` | Task completed | Terminal action |
| `FAIL` | Task failed | Terminal action |

## Running Evaluations

### Full Benchmark (369 tasks)

```bash
# This takes several hours depending on provider
python -m pilot.benchmarks.osworld_runner \
    --osworld-path /path/to/OSWorld \
    --provider aws \
    --output full_benchmark_results.json
```

### Domain-Specific Evaluation

```bash
# OS tasks only (file operations, settings, etc.)
python -m pilot.benchmarks.osworld_runner \
    --osworld-path /path/to/OSWorld \
    --domain os

# Office tasks (LibreOffice, etc.)
python -m pilot.benchmarks.osworld_runner \
    --osworld-path /path/to/OSWorld \
    --domain office

# Available domains: os, office, daily, professional, workflow
```

### Debugging Single Tasks

```python
from pilot.benchmarks import OSWorldAgentAdapter

# Create adapter
agent = OSWorldAgentAdapter(
    observation_type="screenshot_a11y_tree"
)

# Simulate observation
obs = {
    "screenshot": open("screenshot.png", "rb").read(),
    "accessibility_tree": "<root>...</root>",
    "instruction": "Open Firefox browser"
}

# Get prediction
response, actions = agent.predict("Open Firefox browser", obs)
print(f"Response: {response}")
print(f"Actions: {actions}")
```

## Results Format

Output JSON structure:

```json
{
    "total_tasks": 369,
    "completed": 369,
    "successful": 45,
    "failed": 324,
    "average_score": 0.122,
    "success_rate": 0.122,
    "task_results": [
        {
            "task_id": "abc123",
            "instruction": "Install Firefox browser",
            "steps": [...],
            "success": true,
            "score": 1.0,
            "error": null
        }
    ]
}
```

## Known Limitations

### Current Challenges

1. **GUI Grounding**: Translating high-level actions to precise coordinates
2. **Action Timing**: Knowing when UI has finished updating
3. **Error Recovery**: Handling unexpected dialogs or states
4. **Long Sequences**: Tasks requiring many sequential steps

### Google Drive Tasks

OSWorld includes 8 Google Drive tasks that may fail due to network/auth issues. You can either:
- Manually configure them (full 369 tasks)
- Exclude them (361 tasks) - officially accepted

## Comparison with Other Benchmarks

| Benchmark | Tasks | Environment | Multimodal | Cross-App |
|-----------|-------|-------------|------------|-----------|
| **OSWorld** | 369 | Full Computer | ✓ | ✓ |
| WebArena | 812 | Web Only | ✓ | ✗ |
| MiniWoB++ | 125 | Toy Web | ✓ | ✗ |
| GAIA | 466 | No Env | ✗ | ✗ |

## Resources

- [OSWorld Paper](https://arxiv.org/abs/2404.07972)
- [OSWorld GitHub](https://github.com/xlang-ai/OSWorld)
- [OSWorld Leaderboard](https://os-world.github.io/#benchmark)
- [Setup Guide](https://github.com/xlang-ai/OSWorld/blob/main/SETUP_GUIDELINE.md)

## Troubleshooting

### VM Connection Issues

```bash
# Check if VM is running
docker ps  # for Docker
vmrun list  # for VMware

# Test VNC connection
vncviewer localhost:5900
```

### Action Execution Failures

1. Ensure screen resolution matches (1920x1080)
2. Check coordinate bounds
3. Verify element is visible/interactable

### Import Errors

```bash
# Make sure OSWorld is in Python path
export PYTHONPATH="/path/to/OSWorld:$PYTHONPATH"
```

### Performance Tips

1. Use AWS provider for fastest evaluation (~1 hour for full benchmark)
2. Run tasks in parallel across multiple VMs
3. Use headless mode for unattended runs
