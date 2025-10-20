"""
Basic usage examples for Computer Use Agent.
"""

import asyncio
from computer_use.utils.platform_detector import detect_platform
from computer_use.utils.safety_checker import SafetyChecker
from computer_use.crew import ComputerUseCrew


async def example_browser_task():
    """
    Example: Browser automation task.
    """
    print("\n" + "=" * 60)
    print("Example 1: Browser Task")
    print("=" * 60)

    capabilities = detect_platform()
    safety_checker = SafetyChecker()

    crew = ComputerUseCrew(capabilities, safety_checker)

    task = "Download HD image of Cristiano Ronaldo"
    print(f"\nTask: {task}")

    result = await crew.execute_task(task)
    print(f"\nSuccess: {result['overall_success']}")


async def example_gui_task():
    """
    Example: GUI automation task.
    """
    print("\n" + "=" * 60)
    print("Example 2: GUI Task")
    print("=" * 60)

    capabilities = detect_platform()
    safety_checker = SafetyChecker()

    crew = ComputerUseCrew(capabilities, safety_checker)

    task = "Open Calculator app"
    print(f"\nTask: {task}")

    result = await crew.execute_task(task)
    print(f"\nSuccess: {result['overall_success']}")


async def example_system_task():
    """
    Example: System operation task.
    """
    print("\n" + "=" * 60)
    print("Example 3: System Task")
    print("=" * 60)

    capabilities = detect_platform()
    safety_checker = SafetyChecker()

    crew = ComputerUseCrew(capabilities, safety_checker)

    task = "Create a new folder named 'test_folder' in Downloads"
    print(f"\nTask: {task}")

    result = await crew.execute_task(task)
    print(f"\nSuccess: {result['overall_success']}")


async def main():
    """
    Run all examples.
    """
    print("\n🤖 Computer Use Agent - Usage Examples\n")

    print("Note: Make sure you have configured your .env file with API keys")
    print("before running these examples.\n")

    try:
        await example_browser_task()
    except Exception as e:
        print(f"Error in browser task: {e}")

    try:
        await example_gui_task()
    except Exception as e:
        print(f"Error in GUI task: {e}")

    try:
        await example_system_task()
    except Exception as e:
        print(f"Error in system task: {e}")


if __name__ == "__main__":
    asyncio.run(main())
