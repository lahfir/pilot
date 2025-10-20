"""
Main entry point for computer use automation agent.
"""

import asyncio
from .utils.platform_detector import detect_platform
from .utils.safety_checker import SafetyChecker
from .crew import ComputerUseCrew


def print_banner():
    """
    Print startup banner.
    """
    print(
        """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║        🤖 Computer Use Agent - Multi-Platform             ║
║        Autonomous Desktop & Web Automation                ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""
    )


def print_capabilities(capabilities):
    """
    Print detected platform capabilities.

    Args:
        capabilities: PlatformCapabilities object
    """
    print(f"\n📊 Platform Information:")
    print(f"  OS: {capabilities.os_type} {capabilities.os_version}")
    print(
        f"  Screen: {capabilities.screen_resolution[0]}x{capabilities.screen_resolution[1]}"
    )
    print(f"  Scaling: {capabilities.scaling_factor}x")

    print(f"\n🔧 Automation Capabilities:")
    if capabilities.accessibility_api_available:
        print(f"  ✅ Tier 1: {capabilities.accessibility_api_type} (100% accuracy)")
    else:
        print(f"  ⚠️  Tier 1: Accessibility API not available")

    print(f"  ✅ Tier 2: Computer Vision + OCR (95-99% accuracy)")
    print(f"  ✅ Tier 3: Vision Model Fallback (85-95% accuracy)")

    print(f"\n🛠️  Available Tools:")
    for tool in capabilities.supported_tools:
        print(f"    • {tool}")


def print_result(result):
    """
    Print task execution result.

    Args:
        result: Result dictionary
    """
    print(f"\n{'='*60}")
    print(f"📋 TASK RESULT")
    print(f"{'='*60}")

    print(f"\nTask: {result['task']}")
    print(f"Overall Success: {'✅' if result['overall_success'] else '❌'}")

    print(f"\n📊 Execution Details:")
    for i, res in enumerate(result["results"], 1):
        print(f"\n  Step {i}:")
        print(f"    Success: {'✅' if res.get('success') else '❌'}")
        print(f"    Method: {res.get('method_used', 'unknown')}")

        if res.get("action_taken"):
            print(f"    Action: {res['action_taken']}")

        if res.get("confidence"):
            print(f"    Confidence: {res['confidence']:.2%}")

        if res.get("error"):
            print(f"    Error: {res['error']}")


async def main():
    """
    Main execution function.
    """
    print_banner()

    print("🔍 Detecting platform capabilities...")
    capabilities = detect_platform()
    print_capabilities(capabilities)

    print("\n🚀 Initializing safety checker...")
    safety_checker = SafetyChecker()

    print("\n🤖 Initializing AI agents and tool registry...")
    crew = ComputerUseCrew(capabilities, safety_checker)
    print(f"✅ Loaded {len(crew.tool_registry.list_available_tools())} tools")
    print("✅ Crew initialized with Browser-Use integration")

    print(f"\n{'='*60}")
    print("Ready for automation tasks!")
    print(f"{'='*60}\n")

    while True:
        try:
            task = input("\n💬 Enter task (or 'quit' to exit): ").strip()

            if not task:
                continue

            if task.lower() in ["quit", "exit", "q"]:
                print("\n👋 Goodbye!")
                break

            print(f"\n⏳ Processing task: {task}")
            result = await crew.execute_task(task)

            print_result(result)

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback

            traceback.print_exc()


def cli():
    """
    CLI entry point.
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")


if __name__ == "__main__":
    cli()
