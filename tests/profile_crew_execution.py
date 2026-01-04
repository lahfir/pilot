"""
Profiling script for CrewAI GUI Agent execution.
Traces all LLM calls, tool calls, timing, and outputs.
"""

import asyncio
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List

os.environ["CREWAI_TELEMETRY"] = "false"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ExecutionProfiler:
    """Profiles all calls during crew execution."""

    def __init__(self):
        self.start_time = None
        self.last_event_time = None
        self.tool_calls: List[Dict[str, Any]] = []
        self.llm_calls: List[Dict[str, Any]] = []
        self.events: List[Dict[str, Any]] = []

    def log_tool(self, name: str, duration: float, inputs: str, output: str):
        """Log a tool call."""
        now = time.time()
        gap = now - self.last_event_time if self.last_event_time else 0
        self.last_event_time = now

        entry = {
            "type": "tool",
            "name": name,
            "duration": duration,
            "gap_before": gap - duration,
            "timestamp": now - self.start_time if self.start_time else 0,
            "inputs": inputs,
            "output": output,
        }
        self.tool_calls.append(entry)
        self.events.append(entry)

    def log_llm(self, duration: float, prompt_len: int, response_len: int):
        """Log an LLM call."""
        now = time.time()
        gap = now - self.last_event_time if self.last_event_time else 0
        self.last_event_time = now

        entry = {
            "type": "llm",
            "duration": duration,
            "gap_before": gap - duration,
            "timestamp": now - self.start_time if self.start_time else 0,
            "prompt_len": prompt_len,
            "response_len": response_len,
        }
        self.llm_calls.append(entry)
        self.events.append(entry)

    def start(self):
        """Start profiling."""
        self.start_time = time.time()
        self.last_event_time = time.time()
        self.tool_calls = []
        self.llm_calls = []
        self.events = []

    def print_summary(self):
        """Print profiling summary."""
        total_time = time.time() - self.start_time if self.start_time else 0

        print("\n" + "=" * 80)
        print("EXECUTION PROFILE SUMMARY")
        print("=" * 80)

        print(f"\nTotal execution time: {total_time:.2f}s")

        tool_time = sum(c["duration"] for c in self.tool_calls)
        llm_time = sum(c["duration"] for c in self.llm_calls)
        gap_time = sum(max(0, c.get("gap_before", 0)) for c in self.events)

        print(f"\nTOOL CALLS: {len(self.tool_calls)}, Total time: {tool_time:.2f}s")
        print(f"LLM CALLS: {len(self.llm_calls)}, Total time: {llm_time:.2f}s")
        print(f"GAP TIME (overhead/waiting): {gap_time:.2f}s")
        print(f"ACCOUNTED: {tool_time + llm_time + gap_time:.2f}s / {total_time:.2f}s")

        print("\n--- EVENT TIMELINE ---")
        for i, event in enumerate(self.events):
            ts = event["timestamp"]
            dur = event["duration"]
            gap = event.get("gap_before", 0)

            if gap > 0.5:
                print(f"  ... [{gap:.2f}s GAP/WAITING] ...")

            if event["type"] == "llm":
                print(
                    f"  @{ts:6.1f}s | LLM [{dur:.2f}s] "
                    f"prompt={event['prompt_len']} -> response={event['response_len']}"
                )
            else:
                print(f"  @{ts:6.1f}s | TOOL [{dur:.2f}s] {event['name']}")

        print("\n--- SLOWEST OPERATIONS ---")
        sorted_events = sorted(self.events, key=lambda x: x["duration"], reverse=True)
        for event in sorted_events[:10]:
            if event["type"] == "llm":
                print(f"  [{event['duration']:.2f}s] LLM call")
            else:
                print(f"  [{event['duration']:.2f}s] {event['name']}")

        print("\n--- LARGEST GAPS (overhead/coordination) ---")
        sorted_gaps = sorted(
            self.events, key=lambda x: x.get("gap_before", 0), reverse=True
        )
        for event in sorted_gaps[:5]:
            gap = event.get("gap_before", 0)
            if gap > 0.1:
                name = event["name"] if event["type"] == "tool" else "LLM"
                print(f"  [{gap:.2f}s] before {name}")

        print("\n" + "=" * 80)


profiler = ExecutionProfiler()


def patch_gui_tools(gui_tools: Dict[str, Any]):
    """Patch all GUI tools to log executions."""
    for tool_name, tool in gui_tools.items():
        if hasattr(tool, "_run"):
            original_run = tool._run

            def make_traced_run(name, orig):
                def traced_run(*args, **kwargs):
                    print(f"\n{'='*60}")
                    print(f">>> TOOL START: {name}")
                    print(f"    Args: {args}")
                    print(f"    Kwargs: {kwargs}")
                    sys.stdout.flush()

                    start = time.time()
                    try:
                        result = orig(*args, **kwargs)
                        duration = time.time() - start

                        success = getattr(result, "success", None)
                        action = getattr(result, "action_taken", None)
                        data = getattr(result, "data", None)
                        error = getattr(result, "error", None)

                        print(f"<<< TOOL END: {name} [{duration:.2f}s]")
                        print(f"    Success: {success}")
                        print(f"    Action: {action}")
                        if data:
                            print(f"    Data: {str(data)[:300]}")
                        if error:
                            print(f"    Error: {error}")
                        print(f"{'='*60}")
                        sys.stdout.flush()

                        profiler.log_tool(
                            name,
                            duration,
                            f"args={args}, kwargs={kwargs}",
                            f"success={success}, action={action}",
                        )
                        return result
                    except Exception as e:
                        duration = time.time() - start
                        print(f"<<< TOOL ERROR: {name} [{duration:.2f}s] - {e}")
                        print(f"{'='*60}")
                        sys.stdout.flush()
                        profiler.log_tool(name, duration, str(kwargs), f"error={e}")
                        raise

                return traced_run

            tool._run = make_traced_run(tool_name, original_run)
            print(f"[PROFILER] Patched {tool_name}")


def patch_llm_calls():
    """Patch LiteLLM's completion function to log all LLM calls."""
    patched = False

    try:
        import litellm

        original_completion = litellm.completion

        def traced_completion(*args, **kwargs):
            model = kwargs.get("model", args[0] if args else "unknown")
            messages = kwargs.get("messages", args[1] if len(args) > 1 else [])

            if isinstance(messages, list):
                prompt_len = sum(len(str(m.get("content", ""))) for m in messages)
                msg_count = len(messages)
                last_msg = (
                    str(messages[-1].get("content", ""))[:400] if messages else ""
                )
            else:
                prompt_len = len(str(messages))
                msg_count = 1
                last_msg = str(messages)[:400]

            print(f"\n{'*'*60}")
            print(f">>> LLM CALL START (litellm.completion)")
            print(f"    Model: {model}")
            print(f"    Messages: {msg_count}")
            print(f"    Prompt length: {prompt_len} chars")
            print(f"    Last message preview:")
            for line in last_msg.split("\n")[:3]:
                print(f"      {line[:120]}")
            sys.stdout.flush()

            start = time.time()
            result = original_completion(*args, **kwargs)
            duration = time.time() - start

            response_text = ""
            if hasattr(result, "choices") and result.choices:
                choice = result.choices[0]
                if hasattr(choice, "message") and choice.message:
                    response_text = str(choice.message.content or "")
            response_len = len(response_text)

            print(f"<<< LLM CALL END [{duration:.2f}s]")
            print(f"    Response length: {response_len} chars")
            print(f"    Response preview:")
            for line in response_text[:600].split("\n")[:5]:
                print(f"      {line[:120]}")
            print(f"{'*'*60}")
            sys.stdout.flush()

            profiler.log_llm(duration, prompt_len, response_len)
            return result

        litellm.completion = traced_completion
        print("[PROFILER] Patched litellm.completion")
        patched = True

    except Exception as e:
        print(f"[PROFILER] Could not patch litellm: {e}")

    try:
        from crewai import LLM

        original_call = LLM.call

        def traced_call(self, messages, *args, **kwargs):
            model = getattr(self, "model", "unknown")

            if isinstance(messages, str):
                prompt_len = len(messages)
                last_msg = messages[:300]
            else:
                prompt_len = sum(len(str(m.get("content", ""))) for m in messages)
                last_msg = (
                    str(messages[-1].get("content", ""))[:300] if messages else ""
                )

            print(f"\n{'#'*60}")
            print(f">>> CREWAI LLM.call START")
            print(f"    Model: {model}")
            print(f"    Prompt length: {prompt_len} chars")
            sys.stdout.flush()

            start = time.time()
            result = original_call(self, messages, *args, **kwargs)
            duration = time.time() - start

            response_text = str(result) if result else ""
            response_len = len(response_text)

            print(f"<<< CREWAI LLM.call END [{duration:.2f}s]")
            print(f"    Response length: {response_len} chars")
            print(f"{'#'*60}")
            sys.stdout.flush()

            if not patched:
                profiler.log_llm(duration, prompt_len, response_len)
            return result

        LLM.call = traced_call
        print("[PROFILER] Patched crewai.LLM.call")

    except Exception as e:
        print(f"[PROFILER] Could not patch CrewAI LLM: {e}")


async def run_profiled_task(task: str):
    """Run a task with full profiling."""
    import logging

    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    print("=" * 80)
    print(f"PROFILING TASK: {task}")
    print("=" * 80)
    print(f"Started at: {datetime.now().isoformat()}")
    print()

    print("[PROFILER] Patching LLM...")
    patch_llm_calls()

    from computer_use.crew import ComputerUseCrew
    from computer_use.utils.platform_detector import detect_platform
    from computer_use.utils.safety_checker import SafetyChecker

    capabilities = detect_platform()
    safety_checker = SafetyChecker()

    crew = ComputerUseCrew(
        capabilities=capabilities,
        safety_checker=safety_checker,
    )

    print("[PROFILER] Patching GUI tools...")
    patch_gui_tools(crew.gui_tools)

    profiler.start()

    print("\n--- STARTING CREW EXECUTION ---\n")
    sys.stdout.flush()

    try:
        result = await crew.execute_task(task)
        print("\n--- CREW EXECUTION COMPLETE ---\n")
        print(f"Result: {result}")
    except KeyboardInterrupt:
        print("\n--- EXECUTION INTERRUPTED ---\n")
    except Exception as e:
        print(f"\n--- EXECUTION ERROR: {e} ---\n")
        import traceback

        traceback.print_exc()

    profiler.print_summary()


if __name__ == "__main__":
    task = (
        "Send /tmp/browser-use-downloads-8d1e9868/Heir-of-Fire-By-Sarah-J-Maas.pdf "
        "to Dr.Pondatti using Messages"
    )

    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])

    asyncio.run(run_profiled_task(task))
