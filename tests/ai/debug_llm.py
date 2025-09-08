#!/usr/bin/env python3
"""Test the core llm_suggest_storylets function."""

from dotenv import load_dotenv
import os
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

print(f'API Key available: {bool(os.getenv("OPENAI_API_KEY"))}')

# Test if basic llm_suggest_storylets works with simple parameters
from src.services.llm_service import llm_suggest_storylets

print('Testing basic llm_suggest_storylets...')
try:
    storylets = llm_suggest_storylets(n=2, themes=['cave', 'mining'], bible={
        'setting': 'underground mine',
        'allowed_items': ['pickaxe', 'torch', 'rope']
    })
    
    print(f'Returned {len(storylets)} storylets')
    
    if len(storylets) == 0:
        print('❌ No storylets generated - investigating API call...')
        
        # Let's test the OpenAI API directly
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        simple_response = client.chat.completions.create(
            model="gpt-5-2025-08-07",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "Return a JSON object with a 'test' field."},
                {"role": "user", "content": "Create JSON with test: hello"}
            ],
            max_completion_tokens=50
        )
        
        print('Direct API test result:')
        print(simple_response.choices[0].message.content)
        
    else:
        for i, storylet in enumerate(storylets, 1):
            print(f'{i}. {storylet.get("title", "No title")}')
            print(f'   Text: {storylet.get("text_template", "No text")[:50]}...')
            print(f'   Choices: {len(storylet.get("choices", []))}')

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
