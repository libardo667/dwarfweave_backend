"""Tolerant storylet JSON parsing (item 08).

Pins the exact response shapes seen in the 2026-05-27 multi-model run.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.services.llm_client import parse_storylets


def test_bare_array():
    assert parse_storylets('[{"title": "A"}, {"title": "B"}]') == [{"title": "A"}, {"title": "B"}]


def test_object_with_storylets_key():
    assert parse_storylets('{"storylets": [{"title": "A"}]}') == [{"title": "A"}]


def test_markdown_fenced():
    assert parse_storylets("```json\n[{\"title\": \"A\"}]\n```") == [{"title": "A"}]


def test_array_with_trailing_prose_qwen_case():
    # qwen appended a "### World Variables" glossary after the array.
    text = '[{"title": "A"}]\n\n### World Variables\n- relation_leviathan: tracks ...'
    assert parse_storylets(text) == [{"title": "A"}]


def test_single_storylet_object():
    assert parse_storylets('{"title": "Solo", "text": "x"}') == [{"title": "Solo", "text": "x"}]


def test_garbage_and_empty_return_empty():
    # gpt-5-nano emitted prose with no JSON array -> graceful empty, not a crash.
    assert parse_storylets("I am a reasoning model; here is my plan, no JSON.") == []
    assert parse_storylets("") == []
