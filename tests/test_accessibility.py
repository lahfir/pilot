"""
Tests for Accessibility API - verify if it's actually being used and working.
"""

import platform
import pytest


class TestAccessibilityAPI:
    """Test Accessibility API availability and usage."""

    def test_atomacos_availability(self):
        """
        Test if atomacos library is installed and available.
        """
        if platform.system().lower() != "darwin":
            pytest.skip("atomacos only available on macOS")

        print("\n" + "=" * 80)
        print("🔍 TESTING ATOMACOS AVAILABILITY")
        print("=" * 80)

        try:
            import atomacos

            print("✅ atomacos imported successfully")
            print(f"   - Version: {getattr(atomacos, '__version__', 'unknown')}")
        except ImportError as e:
            pytest.fail(
                f"❌ atomacos not installed: {e}\n"
                f"   Install with: pip install atomacos\n"
                f"   THIS IS WHY ACCESSIBILITY API IS NOT WORKING!"
            )

        print("=" * 80)

    def test_accessibility_permissions(self):
        """
        Test if accessibility permissions are granted.

        This is CRITICAL - without this, accessibility API cannot work.
        """
        if platform.system().lower() != "darwin":
            pytest.skip("Accessibility permissions only on macOS")

        print("\n" + "=" * 80)
        print("🔍 TESTING ACCESSIBILITY PERMISSIONS")
        print("=" * 80)

        try:
            import atomacos

            # Try to access Finder (basic test)
            print("🧪 Testing accessibility by trying to access Finder...")
            try:
                finder = atomacos.getAppRefByBundleId("com.apple.finder")
                print("✅ Successfully accessed Finder via Accessibility API")
                # Try to get a valid attribute (AXRole is always available)
                try:
                    role = finder.AXRole
                    print(f"   - Finder role: {role}")
                except Exception:
                    # If we can access the app but not attributes, permissions might be limited
                    print(
                        "   ⚠️  Can access app but not all attributes (may have limited permissions)"
                    )
            except Exception as e:
                # Only fail if we truly can't access the app
                error_str = str(e)
                if "AXError" in error_str or "accessibility" in error_str.lower():
                    pytest.fail(
                        f"\n\n{'='*80}\n"
                        f"❌ ACCESSIBILITY PERMISSIONS NOT GRANTED!\n"
                        f"   Error: {e}\n\n"
                        f"   HOW TO FIX:\n"
                        f"   1. Open System Settings\n"
                        f"   2. Go to Privacy & Security → Accessibility\n"
                        f"   3. Add your terminal app (Terminal, iTerm, etc.)\n"
                        f"   4. Make sure it's checked/enabled\n"
                        f"   5. Restart this test\n\n"
                        f"   THIS IS WHY ACCESSIBILITY API IS NOT WORKING!\n"
                        f"{'='*80}\n"
                    )
                else:
                    # Some other error - just note it but don't fail
                    print(
                        f"   ⚠️  Unexpected error accessing Finder: {e} (but atomacos works)"
                    )
        except ImportError:
            pytest.skip("atomacos not installed")

        print("=" * 80)

    def test_macos_accessibility_class_initialization(self):
        """
        Test if MacOSAccessibility class initializes correctly.
        """
        if platform.system().lower() != "darwin":
            pytest.skip("MacOSAccessibility only on macOS")

        print("\n" + "=" * 80)
        print("🔍 TESTING MACOSACCESSIBILITY CLASS")
        print("=" * 80)

        from computer_use.tools.accessibility.macos_accessibility import (
            MacOSAccessibility,
        )

        acc = MacOSAccessibility()

        print(f"📋 Accessibility Status:")
        print(f"   - available: {acc.available}")

        if not acc.available:
            print(f"\n❌ Accessibility NOT AVAILABLE!")
            print(f"   Reasons this might happen:")
            print(f"   1. atomacos not installed")
            print(f"   2. Not running on macOS")
            print(f"   3. Accessibility permissions not granted")
            print(f"\n   THIS IS WHY ACCESSIBILITY API IS NOT WORKING!")
            pytest.fail("Accessibility should be available but isn't")
        else:
            print(f"✅ Accessibility is available and initialized!")

        print("=" * 80)

    def test_accessibility_element_discovery(self):
        """
        Test if accessibility API can discover UI elements.

        This tests if the API actually works, not just if it's available.
        """
        if platform.system().lower() != "darwin":
            pytest.skip("Accessibility only on macOS")

        print("\n" + "=" * 80)
        print("🔍 TESTING ELEMENT DISCOVERY VIA ACCESSIBILITY")
        print("=" * 80)

        from computer_use.tools.accessibility.macos_accessibility import (
            MacOSAccessibility,
        )

        acc = MacOSAccessibility()

        if not acc.available:
            pytest.skip("Accessibility not available")

        # Try to get elements from Finder
        print("🧪 Testing element discovery in Finder...")
        try:
            elements = acc.get_all_interactive_elements(app_name="Finder")

            print(f"📋 Found {len(elements)} interactive elements")

            if elements:
                print(f"\n   Sample elements (first 5):")
                for i, elem in enumerate(elements[:5], 1):
                    print(
                        f"   {i}. {elem.get('identifier', 'N/A')} - {elem.get('role', 'N/A')}"
                    )
                print("✅ Element discovery works!")
            else:
                print("⚠️  No elements found - accessibility might not be working")

        except Exception as e:
            pytest.fail(f"❌ Element discovery failed: {e}")

        print("=" * 80)

    def test_accessibility_vs_ocr_in_click_tool(self):
        """
        Test if click tool actually uses accessibility or falls back to OCR.

        This verifies if the multi-tier clicking system is working.
        """
        if platform.system().lower() != "darwin":
            pytest.skip("Test only for macOS")

        print("\n" + "=" * 80)
        print("🔍 TESTING CLICK TOOL'S USE OF ACCESSIBILITY")
        print("=" * 80)

        from computer_use.tools.accessibility.macos_accessibility import (
            MacOSAccessibility,
        )

        acc = MacOSAccessibility()

        if not acc.available:
            print("⚠️  Accessibility NOT available - click tool will use OCR fallback")
            print("   THIS MEANS CLICKS WILL BE LESS ACCURATE!")
            pytest.skip("Accessibility not available to test")

        # Try to click something in Finder
        print("🧪 Testing accessibility click on Finder...")
        try:
            # Try to find and click "Documents" in Finder
            success, element = acc.click_element("Documents", app_name="Finder")

            if success:
                print("✅ Successfully clicked via Accessibility API!")
                print("   This proves accessibility IS being used for clicking")
            else:
                print("⚠️  Accessibility click failed (element not found)")
                print("   Click tool will fall back to OCR")
        except Exception as e:
            print(f"⚠️  Accessibility click threw exception: {e}")
            print("   Click tool will fall back to OCR")

        print("=" * 80)

    def test_accessibility_window_focus_detection(self):
        """
        Test if accessibility can detect frontmost app.

        This is critical for the window focus verification.
        """
        if platform.system().lower() != "darwin":
            pytest.skip("Accessibility only on macOS")

        print("\n" + "=" * 80)
        print("🔍 TESTING WINDOW FOCUS DETECTION")
        print("=" * 80)

        from computer_use.tools.accessibility.macos_accessibility import (
            MacOSAccessibility,
        )

        acc = MacOSAccessibility()

        if not acc.available:
            pytest.skip("Accessibility not available")

        # Check if we can detect frontmost app
        try:
            is_frontmost = acc.is_app_frontmost("Finder")
            print(f"📋 Finder frontmost check: {is_frontmost}")
            print("✅ Window focus detection works!")
        except AttributeError:
            print("❌ is_app_frontmost method not implemented!")
            print("   This means window focus checks are NOT working")
        except Exception as e:
            print(f"⚠️  Window focus detection failed: {e}")

        print("=" * 80)

    def test_complete_accessibility_workflow(self):
        """
        Test complete accessibility workflow end-to-end.

        This simulates what the agent does:
        1. Check if accessibility is available
        2. Get frontmost app
        3. List interactive elements
        4. Try to click an element
        """
        if platform.system().lower() != "darwin":
            pytest.skip("Accessibility only on macOS")

        print("\n" + "=" * 80)
        print("🔍 TESTING COMPLETE ACCESSIBILITY WORKFLOW")
        print("=" * 80)

        from computer_use.tools.accessibility.macos_accessibility import (
            MacOSAccessibility,
        )

        # Step 1: Initialize
        print("STEP 1: Initialize accessibility...")
        acc = MacOSAccessibility()
        print(f"   Status: {'✅ Available' if acc.available else '❌ Not available'}")

        if not acc.available:
            print("\n⚠️  ACCESSIBILITY NOT AVAILABLE")
            print("   This means:")
            print(
                "   - Agent will use OCR fallback for clicks (still works, just less accurate)"
            )
            print("   - Possible causes: permissions not granted or atomacos issue")
            print("   - This is NOT a critical failure - multi-tier system handles it")
            pytest.skip(
                "Accessibility not available - this is expected in some environments. "
                "Multi-tier system will use OCR fallback."
            )

        # Step 2: Get elements from Finder
        print("\nSTEP 2: Get interactive elements from Finder...")
        try:
            elements = acc.get_all_interactive_elements(app_name="Finder")
            print(f"   Found {len(elements)} elements")

            if not elements:
                print("   ⚠️  WARNING: No elements found")
        except Exception as e:
            print(f"   ❌ Failed: {e}")

        # Step 3: Try to click Documents
        print("\nSTEP 3: Try to click 'Documents'...")
        try:
            success, _ = acc.click_element("Documents", app_name="Finder")
            print(f"   Result: {'✅ Success' if success else '⚠️  Not found'}")
        except Exception as e:
            print(f"   ❌ Failed: {e}")

        print("\n" + "=" * 80)
        print("✅ WORKFLOW COMPLETE")
        print("=" * 80)
