# Inter-Agent Communication System

## Overview

The system now has robust inter-agent communication with proper data passing, file tracking, and context sharing between Browser, GUI, and System agents.

## Browser Agent → GUI/System Agent

### Data Structure

When the Browser agent completes, it returns a structured output:

```python
{
    "success": True/False,
    "message": "Browser task completed: ...",
    "data": {
        "result": str(AgentHistoryList),
        "output": {
            "text": "Summary of what was accomplished",
            "files": [
                "/path/to/downloaded/file1.csv",
                "/path/to/downloaded/file2.pdf",
            ],
            "file_details": [
                {
                    "path": "/absolute/path/to/file.csv",
                    "name": "file.csv",
                    "size": 12345  # bytes
                },
                ...
            ],
            "work_directory": "/tmp/browser_agent_xxx/"
        },
        "task_complete": True  # Whether agent called done
    }
}
```

### File Tracking

1. **Attachments**: Files explicitly attached by Browser-Use via `attachments` field
2. **Work Directory**: All files in `browseruse_agent_data/` subdirectory
3. **Absolute Paths**: All file paths are converted to absolute paths for easy access

### Example Workflow

**Task**: "Go to census.gov, download demographic data, then open Numbers and create a table"

```
1. Browser Agent:
   - Navigates to census.gov
   - Downloads CSV file
   - Returns:
     {
       "success": True,
       "data": {
         "output": {
           "text": "Downloaded demographic data from census.gov",
           "files": ["/tmp/browser_agent_abc123/data.csv"],
           "file_details": [{
             "name": "demographics_2024.csv",
             "path": "/tmp/browser_agent_abc123/data.csv",
             "size": 524288
           }]
         }
       }
     }

2. GUI Agent receives context:
   ============================================================
   PREVIOUS AGENT WORK (Build on this!):
   ============================================================

   ✅ Agent 1 (browser): Downloaded data

   📝 Summary:
   Downloaded demographic data from census.gov

   📁 DOWNLOADED FILES (use these paths!):
      • /tmp/browser_agent_abc123/data.csv

   📊 File Details:
      • demographics_2024.csv (512.0 KB)
        Path: /tmp/browser_agent_abc123/data.csv

   ============================================================
   🎯 YOUR JOB: Use the files/data above to complete the current task!
   ============================================================

3. GUI Agent:
   - Opens Numbers app
   - Imports /tmp/browser_agent_abc123/data.csv
   - Creates formatted table
```

## GUI Agent Context Display

The GUI agent now receives rich, structured context in its prompt:

### Before (Old System)

```
PREVIOUS AGENT WORK:
  ✅ Agent 1 (browser): Downloaded data
     Output: Some text
```

### After (New System)

```
============================================================
PREVIOUS AGENT WORK (Build on this!):
============================================================

✅ Agent 1 (browser): Downloaded data

📝 Summary:
Downloaded demographic data from census.gov

📁 DOWNLOADED FILES (use these paths!):
   • /tmp/browser_agent_abc123/demographics_2024.csv

📊 File Details:
   • demographics_2024.csv (512.0 KB)
     Path: /tmp/browser_agent_abc123/demographics_2024.csv

============================================================
🎯 YOUR JOB: Use the files/data above to complete the current task!
============================================================
```

## Crew Orchestrator Improvements

### Smart Handoff Detection

```python
browser_completed_attempt = result.get("data", {}).get("task_complete", False)

if result.get("success"):
    # Full success
    print_success("Browser task completed successfully")
elif browser_completed_attempt:
    # Partial success - agent tried but couldn't fully succeed
    print_warning("Browser completed attempt but couldn't fully succeed")
    print_info(f"Browser says: {output['text']}")
    print_info(f"Files available: {len(output['files'])} file(s)")
    # Continue to GUI agent ✅
else:
    # Complete failure - browser crashed/errored
    print_failure("Browser task failed")
    return failure
```

### Display Output

When browser completes with files:

```
⚠️  Browser completed attempt but couldn't fully succeed
ℹ️  Browser says: Downloaded data but couldn't find all requested information
ℹ️  Files available: 3 file(s)
    • /tmp/browser_agent_abc/file1.csv
    • /tmp/browser_agent_abc/file2.pdf
    • /tmp/browser_agent_abc/report.txt
```

## Type Safety

### Browser Tool (`browser_tool.py`)

Now uses proper Browser-Use types:

```python
from browser_use.agent.views import AgentHistoryList

result: AgentHistoryList = await agent.run()

# Typed API instead of hasattr checks
agent_called_done = result.is_done()
task_completed_successfully = result.is_successful()
final_output = result.final_result()
error_list = result.errors()
```

### Before (60+ lines of hasattr)

```python
if result and hasattr(result, "errors") and result.errors():
    has_errors = True
    ...
if result and hasattr(result, "history"):
    for item in result.history:
        if hasattr(item, "result") and item.result:
            ...
```

### After (15 clean lines)

```python
agent_called_done = result.is_done()
task_completed_successfully = result.is_successful()
final_output = result.final_result()
error_list = result.errors()
```

## Key Benefits

1. **File Tracking**: Downloaded files are properly tracked with absolute paths
2. **Structured Output**: Browser output is a typed dictionary, not a string
3. **Rich Context**: GUI agent receives formatted, easy-to-parse context
4. **Type Safety**: Using Browser-Use's typed API instead of manual parsing
5. **Smart Handoffs**: Distinguishes between full success, partial success, and failure
6. **Clear Instructions**: GUI agent gets explicit "here are the files, use them" messages

## Example Use Cases

### Case 1: Download & Process

```
Task: "Download sales data from company portal, create a chart in Numbers"

Browser → Downloads file to /tmp/browser_agent_xxx/sales_2024.csv
GUI → Opens Numbers, imports that exact file, creates chart
```

### Case 2: Research & Document

```
Task: "Research fashion trends on census.gov, create presentation in Keynote"

Browser → Gathers data, saves to /tmp/browser_agent_xxx/notes.txt
GUI → Opens Keynote, creates slides using notes.txt content
```

### Case 3: Partial Success Handoff

```
Task: "Download report and email it"

Browser → Downloads report but can't find email interface
         Returns: success=False, task_complete=True, files=[report.pdf]
GUI → Opens Mail app, attaches report.pdf, composes email
```

## Technical Implementation

### File Discovery Process

1. Check Browser-Use `attachments` field (explicitly marked files)
2. Scan `browseruse_agent_data/` directory (all created/downloaded files)
3. Convert all paths to absolute paths
4. Extract file metadata (name, size)
5. Package into structured output

### Context Passing

1. Browser agent completes → returns `ActionResult`
2. Crew calls `result.model_dump()` → dictionary
3. Dictionary added to `context["previous_results"]`
4. GUI agent receives context in `execute_task(task, context)`
5. GUI agent formats context into rich prompt for LLM
6. LLM sees clear file paths and instructions

## Future Improvements

- [ ] Automatic file cleanup after task completion
- [ ] Support for cloud storage (S3, Drive) integration
- [ ] File type detection and preview generation
- [ ] Checksum verification for downloaded files
- [ ] Progress tracking for large downloads
