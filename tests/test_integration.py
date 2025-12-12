"""
Integration tests - test complete workflows end-to-end.
"""

import platform
import pytest
import time


class TestIntegration:
    """Integration tests for complete workflows."""

    @pytest.mark.skipif(
        platform.system().lower() != "darwin", reason="macOS specific test"
    )
    def test_complete_finder_workflow(self):
        """
        Test complete workflow: Focus Finder → Screenshot → OCR → Verify content.

        This is the most critical integration test.
        """
        print("\n" + "=" * 80)
        print("🔍 INTEGRATION TEST: COMPLETE FINDER WORKFLOW")
        print("=" * 80)

        from computer_use.tools.process_tool import ProcessTool
        from computer_use.tools.screenshot_tool import ScreenshotTool
        from computer_use.tools.vision.ocr_tool import OCRTool

        # Step 1: Focus Finder
        print("\nSTEP 1: Focus Finder")
        print("-" * 40)
        process_tool = ProcessTool()
        result = process_tool.open_application("Finder")

        print(f"   Focus result: {result}")
        assert result["success"], "Failed to focus Finder"
        time.sleep(1)

        # Step 2: Capture window
        print("\nSTEP 2: Capture Finder window")
        print("-" * 40)
        screenshot_tool = ScreenshotTool()

        try:
            screenshot, metadata = screenshot_tool.capture_active_window("Finder")
            print(f"   ✅ Captured: {screenshot.size}")
            print(f"   Metadata: {metadata}")
        except Exception as e:
            pytest.fail(f"❌ Screenshot failed: {e}")

        # Step 3: Run OCR
        print("\nSTEP 3: Run OCR on captured window")
        print("-" * 40)
        ocr_tool = OCRTool()
        results = ocr_tool.extract_all_text(screenshot)

        print(f"   Found {len(results)} text items")

        if not results:
            pytest.fail("❌ OCR returned no results")

        text = " ".join([item.text for item in results])
        print(f"   Text preview: {text[:200]}...")

        # Step 4: Verify content is Finder-related
        print("\nSTEP 4: Verify content is from Finder")
        print("-" * 40)
        finder_keywords = ["Recents", "Downloads", "Documents", "Applications"]
        matches = [kw for kw in finder_keywords if kw in text]

        print(f"   Finder keywords found: {matches}")

        if matches:
            print("✅ Content verified as Finder!")
        else:
            print("⚠️  WARNING: No Finder keywords found")
            print(f"   Full text: {text}")

        print("\n" + "=" * 80)
        print("✅ INTEGRATION TEST COMPLETE")
        print("=" * 80)

    @pytest.mark.skipif(
        platform.system().lower() != "darwin", reason="macOS specific test"
    )
    def test_read_screen_text_tool_integration(self):
        """
        Test the actual read_screen_text tool that the agent uses.

        This simulates exactly what the agent does.
        """
        print("\n" + "=" * 80)
        print("🔍 INTEGRATION TEST: READ_SCREEN_TEXT TOOL")
        print("=" * 80)

        # Check if CrewAI is available
        try:
            import crewai  # noqa: F401
        except ImportError:
            pytest.skip(
                "CrewAI not available in test environment - skipping integration test"
            )

        from computer_use.crew_tools.gui_basic_tools import (
            ReadScreenTextTool,
            OpenApplicationTool,
        )
        from computer_use.tool_registry import ToolRegistry

        # Initialize registry and tools
        registry = ToolRegistry()
        open_tool = OpenApplicationTool(registry)
        read_tool = ReadScreenTextTool(registry)

        # Step 1: Open Finder
        print("\nSTEP 1: Open Finder")
        result = open_tool._run(app_name="Finder")
        print(f"   Result: {result.success}")
        assert result.success, "Failed to open Finder"
        time.sleep(1)

        # Step 2: Read screen text
        print("\nSTEP 2: Read screen text")
        result = read_tool._run(app_name="Finder")

        print(f"   Success: {result.success}")
        print(f"   Action: {result.action_taken}")

        if result.success:
            print(f"   ✅ Read succeeded!")
            if result.data and "text" in result.data:
                text = result.data["text"]
                print(f"   Text length: {len(text)} chars")
                print(f"   Preview: {text[:200]}...")
        else:
            print(f"   ❌ Read failed: {result.error}")
            pytest.fail(f"read_screen_text failed: {result.error}")

        print("\n" + "=" * 80)
        print("✅ READ_SCREEN_TEXT TEST COMPLETE")
        print("=" * 80)

    @pytest.mark.skipif(
        platform.system().lower() != "darwin", reason="macOS specific test"
    )
    def test_accessibility_vs_ocr_click_fallback(self):
        """
        Test if click tool correctly falls back from accessibility to OCR.

        This verifies the multi-tier clicking system.
        """
        print("\n" + "=" * 80)
        print("🔍 INTEGRATION TEST: MULTI-TIER CLICK SYSTEM")
        print("=" * 80)

        # Check if CrewAI is available
        try:
            import crewai  # noqa: F401
        except ImportError:
            pytest.skip(
                "CrewAI not available in test environment - skipping integration test"
            )

        from computer_use.crew_tools.gui_basic_tools import (
            ClickElementTool,
            OpenApplicationTool,
        )
        from computer_use.tool_registry import ToolRegistry
        from computer_use.tools.accessibility.macos_accessibility import (
            MacOSAccessibility,
        )

        # Check if accessibility is available
        acc = MacOSAccessibility()
        print(f"\n📋 Accessibility Status: {acc.available}")

        # Initialize tools
        registry = ToolRegistry()
        open_tool = OpenApplicationTool(registry)
        click_tool = ClickElementTool(registry)

        # Open Finder
        print("\nSTEP 1: Open Finder")
        result = open_tool._run(app_name="Finder")
        assert result.success
        time.sleep(1)

        # Try to click "Documents"
        print("\nSTEP 2: Try to click 'Documents'")
        result = click_tool._run(
            target="Documents", click_type="single", current_app="Finder"
        )

        print(f"   Success: {result.success}")
        print(f"   Method: {result.method_used}")

        if acc.available:
            if "accessibility" in result.method_used.lower():
                print("   ✅ Used Accessibility API (best accuracy)")
            elif "ocr" in result.method_used.lower():
                print(
                    "   ⚠️  Used OCR fallback (accessibility was available but failed)"
                )
        else:
            if "ocr" in result.method_used.lower():
                print("   ✅ Used OCR fallback (accessibility not available)")
            else:
                print("   ⚠️  Unexpected method")

        print("\n" + "=" * 80)
        print("✅ MULTI-TIER CLICK TEST COMPLETE")
        print("=" * 80)

    def test_ocr_engine_selection_integration(self):
        """
        Test which OCR engine is actually selected and used.
        """
        print("\n" + "=" * 80)
        print("🔍 INTEGRATION TEST: OCR ENGINE SELECTION")
        print("=" * 80)

        from computer_use.tools.vision.ocr_factory import create_ocr_engine
        from PIL import Image, ImageDraw

        # Create test image
        img = Image.new("RGB", (400, 100), color="white")
        draw = ImageDraw.Draw(img)
        draw.text((50, 30), "TEST TEXT", fill="black")

        # Get selected engine
        print("\nSTEP 1: Get OCR engine from factory")
        engine = create_ocr_engine()

        if not engine:
            pytest.fail("❌ No OCR engine created")

        engine_name = engine.__class__.__name__
        print(f"   Selected: {engine_name}")

        # Test it
        print("\nSTEP 2: Test OCR on simple image")
        results = engine.recognize_text(img)

        print(f"   Results: {len(results)} items")
        if results:
            text = " ".join([r.text for r in results])
            print(f"   Text: {text}")
            print(f"   ✅ {engine_name} works!")
        else:
            print(f"   ⚠️  {engine_name} returned no results")

        # Check if it's Vision or fallback
        if platform.system().lower() == "darwin":
            if "Vision" in engine_name:
                print("\n✅ Using native Vision Framework (optimal)")
            else:
                print(f"\n⚠️  WARNING: Using {engine_name} instead of Vision")
                print("   This might be slower and less accurate")

        print("\n" + "=" * 80)
        print("✅ OCR ENGINE SELECTION TEST COMPLETE")
        print("=" * 80)
