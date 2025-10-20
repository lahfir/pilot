# Inter-Agent Communication System

## Overview

The system features robust inter-agent communication with full type safety:

- **Type-Safe Data Passing**: All agents use Pydantic `ActionResult` models
- **Smart Handoffs**: Agents recognize boundaries and delegate appropriately
- **File Tracking**: Downloaded files tracked with complete metadata
- **Context Sharing**: Rich context passed between Browser, GUI, and System agents
- **Principle-Based Intelligence**: Generic guidelines that scale to any task

---

## Browser Agent Intelligence

### Principle-Based Guidelines

The Browser agent operates with clear, generic principles about its role:

```python
🎯 BROWSER AGENT PRINCIPLES

Your role: WEB AUTOMATION SPECIALIST
- Navigate websites, find information, download/extract data
- Work with web pages, forms, downloads, search results
- Other agents handle: desktop apps, file processing, terminal commands

Success = Gathering the requested data, NOT processing it
✅ Downloaded files? → done() (let other agents open/process them)
✅ Extracted to file? → done() (your job complete)
✅ Cannot read file format? → done() if you downloaded it
✅ Task needs desktop app? → done() with data (let GUI agent handle)

Key insight: If you got the data but can't process it further in a browser,
you've succeeded! Call done() and describe what you gathered.
```

### Loop Prevention

```python
agent = Agent(
    task=full_task,
    llm=self.llm_client,
    browser_session=browser_session,
    max_failures=5,      # Allow retries for complex tasks
)

result = await agent.run(max_steps=30)  # Hard limit to prevent infinite loops
```

**Why This Works**:

- **Generic**: Applies to any task (census data, downloads, APIs, scraping)
- **Principle-Based**: Agent reasons about boundaries, not rigid rules
- **Self-Aware**: Understands its role as a specialist, not generalist

---

## Type-Safe Data Structures

### ActionResult Schema

All agents return `ActionResult` (Pydantic model):

```python
from schemas.actions import ActionResult

class ActionResult(BaseModel):
    success: bool
    action_taken: str
    method_used: str
    confidence: float
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    handoff_requested: bool = False
    suggested_agent: Optional[str] = None
    handoff_reason: Optional[str] = None
    handoff_context: Optional[Dict[str, Any]] = None
```

### BrowserOutput Schema

Browser agent packages output in structured format:

```python
from schemas.browser_output import BrowserOutput, FileDetail

class FileDetail(BaseModel):
    path: str   # Absolute path
    name: str   # Filename
    size: int   # Bytes

class BrowserOutput(BaseModel):
    text: str                               # Summary of actions
    files: List[str] = []                   # File paths
    file_details: List[FileDetail] = []     # Full metadata
    work_directory: Optional[str] = None    # Temp directory

    def has_files(self) -> bool
    def get_file_count(self) -> int
    def get_total_size_kb(self) -> float
    def format_summary(self) -> str
```

### Browser Agent Return Example

```python
# Browser agent returns typed ActionResult
result = ActionResult(
    success=True,
    action_taken="Downloaded data from census.gov",
    method_used="browser",
    confidence=1.0,
    data={
        "result": str(AgentHistoryList),
        "output": BrowserOutput(
            text="Downloaded demographic data from census.gov",
            files=["/tmp/browser_agent_abc/demographics_2024.csv"],
            file_details=[
                FileDetail(
                    path="/tmp/browser_agent_abc/demographics_2024.csv",
                    name="demographics_2024.csv",
                    size=524288
                )
            ],
            work_directory="/tmp/browser_agent_abc/"
        ).model_dump(),  # Serialized for data field
        "task_complete": True
    }
)

# Type-safe access
if result.success:  # Direct attribute
    output_dict = result.data["output"]
    browser_output = BrowserOutput(**output_dict)  # Parse to typed object

    print(browser_output.text)
    for file_path in browser_output.files:
        print(f"File: {file_path}")
```

---

## File Tracking

### Discovery Process

1. **Attachments**: Files explicitly marked by Browser-Use via `attachments` field
2. **Work Directory**: All files in `browseruse_agent_data/` subdirectory
3. **Absolute Paths**: All paths converted to absolute for easy access
4. **Metadata**: Extract name, size, and other details

### Implementation

```python
# Check Browser-Use attachments
if result.history and len(result.history) > 0:
    attachments = result.history[-1].result[-1].attachments
    if attachments:
        for attachment in attachments:
            attachment_path = Path(attachment)
            if attachment_path.exists():
                downloaded_files.append(str(attachment_path.absolute()))
                file_details.append(FileDetail(
                    path=str(attachment_path.absolute()),
                    name=attachment_path.name,
                    size=attachment_path.stat().st_size
                ))

# Scan browser's working directory
browser_data_dir = temp_dir / "browseruse_agent_data"
if browser_data_dir.exists():
    for file_path in browser_data_dir.rglob("*"):
        if file_path.is_file():
            downloaded_files.append(str(file_path.absolute()))
            file_details.append(FileDetail(
                path=str(file_path.absolute()),
                name=file_path.name,
                size=file_path.stat().st_size
            ))
```

---

## Context Passing Flow

### Type-Safe Serialization Strategy

**Principle**: Keep types as long as possible, serialize only at boundaries.

```python
# 1. Agent Execution → Returns ActionResult (typed)
result: ActionResult = await self._execute_browser(task, context)

# 2. Internal Storage → Keep as ActionResult for type safety
results.append(result)  # Typed list

# 3. Context Serialization → Convert to dict for context passing
context["previous_results"].append(result.model_dump())

# 4. Next Agent → Receives context, parses back to typed objects
for res in context.get("previous_results", []):
    output = res.get("data", {}).get("output")
    if isinstance(output, dict):
        browser_output = BrowserOutput(**output)  # Type-safe!
        print(browser_output.text)
        for file in browser_output.files:
            print(file)

# 5. Final Serialization → Convert all at the very end
def _build_result(self, task, analysis, results, success):
    return {
        "task": task,
        "results": [r.model_dump() for r in results],  # Serialize once
        "overall_success": success
    }
```

---

## Crew Orchestrator

### Type-Safe Agent Execution

All executor methods return `ActionResult`:

```python
async def _execute_browser(self, task: str, context: dict) -> ActionResult:
    """Execute browser agent, returns typed ActionResult."""
    return await self.browser_agent.execute_task(task, context=context)

async def _execute_gui(self, task: str, context: dict) -> ActionResult:
    """Execute GUI agent, returns typed ActionResult."""
    return await self.gui_agent.execute_task(task, context=context)

async def _execute_system(self, task: str, context: dict) -> ActionResult:
    """Execute system agent, returns typed ActionResult."""
    return await self.system_agent.execute_task(task, context)
```

### Type-Safe Field Access

```python
# Direct attribute access (type-safe)
if result.success:
    if result.handoff_requested:
        suggested = result.suggested_agent
        print_handoff("GUI", suggested.upper() if suggested else "UNKNOWN", result.handoff_reason)

        context["handoff_context"] = result.handoff_context

        if suggested == "system":
            handoff_result = await self._execute_system(task, context)

            if handoff_result.success:
                print_success("System agent completed handoff task")
            else:
                print_failure(f"System agent failed: {handoff_result.error}")
```

### Smart Handoff Detection

```python
# Browser agent completion check
browser_completed_attempt = (
    result.data.get("task_complete", False) if result.data else False
)

if result.success:
    print_success("Browser task completed successfully")

    if browser_completed_attempt and not (analysis.requires_gui or analysis.requires_system):
        print_success("Task fully completed by Browser agent")
        return self._build_result(task, analysis, results, True)

elif browser_completed_attempt:
    # Partial success - agent tried but couldn't fully succeed
    print_warning("Browser completed attempt but couldn't fully succeed")

    if result.data and "output" in result.data:
        output_data = result.data["output"]
        browser_output = BrowserOutput(**output_data)
        print_info(f"Browser says: {browser_output.text}")

        if browser_output.has_files():
            print_info(f"Files available: {browser_output.get_file_count()} file(s)")
            for file_path in browser_output.files[:3]:
                console.print(f"  [dim]• {file_path}[/dim]")
    # Continue to GUI agent
else:
    print_failure(f"Browser task failed: {result.error or 'Unknown error'}")
    return self._build_result(task, analysis, results, False)
```

### Overall Success Check

```python
# Type-safe list comprehension
overall_success = all(r.success for r in results)
```

---

## GUI Agent Context Display

### Rich Context in Prompt

The GUI agent receives beautifully formatted context:

```
============================================================
PREVIOUS AGENT WORK (Build on this!):
============================================================

✅ Agent 1 (browser): Downloaded data from census.gov

📝 Summary:
Downloaded demographic data from census.gov

📁 DOWNLOADED FILES (use these paths!):
   • /tmp/browser_agent_abc/demographics_2024.csv

📊 File Details:
   • demographics_2024.csv (512.0 KB)
     Path: /tmp/browser_agent_abc/demographics_2024.csv

============================================================
🎯 YOUR JOB: Use the files/data above to complete the current task!
============================================================
```

### Context Generation Code

```python
if self.context and self.context.get("previous_results"):
    prev_results = self.context.get("previous_results", [])

    for i, res in enumerate(prev_results, 1):
        agent_type = res.get("method_used", "unknown")
        action = res.get("action_taken", "")
        success = "✅" if res.get("success") else "❌"

        previous_work_context += f"\n{success} Agent {i} ({agent_type}): {action}\n"

        if res.get("data"):
            data = res.get("data", {})
            output = data.get("output")

            if isinstance(output, dict):
                try:
                    browser_output = BrowserOutput(**output)
                    previous_work_context += f"\n📝 Summary:\n{browser_output.text}\n"

                    if browser_output.has_files():
                        previous_work_context += "\n📁 DOWNLOADED FILES (use these paths!):\n"
                        for file_path in browser_output.files:
                            previous_work_context += f"   • {file_path}\n"

                        previous_work_context += "\n📊 File Details:\n"
                        for file_detail in browser_output.file_details:
                            size_kb = file_detail.size / 1024
                            previous_work_context += f"   • {file_detail.name} ({size_kb:.1f} KB)\n"
                            previous_work_context += f"     Path: {file_detail.path}\n"
                except Exception:
                    # Fallback for non-BrowserOutput data
                    if output.get("text"):
                        previous_work_context += f"\n📝 Summary:\n{output['text']}\n"
```

---

## Example Workflows

### Case 1: Download & Process

```
Task: "Download sales data from company portal, create chart in Numbers"

1. Browser Agent:
   - Navigates to portal
   - Downloads sales_2024.csv to /tmp/browser_agent_xxx/
   - Calls done() with file path
   - Returns ActionResult with BrowserOutput

2. GUI Agent receives context:
   📁 DOWNLOADED FILES:
      • /tmp/browser_agent_xxx/sales_2024.csv (1.2 MB)

   🎯 YOUR JOB: Use the files above to complete the current task!

3. GUI Agent:
   - Opens Numbers app
   - Imports /tmp/browser_agent_xxx/sales_2024.csv
   - Creates formatted chart
```

### Case 2: Research & Document

```
Task: "Research fashion trends on census.gov, create presentation in Keynote"

1. Browser Agent:
   - Gathers census data
   - Downloads 3 demographic files
   - Calls done() with file list

2. GUI Agent:
   - Opens Keynote
   - Creates slides using census data
   - Formats presentation
```

### Case 3: Partial Success Handoff

```
Task: "Download report and email it"

1. Browser Agent:
   - Downloads report.pdf successfully
   - Can't find email interface in browser
   - Calls done() with: success=False, task_complete=True, files=[report.pdf]

2. GUI Agent:
   - Receives file path for report.pdf
   - Opens Mail app
   - Attaches report.pdf
   - Composes and sends email
```

---

## Benefits of Type Safety

| **Aspect**      | **Implementation**                     |
| --------------- | -------------------------------------- |
| Return Types    | `ActionResult` (Pydantic)              |
| Field Access    | Direct attributes (`result.success`)   |
| Type Checking   | Compile-time via mypy/IDE              |
| IDE Support     | Full autocomplete and refactoring      |
| Error Detection | Before runtime                         |
| Documentation   | Self-documenting schemas               |
| Maintenance     | Schema changes propagate automatically |
| Performance     | No repeated serialization              |

---

## Browser-Use Integration

### Typed API Usage

```python
from browser_use import Agent, BrowserSession, BrowserProfile
from browser_use.agent.views import AgentHistoryList

# Create and run agent
agent = Agent(
    task=full_task,
    llm=self.llm_client,
    browser_session=browser_session,
    max_failures=5,
)

result: AgentHistoryList = await agent.run(max_steps=30)

# Use typed API
agent_called_done = result.is_done()
task_completed_successfully = result.is_successful()
final_output = result.final_result()
error_list = result.errors()
```

**No More `hasattr` Checks**: Browser-Use provides clean typed interface.

---

## Future Enhancements

- [ ] Automatic file cleanup after task completion
- [ ] Cloud storage integration (S3, Google Drive)
- [ ] File type detection and preview generation
- [ ] Checksum verification for downloads
- [ ] Progress tracking for large downloads
- [ ] Persistent context across sessions
- [ ] Cost tracking per agent execution

---

**End of Documentation**
