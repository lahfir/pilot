"""
Provider-agnostic image analysis tool for CrewAI.
Works with OpenAI, Anthropic, and Google Gemini vision models.
"""

import base64
import os

from crewai.tools import BaseTool
from pydantic import Field


class AnalyzeImageTool(BaseTool):
    """
    Analyze an image using vision-capable LLM.
    Works with OpenAI, Anthropic, and Google Gemini.
    """

    name: str = "analyze_image"
    description: str = (
        "Analyze an image and describe its contents. "
        "Pass the image file path to get a detailed description."
    )
    image_path: str = Field(
        default="",
        description="Path to the image file to analyze",
    )

    def _run(self, image_path: str = "") -> str:
        """
        Analyze an image and return a description.

        Args:
            image_path: Path to the image file

        Returns:
            Description of the image contents
        """
        if not image_path:
            return "Error: No image path provided"

        if not os.path.exists(image_path):
            return f"Error: Image file not found: {image_path}"

        try:
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            provider = os.getenv("VISION_LLM_PROVIDER") or os.getenv(
                "LLM_PROVIDER", "openai"
            )

            if provider == "google":
                return self._analyze_with_gemini(image_data, image_path)
            elif provider == "anthropic":
                return self._analyze_with_anthropic(image_data)
            else:
                return self._analyze_with_openai(image_data)

        except Exception as e:
            return f"Error analyzing image: {str(e)}"

    def _analyze_with_gemini(self, image_data: str, image_path: str) -> str:
        """Analyze image using Google Gemini."""
        import google.generativeai as genai
        from PIL import Image

        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "Error: GOOGLE_API_KEY or GEMINI_API_KEY not found"

        genai.configure(api_key=api_key)

        model_name = os.getenv("VISION_LLM_MODEL") or os.getenv(
            "LLM_MODEL", "gemini-2.0-flash-exp"
        )
        if model_name.startswith("gemini/"):
            model_name = model_name[7:]

        model = genai.GenerativeModel(model_name)

        image = Image.open(image_path)

        response = model.generate_content(
            [
                "Describe this image in detail. What do you see? "
                "Include any text, UI elements, and notable features.",
                image,
            ]
        )

        return response.text

    def _analyze_with_anthropic(self, image_data: str) -> str:
        """Analyze image using Anthropic Claude."""
        from anthropic import Anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return "Error: ANTHROPIC_API_KEY not found"

        client = Anthropic(api_key=api_key)

        model_name = os.getenv("VISION_LLM_MODEL") or "claude-3-5-sonnet-20241022"

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
                                "media_type": "image/png",
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": "Describe this image in detail. What do you see? "
                            "Include any text, UI elements, and notable features.",
                        },
                    ],
                }
            ],
        )

        return response.content[0].text

    def _analyze_with_openai(self, image_data: str) -> str:
        """Analyze image using OpenAI GPT-4 Vision."""
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "Error: OPENAI_API_KEY not found"

        client = OpenAI(api_key=api_key)

        model_name = os.getenv("VISION_LLM_MODEL") or "gpt-4o"

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe this image in detail. What do you see? "
                            "Include any text, UI elements, and notable features.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_data}",
                            },
                        },
                    ],
                }
            ],
            max_tokens=1024,
        )

        return response.choices[0].message.content
