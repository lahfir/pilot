"""
Integration tests for Calculator and System Settings automation.
Tests the full flow of opening apps and getting accessible elements.
"""

import platform
import subprocess
import time

import pytest


class TestCalculatorIntegration:
    """Test Calculator app automation."""

    @pytest.fixture(autouse=True)
    def setup_calculator(self):
        """Open Calculator before each test."""
        if platform.system().lower() != "darwin":
            pytest.skip("Calculator tests only on macOS")

        # Open Calculator
        subprocess.run(["open", "-a", "Calculator"], check=False, capture_output=True)
        time.sleep(1.0)  # Give app time to fully launch

        yield

        # Close Calculator after test
        subprocess.run(
            ["osascript", "-e", 'quit app "Calculator"'],
            check=False,
            capture_output=True,
        )

    def test_calculator_accessibility_elements(self):
        """
        Test that we can get accessible elements from Calculator.
        This is the CRITICAL test that was failing.
        """
        from computer_use.tools.accessibility.macos_accessibility import (
            MacOSAccessibility,
        )

        print("\n" + "=" * 80)
        print("🧪 TESTING CALCULATOR ACCESSIBILITY")
        print("=" * 80)

        accessibility = MacOSAccessibility()

        if not accessibility.available:
            pytest.fail("❌ Accessibility API not available!")

        print("\n1️⃣  Getting all UI elements from Calculator...")
        elements = accessibility.get_all_ui_elements("Calculator")

        print(f"\n📊 Results:")
        total_elements = sum(len(v) for v in elements.values())
        print(f"   Total elements: {total_elements}")

        for category, items in elements.items():
            if items:
                print(f"   • {category}: {len(items)}")
                if len(items) <= 5:
                    for item in items:
                        print(
                            f"      - {item.get('title', item.get('identifier', 'N/A'))}"
                        )

        # CRITICAL ASSERTION
        assert total_elements > 0, (
            f"❌ FAILED: Got 0 elements from Calculator!\n"
            f"   This means accessibility API is not working.\n"
            f"   Debug info:\n"
            f"   - Accessibility available: {accessibility.available}\n"
            f"   - Elements dict: {elements}"
        )

        print(f"\n✅ SUCCESS: Got {total_elements} elements from Calculator")

        # Check for specific button elements
        interactive = elements.get("interactive", [])
        button_count = sum(
            1 for elem in interactive if "button" in elem.get("role", "").lower()
        )
        print(f"   Found {button_count} buttons")

        assert button_count > 0, "❌ No buttons found in Calculator!"

        print("=" * 80)

    def test_calculator_has_buttons(self):
        """Test that Calculator has interactive buttons."""
        from computer_use.tools.accessibility.macos_accessibility import (
            MacOSAccessibility,
        )

        print("\n" + "=" * 80)
        print("🧪 TESTING CALCULATOR HAS BUTTONS")
        print("=" * 80)

        # Re-focus Calculator
        subprocess.run(["open", "-a", "Calculator"], check=False, capture_output=True)
        time.sleep(0.5)

        accessibility = MacOSAccessibility()
        elements = accessibility.get_all_ui_elements("Calculator")

        interactive = elements.get("interactive", [])

        print(f"\n📊 Found {len(interactive)} interactive element(s)")
        if len(interactive) <= 10:
            for elem in interactive:
                print(f"   • {elem.get('title', 'N/A')} (role: {elem.get('role')})")

        assert len(interactive) > 0, "❌ No interactive elements found in Calculator!"

        print(f"\n✅ SUCCESS: Found {len(interactive)} interactive elements")
        print("=" * 80)

    def test_calculator_number_buttons(self):
        """Test that we can find number buttons in Calculator."""
        from computer_use.tools.accessibility.macos_accessibility import (
            MacOSAccessibility,
        )

        print("\n" + "=" * 80)
        print("🧪 TESTING CALCULATOR NUMBER BUTTONS")
        print("=" * 80)

        # Re-focus Calculator
        subprocess.run(["open", "-a", "Calculator"], check=False, capture_output=True)
        time.sleep(0.5)

        accessibility = MacOSAccessibility()
        elements = accessibility.get_all_ui_elements("Calculator")

        interactive = elements.get("interactive", [])

        # Look for number buttons (0-9)
        number_buttons = [
            elem
            for elem in interactive
            if elem.get("title") in [str(i) for i in range(10)]
        ]

        print(f"\n📊 Found {len(number_buttons)} number button(s)")
        for btn in sorted(number_buttons, key=lambda x: x.get("title", "")):
            print(f"   • {btn.get('title')} at {btn.get('bounds')}")

        assert (
            len(number_buttons) >= 10
        ), f"❌ Expected 10 number buttons, got {len(number_buttons)}"

        print("\n✅ SUCCESS: Found all number buttons")
        print("=" * 80)


class TestSystemSettingsIntegration:
    """Test System Settings app automation."""

    @pytest.fixture(autouse=True)
    def setup_system_settings(self):
        """Open System Settings before each test."""
        if platform.system().lower() != "darwin":
            pytest.skip("System Settings tests only on macOS")

        # Open System Settings
        subprocess.run(
            ["open", "-a", "System Settings"], check=False, capture_output=True
        )
        time.sleep(1.5)  # Give app time to fully launch

        yield

        # Close System Settings after test
        subprocess.run(
            ["osascript", "-e", 'quit app "System Settings"'],
            check=False,
            capture_output=True,
        )

    def test_system_settings_accessibility_elements(self):
        """
        Test that we can get accessible elements from System Settings.
        This was also failing with 0 elements.
        """
        from computer_use.tools.accessibility.macos_accessibility import (
            MacOSAccessibility,
        )

        print("\n" + "=" * 80)
        print("🧪 TESTING SYSTEM SETTINGS ACCESSIBILITY")
        print("=" * 80)

        accessibility = MacOSAccessibility()

        if not accessibility.available:
            pytest.fail("❌ Accessibility API not available!")

        print("\n1️⃣  Getting all UI elements from System Settings...")
        elements = accessibility.get_all_ui_elements("System Settings")

        print(f"\n📊 Results:")
        total_elements = sum(len(v) for v in elements.values())
        print(f"   Total elements: {total_elements}")

        for category, items in elements.items():
            if items:
                print(f"   • {category}: {len(items)}")
                if category == "interactive" and len(items) <= 10:
                    for item in items[:10]:
                        print(
                            f"      - {item.get('title', item.get('identifier', 'N/A'))}"
                        )

        # CRITICAL ASSERTION
        assert total_elements > 0, (
            f"❌ FAILED: Got 0 elements from System Settings!\n"
            f"   This means accessibility API is not working.\n"
            f"   Debug info:\n"
            f"   - Accessibility available: {accessibility.available}\n"
            f"   - Elements dict: {elements}"
        )

        print(f"\n✅ SUCCESS: Got {total_elements} elements from System Settings")
        print("=" * 80)

    def test_system_settings_has_interactive_elements(self):
        """Test that System Settings has interactive elements."""
        from computer_use.tools.accessibility.macos_accessibility import (
            MacOSAccessibility,
        )

        print("\n" + "=" * 80)
        print("🧪 TESTING SYSTEM SETTINGS HAS INTERACTIVE ELEMENTS")
        print("=" * 80)

        # Re-focus System Settings
        subprocess.run(
            ["open", "-a", "System Settings"], check=False, capture_output=True
        )
        time.sleep(0.5)

        accessibility = MacOSAccessibility()
        elements = accessibility.get_all_ui_elements("System Settings")

        interactive = elements.get("interactive", [])

        print(f"\n📊 Found {len(interactive)} interactive element(s)")
        if len(interactive) <= 10:
            for elem in interactive:
                print(f"   • {elem.get('title', 'N/A')} (role: {elem.get('role')})")

        assert (
            len(interactive) > 0
        ), "❌ No interactive elements found in System Settings!"

        print(f"\n✅ SUCCESS: Found {len(interactive)} interactive elements")
        print("=" * 80)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
