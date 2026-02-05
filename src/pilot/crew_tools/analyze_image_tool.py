"""
Provider-agnostic image analysis tool for CrewAI.
Works with OpenAI, Anthropic, and Google Gemini vision models.
"""

import base64
import io
import os

from PIL import Image
from crewai.tools import BaseTool
from pydantic import Field


def compress_image_for_analysis(
    image_path: str, max_size: int = 1024, quality: int = 70
) -> bytes:
    """
    Compress image for LLM analysis to reduce token usage.

    Args:
        image_path: Path to the image file
        max_size: Maximum dimension (width or height) in pixels
        quality: JPEG quality (1-100)

    Returns:
        Compressed image as bytes
    """
    img = Image.open(image_path)

    if max(img.size) > max_size:
        ratio = max_size / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    buffer = io.BytesIO()
    img.convert("RGB").save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    return buffer.read()


class AnalyzeImageTool(BaseTool):
    """
    Analyze an image using vision-capable LLM.
    Works with OpenAI, Anthropic, and Google Gemini.
    """

    name: str = "analyze_image"
    description: str = (
        "Analyze an image and describe its contents. "
        "Pass image_path to get a description. "
        "Optionally pass goal to verify if a specific condition is met "
        "(returns 'ACHIEVED: evidence' or 'NOT ACHIEVED: reason')."
    )
    image_path: str = Field(
        default="",
        description="Path to the image file to analyze",
    )
    goal: str = Field(
        default="",
        description="Optional goal to verify (e.g., 'calculator shows 4')",
    )

    def _run(self, image_path: str = "", goal: str = "") -> str:
        """
        Analyze an image and return a description or goal verification.

        Args:
            image_path: Path to the image file
            goal: Optional goal to verify (e.g., "calculator shows 4")

        Returns:
            If goal provided: "ACHIEVED: evidence" or "NOT ACHIEVED: reason"
            If no goal: General description of image contents
        """
        if not image_path:
            return "Error: No image path provided"

        if not os.path.exists(image_path):
            return f"Error: Image file not found: {image_path}"

        try:
            compressed_bytes = compress_image_for_analysis(image_path)
            image_data = base64.b64encode(compressed_bytes).decode("utf-8")

            provider = os.getenv("VISION_LLM_PROVIDER") or os.getenv(
                "LLM_PROVIDER", "openai"
            )

            if provider == "google":
                return self._analyze_with_gemini(image_data, image_path, goal)
            elif provider == "anthropic":
                return self._analyze_with_anthropic(image_data, image_path, goal)
            else:
                return self._analyze_with_openai(image_data, image_path, goal)

        except Exception as e:
            return f"Error analyzing image: {str(e)}"

    def _build_prompt(self, goal: str) -> str:
        """Build the analysis prompt based on whether a goal is provided."""
        if goal:
            return f"""Analyze this screenshot carefully.

GOAL TO VERIFY: {goal}

Instructions:
1. Describe what you see on screen
2. If there are numbers or text displays, quote them EXACTLY
3. State whether the goal is achieved

Format your response as:
SCREEN STATE: [describe what you see]
DISPLAY VALUE: [exact value shown, or "N/A" if no numeric display]
GOAL STATUS: ACHIEVED or NOT ACHIEVED
EVIDENCE: [why]
"""
        else:
            return (
                "Describe this image in detail. What do you see? "
                "Include any text, UI elements, and notable features. "
                "If there are numeric displays or text fields, quote their exact values."
            )

    def _analyze_with_gemini(self, image_data: str, image_path: str, goal: str) -> str:
        """Analyze image using Google Gemini."""
        from google import genai
        from google.genai import types

        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "Error: GOOGLE_API_KEY or GEMINI_API_KEY not found"

        model_name = os.getenv("VISION_LLM_MODEL") or os.getenv(
            "LLM_MODEL", "gemini-2.0-flash-exp"
        )
        if model_name.startswith("gemini/"):
            model_name = model_name[7:]

        image_bytes = compress_image_for_analysis(image_path)
        prompt = self._build_prompt(goal)

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/jpeg",
                ),
                prompt,
            ],
        )

        return response.text

    def _analyze_with_anthropic(
        self, image_data: str, image_path: str, goal: str
    ) -> str:
        """Analyze image using Anthropic Claude."""
        from anthropic import Anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return "Error: ANTHROPIC_API_KEY not found"

        client = Anthropic(api_key=api_key)
        model_name = os.getenv("VISION_LLM_MODEL") or "claude-3-5-sonnet-20241022"
        prompt = self._build_prompt(goal)

        response = client.messages.create(
            model=model_name,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                }
            ],
        )

        return response.content[0].text

    def _analyze_with_openai(self, image_data: str, image_path: str, goal: str) -> str:
        """Analyze image using OpenAI GPT-4 Vision."""
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "Error: OPENAI_API_KEY not found"

        client = OpenAI(api_key=api_key)
        model_name = os.getenv("VISION_LLM_MODEL") or "gpt-4o"
        prompt = self._build_prompt(goal)

        response = client.responses.create(
            model=model_name,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": prompt,
                        },
                        {
                            "type": "input_image",
                            "image_url": f"data:image/jpeg;base64,{image_data}",
                        },
                    ],
                }
            ],
        )

        return response.output_text
