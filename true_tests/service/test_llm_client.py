"""Centralized LLM client + OpenRouter-first config (item 07)."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.services.llm_client import LLMSettings, get_llm, ai_disabled


def test_openrouter_is_default_provider():
    s = LLMSettings(openrouter_api_key="test-key", openai_api_key=None, llm_model="anthropic/claude-x")
    client, model = get_llm(s)
    assert client is not None
    assert "openrouter.ai" in str(client.base_url)
    assert model == "anthropic/claude-x"


def test_openai_fallback_strips_provider_prefix():
    s = LLMSettings(openrouter_api_key=None, openai_api_key="test-key", llm_model="openai/gpt-4o")
    client, model = get_llm(s)
    assert client is not None
    assert "openai.com" in str(client.base_url)
    assert model == "gpt-4o"  # provider prefix stripped for the direct OpenAI endpoint


def test_no_key_returns_none_client():
    s = LLMSettings(openrouter_api_key=None, openai_api_key=None, llm_model="openai/gpt-4o")
    client, model = get_llm(s)
    assert client is None
    assert model == "openai/gpt-4o"


def test_ai_disabled_during_tests():
    # PYTEST_CURRENT_TEST is set while pytest runs, so live calls are suppressed.
    assert ai_disabled() is True
