"""
Main entry point for computer use automation agent.
"""

import asyncio
import sys
from .utils.platform_detector import detect_platform
from .utils.safety_checker import SafetyChecker
from .utils.command_confirmation import CommandConfirmation
from .utils.permissions import check_and_request_permissions
from .utils.logging_config import setup_logging
from .utils.ui import (
    print_banner,
    print_platform_info,
    print_section_header,
    print_task_result,
    console,
)
from .crew import ComputerUseCrew


async def main():
    """
    Main execution function.
    """
    setup_logging()

    print_banner()

    if not check_and_request_permissions():
        console.print("[yellow]Exiting due to missing permissions.[/yellow]")
        sys.exit(1)

    print_section_header("Platform Detection", "🔍")
    capabilities = detect_platform()
    print_platform_info(capabilities)

    print_section_header("Initializing Systems", "🚀")

    console.print("[cyan]• Safety Checker[/cyan]")
    safety_checker = SafetyChecker()

    console.print("[cyan]• Command Confirmation System[/cyan]")
    confirmation_manager = CommandConfirmation()

    console.print("[cyan]• AI Agents & Tool Registry[/cyan]")
    crew = ComputerUseCrew(
        capabilities, safety_checker, confirmation_manager=confirmation_manager
    )
    console.print(
        f"[green]✅ Loaded {len(crew.tool_registry.list_available_tools())} tools[/green]"
    )
    console.print("[green]✅ Crew initialized with Browser-Use integration[/green]")

    print_section_header("Ready for Automation", "✨")

    while True:
        try:
            task = console.input(
                "\n[bold cyan]💬 Enter task (or 'quit' to exit):[/bold cyan] "
            ).strip()

            if not task:
                continue

            if task.lower() in ["quit", "exit", "q"]:
                console.print("\n[bold cyan]👋 Goodbye![/bold cyan]")
                break

            console.print(
                f"\n[bold yellow]⏳ Processing:[/bold yellow] [white]{task}[/white]"
            )
            result = await crew.execute_task(task)

            print_task_result(result)

        except KeyboardInterrupt:
            console.print("\n\n[yellow]⚠️  Interrupted by user[/yellow]")
            break
        except Exception as e:
            console.print(f"\n[red]❌ Error: {e}[/red]")
            import traceback

            traceback.print_exc()


def cli():
    """
    CLI entry point.
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n\n[bold cyan]👋 Goodbye![/bold cyan]")


if __name__ == "__main__":
    cli()
