"""Centralized LLM client + configuration (item 07).

OpenRouter-first: by default the OpenAI SDK is pointed at OpenRouter
(``https://openrouter.ai/api/v1``) using ``OPENROUTER_API_KEY``, which unlocks many
models through one account. Falls back to direct OpenAI when only ``OPENAI_API_KEY``
is set. This is the single place that decides provider / model / key.
"""

import os
from functools import lru_cache
from typing import Optional, Tuple

from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openrouter_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = "openai/gpt-4o"
    llm_title: Optional[str] = "DwarfWeave"   # OpenRouter X-Title (optional)
    llm_referer: Optional[str] = None          # OpenRouter HTTP-Referer (optional)


@lru_cache
def get_settings() -> LLMSettings:
    return LLMSettings()


def ai_disabled() -> bool:
    """True in tests / fast-dev / when explicitly disabled — callers use fallbacks."""
    return (
        os.getenv("DW_FAST_TEST") == "1"
        or os.getenv("DW_DISABLE_AI") == "1"
        or bool(os.getenv("PYTEST_CURRENT_TEST"))
    )


def ai_available() -> bool:
    """True only when live generation should happen (not disabled, and a key exists)."""
    if ai_disabled():
        return False
    s = get_settings()
    return bool(s.openrouter_api_key or s.openai_api_key)


def get_llm(settings: Optional[LLMSettings] = None) -> Tuple[Optional[object], str]:
    """Return ``(client, model)``. ``client`` is None when no API key is configured.

    OpenRouter is preferred; direct OpenAI is the fallback (with the ``provider/``
    prefix stripped from the model slug for the OpenAI endpoint).
    """
    s = settings or get_settings()
    from openai import OpenAI

    if s.openrouter_api_key:
        headers = {}
        if s.llm_referer:
            headers["HTTP-Referer"] = s.llm_referer
        if s.llm_title:
            headers["X-Title"] = s.llm_title
        client = OpenAI(
            api_key=s.openrouter_api_key,
            base_url=s.llm_base_url,
            default_headers=headers or None,
        )
        return client, s.llm_model

    if s.openai_api_key:
        # Direct OpenAI: drop any "provider/" prefix from the model slug.
        return OpenAI(api_key=s.openai_api_key), s.llm_model.split("/", 1)[-1]

    return None, s.llm_model
