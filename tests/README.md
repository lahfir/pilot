# Computer-Use Tests

Comprehensive test suite for the computer-use automation framework.

## Test Categories

### 1. OCR Engine Tests (`test_ocr_engines.py`)

**Purpose:** Diagnose why macOS Vision Framework is failing and falling back to EasyOCR.

Tests:

- ✅ Vision Framework dependency availability
- ✅ Vision Framework initialization
- ✅ Vision OCR functionality
- ✅ OCR factory engine selection
- ✅ Comparison of all OCR engines
- ✅ Missing dependencies detection

**Run:** `pytest tests/test_ocr_engines.py -v`

### 2. Accessibility API Tests (`test_accessibility.py`)

**Purpose:** Verify if Accessibility API is actually being used for clicking.

Tests:

- ✅ atomacos library availability
- ✅ Accessibility permissions
- ✅ MacOSAccessibility class initialization
- ✅ Element discovery
- ✅ Accessibility vs OCR in click tool
- ✅ Window focus detection
- ✅ Complete accessibility workflow

**Run:** `pytest tests/test_accessibility.py -v`

### 3. Screenshot Tool Tests (`test_screenshot.py`)

**Purpose:** Verify screenshot tool captures actual windows, not overlapping content.

Tests:

- ✅ Screenshot tool initialization
- ✅ Fullscreen capture
- ✅ Window-specific capture (Finder)
- ✅ Actual window vs overlapping content (critical fix verification)
- ✅ Window capture → OCR sequence
- ✅ Region capture

**Run:** `pytest tests/test_screenshot.py -v`

### 4. Integration Tests (`test_integration.py`)

**Purpose:** Test complete workflows end-to-end.

Tests:

- ✅ Complete Finder workflow (focus → screenshot → OCR → verify)
- ✅ read_screen_text tool integration
- ✅ Multi-tier click system (accessibility → OCR fallback)
- ✅ OCR engine selection integration

**Run:** `pytest tests/test_integration.py -v`

## Running Tests

### Run All Tests

```bash
cd /Users/lahfir/Documents/Projects/computer-use
pytest tests/ -v
```

### Run Specific Test Category

```bash
# OCR tests
pytest tests/test_ocr_engines.py -v

# Accessibility tests
pytest tests/test_accessibility.py -v

# Screenshot tests
pytest tests/test_screenshot.py -v

# Integration tests
pytest tests/test_integration.py -v
```

### Run Tests by Marker

```bash
# Only OCR tests
pytest -m ocr -v

# Only accessibility tests
pytest -m accessibility -v

# Only integration tests
pytest -m integration -v
```

### Run Specific Test

```bash
pytest tests/test_ocr_engines.py::TestOCREngines::test_macos_vision_availability -v
```

## Common Issues and Fixes

### Issue: Vision Framework Failing

**Symptoms:**

- Tests show "Vision Framework not available"
- System uses EasyOCR instead

**Solution:**

```bash
pip install pyobjc-framework-Vision pyobjc-framework-Quartz pyobjc-framework-Cocoa
```

### Issue: Accessibility Not Working

**Symptoms:**

- Tests show "Accessibility permissions not granted"
- Clicks use OCR instead of Accessibility API

**Solution:**

1. Open System Settings
2. Go to Privacy & Security → Accessibility
3. Add your terminal app (Terminal, iTerm, Cursor, etc.)
4. Make sure it's checked/enabled
5. Restart terminal and run tests again

**Also need:**

```bash
pip install atomacos
```

### Issue: Window Capture Returns Wrong Content

**Symptoms:**

- Screenshot says "Captured Finder" but OCR reads VS Code text
- read_screen_text fails with "window not found"

**Solution:**

- This was the bug fixed in `screenshot_tool.py`
- Run: `pytest tests/test_screenshot.py::TestScreenshotTool::test_window_capture_captures_actual_window_not_overlapping_content -v`
- If this test fails, the fix didn't work

## Test Output Interpretation

### ✅ Green/Passing

- Feature is working correctly
- No action needed

### ⚠️ Yellow/Warning

- Feature is working but with fallbacks
- Example: "Using OCR fallback (accessibility not available)"
- Not critical but could be improved

### ❌ Red/Failing

- Feature is broken
- Fix required
- Test output will show:
  - What failed
  - Why it failed
  - How to fix it

## Continuous Testing

### Watch Mode (reruns tests on file changes)

```bash
pip install pytest-watch
ptw tests/ -- -v
```

### With Coverage

```bash
pip install pytest-cov
pytest tests/ --cov=src/computer_use --cov-report=html --cov-report=term
```

View coverage report: `open htmlcov/index.html`

## Writing New Tests

### Template

```python
def test_my_feature(self):
    """
    Test description here.
    """
    print("\n" + "=" * 80)
    print("🔍 TESTING MY FEATURE")
    print("=" * 80)

    # Test code here

    print("=" * 80)
```

### Best Practices

1. **Clear test names**: `test_accessibility_permissions_granted`
2. **Docstrings**: Explain what the test checks
3. **Print output**: Help diagnose failures
4. **Assertions**: Clear failure messages
5. **Skip when needed**: Use `@pytest.mark.skipif` for platform-specific tests

## Troubleshooting

### pytest not found

```bash
pip install pytest
```

### Import errors

```bash
# Make sure you're in the project root
cd /Users/lahfir/Documents/Projects/computer-use

# Run with python -m
python -m pytest tests/ -v
```

### Permission errors (macOS)

```bash
# Grant accessibility permissions to terminal
# See "Common Issues and Fixes" above
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Run tests
  run: |
    pip install pytest
    pytest tests/ -v
```

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
pytest tests/ --tb=short -q
```
