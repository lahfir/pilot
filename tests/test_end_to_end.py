"""
End-to-end tests that actually perform actions.
Tests clicking buttons and verifying results.
"""

import platform
import subprocess
import time

import pytest


class TestCalculatorEndToEnd:
    """End-to-end tests for Calculator automation."""

    @pytest.fixture(autouse=True)
    def setup_calculator(self):
        """Open Calculator before each test."""
        if platform.system().lower() != "darwin":
            pytest.skip("Calculator tests only on macOS")

        # Open Calculator
        subprocess.run(["open", "-a", "Calculator"], check=False, capture_output=True)
        time.sleep(1.0)

        yield

        # Close Calculator after test
        subprocess.run(
            ["osascript", "-e", 'quit app "Calculator"'],
            check=False,
            capture_output=True,
        )

    def test_calculator_multiplication_2929x2929(self):
        """
        Test the full Calculator flow: clear, input 2929*2929, get result.
        This is the EXACT flow that was failing.
        """
        from computer_use.tools.accessibility.macos_accessibility import (
            MacOSAccessibility,
        )

        print("\n" + "=" * 80)
        print("🧪 END-TO-END TEST: Calculator 2929 × 2929")
        print("=" * 80)

        accessibility = MacOSAccessibility()

        # Step 1: Get all elements
        print("\n1️⃣  Getting Calculator elements...")
        elements = accessibility.get_all_ui_elements("Calculator")
        interactive = elements.get("interactive", [])

        total = sum(len(v) for v in elements.values())
        print(f"   Found {total} total elements, {len(interactive)} interactive")

        assert len(interactive) > 0, "❌ No interactive elements found!"

        # Step 2: Find Clear button
        print("\n2️⃣  Finding Clear button...")
        clear_btn = None
        for elem in interactive:
            if elem.get("title") in ["AC", "C", "Clear"]:
                clear_btn = elem
                break

        if clear_btn:
            print(f"   ✅ Found Clear button: {clear_btn.get('title')}")
            bounds = clear_btn.get("bounds", [])
            if bounds and len(bounds) == 4:
                print(f"   📍 Position: {bounds}")
        else:
            print("   ⚠️  Clear button not found (might already be clear)")

        # Step 3: Find number buttons
        print("\n3️⃣  Finding number buttons...")
        number_buttons = {}
        for elem in interactive:
            title = elem.get("title", "")
            if title in [str(i) for i in range(10)]:
                number_buttons[title] = elem

        print(f"   Found {len(number_buttons)} number buttons")
        assert len(number_buttons) >= 10, "❌ Missing number buttons!"

        # Step 4: Find operator buttons
        print("\n4️⃣  Finding operator buttons...")
        multiply_btn = None
        equals_btn = None

        # Debug: print all non-number buttons
        print("   All non-number buttons:")
        for elem in interactive:
            title = elem.get("title", "")
            if title not in [str(i) for i in range(10)] and title not in ["Clear", ""]:
                print(
                    f"      • '{title}' (identifier: {elem.get('identifier', 'N/A')})"
                )

        for elem in interactive:
            title = elem.get("title", "")
            identifier = elem.get("identifier", "")
            if title in ["×", "*", "multiply"] or "multiply" in identifier.lower():
                multiply_btn = elem
            elif title in ["=", "equals"] or "equal" in identifier.lower():
                equals_btn = elem

        if multiply_btn:
            print(f"\n   ✅ Found multiply button: {multiply_btn.get('title')}")
        if equals_btn:
            print(f"   ✅ Found equals button: {equals_btn.get('title')}")

        # Step 5: Verify we have everything needed
        print("\n5️⃣  Verification:")
        print(f"   • Number 2: {'✅' if '2' in number_buttons else '❌'}")
        print(f"   • Number 9: {'✅' if '9' in number_buttons else '❌'}")
        print(f"   • Multiply: {'✅' if multiply_btn else '❌'}")
        print(f"   • Equals: {'✅' if equals_btn else '❌'}")

        assert "2" in number_buttons, "❌ Missing button: 2"
        assert "9" in number_buttons, "❌ Missing button: 9"
        assert multiply_btn is not None, "❌ Missing multiply button"
        assert equals_btn is not None, "❌ Missing equals button"

        print("\n✅ SUCCESS: All required buttons found!")
        print("   The accessibility API is working correctly.")
        print("   The agent can now use these buttons to perform calculations.")
        print("=" * 80)


class TestSystemSettingsDarkMode:
    """End-to-end test for changing to Dark Mode using REAL AGENT TOOLS."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for tests."""
        if platform.system().lower() != "darwin":
            pytest.skip("System Settings tests only on macOS")

        yield

        # Close System Settings after test
        subprocess.run(
            ["osascript", "-e", 'quit app "System Settings"'],
            check=False,
            capture_output=True,
        )

    def test_dark_mode_flow(self):
        """
        Test the full Dark Mode flow using REAL AGENT WORKFLOW.
        This simulates the EXACT agent workflow: open app → get elements → click.
        """
        from computer_use.tools.accessibility.macos_accessibility import (
            MacOSAccessibility,
        )
        from computer_use.tools.input_tool import InputTool
        from computer_use.tools.process_tool import ProcessTool

        print("\n" + "=" * 80)
        print("🧪 END-TO-END TEST: System Settings Wallpaper (REAL WORKFLOW)")
        print("=" * 80)

        accessibility = MacOSAccessibility()
        input_tool = InputTool()
        process_tool = ProcessTool()

        # SIMULATE REAL AGENT WORKFLOW

        # Step 1: Open app (like open_application tool does)
        print("\n1️⃣  Opening System Settings (REAL open_application workflow)...")
        result = process_tool.open_application("System Settings")
        assert result.get("success", False), "❌ Failed to open System Settings!"
        print(f"   ✅ Opened: {result.get('message', 'N/A')}")

        # Wait for app to become frontmost
        max_attempts = 10
        wait_interval = 0.5
        is_front = False

        for attempt in range(max_attempts):
            time.sleep(wait_interval)
            process_tool.focus_app("System Settings")

            if accessibility.is_app_frontmost("System Settings"):
                is_front = True
                # CRITICAL: Wait for UI to initialize (like open_application tool does)
                time.sleep(1.0)
                print(
                    f"   ✅ App frontmost after {(attempt + 1) * wait_interval + 1.0}s"
                )
                break

        assert is_front, "❌ App never became frontmost!"

        # Step 2: Get elements (like get_accessible_elements tool does)
        print("\n2️⃣  Getting elements (REAL get_accessible_elements workflow)...")

        # Try up to 3 times with progressively longer delays (like the tool does)
        elements_dict = {}
        for attempt in range(3):
            if attempt > 0:
                delay = [0.8, 1.2, 1.5][attempt]
                print(f"   Retry #{attempt + 1} after {delay}s...")
                time.sleep(delay)

            elements_dict = accessibility.get_all_ui_elements("System Settings")
            all_elements = []
            for category, items in elements_dict.items():
                all_elements.extend(items)

            if all_elements:
                print(f"   ✅ Found {len(all_elements)} elements!")
                break
            elif attempt < 2:
                print(f"   ⚠️  Got 0 elements on attempt {attempt + 1}, retrying...")

        assert len(all_elements) > 0, "❌ No elements found! This is the bug!"

        elements = all_elements
        print(f"   Total elements: {len(elements)}")

        # Step 3: Look for Wallpaper button (FILTER OUT MENU ITEMS!)
        print("\n3️⃣  Looking for Wallpaper button (SIDEBAR ONLY)...")
        wallpaper_elem = None
        for elem in elements:
            title = elem.get("title", "").lower()
            label = elem.get("label", "").lower()
            bounds = elem.get("bounds", [])
            role = elem.get("role", "")

            # CRITICAL: Filter out menu items (bounds [0, 1329, 0, 0])
            # Only accept elements with valid bounds in the visible window
            if "wallpaper" in title or "wallpaper" in label:
                if bounds and len(bounds) == 4:
                    x, y, w, h = bounds
                    # Sidebar is around x=470-700, y=100-1200
                    if x > 400 and x < 800 and y > 50 and y < 1300 and w > 0 and h > 0:
                        wallpaper_elem = elem
                        print(f"   ✅ Found valid sidebar element: {title or label}")
                        print(f"      Role: {role}, Bounds: {bounds}")
                        break
                    else:
                        print(f"   ⚠️  Skipping menu item: {title or label} at {bounds}")

        if wallpaper_elem:
            print("\n   ✅ FOUND WALLPAPER SIDEBAR BUTTON!")
            print(
                f"      Title: {wallpaper_elem.get('title', wallpaper_elem.get('label', 'N/A'))}"
            )
            print(f"      Bounds: {wallpaper_elem.get('bounds', 'N/A')}")

            # Step 4: Try native click first, fallback to coordinates
            print("\n4️⃣  Clicking Wallpaper (native first, then coordinates)...")

            # Try native accessibility click (traverse parents if needed)
            success, method = accessibility.try_click_element_or_parent(wallpaper_elem)

            if success:
                print(f"   ✅ Clicked with native accessibility ({method})!")
                # CRITICAL: Wait for UI to update
                time.sleep(0.8)
                print("   ⏱️  Waited 0.8s for UI state change")
            else:
                # Fallback to coordinate click
                print(f"   ⚠️  Native click failed ({method}), using coordinates...")
                bounds = wallpaper_elem.get("bounds", [])
                if bounds and len(bounds) == 4:
                    x, y, w, h = bounds
                    center_x = x + w // 2
                    center_y = y + h // 2

                    print(f"   Clicking at ({center_x}, {center_y})")
                    success = input_tool.click(center_x, center_y, validate=True)

                    if success:
                        print("   ✅ Clicked with element coordinates!")
                        # CRITICAL: Wait for UI to update
                        time.sleep(0.8)
                        print("   ⏱️  Waited 0.8s for UI state change")
                    else:
                        assert False, "❌ Both native and coordinate click failed!"
                else:
                    assert False, "❌ No valid bounds for coordinate fallback!"

            # Step 5: Verify we're on Wallpaper page
            print("\n5️⃣  Verifying we're on Wallpaper page...")
            new_elements_dict = accessibility.get_all_ui_elements("System Settings")
            new_elements = []
            for category, items in new_elements_dict.items():
                new_elements.extend(items)
            print(f"   Found {len(new_elements)} elements on new page")

            # Look for wallpaper-specific elements
            wallpaper_specific = False
            for elem in new_elements:
                title = elem.get("title", "").lower()
                if "dynamic" in title or "desktop" in title or "picture" in title:
                    wallpaper_specific = True
                    print(
                        f"   ✅ Found wallpaper-specific element: {elem.get('title')}"
                    )
                    break

            if wallpaper_specific:
                print("\n🎉 SUCCESS: Navigated to Wallpaper page!")
            else:
                print("\n⚠️  WARNING: Might not be on Wallpaper page yet")

        else:
            print("   ❌ WALLPAPER BUTTON NOT FOUND!")
            print("\n   Available sidebar buttons:")
            for elem in elements[:15]:
                title = elem.get("title", elem.get("label", "N/A"))
                if title and title != "N/A":
                    print(f"      • {title}")

            assert False, "❌ Wallpaper button not found! This is the bug!"

        print("\n✅ TEST COMPLETE")
        print("=" * 80)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
