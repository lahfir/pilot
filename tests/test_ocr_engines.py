"""
Tests for OCR engines - diagnose why Vision API is failing and falling back to EasyOCR.
"""

import platform
import pytest
from PIL import Image, ImageDraw, ImageFont


class TestOCREngines:
    """Test OCR engine availability and functionality."""

    @pytest.fixture
    def test_image(self):
        """
        Create a test image with text for OCR testing.

        Returns:
            PIL Image with "Hello World" text
        """
        img = Image.new("RGB", (400, 100), color="white")
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
        except Exception:
            font = ImageFont.load_default()

        draw.text((50, 30), "Hello World", fill="black", font=font)
        return img

    def test_macos_vision_availability(self):
        """
        Test if macOS Vision Framework is available and working.

        This test will diagnose WHY Vision API might be failing.
        """
        if platform.system().lower() != "darwin":
            pytest.skip("Vision Framework only available on macOS")

        print("\n" + "=" * 80)
        print("🔍 TESTING MACOS VISION FRAMEWORK AVAILABILITY")
        print("=" * 80)

        # Test 1: Check if Vision module can be imported
        try:
            import Vision

            assert Vision is not None
            print("✅ Vision module imported successfully")
        except ImportError as e:
            pytest.fail(
                f"❌ Vision module import failed: {e}\n"
                f"   Install with: pip install pyobjc-framework-Vision"
            )

        # Test 2: Check if Quartz module can be imported
        try:
            import Quartz

            assert Quartz is not None
            print("✅ Quartz module imported successfully")
        except ImportError as e:
            pytest.fail(
                f"❌ Quartz module import failed: {e}\n"
                f"   Install with: pip install pyobjc-framework-Quartz"
            )

        # Test 3: Check if Foundation module can be imported
        try:
            from Foundation import NSData, NSURL

            assert NSData is not None
            assert NSURL is not None
            print("✅ Foundation module imported successfully")
        except ImportError as e:
            pytest.fail(
                f"❌ Foundation module import failed: {e}\n"
                f"   Install with: pip install pyobjc-framework-Cocoa"
            )

        # Test 4: Check if Vision engine initializes
        try:
            from computer_use.tools.vision.macos_vision_ocr import MacOSVisionOCR

            engine = MacOSVisionOCR()
            print("✅ MacOSVisionOCR initialized")
            print(f"   - vision_available: {engine.vision_available}")
            assert engine.vision_available, (
                "Vision framework should be available but isn't"
            )
        except Exception as e:
            pytest.fail(f"❌ MacOSVisionOCR initialization failed: {e}")

        # Test 5: Check is_available() method
        assert engine.is_available(), "is_available() should return True"
        print("✅ is_available() returns True")

        print("=" * 80)

    def test_macos_vision_ocr_functionality(self, test_image):
        """
        Test if Vision Framework can actually recognize text.

        This will show if Vision API works but is failing at recognition.
        """
        if platform.system().lower() != "darwin":
            pytest.skip("Vision Framework only available on macOS")

        print("\n" + "=" * 80)
        print("🔍 TESTING MACOS VISION OCR FUNCTIONALITY")
        print("=" * 80)

        from computer_use.tools.vision.macos_vision_ocr import MacOSVisionOCR

        engine = MacOSVisionOCR()
        if not engine.is_available():
            pytest.skip("Vision Framework not available")

        print(f"📸 Test image size: {test_image.size}")

        # Attempt OCR
        results = engine.recognize_text(test_image)

        print("📝 OCR Results:")
        print(f"   - Number of text items: {len(results)}")

        if results:
            for i, result in enumerate(results):
                print(
                    f"   - Item {i + 1}: '{result.text}' (confidence: {result.confidence:.2f})"
                )

            # Check if we found "Hello World"
            text = " ".join([r.text for r in results])
            assert "Hello" in text or "World" in text, (
                f"Expected to find 'Hello World' but got: {text}"
            )
            print("✅ Vision OCR successfully recognized text!")
        else:
            pytest.fail(
                "❌ Vision OCR returned no results - THIS IS WHY IT'S FALLING BACK!"
            )

        print("=" * 80)

    def test_ocr_factory_selection(self):
        """
        Test which OCR engine the factory selects and why.
        """
        print("\n" + "=" * 80)
        print("🔍 TESTING OCR FACTORY ENGINE SELECTION")
        print("=" * 80)

        from computer_use.tools.vision.ocr_factory import (
            create_ocr_engine,
            get_all_available_ocr_engines,
        )

        # Get all available engines
        all_engines = get_all_available_ocr_engines()
        print(f"\n📋 All available engines ({len(all_engines)}):")
        for i, engine in enumerate(all_engines, 1):
            engine_name = engine.__class__.__name__
            print(f"   {i}. {engine_name}")

        # Get the selected engine
        print("\n🎯 Selected engine by factory:")
        selected_engine = create_ocr_engine()

        if selected_engine:
            engine_name = selected_engine.__class__.__name__
            print(f"   Engine: {engine_name}")

            # Check if it's Vision or fallback
            if platform.system().lower() == "darwin":
                if "Vision" not in engine_name:
                    print(
                        f"   ⚠️  WARNING: Not using Vision! Using {engine_name} instead"
                    )
                    print("   This is why you're seeing EasyOCR fallback!")
                else:
                    print("   ✅ Using Vision Framework as expected")
        else:
            pytest.fail("❌ No OCR engine created!")

        print("=" * 80)

    def test_all_ocr_engines_on_same_image(self, test_image):
        """
        Test all available OCR engines on the same image to compare.

        This will show which engines work and which don't.
        """
        print("\n" + "=" * 80)
        print("🔍 TESTING ALL OCR ENGINES ON SAME IMAGE")
        print("=" * 80)

        from computer_use.tools.vision.ocr_factory import get_all_available_ocr_engines

        engines = get_all_available_ocr_engines()

        if not engines:
            pytest.skip("No OCR engines available")

        results_by_engine = {}

        for engine in engines:
            engine_name = engine.__class__.__name__
            print(f"\n🧪 Testing {engine_name}...")

            try:
                results = engine.recognize_text(test_image)
                results_by_engine[engine_name] = results

                print(f"   - Found {len(results)} text items")
                if results:
                    text = " ".join([r.text for r in results])
                    print(f"   - Text: {text}")
                    print(f"   ✅ {engine_name} works!")
                else:
                    print(f"   ⚠️  {engine_name} returned no results")
            except Exception as e:
                print(f"   ❌ {engine_name} failed: {e}")
                results_by_engine[engine_name] = None

        # Summary
        print("\n📊 SUMMARY:")
        working_engines = [
            name for name, results in results_by_engine.items() if results
        ]
        failing_engines = [
            name for name, results in results_by_engine.items() if not results
        ]

        print(
            f"   ✅ Working: {', '.join(working_engines) if working_engines else 'None'}"
        )
        print(
            f"   ❌ Failing: {', '.join(failing_engines) if failing_engines else 'None'}"
        )

        print("=" * 80)

    def test_vision_framework_dependencies(self):
        """
        Test all Vision Framework dependencies to find missing pieces.
        """
        if platform.system().lower() != "darwin":
            pytest.skip("Vision Framework only available on macOS")

        print("\n" + "=" * 80)
        print("🔍 TESTING VISION FRAMEWORK DEPENDENCIES")
        print("=" * 80)

        dependencies = {
            "Vision": "pyobjc-framework-Vision",
            "Quartz": "pyobjc-framework-Quartz",
            "Foundation": "pyobjc-framework-Cocoa",
            "AppKit": "pyobjc-framework-Cocoa",
        }

        missing = []

        for module_name, package_name in dependencies.items():
            try:
                __import__(module_name)
                print(f"✅ {module_name} available")
            except ImportError:
                print(
                    f"❌ {module_name} MISSING - install with: pip install {package_name}"
                )
                missing.append((module_name, package_name))

        if missing:
            packages = " ".join([pkg for _, pkg in missing])
            pytest.fail(
                f"\n\n{'=' * 80}\n"
                f"❌ MISSING DEPENDENCIES FOUND!\n"
                f"   This is why Vision Framework is failing.\n"
                f"   Install with: pip install {packages}\n"
                f"{'=' * 80}\n"
            )

        print("=" * 80)
