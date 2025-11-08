"""
Pytest configuration and fixtures.
"""

import sys
from pathlib import Path


def pytest_configure(config):
    """Configure pytest."""
    # Add src to path
    src_path = Path(__file__).parent.parent / "src"
    sys.path.insert(0, str(src_path))
    
    print("\n" + "=" * 80)
    print("🧪 PYTEST CONFIGURATION")
    print("=" * 80)
    print(f"   Python: {sys.version.split()[0]}")
    print(f"   Platform: {sys.platform}")
    print(f"   Src path: {src_path}")
    print("=" * 80 + "\n")


def pytest_collection_modifyitems(config, items):
    """
    Modify test items to add helpful markers.
    """
    for item in items:
        # Add markers based on test name
        if "accessibility" in item.nodeid.lower():
            item.add_marker("accessibility")
        if "ocr" in item.nodeid.lower():
            item.add_marker("ocr")
        if "screenshot" in item.nodeid.lower():
            item.add_marker("screenshot")
        if "integration" in item.nodeid.lower():
            item.add_marker("integration")

