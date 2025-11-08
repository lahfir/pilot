# CrewAI Inter-Agent Communication System

## Overview

This document explains how agents communicate and share data in our CrewAI-powered computer use system.

## Problem We Solved

### Before

❌ **Manual String Concatenation**

```python
context = {"task": task, "previous_results": []}
context=str(context)  # Just converting to string!
```

- Browser agent downloads file → other agents don't know file path
- No structured data passing
- Manual context management

### After

✅ **CrewAI Native Context Passing**

```python
browser_task = Task(
    description="...",
    context=[previous_task],  # CrewAI handles output passing!
)
```

- Browser agent downloads file → System/GUI agents **automatically receive file path**
- Structured data with **📁 DOWNLOADED FILE markers**
- CrewAI handles all context management

---

## How It Works

### 1. Sequential Task Chaining

```python
# Browser task executes first
browser_task = Task(
    description="Download Nvidia report",
    agent=browser_agent,
    context=[],  # No previous tasks
)

# System task receives browser output automatically
system_task = Task(
    description="Save to Documents",
    agent=system_agent,
    context=[browser_task],  # ← Gets browser_task output!
)
```

### 2. Structured Output Format

All tools now return structured data:

```
✅ SUCCESS: Downloaded file from example.com

📊 EXTRACTED DATA:
Company: Nvidia Corp
Stock Price: $195.21

📁 DOWNLOADED FILE: /Users/john/Downloads/nvidia_report.pdf
```

### 3. Context Template Variables

Tasks use `{context}` which CrewAI replaces with previous task outputs:

```yaml
description: >
  Complete this task: {subtask}

  Previous results: {context}  # ← CrewAI fills this automatically!
```

---

## Real-World Example

**User Request**: "Research Nvidia and save summary to Documents"

### Agent Flow

1. **Browser Agent** (Task 1)

   ```
   Input: "Research Nvidia online"
   Output: ✅ SUCCESS: Extracted company info
           📊 EXTRACTED DATA: [Nvidia details]
           📁 DOWNLOADED FILE: /tmp/nvidia.pdf
   ```

2. **System Agent** (Task 2)

   ```
   Input: "Save to Documents"
   Context: {browser_task output}  ← Automatically includes file path!

   Agent sees: "Previous task downloaded /tmp/nvidia.pdf"
   Action: mv /tmp/nvidia.pdf ~/Documents/nvidia_summary.pdf
   ```

### Without CrewAI Context Passing

❌ System agent would need to:

- Parse unstructured text manually
- Guess file locations
- No guaranteed data format

### With CrewAI Context Passing

✅ System agent automatically:

- Receives structured file path
- Knows what previous agent did
- Can build on previous work

---

## Key Features

### 📁 File Path Sharing

When browser agent downloads:

```python
output_parts.append(f"\n📁 DOWNLOADED FILE: {file_path}")
```

Next agent receives this in their context!

### 📊 Data Extraction Sharing

When browser agent extracts data:

```python
output_parts.append(f"\n📊 EXTRACTED DATA:\n{data}")
```

Next agent can process this data!

### 📝 Text Content Sharing

When browser/GUI agent reads text:

```python
output_parts.append(f"\n📝 TEXT:\n{text}")
```

Next agent can use this text!

---

## LLM Schema Clarity Fixes

### Problem

LLM was passing dict instead of string:

```python
# ❌ What LLM did (WRONG):
{"task": {"description": "...", "type": "str"}}

# ✅ What it should do:
{"task": "Search for Nvidia stock"}
```

### Solution

```python
task: str = Field(
    ...,
    description="Simple string describing the web task. Example: 'Go to yahoo finance and get NVDA stock price'",
)
```

Added **explicit examples** in field descriptions so LLM understands the format.

---

## Benefits

### 🔗 Automatic Context Passing

- No manual string concatenation
- CrewAI handles all data flow
- Type-safe and structured

### 📂 File Sharing Between Agents

- Browser downloads → System/GUI can access
- Clear file path markers
- No ambiguity

### 🧠 Intelligent Collaboration

- Each agent builds on previous work
- Shared context across entire workflow
- No duplicate work

### 🛡️ Error Resilience

- If browser fails, next agent knows why
- Structured error messages
- Clear success/failure indicators

---

## Configuration

### Task Context Setup (`crew.py`)

```python
# Each task automatically receives previous task output
context=[previous_task] if previous_task else []
```

### Tool Output Format (`web_tools.py`)

```python
output_parts = [f"✅ SUCCESS: {action}"]
if "file_path" in data:
    output_parts.append(f"\n📁 DOWNLOADED FILE: {data['file_path']}")
```

### Template Variables (`tasks.yaml`)

```yaml
description: >
  {subtask}
  Previous results: {context}  # CrewAI fills this
```

---

## Testing the System

### Test Scenario

```
User: "Download Nvidia report and move it to Documents"
```

**Expected Flow**:

1. Browser agent downloads → returns file path
2. System agent receives path via context
3. System agent moves file using received path
4. Success! No manual parsing needed

### Verification

Check agent outputs for:

- ✅ `📁 DOWNLOADED FILE:` markers
- ✅ Next agent mentioning the file path
- ✅ No "file not found" errors

---

## Future Enhancements

### 1. Shared Memory (CrewAI Memory)

```python
crew = Crew(
    agents=[...],
    tasks=[...],
    memory=True,  # ← Enable long-term memory
)
```

Agents remember across multiple user requests!

### 2. Entity Memory

```python
from crewai import Entity

nvidia = Entity(
    name="Nvidia",
    stock_price="$195.21",
    last_updated="2025-11-06",
)
```

Structured knowledge base for agents.

### 3. Parallel Task Execution

```python
process=Process.parallel  # Execute independent tasks simultaneously
```

Browser + GUI agents work at same time!

---

## Summary

✅ **Now**: CrewAI handles all inter-agent communication
✅ **File Sharing**: Download paths automatically shared
✅ **Structured Data**: Clear markers for different data types
✅ **No Manual Parsing**: Agents receive typed, structured context
✅ **Scalable**: Easy to add new agents to the chain

**The system is now a true multi-agent collaboration platform!** 🚀
