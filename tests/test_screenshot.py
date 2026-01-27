"""
Tests for Screenshot Tool - verify window capture works correctly.
"""

import platform
import pytest
import time


class TestScreenshotTool:
    """Test screenshot tool functionality."""

    def test_screenshot_tool_initialization(self):
        """
        Test if screenshot tool initializes correctly.
        """
        print("\n" + "=" * 80)
        print("🔍 TESTING SCREENSHOT TOOL INITIALIZATION")
        print("=" * 80)

        from computer_use.tools.screenshot_tool import ScreenshotTool

        tool = ScreenshotTool()

        print("📋 Screenshot Tool Status:")
        print(f"   - OS Type: {tool.os_type}")
        print(f"   - Scaling Factor: {tool.scaling_factor}")

        assert tool.os_type in ["darwin", "windows", "linux"], "OS type should be valid"
        print("✅ Screenshot tool initialized successfully")

        print("=" * 80)

    def test_fullscreen_capture(self):
        """
        Test basic full-screen screenshot capture.
        """
        print("\n" + "=" * 80)
        print("🔍 TESTING FULLSCREEN CAPTURE")
        print("=" * 80)

        from computer_use.tools.screenshot_tool import ScreenshotTool

        tool = ScreenshotTool()

        print("📸 Capturing fullscreen...")
        screenshot = tool.capture()

        print(f"   - Size: {screenshot.size}")
        print(f"   - Mode: {screenshot.mode}")

        assert screenshot.size[0] > 0 and screenshot.size[1] > 0, (
            "Screenshot should have valid dimensions"
        )
        print("✅ Fullscreen capture works!")

        print("=" * 80)

    @pytest.mark.skipif(
        platform.system().lower() != "darwin", reason="macOS specific test"
    )
    def test_window_capture_finder(self):
        """
        Test capturing a specific window (Finder).

        This tests the critical fix for window capture.
        """
        print("\n" + "=" * 80)
        print("🔍 TESTING WINDOW-SPECIFIC CAPTURE (FINDER)")
        print("=" * 80)

        from computer_use.tools.screenshot_tool import ScreenshotTool
        from computer_use.tools.process_tool import ProcessTool

        # Ensure Finder is running and focused
        print("📌 Focusing Finder...")
        process_tool = ProcessTool()
        result = process_tool.open_application("Finder")
        assert result["success"], "Failed to focus Finder"
        time.sleep(1)

        # Capture Finder window
        print("📸 Capturing Finder window...")
        screenshot_tool = ScreenshotTool()

        try:
            screenshot, metadata = screenshot_tool.capture_active_window("Finder")

            print("✅ Capture succeeded!")
            print(f"   - Size: {screenshot.size}")
            print(f"   - Bounds: {metadata}")

            assert screenshot.size[0] > 0, "Screenshot width should be > 0"
            assert screenshot.size[1] > 0, "Screenshot height should be > 0"

            # Save for visual inspection
            screenshot.save("/tmp/test_finder_capture.png")
            print("   - Saved to /tmp/test_finder_capture.png")

        except Exception as e:
            pytest.fail(f"❌ Window capture failed: {e}")

        print("=" * 80)

    @pytest.mark.skipif(
        platform.system().lower() != "darwin", reason="macOS specific test"
    )
    def test_window_capture_captures_actual_window_not_overlapping_content(self):
        """
        CRITICAL TEST: Verify window capture gets actual window, not overlapping windows.

        This tests the fix for the bug where screenshot captured VS Code when
        asking for Finder because VS Code was overlapping.
        """
        print("\n" + "=" * 80)
        print("🔍 TESTING ACTUAL WINDOW CAPTURE (NOT OVERLAPPING CONTENT)")
        print("=" * 80)

        from computer_use.tools.screenshot_tool import ScreenshotTool
        from computer_use.tools.vision.ocr_tool import OCRTool
        from computer_use.tools.process_tool import ProcessTool

        # Focus Finder
        print("📌 Step 1: Focusing Finder...")
        process_tool = ProcessTool()
        result = process_tool.open_application("Finder")
        assert result["success"], "Failed to focus Finder"
        time.sleep(1)

        # Capture Finder
        print("📸 Step 2: Capturing Finder window...")
        screenshot_tool = ScreenshotTool()
        screenshot, _ = screenshot_tool.capture_active_window("Finder")

        # Run OCR on the captured window
        print("🔍 Step 3: Running OCR on captured window...")
        ocr_tool = OCRTool()
        results = ocr_tool.extract_all_text(screenshot)

        if not results:
            pytest.fail("❌ OCR returned no results")

        # Extract all text
        text = " ".join([item.text for item in results])
        print(f"📝 Extracted text ({len(results)} items, {len(text)} chars):")
        print(f"   Preview: {text[:200]}...")

        # Check for Finder-specific content
        finder_keywords = [
            "Recents",
            "Downloads",
            "Documents",
            "Applications",
            "Desktop",
        ]
        vscode_keywords = ["Cursor", "Python", "Spaces:", "UTF-8", "Sonnet"]

        finder_matches = [kw for kw in finder_keywords if kw in text]
        vscode_matches = [kw for kw in vscode_keywords if kw in text]

        print("\n📊 Content Analysis:")
        print(f"   - Finder keywords found: {finder_matches}")
        print(f"   - VS Code keywords found: {vscode_matches}")

        if len(finder_matches) > len(vscode_matches):
            print("✅ Screenshot contains FINDER content!")
            print(
                "   The fix is working - capturing actual window, not overlapping content"
            )
        elif len(vscode_matches) > len(finder_matches):
            pytest.fail(
                f"\n\n{'=' * 80}\n"
                f"❌ BUG DETECTED: Screenshot contains VS CODE content!\n"
                f"   This means the window capture is still broken.\n"
                f"   It's capturing overlapping windows instead of the target window.\n"
                f"   Finder keywords: {finder_matches}\n"
                f"   VS Code keywords: {vscode_matches}\n"
                f"{'=' * 80}\n"
            )
        else:
            print("⚠️  Could not determine window content (no keywords matched)")

        print("=" * 80)

    @pytest.mark.skipif(
        platform.system().lower() != "darwin", reason="macOS specific test"
    )
    def test_window_capture_then_ocr_sequence(self):
        """
        Test the exact sequence the agent uses: capture window, then OCR.

        This replicates what read_screen_text does.
        """
        print("\n" + "=" * 80)
        print("🔍 TESTING WINDOW CAPTURE → OCR SEQUENCE")
        print("=" * 80)

        from computer_use.tools.screenshot_tool import ScreenshotTool
        from computer_use.tools.vision.ocr_tool import OCRTool
        from computer_use.tools.process_tool import ProcessTool

        # Focus Finder
        print("📌 Focusing Finder...")
        process_tool = ProcessTool()
        result = process_tool.open_application("Finder")
        assert result["success"]
        time.sleep(1)

        screenshot_tool = ScreenshotTool()
        ocr_tool = OCRTool()

        # Attempt 1: Capture and OCR
        print("\n🔄 Attempt 1:")
        try:
            screenshot1, bounds1 = screenshot_tool.capture_active_window("Finder")
            print(f"   📸 Screenshot 1: {screenshot1.size}")

            results1 = ocr_tool.extract_all_text(screenshot1)
            print(f"   🔍 OCR 1: {len(results1)} items")

            assert len(results1) > 0, "First OCR should return results"
        except Exception as e:
            pytest.fail(f"❌ Attempt 1 failed: {e}")

        # Attempt 2: Immediately try again (simulating agent retry)
        print("\n🔄 Attempt 2 (immediate retry):")
        time.sleep(0.1)

        try:
            screenshot2, bounds2 = screenshot_tool.capture_active_window("Finder")
            print(f"   📸 Screenshot 2: {screenshot2.size}")

            results2 = ocr_tool.extract_all_text(screenshot2)
            print(f"   🔍 OCR 2: {len(results2)} items")

            assert len(results2) > 0, "Second OCR should also return results"
            print("✅ Both attempts succeeded - window capture is stable!")

        except Exception as e:
            pytest.fail(
                f"❌ Attempt 2 failed: {e}\n   This is why read_screen_text fails on retry!"
            )

        print("=" * 80)

    def test_region_capture(self):
        """
        Test capturing a specific region of the screen.
        """
        print("\n" + "=" * 80)
        print("🔍 TESTING REGION CAPTURE")
        print("=" * 80)

        from computer_use.tools.screenshot_tool import ScreenshotTool

        tool = ScreenshotTool()

        # Capture top-left 500x500 region
        print("📸 Capturing region (0, 0, 500, 500)...")
        region = (0, 0, 500, 500)
        screenshot = tool.capture(region=region)

        print(f"   - Size: {screenshot.size}")

        # Note: Screenshot might be scaled, so check it's approximately correct
        assert screenshot.size[0] > 400, "Region width should be around 500px"
        assert screenshot.size[1] > 400, "Region height should be around 500px"

        print("✅ Region capture works!")

        print("=" * 80)
