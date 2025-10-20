"""
Setup script for computer use automation agent.
"""

from setuptools import setup, find_packages

setup(
    name="computer-use",
    version="0.1.0",
    description="Cross-platform computer use agent with multi-tier accuracy system",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Computer Use Team",
    python_requires=">=3.10",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "crewai[tools]>=0.86.0",
        "browser-use>=0.1.0",
        "pydantic>=2.0.0",
        "pillow>=10.0.0",
        "pyautogui>=0.9.54",
        "psutil>=5.9.0",
        "python-dotenv>=1.0.0",
        "opencv-python>=4.8.0",
        "easyocr>=1.7.0",
        "numpy>=1.24.0",
        "pyyaml>=6.0.0",
        "langchain-openai>=0.0.5",
        "langchain-anthropic>=0.1.0",
        "langchain-google-genai>=0.0.5",
        "langchain-community>=0.0.10",
    ],
    extras_require={
        "macos": [
            "pyobjc-framework-ApplicationServices>=10.0",
            "pyobjc-framework-Cocoa>=10.0",
            "pyobjc-framework-Quartz>=10.0",
        ],
        "windows": [
            "pywinauto>=0.6.8",
            "comtypes>=1.2.0",
        ],
        "linux": [
            "python-atspi>=2.46.0",
            "python-xlib>=0.33",
        ],
    },
    entry_points={
        "console_scripts": [
            "computer-use=computer_use.main:cli",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)

