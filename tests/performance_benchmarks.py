"""
Performance Benchmarks for Computer-Use Project.

Measures execution time of critical operations before and after optimizations.
Run this file before and after applying optimizations to compare results.

Usage:
    python tests/performance_benchmarks.py --save-baseline
    python tests/performance_benchmarks.py --compare

Results are saved to tests/benchmark_results/ directory.
"""

import argparse
import gc
import json
import os
import statistics
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

RESULTS_DIR = Path(__file__).parent / "benchmark_results"
RESULTS_DIR.mkdir(exist_ok=True)


@dataclass
class BenchmarkResult:
    """Result of a single benchmark."""

    name: str
    times: List[float] = field(default_factory=list)
    iterations: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def mean(self) -> float:
        """Mean execution time in milliseconds."""
        return statistics.mean(self.times) * 1000 if self.times else 0

    @property
    def median(self) -> float:
        """Median execution time in milliseconds."""
        return statistics.median(self.times) * 1000 if self.times else 0

    @property
    def std_dev(self) -> float:
        """Standard deviation in milliseconds."""
        if len(self.times) < 2:
            return 0
        return statistics.stdev(self.times) * 1000

    @property
    def min_time(self) -> float:
        """Minimum execution time in milliseconds."""
        return min(self.times) * 1000 if self.times else 0

    @property
    def max_time(self) -> float:
        """Maximum execution time in milliseconds."""
        return max(self.times) * 1000 if self.times else 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "iterations": self.iterations,
            "mean_ms": round(self.mean, 2),
            "median_ms": round(self.median, 2),
            "std_dev_ms": round(self.std_dev, 2),
            "min_ms": round(self.min_time, 2),
            "max_ms": round(self.max_time, 2),
            "error_count": len(self.errors),
        }


class PerformanceBenchmark:
    """
    Performance benchmark suite for computer-use operations.

    Measures initialization times, tool operations, and overall latency
    to enable before/after optimization comparisons.
    """

    def __init__(self, warmup_iterations: int = 1, test_iterations: int = 5):
        """
        Initialize benchmark suite.

        Args:
            warmup_iterations: Number of warmup runs before measuring
            test_iterations: Number of measured iterations per benchmark
        """
        self.warmup_iterations = warmup_iterations
        self.test_iterations = test_iterations
        self.results: Dict[str, BenchmarkResult] = {}

    def _run_benchmark(
        self,
        name: str,
        func: Callable,
        setup: Optional[Callable] = None,
        teardown: Optional[Callable] = None,
    ) -> BenchmarkResult:
        """
        Run a single benchmark with warmup and multiple iterations.

        Args:
            name: Benchmark name
            func: Function to benchmark
            setup: Optional setup function called before each iteration
            teardown: Optional teardown function called after each iteration

        Returns:
            BenchmarkResult with timing data
        """
        result = BenchmarkResult(name=name)

        for _ in range(self.warmup_iterations):
            try:
                if setup:
                    setup()
                func()
                if teardown:
                    teardown()
            except Exception:
                pass
            gc.collect()

        for i in range(self.test_iterations):
            try:
                if setup:
                    setup()

                gc.collect()
                start = time.perf_counter()
                func()
                end = time.perf_counter()

                result.times.append(end - start)
                result.iterations += 1

                if teardown:
                    teardown()
            except Exception as e:
                result.errors.append(f"Iteration {i}: {str(e)}")

            gc.collect()

        self.results[name] = result
        return result

    def benchmark_module_import(self) -> BenchmarkResult:
        """Benchmark importing the main module."""

        def import_module():
            import importlib

            if "computer_use" in sys.modules:
                del sys.modules["computer_use"]
            if "computer_use.crew" in sys.modules:
                del sys.modules["computer_use.crew"]
            importlib.import_module("computer_use.crew")

        return self._run_benchmark("module_import", import_module)

    def benchmark_ocr_initialization(self) -> BenchmarkResult:
        """Benchmark OCR engine initialization."""

        def init_ocr():
            from computer_use.tools.vision.ocr_factory import create_ocr_engine

            engine = create_ocr_engine(use_gpu=False)
            return engine

        return self._run_benchmark("ocr_initialization", init_ocr)

    def benchmark_paddleocr_initialization(self) -> BenchmarkResult:
        """Benchmark PaddleOCR engine initialization specifically."""

        def init_paddle():
            from computer_use.tools.vision.paddleocr_engine import PaddleOCREngine

            engine = PaddleOCREngine(use_gpu=False)
            return engine

        return self._run_benchmark("paddleocr_initialization", init_paddle)

    def benchmark_accessibility_initialization(self) -> BenchmarkResult:
        """Benchmark accessibility API initialization."""
        import platform

        system = platform.system().lower()

        def init_accessibility():
            if system == "darwin":
                from computer_use.tools.accessibility.macos_accessibility import (
                    MacOSAccessibility,
                )

                return MacOSAccessibility(1920, 1080)
            elif system == "windows":
                from computer_use.tools.accessibility.windows_accessibility import (
                    WindowsAccessibility,
                )

                return WindowsAccessibility(1920, 1080)
            else:
                from computer_use.tools.accessibility.linux_accessibility import (
                    LinuxAccessibility,
                )

                return LinuxAccessibility(1920, 1080)

        return self._run_benchmark("accessibility_initialization", init_accessibility)

    def benchmark_screenshot_capture(self) -> BenchmarkResult:
        """Benchmark screenshot capture."""
        from computer_use.tools.screenshot_tool import ScreenshotTool

        tool = ScreenshotTool()

        def capture():
            return tool.capture()

        return self._run_benchmark("screenshot_capture", capture)

    def benchmark_screenshot_region_capture(self) -> BenchmarkResult:
        """Benchmark region-specific screenshot capture."""
        from computer_use.tools.screenshot_tool import ScreenshotTool

        tool = ScreenshotTool()

        def capture_region():
            return tool.capture(region=(0, 0, 200, 200))

        return self._run_benchmark("screenshot_region_capture", capture_region)

    def benchmark_ocr_text_extraction(self) -> BenchmarkResult:
        """Benchmark OCR text extraction from screenshot."""
        from PIL import Image

        from computer_use.tools.vision.ocr_tool import OCRTool

        ocr = OCRTool()
        test_image = Image.new("RGB", (800, 600), color=(255, 255, 255))

        def extract_text():
            return ocr.extract_all_text(test_image)

        return self._run_benchmark("ocr_text_extraction", extract_text)

    def benchmark_accessibility_element_discovery(self) -> BenchmarkResult:
        """Benchmark accessibility element discovery."""
        import platform

        system = platform.system().lower()

        if system == "darwin":
            from computer_use.tools.accessibility.macos_accessibility import (
                MacOSAccessibility,
            )

            accessibility = MacOSAccessibility()
        elif system == "windows":
            from computer_use.tools.accessibility.windows_accessibility import (
                WindowsAccessibility,
            )

            accessibility = WindowsAccessibility()
        else:
            return BenchmarkResult(
                name="accessibility_element_discovery",
                errors=["Linux accessibility benchmark not supported"],
            )

        if not accessibility.available:
            return BenchmarkResult(
                name="accessibility_element_discovery",
                errors=["Accessibility API not available"],
            )

        def get_elements():
            return accessibility.get_elements("Finder", interactive_only=True)

        return self._run_benchmark("accessibility_element_discovery", get_elements)

    def benchmark_accessibility_element_discovery_cached(self) -> BenchmarkResult:
        """Benchmark accessibility element discovery with caching."""
        import platform

        system = platform.system().lower()

        if system == "darwin":
            from computer_use.tools.accessibility.macos_accessibility import (
                MacOSAccessibility,
            )

            accessibility = MacOSAccessibility()
        elif system == "windows":
            from computer_use.tools.accessibility.windows_accessibility import (
                WindowsAccessibility,
            )

            accessibility = WindowsAccessibility()
        else:
            return BenchmarkResult(
                name="accessibility_element_discovery_cached",
                errors=["Linux accessibility benchmark not supported"],
            )

        if not accessibility.available:
            return BenchmarkResult(
                name="accessibility_element_discovery_cached",
                errors=["Accessibility API not available"],
            )

        accessibility.get_elements("Finder", interactive_only=True, use_cache=False)

        def get_elements_cached():
            return accessibility.get_elements(
                "Finder", interactive_only=True, use_cache=True
            )

        return self._run_benchmark(
            "accessibility_element_discovery_cached", get_elements_cached
        )

    def benchmark_pyautogui_click(self) -> BenchmarkResult:
        """Benchmark pyautogui click operation (measures PAUSE overhead)."""
        import pyautogui

        original_pause = pyautogui.PAUSE

        def click_operation():
            pyautogui.click(100, 100, _pause=True)

        result = self._run_benchmark("pyautogui_click", click_operation)
        pyautogui.PAUSE = original_pause
        return result

    def benchmark_input_tool_click(self) -> BenchmarkResult:
        """Benchmark InputTool click operation."""
        from computer_use.tools.input_tool import InputTool

        tool = InputTool()

        def click():
            tool.click(100, 100, validate=False)

        return self._run_benchmark("input_tool_click", click)

    def benchmark_input_tool_type(self) -> BenchmarkResult:
        """Benchmark InputTool typing operation."""
        from computer_use.tools.input_tool import InputTool

        tool = InputTool()

        def type_text():
            tool.type_text("hello", interval=0.01)

        return self._run_benchmark("input_tool_type", type_text)

    def benchmark_platform_registry_initialization(self) -> BenchmarkResult:
        """Benchmark PlatformToolRegistry initialization."""
        from computer_use.utils.platform_detector import PlatformCapabilities

        capabilities = PlatformCapabilities()

        def init_registry():
            from computer_use.tools.platform_registry import PlatformToolRegistry

            return PlatformToolRegistry(capabilities)

        return self._run_benchmark("platform_registry_initialization", init_registry)

    def benchmark_crew_initialization(self) -> BenchmarkResult:
        """Benchmark ComputerUseCrew initialization (full system startup)."""
        from computer_use.utils.platform_detector import PlatformCapabilities
        from computer_use.utils.safety_checker import SafetyChecker

        capabilities = PlatformCapabilities()
        safety_checker = SafetyChecker()

        def init_crew():
            from computer_use.crew import ComputerUseCrew

            return ComputerUseCrew(capabilities, safety_checker)

        return self._run_benchmark("crew_initialization", init_crew)

    def benchmark_agent_creation(self) -> BenchmarkResult:
        """Benchmark CrewAI agent creation."""
        from computer_use.utils.platform_detector import PlatformCapabilities
        from computer_use.utils.safety_checker import SafetyChecker

        capabilities = PlatformCapabilities()
        safety_checker = SafetyChecker()

        from computer_use.crew import ComputerUseCrew

        crew = ComputerUseCrew(capabilities, safety_checker)

        def create_agents():
            return crew._create_crewai_agents()

        return self._run_benchmark("agent_creation", create_agents)

    def benchmark_llm_config_get_llm(self) -> BenchmarkResult:
        """Benchmark LLM client initialization."""
        os.environ.setdefault("OPENAI_API_KEY", "test-key-for-benchmark")

        def get_llm():
            from computer_use.config.llm_config import LLMConfig

            try:
                return LLMConfig.get_llm(provider="openai", model="gpt-4o-mini")
            except Exception:
                pass

        return self._run_benchmark("llm_config_get_llm", get_llm)

    def benchmark_timing_config_access(self) -> BenchmarkResult:
        """Benchmark timing configuration access."""

        def get_timing():
            from computer_use.config.timing_config import get_timing_config

            config = get_timing_config()
            _ = config.ui_state_change_delay
            _ = config.app_launch_max_attempts
            return config

        return self._run_benchmark("timing_config_access", get_timing)

    def run_all_benchmarks(self) -> Dict[str, BenchmarkResult]:
        """Run all benchmarks and return results."""
        print("\n" + "=" * 60)
        print("COMPUTER-USE PERFORMANCE BENCHMARK SUITE")
        print("=" * 60)

        benchmarks = [
            ("Module Import", self.benchmark_module_import),
            ("Timing Config Access", self.benchmark_timing_config_access),
            ("Screenshot Capture", self.benchmark_screenshot_capture),
            ("Screenshot Region", self.benchmark_screenshot_region_capture),
            ("Input Tool Click", self.benchmark_input_tool_click),
            ("Input Tool Type", self.benchmark_input_tool_type),
            ("PyAutoGUI Click", self.benchmark_pyautogui_click),
            ("Accessibility Init", self.benchmark_accessibility_initialization),
            ("Accessibility Elements", self.benchmark_accessibility_element_discovery),
            (
                "Accessibility Cached",
                self.benchmark_accessibility_element_discovery_cached,
            ),
            ("OCR Initialization", self.benchmark_ocr_initialization),
            ("OCR Text Extraction", self.benchmark_ocr_text_extraction),
            ("Platform Registry Init", self.benchmark_platform_registry_initialization),
            ("LLM Config Get", self.benchmark_llm_config_get_llm),
            ("Crew Initialization", self.benchmark_crew_initialization),
            ("Agent Creation", self.benchmark_agent_creation),
        ]

        for name, benchmark_func in benchmarks:
            print(f"\n[{name}]", end=" ", flush=True)
            try:
                result = benchmark_func()
                if result.errors:
                    print(f"⚠️  {result.errors[0][:50]}")
                else:
                    print(f"✓ {result.mean:.2f}ms (±{result.std_dev:.2f}ms)")
            except Exception as e:
                print(f"✗ Error: {str(e)[:50]}")
                self.results[name] = BenchmarkResult(name=name, errors=[str(e)])

        return self.results

    def save_results(self, filename: str = None) -> Path:
        """
        Save benchmark results to JSON file.

        Args:
            filename: Optional filename. Defaults to timestamped file.

        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_{timestamp}.json"

        filepath = RESULTS_DIR / filename

        data = {
            "timestamp": datetime.now().isoformat(),
            "warmup_iterations": self.warmup_iterations,
            "test_iterations": self.test_iterations,
            "results": {name: r.to_dict() for name, r in self.results.items()},
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        print(f"\nResults saved to: {filepath}")
        return filepath

    def save_as_baseline(self) -> Path:
        """Save results as the baseline for comparison."""
        return self.save_results("baseline.json")

    @staticmethod
    def load_results(filepath: Path) -> Dict[str, Any]:
        """Load benchmark results from JSON file."""
        with open(filepath, "r") as f:
            return json.load(f)

    @staticmethod
    def compare_results(
        baseline_path: Path, current_path: Path
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compare two benchmark result files.

        Args:
            baseline_path: Path to baseline results
            current_path: Path to current results

        Returns:
            Dictionary with comparison data
        """
        baseline = PerformanceBenchmark.load_results(baseline_path)
        current = PerformanceBenchmark.load_results(current_path)

        comparison = {}

        all_benchmarks = set(baseline["results"].keys()) | set(
            current["results"].keys()
        )

        for name in all_benchmarks:
            base_result = baseline["results"].get(name, {})
            curr_result = current["results"].get(name, {})

            base_mean = base_result.get("mean_ms", 0)
            curr_mean = curr_result.get("mean_ms", 0)

            if base_mean > 0:
                improvement_pct = ((base_mean - curr_mean) / base_mean) * 100
            else:
                improvement_pct = 0

            comparison[name] = {
                "baseline_ms": base_mean,
                "current_ms": curr_mean,
                "difference_ms": round(base_mean - curr_mean, 2),
                "improvement_pct": round(improvement_pct, 1),
                "status": (
                    "improved"
                    if improvement_pct > 5
                    else ("regressed" if improvement_pct < -5 else "unchanged")
                ),
            }

        return comparison

    @staticmethod
    def print_comparison(comparison: Dict[str, Dict[str, Any]]) -> None:
        """Print formatted comparison results."""
        print("\n" + "=" * 80)
        print("PERFORMANCE COMPARISON: BASELINE vs CURRENT")
        print("=" * 80)
        print(
            f"{'Benchmark':<40} {'Baseline':>10} {'Current':>10} {'Change':>10} {'Status':>10}"
        )
        print("-" * 80)

        total_baseline = 0
        total_current = 0

        for name, data in sorted(comparison.items()):
            baseline = data["baseline_ms"]
            current = data["current_ms"]
            diff = data["difference_ms"]
            status = data["status"]

            total_baseline += baseline
            total_current += current

            status_icon = (
                "✓" if status == "improved" else ("✗" if status == "regressed" else "─")
            )
            diff_str = f"{diff:+.1f}ms" if diff != 0 else "0ms"

            print(
                f"{name:<40} {baseline:>9.1f}ms {current:>9.1f}ms {diff_str:>10} {status_icon:>10}"
            )

        print("-" * 80)
        total_diff = total_baseline - total_current
        total_pct = (
            ((total_baseline - total_current) / total_baseline * 100)
            if total_baseline > 0
            else 0
        )
        print(
            f"{'TOTAL':<40} {total_baseline:>9.1f}ms {total_current:>9.1f}ms {total_diff:+.1f}ms {total_pct:+.1f}%"
        )
        print("=" * 80)


def main():
    """Main entry point for benchmark CLI."""
    parser = argparse.ArgumentParser(
        description="Performance benchmarks for computer-use project"
    )
    parser.add_argument(
        "--save-baseline",
        action="store_true",
        help="Run benchmarks and save as baseline",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Run benchmarks and compare with baseline",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Number of test iterations per benchmark",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=1,
        help="Number of warmup iterations",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode: fewer iterations for faster results",
    )

    args = parser.parse_args()

    if args.quick:
        iterations = 2
        warmup = 0
    else:
        iterations = args.iterations
        warmup = args.warmup

    benchmark = PerformanceBenchmark(
        warmup_iterations=warmup,
        test_iterations=iterations,
    )

    benchmark.run_all_benchmarks()

    if args.save_baseline:
        benchmark.save_as_baseline()
        print("\n✓ Baseline saved. Run with --compare after optimizations.")
    elif args.compare:
        baseline_path = RESULTS_DIR / "baseline.json"
        if not baseline_path.exists():
            print("\n✗ No baseline found. Run with --save-baseline first.")
            return 1

        current_path = benchmark.save_results()
        comparison = PerformanceBenchmark.compare_results(baseline_path, current_path)
        PerformanceBenchmark.print_comparison(comparison)
    else:
        benchmark.save_results()

    return 0


if __name__ == "__main__":
    sys.exit(main())
