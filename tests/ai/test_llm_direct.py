#!/usr/bin/env python3
"""Test if LLM service can access OpenAI API directly."""

from dotenv import load_dotenv
import os

# Explicitly load environment variables
load_dotenv()

from src.services.llm_service import llm_suggest_storylets

print('Testing LLM with explicit env loading...')
print(f'API Key available: {bool(os.getenv("OPENAI_API_KEY"))}')
print(f'API Key length: {len(os.getenv("OPENAI_API_KEY", ""))}')

try:
    storylets = llm_suggest_storylets(n=2, themes=['exploration'], bible={'test': True})
    print(f'Generated {len(storylets)} storylets')
    
    # Check if these are fallback storylets or real AI-generated ones
    titles = [s.get('title', '') for s in storylets]
    if 'Creak in the Dark' in titles and 'Mushroom Cache' in titles:
        print('⚠️  These are fallback storylets (API not working)')
        print('Debugging the issue...')
        
        # Test if OpenAI import works
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            print('✅ OpenAI client created successfully')
            
            # Test a simple API call
            response = client.chat.completions.create(
                model="gpt-5-2025-08-07",
                messages=[{"role": "user", "content": "Say hello"}],
                max_completion_tokens=10
            )
            print('✅ OpenAI API is working!')
            print(f'Response: {response.choices[0].message.content}')
            
        except Exception as e:
            print(f'❌ OpenAI API error: {e}')
    else:
        print('✅ These appear to be AI-generated storylets!')
        for i, storylet in enumerate(storylets, 1):
            print(f'{i}. {storylet.get("title", "Untitled")}')
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
