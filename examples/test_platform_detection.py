"""
Test platform detection and tool initialization.
"""

from computer_use.utils.platform_detector import detect_platform
from computer_use.utils.safety_checker import SafetyChecker
from computer_use.utils.coordinate_validator import CoordinateValidator
from computer_use.tools.platform_registry import PlatformToolRegistry


def main():
    """
    Test platform detection and tool registry.
    """
    print("\n🔍 Testing Platform Detection\n")

    print("1. Detecting platform capabilities...")
    capabilities = detect_platform()

    print(f"\n📊 Platform Information:")
    print(f"  OS Type: {capabilities.os_type}")
    print(f"  OS Version: {capabilities.os_version}")
    print(
        f"  Screen Resolution: {capabilities.screen_resolution[0]}x{capabilities.screen_resolution[1]}"
    )
    print(f"  Scaling Factor: {capabilities.scaling_factor}x")

    print(f"\n🔧 Accessibility API:")
    print(f"  Available: {capabilities.accessibility_api_available}")
    if capabilities.accessibility_api_available:
        print(f"  Type: {capabilities.accessibility_api_type}")

    print(f"\n🛠️  Supported Tools:")
    for tool in capabilities.supported_tools:
        print(f"    • {tool}")

    print("\n\n2. Initializing tool registry...")
    safety_checker = SafetyChecker()
    coordinate_validator = CoordinateValidator(
        capabilities.screen_resolution[0], capabilities.screen_resolution[1]
    )

    tool_registry = PlatformToolRegistry(
        capabilities,
        safety_checker=safety_checker,
        coordinate_validator=coordinate_validator,
    )

    print(
        f"\n✅ Tool registry initialized with {len(tool_registry.list_available_tools())} tools"
    )

    print("\n📋 Available Tools:")
    for tool_name in tool_registry.list_available_tools():
        print(f"    • {tool_name}")

    print("\n\n3. Testing capabilities summary...")
    summary = tool_registry.get_capabilities_summary()

    print(f"\n📈 Capabilities Summary:")
    print(f"  Tier 1 (Accessibility): {'✅' if summary['tier1_available'] else '❌'}")
    print(f"  Tier 2 (CV + OCR): {'✅' if summary['tier2_available'] else '❌'}")
    print(f"  Tier 3 (Vision): {'✅' if summary['tier3_available'] else '❌'}")

    print("\n\n4. Testing safety checker...")
    test_commands = [
        "ls -la",
        "rm -rf /",
        "cp file.txt backup.txt",
        "del important.txt",
    ]

    print(f"\n🔒 Safety Check Results:")
    for cmd in test_commands:
        is_destructive = safety_checker.is_destructive(cmd)
        requires_confirm = safety_checker.requires_confirmation(command=cmd)

        print(f"\n  Command: {cmd}")
        print(f"    Destructive: {'⚠️  Yes' if is_destructive else '✅ No'}")
        print(f"    Needs Confirmation: {'⚠️  Yes' if requires_confirm else '✅ No'}")

    print("\n\n5. Testing coordinate validator...")
    test_coords = [
        (500, 300),
        (-10, 50),
        (5000, 5000),
        (10, 10),
    ]

    print(f"\n📍 Coordinate Validation:")
    for x, y in test_coords:
        is_valid, error = coordinate_validator.validate_coordinates(x, y, strict=False)

        print(f"\n  ({x}, {y})")
        print(f"    Valid: {'✅' if is_valid else '❌'}")
        if error:
            print(f"    Error: {error}")

    print("\n\n✅ All tests completed!")


if __name__ == "__main__":
    main()

