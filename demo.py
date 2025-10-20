"""
Quick demo of the Computer Use Agent
"""

import asyncio
from src.computer_use.utils.platform_detector import detect_platform
from src.computer_use.utils.safety_checker import SafetyChecker
from src.computer_use.crew import ComputerUseCrew


def print_banner():
    """Print demo banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║        🤖 COMPUTER USE AGENT - DEMO                      ║
    ║        Multi-Tier Accuracy System                        ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(banner)


async def demo_platform_detection():
    """Demonstrate platform detection"""
    print("\n" + "=" * 60)
    print("📋 DEMO 1: Platform Detection")
    print("=" * 60)

    capabilities = detect_platform()

    print(f"\n🖥️  Platform Information:")
    print(f"   OS Type: {capabilities.os_type}")
    print(f"   OS Version: {capabilities.os_version}")
    print(f"   Screen Resolution: {capabilities.screen_resolution}")
    print(f"   Scaling Factor: {capabilities.scaling_factor}")
    print(
        f"   Accessibility API: {'✅ Available' if capabilities.accessibility_api_available else '❌ Not Available'}"
    )

    if capabilities.accessibility_api_available:
        print(f"   API Type: {capabilities.accessibility_api_type}")

    print(f"\n🛠️  Available Tools: {len(capabilities.supported_tools)}")
    for tool in capabilities.supported_tools:
        print(f"   ✓ {tool}")

    return capabilities


async def demo_safety_checker():
    """Demonstrate safety checker"""
    print("\n" + "=" * 60)
    print("🛡️  DEMO 2: Safety Checker")
    print("=" * 60)

    safety_checker = SafetyChecker()

    test_commands = ["ls -la", "rm important.txt", "rm -rf /", "cp file.txt backup.txt"]

    print("\n🔍 Testing commands:")
    for cmd in test_commands:
        is_destructive = safety_checker.is_destructive(cmd)
        requires_confirm = safety_checker.requires_confirmation(command=cmd)

        status = "🔴 DANGEROUS" if is_destructive else "🟢 SAFE"
        confirm = " (requires confirmation)" if requires_confirm else ""

        print(f"   {status} | {cmd}{confirm}")

    return safety_checker


async def demo_crew_initialization(capabilities, safety_checker):
    """Demonstrate crew initialization"""
    print("\n" + "=" * 60)
    print("👥 DEMO 3: Crew Initialization")
    print("=" * 60)

    print("\n🤖 Initializing Computer Use Crew...")
    crew = ComputerUseCrew(capabilities, safety_checker)

    print(f"\n✅ Crew initialized successfully!")
    print(f"   Loaded {len(crew.tool_registry.list_available_tools())} tools")

    print("\n📋 Agent Configuration:")
    print(f"   ✓ Coordinator Agent (Task Analysis)")
    print(f"   ✓ Browser Agent (Web Automation via Browser-Use)")
    print(f"   ✓ GUI Agent (Desktop Automation with Multi-Tier)")
    print(f"   ✓ System Agent (Terminal & File Operations)")

    print("\n🔧 Tool Registry:")
    for tool_name in crew.tool_registry.list_available_tools():
        print(f"   ✓ {tool_name}")

    return crew


async def demo_task_analysis(crew):
    """Demonstrate task analysis"""
    print("\n" + "=" * 60)
    print("🧠 DEMO 4: Task Analysis")
    print("=" * 60)

    test_tasks = [
        "Download image of a car",
        "Open Calculator app",
        "Create a folder named test in Downloads",
    ]

    print("\n🔍 Analyzing sample tasks:")
    for task in test_tasks:
        print(f"\n   Task: '{task}'")
        result = await crew.coordinator_agent.analyze_task(task)
        print(f"   ├─ Type: {result.task_type.value}")
        print(f"   ├─ Browser: {'✓' if result.requires_browser else '✗'}")
        print(f"   ├─ GUI: {'✓' if result.requires_gui else '✗'}")
        print(f"   ├─ System: {'✓' if result.requires_system else '✗'}")
        print(f"   └─ Reasoning: {result.reasoning}")


async def main():
    """Run all demos"""
    print_banner()

    try:
        # Demo 1: Platform Detection
        capabilities = await demo_platform_detection()

        # Demo 2: Safety Checker
        safety_checker = await demo_safety_checker()

        # Demo 3: Crew Initialization
        crew = await demo_crew_initialization(capabilities, safety_checker)

        # Demo 4: Task Analysis
        await demo_task_analysis(crew)

        print("\n" + "=" * 60)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("=" * 60)

        print("\n💡 Next Steps:")
        print("   1. Set your API keys in .env file")
        print("   2. Run: uv run python -m computer_use.main")
        print("   3. Enter tasks to automate!\n")

    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
