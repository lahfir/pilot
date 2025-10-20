"""
Test script to verify installation without needing API keys.
"""

import sys
from src.computer_use.utils.platform_detector import detect_platform
from src.computer_use.utils.safety_checker import SafetyChecker


def print_banner():
    """Print test banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║     ✓ INSTALLATION TEST - NO API KEYS REQUIRED           ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def test_imports():
    """Test that all core imports work"""
    print("\n" + "=" * 60)
    print("📦 Testing Imports")
    print("=" * 60)

    try:
        from src.computer_use.utils.platform_detector import detect_platform

        print("✓ Platform detector")

        from src.computer_use.utils.safety_checker import SafetyChecker

        print("✓ Safety checker")

        from src.computer_use.utils.platform_helper import PlatformHelper

        print("✓ Platform helper")

        from src.computer_use.utils.coordinate_validator import CoordinateValidator

        print("✓ Coordinate validator")

        from src.computer_use.tools.screenshot_tool import ScreenshotTool

        print("✓ Screenshot tool")

        from src.computer_use.tools.input_tool import InputTool

        print("✓ Input tool")

        from src.computer_use.tools.process_tool import ProcessTool

        print("✓ Process tool")

        from src.computer_use.tools.file_tool import FileTool

        print("✓ File tool")

        from src.computer_use.tools.browser_tool import BrowserTool

        print("✓ Browser tool")

        from src.computer_use.schemas.task_analysis import TaskAnalysis, TaskType

        print("✓ Schemas")

        print("\n✅ All core imports successful!")
        return True

    except ImportError as e:
        print(f"\n❌ Import failed: {e}")
        return False


def test_platform_detection():
    """Test platform detection"""
    print("\n" + "=" * 60)
    print("🖥️  Testing Platform Detection")
    print("=" * 60)

    try:
        capabilities = detect_platform()

        print(f"\n  OS Type: {capabilities.os_type}")
        print(f"  OS Version: {capabilities.os_version}")
        print(f"  Screen Resolution: {capabilities.screen_resolution}")
        print(f"  Scaling Factor: {capabilities.scaling_factor}")
        print(
            f"  Accessibility API: {'✅' if capabilities.accessibility_api_available else '❌'}"
        )

        if capabilities.accessibility_api_available:
            print(f"  API Type: {capabilities.accessibility_api_type}")

        print(f"\n  Available Tools ({len(capabilities.supported_tools)}):")
        for tool in capabilities.supported_tools:
            print(f"    ✓ {tool}")

        print("\n✅ Platform detection successful!")
        return True

    except Exception as e:
        print(f"\n❌ Platform detection failed: {e}")
        return False


def test_safety_checker():
    """Test safety checker"""
    print("\n" + "=" * 60)
    print("🛡️  Testing Safety Checker")
    print("=" * 60)

    try:
        safety_checker = SafetyChecker()

        test_cases = [
            ("ls -la", False),
            ("rm -rf /", True),
            ("cp file.txt backup.txt", False),
            ("rm important.txt", True),
        ]

        print("\n  Command Safety Tests:")
        all_passed = True
        for cmd, should_be_destructive in test_cases:
            is_destructive = safety_checker.is_destructive(cmd)
            passed = is_destructive == should_be_destructive

            symbol = "✓" if passed else "✗"
            status = "DANGEROUS" if is_destructive else "SAFE"

            print(f"    {symbol} {cmd:30s} [{status}]")

            if not passed:
                all_passed = False

        if all_passed:
            print("\n✅ Safety checker working correctly!")
        else:
            print("\n⚠️  Some safety checks failed")

        return all_passed

    except Exception as e:
        print(f"\n❌ Safety checker failed: {e}")
        return False


def test_tool_initialization():
    """Test that tools can be initialized"""
    print("\n" + "=" * 60)
    print("🔧 Testing Tool Initialization")
    print("=" * 60)

    try:
        from src.computer_use.tools.screenshot_tool import ScreenshotTool
        from src.computer_use.tools.process_tool import ProcessTool
        from src.computer_use.tools.file_tool import FileTool
        from src.computer_use.utils.safety_checker import SafetyChecker

        safety_checker = SafetyChecker()

        print("\n  Initializing tools:")

        screenshot = ScreenshotTool()
        print("    ✓ Screenshot Tool")

        process = ProcessTool()
        print("    ✓ Process Tool")

        file_tool = FileTool(safety_checker)
        print("    ✓ File Tool")

        print("\n✅ All tools initialized successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Tool initialization failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print_banner()

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Platform Detection", test_platform_detection()))
    results.append(("Safety Checker", test_safety_checker()))
    results.append(("Tool Initialization", test_tool_initialization()))

    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print()
    for test_name, result in results:
        symbol = "✅" if result else "❌"
        print(f"  {symbol} {test_name}")

    print("\n" + "=" * 60)

    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("=" * 60)
        print("\n🎉 Installation verified successfully!")
        print("\n💡 Next step: Add your API keys to .env and run:")
        print("   uv run python demo.py")
        print()
        sys.exit(0)
    else:
        print(f"⚠️  SOME TESTS FAILED ({passed}/{total})")
        print("=" * 60)
        print("\n⚠️  Some components may not work correctly.")
        print("   Check the errors above for details.")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()

