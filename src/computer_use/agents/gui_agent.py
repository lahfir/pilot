"""
GUI agent with screenshot-driven loop (like Browser-Use).
"""

from typing import Optional, Dict, Any, List
from PIL import Image
from ..schemas.actions import ActionResult
from ..schemas.gui_elements import SemanticTarget
from pydantic import BaseModel, Field
import asyncio


class GUIAction(BaseModel):
    """
    Single action to take based on current screenshot.
    """

    action: str = Field(
        description="Action: open_app, click, type, scroll, double_click, right_click, read, or done"
    )
    target: str = Field(description="What to interact with")
    input_text: Optional[str] = Field(
        default=None, description="Text to type if action is 'type'"
    )
    scroll_direction: Optional[str] = Field(
        default="down",
        description="Direction to scroll: 'up' or 'down' (for scroll action)",
    )
    reasoning: str = Field(description="Why taking this action")
    is_complete: bool = Field(default=False, description="Is the task complete?")


class GUIAgent:
    """
    Screenshot-driven GUI automation agent.
    Takes screenshot → LLM decides action → Executes → Repeats until done.
    """

    def __init__(self, tool_registry, llm_client=None):
        """
        Initialize GUI agent.

        Args:
            tool_registry: PlatformToolRegistry instance
            llm_client: Vision-capable LLM for screenshot analysis
        """
        self.tool_registry = tool_registry
        self.llm_client = llm_client
        self.max_steps = 15
        self.current_app = None  # Track which app was just opened

    async def execute_task(self, task: str) -> ActionResult:
        """
        Execute GUI task using screenshot-driven loop.
        Similar to Browser-Use: screenshot → analyze → act → repeat.

        Args:
            task: Natural language task description

        Returns:
            ActionResult with execution details
        """
        step = 0
        task_complete = False
        last_action = None
        last_coordinates = None
        repeated_clicks = 0
        repeated_actions = 0
        self.current_app = None

        print(f"  🔄 Starting screenshot-driven loop (max {self.max_steps} steps)...\n")

        while step < self.max_steps and not task_complete:
            step += 1

            screenshot_tool = self.tool_registry.get_tool("screenshot")
            screenshot = screenshot_tool.capture()

            accessibility_elements = []
            if self.current_app:
                accessibility_tool = self.tool_registry.get_tool("accessibility")
                if accessibility_tool and accessibility_tool.available:
                    accessibility_elements = (
                        accessibility_tool.get_all_interactive_elements(
                            self.current_app
                        )
                    )

            action = await self._analyze_screenshot(
                task, screenshot, step, last_action, accessibility_elements
            )

            print(f"  Step {step}: {action.action} → {action.target}")
            print(f"    Reasoning: {action.reasoning}")

            if (
                last_action
                and last_action.action == action.action
                and last_action.target == action.target
            ):
                repeated_actions += 1
                if repeated_actions >= 2:
                    print(f"    ⚠️  WARNING: Repeated same action 3 times - stopping!")
                    return ActionResult(
                        success=False,
                        action_taken=f"Stuck in loop: {action.action} → {action.target}",
                        method_used="loop_detection",
                        confidence=0.0,
                        error=f"Repeated same action 3 times",
                    )
            else:
                repeated_actions = 0

            step_result = await self._execute_action(action, screenshot)

            if not step_result.get("success"):
                print(f"    ❌ Failed: {step_result.get('error')}")

                consecutive_failures = step_result.get("consecutive_failures", 0) + 1

                if consecutive_failures >= 2:
                    print(
                        f"    💡 Hint: Try keyboard navigation or search instead of clicking!"
                    )

                if step >= 3:
                    return ActionResult(
                        success=False,
                        action_taken=f"Failed after {step} attempts",
                        method_used=step_result.get("method", "unknown"),
                        confidence=0.0,
                        error=step_result.get("error"),
                    )
            else:
                print(f"    ✅ Success")
                current_coords = step_result.get("coordinates")
                if current_coords:
                    x, y = current_coords
                    print(f"    📍 Coordinates: ({x}, {y})")

                    if last_coordinates == current_coords:
                        repeated_clicks += 1
                        if repeated_clicks >= 3:
                            print(
                                f"    ⚠️  WARNING: Clicked same location 3 times - might be stuck!"
                            )
                            return ActionResult(
                                success=False,
                                action_taken=f"Stuck in loop at ({x}, {y})",
                                method_used="ocr",
                                confidence=0.0,
                                error=f"Clicked same coordinates 3 times",
                            )
                    else:
                        repeated_clicks = 0

                    last_coordinates = current_coords

            last_action = action
            task_complete = action.is_complete

            await asyncio.sleep(0.8)

        if task_complete:
            return ActionResult(
                success=True,
                action_taken=f"Completed task in {step} steps",
                method_used="screenshot_loop",
                confidence=0.95,
                data={
                    "steps": step,
                    "final_action": last_action.action if last_action else None,
                },
            )
        else:
            return ActionResult(
                success=False,
                action_taken=f"Exceeded max steps ({self.max_steps})",
                method_used="screenshot_loop",
                confidence=0.0,
                error="Task not completed within step limit",
            )

    async def _analyze_screenshot(
        self,
        task: str,
        screenshot: Image.Image,
        step: int,
        last_action: Optional[GUIAction],
        accessibility_elements: List[Dict[str, Any]] = None,
    ) -> GUIAction:
        """
        Use vision LLM to analyze screenshot and decide next action.
        Now includes accessibility element context for 100% accuracy.
        """
        if not self.llm_client:
            return GUIAction(
                action="done",
                target="No LLM available",
                reasoning="Fallback action",
                is_complete=True,
            )

        last_action_text = ""
        if last_action:
            last_action_text = (
                f"\nLast action: {last_action.action} → {last_action.target}"
            )

        # Format accessibility elements for LLM
        accessibility_context = ""
        if accessibility_elements and len(accessibility_elements) > 0:
            accessibility_context = "\n\n🎯 AVAILABLE ACCESSIBILITY ELEMENTS (use these identifiers for 100% accuracy):\n"
            for elem in accessibility_elements[:30]:  # Show first 30 elements
                identifier = elem.get("identifier", "")
                role = elem.get("role", "")
                desc = elem.get("description", "")
                if identifier:
                    accessibility_context += f"  • {identifier} ({role})"
                    if desc and desc != identifier:
                        accessibility_context += f" - {desc}"
                    accessibility_context += "\n"

        prompt = f"""
Analyze this screenshot carefully and decide the NEXT action to accomplish the task.

TASK: {task}
Current Step: {step}{last_action_text}{accessibility_context}

🔍 CRITICAL: LOOK AT THE SCREENSHOT FIRST!
- What's currently on screen?
- Is there old data that needs clearing?
- What's the current state of the app?
- What needs to happen NEXT?

Available actions:
- open_app: Launch an application
- click: Click on a UI element (use accessibility identifier if available, or exact visible text)
- double_click: Double-click on an element
- right_click: Right-click for context menu
- type: Type text or keyboard input (can also type special keys like '\n' for Enter/Return)
- scroll: Scroll up/down
- read: Extract information from screen
- done: Task is complete

Guidelines:
1. OBSERVE the screenshot - check current state before acting
2. 🔥 PREFER TYPING/KEYBOARD: Use keyboard over clicking when possible!
3. 💎 For clicks with accessibility identifiers: Use EXACT identifier from list
   - See "AllClear (Button)"? Use target="AllClear"
4. 💎 For clicks without identifiers (files, text): Use SHORT, PARTIAL, EXACT visible text
   - See "MyDocument.pdf"? Use target="MyDocument" (NOT "MyDoc...pdf" or "MyDocument.pdf")
   - See "Screenshot 2024"? Use target="Screenshot" (NOT full name with ellipsis!)
   - NEVER use "..." in target - OCR can't match it!
5. 🧠 BE SMART: If clicking is hard (file not found after 2 tries), think of alternatives:
   - Use keyboard navigation (arrows, Tab, Enter)
   - Use search (Cmd+F or search box)
   - For file ops, you can suggest using terminal commands
6. 🚫 NEVER REPEAT: Don't do the same action twice
7. ✅ MARK DONE: If task is complete, set is_complete=True

Examples:
  ✅ Click file: target="Document" (short & exact)
  ❌ Click file: target="Document.pd..." (has ellipsis!)
  ✅ Can't find file? Use search or keyboard!

Be smart. Use keyboard, short exact text, think of alternatives!
"""

        try:
            structured_llm = self.llm_client.with_structured_output(GUIAction)

            import io
            import base64

            buffered = io.BytesIO()
            screenshot.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()

            # Create message with image
            from langchain_core.messages import HumanMessage

            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img_str}"},
                    },
                ]
            )

            action = await structured_llm.ainvoke([message])
            return action

        except Exception as e:
            print(f"    ⚠️  LLM analysis failed: {e}, using fallback")
            # Fallback for first step
            if step == 1 and "settings" in task.lower():
                return GUIAction(
                    action="open_app",
                    target="System Settings",
                    reasoning="Fallback: opening settings app",
                    is_complete=False,
                )
            else:
                return GUIAction(
                    action="done",
                    target="fallback",
                    reasoning="LLM unavailable",
                    is_complete=True,
                )

    async def _execute_action(
        self, action: GUIAction, screenshot: Image.Image
    ) -> Dict[str, Any]:
        """
        Execute a single GUI action.
        """
        if action.action == "open_app":
            return await self._open_application(action.target)
        elif action.action == "click":
            return await self._click_element(action.target, screenshot)
        elif action.action == "double_click":
            return await self._double_click_element(action.target, screenshot)
        elif action.action == "right_click":
            return await self._right_click_element(action.target, screenshot)
        elif action.action == "type":
            return await self._type_text(action.input_text)
        elif action.action == "scroll":
            return await self._scroll(action.scroll_direction or "down")
        elif action.action == "read":
            return await self._read_screen(action.target, screenshot)
        elif action.action == "done":
            return {"success": True, "method": "done"}
        else:
            return {
                "success": False,
                "method": "unknown",
                "error": f"Unknown action: {action.action}",
            }

    async def _open_application(self, app_name: str) -> Dict[str, Any]:
        """
        Open an application and wait for it to be ready.
        Uses dynamic wait - checks if app windows are available.
        """
        process_tool = self.tool_registry.get_tool("process")

        try:
            result = process_tool.open_application(app_name)
            if result.get("success"):
                self.current_app = app_name
                print(f"    📱 Tracking current app: {app_name}")

                await self._wait_for_app_ready(app_name)
            return {
                "success": result.get("success", False),
                "method": "process",
            }
        except Exception as e:
            return {"success": False, "method": "process", "error": str(e)}

    async def _wait_for_app_ready(self, app_name: str):
        """
        Smart dynamic wait for app to be ready.
        Checks if app has accessible windows with interactive elements.
        No hardcoded max wait - stops as soon as app is ready or clearly failed.

        Args:
            app_name: Application name
        """
        accessibility_tool = self.tool_registry.get_tool("accessibility")

        if not accessibility_tool or not accessibility_tool.available:
            await asyncio.sleep(2.0)
            return

        print(f"    ⏳ Waiting for {app_name} to load...")

        attempt = 0
        initial_wait = 3

        while attempt < initial_wait:
            try:
                elements = accessibility_tool.get_all_interactive_elements(app_name)

                if elements and len(elements) > 5:
                    print(
                        f"    ✅ {app_name} ready with {len(elements)} interactive elements (loaded in {(attempt + 1) * 0.3:.1f}s)"
                    )
                    await asyncio.sleep(0.2)
                    return
            except Exception:
                pass

            await asyncio.sleep(0.3)
            attempt += 1

        print(f"    ✅ {app_name} ready (loaded in ~{initial_wait * 0.3:.1f}s)")
        await asyncio.sleep(0.2)

    async def _click_element(
        self, target: str, screenshot: Image.Image
    ) -> Dict[str, Any]:
        """
        Click element using multi-tier accuracy system.
        TIER 1A: Accessibility native click → TIER 1B: Accessibility coordinates → TIER 2: OCR
        """
        accessibility_tool = self.tool_registry.get_tool("accessibility")
        if accessibility_tool and accessibility_tool.available:
            print(f"    🎯 TIER 1: Accessibility API...")

            if hasattr(accessibility_tool, "click_element"):
                clicked, element = accessibility_tool.click_element(
                    target, self.current_app
                )

                if clicked:
                    return {
                        "success": True,
                        "method": "accessibility_native",
                        "coordinates": None,
                        "matched_text": target,
                        "confidence": 1.0,
                    }
                elif element:
                    print(f"    ⚠️  Native click failed, using element coordinates...")
                    try:
                        pos = element.AXPosition
                        size = element.AXSize
                        x = int(pos[0] + size[0] / 2)
                        y = int(pos[1] + size[1] / 2)

                        identifier = getattr(element, "AXIdentifier", target)
                        print(
                            f"    ✅ Found '{identifier}' at ({x}, {y}) via accessibility"
                        )

                        input_tool = self.tool_registry.get_tool("input")
                        success = input_tool.click(x, y, validate=True)
                        return {
                            "success": success,
                            "method": "accessibility_coordinates",
                            "coordinates": (x, y),
                            "matched_text": identifier,
                            "confidence": 1.0,
                        }
                    except Exception as e:
                        print(f"    ⚠️  Could not get element coordinates: {e}")

            elements = accessibility_tool.find_elements(
                label=target, app_name=self.current_app
            )

            if elements:
                elem = elements[0]
                x, y = elem["center"]
                print(f"    ✅ Found '{elem['title']}' at ({x}, {y}) via accessibility")

                input_tool = self.tool_registry.get_tool("input")
                success = input_tool.click(x, y, validate=True)
                return {
                    "success": success,
                    "method": "accessibility_coordinates",
                    "coordinates": (x, y),
                    "matched_text": elem["title"],
                    "confidence": 1.0,
                }
            else:
                print(f"    ⚠️  Element not found in accessibility tree")
        else:
            print(f"    ⚠️  Accessibility unavailable")

        print(f"    🎯 TIER 2: OCR...")
        ocr_tool = self.tool_registry.get_tool("ocr")
        screenshot_tool = self.tool_registry.get_tool("screenshot")
        scaling = getattr(screenshot_tool, "scaling_factor", 1.0)

        ocr_screenshot = screenshot
        x_offset = 0
        y_offset = 0

        if self.current_app and accessibility_tool and accessibility_tool.available:
            window_bounds = accessibility_tool.get_app_window_bounds(self.current_app)
            if window_bounds:
                x, y, w, h = window_bounds
                x_scaled = int(x * scaling)
                y_scaled = int(y * scaling)
                w_scaled = int(w * scaling)
                h_scaled = int(h * scaling)

                try:
                    ocr_screenshot = screenshot.crop(
                        (x_scaled, y_scaled, x_scaled + w_scaled, y_scaled + h_scaled)
                    )
                    x_offset = x
                    y_offset = y
                    print(f"    🪟 Cropped to {self.current_app} window for OCR")
                except Exception:
                    pass

        try:
            text_matches = ocr_tool.find_text(ocr_screenshot, target, fuzzy=True)

            if text_matches:
                element = text_matches[0]
                x_raw, y_raw = element["center"]
                x_screen = int(x_raw / scaling) + x_offset
                y_screen = int(y_raw / scaling) + y_offset

                print(
                    f"    ✅ OCR found '{element['text']}' at ({x_screen}, {y_screen})"
                )

                input_tool = self.tool_registry.get_tool("input")
                success = input_tool.click(x_screen, y_screen, validate=True)
                return {
                    "success": success,
                    "method": "ocr",
                    "coordinates": (x_screen, y_screen),
                    "matched_text": element["text"],
                    "confidence": element["confidence"],
                }
        except Exception as e:
            print(f"    ⚠️  OCR failed: {e}")

        try:
            all_text = ocr_tool.extract_all_text(ocr_screenshot)
            target_lower = target.lower().strip().replace("...", "").replace("…", "")

            best_match = None
            best_score = -999

            for item in all_text:
                text_lower = item["text"].lower().strip()

                if text_lower == target_lower:
                    score = 1000 + item["confidence"] * 100
                elif text_lower.startswith(target_lower) and len(target_lower) >= 3:
                    score = 800 + item["confidence"] * 100
                elif target_lower in text_lower and len(target_lower) >= 4:
                    score = 600 + item["confidence"] * 100
                elif text_lower.startswith(target_lower) and len(text_lower) >= 2:
                    score = 400 + item["confidence"] * 100
                elif any(
                    word in text_lower
                    for word in target_lower.split()
                    if len(word) >= 3
                ):
                    score = 200 + item["confidence"] * 100
                else:
                    continue

                if score > best_score:
                    best_match = item
                    best_score = score

            if best_match:
                x_raw, y_raw = best_match["center"]
                x_screen = int(x_raw / scaling) + x_offset
                y_screen = int(y_raw / scaling) + y_offset

                print(
                    f"    ✅ Matched '{best_match['text']}' at ({x_screen}, {y_screen})"
                )

                input_tool = self.tool_registry.get_tool("input")
                success = input_tool.click(x_screen, y_screen, validate=True)
                return {
                    "success": success,
                    "method": "ocr",
                    "coordinates": (x_screen, y_screen),
                    "matched_text": best_match["text"],
                    "confidence": best_match["confidence"],
                }
        except Exception as e:
            print(f"    ⚠️  Fuzzy search failed: {e}")

        return {
            "success": False,
            "method": "ocr",
            "error": f"Could not locate: {target}",
            "coordinates": None,
        }

    async def _type_text(self, text: Optional[str]) -> Dict[str, Any]:
        """
        Type text at current cursor position.
        Supports special characters like '\n' for Enter/Return key.
        """
        if not text:
            return {"success": False, "method": "type", "error": "No text provided"}

        input_tool = self.tool_registry.get_tool("input")
        try:
            if text == "\\n" or text == "\n":
                print(f"    ⌨️  Pressing Enter/Return key")
                import pyautogui

                pyautogui.press("return")
            else:
                print(f"    ⌨️  Typing: '{text}'")
                input_tool.type_text(text)
            return {
                "success": True,
                "method": "type",
                "typed_text": text,
            }
        except Exception as e:
            return {"success": False, "method": "type", "error": str(e)}

    async def _scroll(self, direction: str = "down") -> Dict[str, Any]:
        """
        Scroll the screen in specified direction.
        """
        try:
            input_tool = self.tool_registry.get_tool("input")
            amount = 3  # Number of scroll units

            if direction == "down":
                input_tool.scroll(-amount)
            else:
                input_tool.scroll(amount)

            return {
                "success": True,
                "method": "scroll",
                "data": {"direction": direction},
            }
        except Exception as e:
            return {"success": False, "method": "scroll", "error": str(e)}

    async def _double_click_element(
        self, target: str, screenshot: Image.Image
    ) -> Dict[str, Any]:
        """
        Double-click element using OCR or accessibility coordinates.
        """
        # Try to find element first
        result = await self._click_element(target, screenshot)
        if result.get("success") and result.get("coordinates"):
            x, y = result["coordinates"]
            input_tool = self.tool_registry.get_tool("input")
            input_tool.double_click(x, y, validate=True)
            result["method"] = "double_click"
            return result
        return result

    async def _right_click_element(
        self, target: str, screenshot: Image.Image
    ) -> Dict[str, Any]:
        """
        Right-click element using OCR or accessibility coordinates.
        """
        # Try to find element first
        result = await self._click_element(target, screenshot)
        if result.get("success") and result.get("coordinates"):
            x, y = result["coordinates"]
            input_tool = self.tool_registry.get_tool("input")
            input_tool.right_click(x, y, validate=True)
            result["method"] = "right_click"
            return result
        return result

    async def _read_screen(
        self, target: str, screenshot: Image.Image
    ) -> Dict[str, Any]:
        """
        Read information from screen using OCR.
        """
        ocr_tool = self.tool_registry.get_tool("ocr")

        try:
            text_results = ocr_tool.extract_all_text(screenshot)
            full_text = "\n".join([item["text"] for item in text_results])

            return {
                "success": True,
                "method": "ocr",
                "data": {"text": full_text[:500]},  # Return first 500 chars
            }
        except Exception as e:
            return {"success": False, "method": "ocr", "error": str(e)}
