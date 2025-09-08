#!/usr/bin/env python3
"""Test script to verify GPT-5 model access and identify correct model name."""

import os
from openai import OpenAI
from dotenv import load_dotenv

def test_gpt5():
    """Test different GPT-5 model identifiers."""
    
    # Load environment variables from .env file
    load_dotenv()
    
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ No OPENAI_API_KEY found in environment or .env file")
        return
    
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
                max_completion_tokens=50
            )
            
            content = response.choices[0].message.content
            print(f"✅ {model_name} works! Response: '{content}'")
            print(f"   Usage: {response.usage}")
            return model_name
            
        except Exception as e:
            print(f"❌ {model_name} failed: {e}")
    
    print("\n🔍 Let's try listing available models...")
    try:
        models = client.models.list()
        gpt_models = [m.id for m in models.data if 'gpt' in m.id.lower()]
        print(f"Available GPT models: {gpt_models}")
    except Exception as e:
        print(f"❌ Failed to list models: {e}")

if __name__ == "__main__":
    test_gpt5()
