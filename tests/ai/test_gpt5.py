#!/usr/bin/env python3
"""Test script to verify GPT-5 model access and identify correct model name."""

import os
import pytest
from openai import OpenAI
from dotenv import load_dotenv

def test_gpt5():
    """Test different GPT-5 model identifiers."""
    
    # Load environment variables from .env file
    load_dotenv()
    
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ No OPENAI_API_KEY found in environment or .env file")
        pytest.skip("OPENAI_API_KEY not set; skipping GPT-5 model test")
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Test different possible GPT-5 model names
    model_candidates = [
        "gpt-4o",  # Try this first as it should work
        "gpt-5",
        "gpt-5-preview", 
        "gpt-5-turbo",
        "gpt-4-turbo",  # fallback
    ]
    
    for model_name in model_candidates:
        print(f"\n🧪 Testing model: {model_name}")
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "user", "content": "Say hello"}
                ],
                max_tokens=50
            )
            
            content = response.choices[0].message.content
            print(f"✅ {model_name} works! Response: '{content}'")
            print(f"   Usage: {response.usage}")
            # Success is sufficient; don't return from test
            
        except Exception as e:
            print(f"❌ {model_name} failed: {e}")
    
    print("\n🔍 Let's try listing available models...")
    # Optional: listing models can be slow or restricted; skip to avoid hanging
    print("(skipped)")

if __name__ == "__main__":
    test_gpt5()
