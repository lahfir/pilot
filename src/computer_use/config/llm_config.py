"""
Provider-agnostic LLM configuration system.
Supports Langchain LLMs for CrewAI agents.
Browser-Use handles its own LLM configuration internally.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Langchain LLMs (for CrewAI agents)
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.llms import Ollama

load_dotenv()


class LLMConfig:
    """
    LLM configuration for CrewAI agents.
    Supports multiple providers: OpenAI, Anthropic, Google, Ollama.

    - General LLM: Used by Coordinator and System agents
    - Vision LLM: Used by GUI agent for screenshot analysis
    """

    @staticmethod
    def get_llm(provider: Optional[str] = None, model: Optional[str] = None):
        """
        Get Langchain LLM for CrewAI agents.

        Args:
            provider: LLM provider (openai, anthropic, google, ollama)
            model: Specific model name

        Returns:
            Langchain LLM instance
        """
        provider = provider or os.getenv("LLM_PROVIDER", "openai")
        model = model or os.getenv("LLM_MODEL")

        if provider == "openai":
            return LLMConfig._get_openai_llm(model)
        elif provider == "anthropic":
            return LLMConfig._get_anthropic_llm(model)
        elif provider == "google":
            return LLMConfig._get_google_llm(model)
        elif provider == "ollama":
            return LLMConfig._get_ollama_llm(model)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    @staticmethod
    def _get_openai_llm(model: Optional[str] = None):
        """Get OpenAI LLM (Langchain)"""
        model_name = model or "gpt-4o-mini"
        return ChatOpenAI(
            model=model_name, temperature=0, api_key=os.getenv("OPENAI_API_KEY")
        )

    @staticmethod
    def _get_anthropic_llm(model: Optional[str] = None):
        """Get Anthropic LLM (Langchain)"""
        model_name = model or "claude-3-5-sonnet-20241022"
        return ChatAnthropic(
            model=model_name, temperature=0, api_key=os.getenv("ANTHROPIC_API_KEY")
        )

    @staticmethod
    def _get_google_llm(model: Optional[str] = None):
        """Get Google LLM (Langchain)"""
        model_name = model or "gemini-2.0-flash-exp"
        return ChatGoogleGenerativeAI(
            model=model_name, temperature=0, google_api_key=os.getenv("GOOGLE_API_KEY")
        )

    @staticmethod
    def _get_ollama_llm(model: Optional[str] = None):
        """Get Ollama LLM (Langchain)"""
        model_name = model or "llama3"
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return Ollama(model=model_name, base_url=base_url)

    @staticmethod
    def get_vision_llm(provider: Optional[str] = None, model: Optional[str] = None):
        """
        Get vision-capable LLM for GUI screenshot analysis.

        Args:
            provider: LLM provider (openai, anthropic, google)
            model: Specific vision model name

        Returns:
            Vision-capable LLM instance
        """
        provider = (
            provider
            or os.getenv("VISION_LLM_PROVIDER")
            or os.getenv("LLM_PROVIDER", "openai")
        )
        model = model or os.getenv("VISION_LLM_MODEL")

        if not model:
            default_vision_models = {
                "openai": "gpt-4o",
                "anthropic": "claude-3-5-sonnet-20241022",
                "google": "gemini-2.0-flash-exp",
            }
            model = default_vision_models.get(provider)

        return LLMConfig.get_llm(provider, model)
