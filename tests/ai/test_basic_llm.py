#!/usr/bin/env python3
"""Test basic LLM generation."""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.llm_service import llm_suggest_storylets

print('Testing basic LLM generation...')
try:
    storylets = llm_suggest_storylets(n=2, themes=['exploration'], bible={})
    print(f'Generated {len(storylets)} storylets')
    for i, storylet in enumerate(storylets, 1):
        print(f'{i}. {storylet.get("title", "Untitled")}')
        print(f'   Requires: {storylet.get("requires", {})}')
        print(f'   Choices: {len(storylet.get("choices", []))}')
        print()
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
