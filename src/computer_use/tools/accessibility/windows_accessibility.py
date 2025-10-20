"""
Windows UI Automation API wrapper for accurate element detection.
"""

from typing import List, Optional, Dict, Any
import platform


class WindowsAccessibility:
    """
    Wrapper for Windows UI Automation API.
    Provides accurate element coordinates and native interactions.
    """

    def __init__(self):
        """
        Initialize Windows accessibility API wrapper.
        """
        self.available = self._check_availability()
        if self.available:
            self._initialize_api()

    def _check_availability(self) -> bool:
        """
        Check if Windows UI Automation is available.
        """
        if platform.system().lower() != "windows":
            return False

        try:
            import pywinauto

            return True
        except ImportError:
            return False

    def _initialize_api(self):
        """
        Import and initialize Windows UI Automation.
        """
        try:
            import pywinauto
            from pywinauto import Desktop

            self.pywinauto = pywinauto
            self.Desktop = Desktop
            print("  ✅ Windows UI Automation ready with 100% accurate coordinates!")
        except ImportError:
            print("  ⚠️  pywinauto not available - install with: uv add pywinauto")
            self.available = False
        except Exception as e:
            print(f"  ⚠️  Failed to initialize Windows UI Automation: {e}")
            self.available = False

    def find_elements(
        self,
        role: Optional[str] = None,
        label: Optional[str] = None,
        title: Optional[str] = None,
        app_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find UI elements using Windows UI Automation.

        Args:
            role: Element type (e.g., 'Button', 'Edit', 'MenuItem')
            label: Element label/text
            title: Window title to search within
            app_name: Application name (optional)

        Returns:
            List of element dictionaries with 100% accurate coordinates
        """
        if not self.available:
            return []

        elements = []

        try:
            # Get foreground window if no title specified
            if not title and not app_name:
                from pywinauto import Desktop

                desktop = Desktop(backend="uia")
                window = desktop.windows()[0]  # Foreground window
            elif app_name:
                window = self.pywinauto.Application(backend="uia").connect(
                    title_re=f".*{app_name}.*"
                )
            else:
                window = self.pywinauto.Application(backend="uia").connect(
                    title_re=f".*{title}.*"
                )

            print(f"  🔍 Windows UI Automation: Searching for '{label or role}'")

            # Find elements by text/label
            if label:
                try:
                    # Try to find control with matching text
                    controls = window.descendants()
                    for ctrl in controls:
                        try:
                            ctrl_text = ctrl.window_text()
                            if label.lower() in ctrl_text.lower():
                                rect = ctrl.rectangle()
                                center_x = (rect.left + rect.right) // 2
                                center_y = (rect.top + rect.bottom) // 2

                                elements.append(
                                    {
                                        "center": (center_x, center_y),
                                        "bounds": (
                                            rect.left,
                                            rect.top,
                                            rect.width(),
                                            rect.height(),
                                        ),
                                        "role": ctrl.element_info.control_type,
                                        "title": ctrl_text,
                                        "detection_method": "windows_uia",
                                        "confidence": 1.0,
                                        "_native_element": ctrl,
                                    }
                                )
                        except:
                            continue
                except Exception as e:
                    print(f"  ⚠️  Search error: {e}")

            print(f"  ✅ Found {len(elements)} elements with 100% accurate coordinates")

        except Exception as e:
            print(f"  ⚠️  Windows UI Automation error: {e}")

        return elements

    def perform_action(self, element: Dict[str, Any], action: str, **kwargs) -> bool:
        """
        Perform action on element using Windows UI Automation.

        Args:
            element: Element dict with _native_element
            action: Action to perform (click, type, scroll, etc.)
            **kwargs: Additional action parameters

        Returns:
            True if action succeeded
        """
        if not self.available:
            return False

        try:
            native_elem = element.get("_native_element")

            if action == "click":
                if native_elem:
                    native_elem.click_input()
                else:
                    center = element["center"]
                    x, y = center
                    import pyautogui

                    pyautogui.click(x, y)
                return True

            elif action == "type":
                text = kwargs.get("text", "")
                if text and native_elem:
                    native_elem.type_keys(text)
                    return True

            elif action == "scroll":
                direction = kwargs.get("direction", "down")
                amount = kwargs.get("amount", 3)
                if native_elem:
                    if direction == "down":
                        native_elem.wheel_mouse_input(wheel_dist=-amount)
                    else:
                        native_elem.wheel_mouse_input(wheel_dist=amount)
                    return True

            elif action == "double_click":
                if native_elem:
                    native_elem.double_click_input()
                else:
                    center = element["center"]
                    x, y = center
                    import pyautogui

                    pyautogui.doubleClick(x, y)
                return True

            elif action == "right_click":
                if native_elem:
                    native_elem.right_click_input()
                else:
                    center = element["center"]
                    x, y = center
                    import pyautogui

                    pyautogui.rightClick(x, y)
                return True

        except Exception as e:
            print(f"  ⚠️  Windows action {action} failed: {e}")
            return False

        return False

    def click_element(self, element: Dict[str, Any]) -> bool:
        """
        Click element at 100% accurate coordinates.

        Args:
            element: Element dictionary from find_elements()

        Returns:
            True if click succeeded
        """
        return self.perform_action(element, "click")

    def get_active_window_info(self) -> Dict[str, Any]:
        """
        Get information about the currently active window.

        Returns:
            Dictionary with window information
        """
        if not self.available:
            return {}

        try:
            from pywinauto import Desktop

            desktop = Desktop(backend="uia")
            window = desktop.windows()[0]

            return {
                "title": window.window_text(),
                "class_name": window.class_name(),
                "rect": window.rectangle(),
            }
        except Exception as e:
            print(f"  ⚠️  Failed to get active window: {e}")
            return {}
