"""
Script to test and set up AI storylet generation.
Run this to check if your OpenAI API key is working and generate some test storylets.
"""

import os
import requests
import json
from typing import Dict, Any
import pytest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def check_api_setup():
    """Check if the API is running and OpenAI key is set."""
    print("🔍 Checking API setup...")
    
    # Check if API is running
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ API is running")
        else:
            print("❌ API is not responding correctly")
            pytest.skip("API not responding correctly at /health")
    except requests.exceptions.ConnectionError:
        print("❌ API is not running. Start it with: uvicorn main:app --reload")
        pytest.skip("API is not running on localhost:8000")
    
    # Check OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print("✅ OpenAI API key is set")
    else:
        print("❌ OpenAI API key is not set")
        print("Set it with: $env:OPENAI_API_KEY='your-key-here' (PowerShell)")
        print("Or create a .env file with: OPENAI_API_KEY=your-key-here")
        pytest.skip("OPENAI_API_KEY not set")

def test_storylet_generation():
    """Test the storylet generation endpoint."""
    print("\n🎲 Testing storylet generation...")
    
    test_payload = {
        "n": 3,
        "themes": ["exploration", "mystery", "danger"],
        "bible": {
            "setting": "cosmic_observatory",
            "available_variables": ["resonance", "location", "has_crystal", "energy"],
            "tone": "atmospheric"
        }
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/author/suggest",
            json=test_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Generated {len(data['storylets'])} storylets!")
            
            for i, storylet in enumerate(data['storylets'], 1):
                print(f"\n📖 Storylet {i}:")
                print(f"   Title: {storylet['title']}")
                print(f"   Text: {storylet['text_template'][:100]}...")
                print(f"   Choices: {len(storylet['choices'])} options")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error testing generation: {e}")

def populate_database():
    """Populate the database with AI-generated storylets."""
    print("\n🏗️ Populating database with AI storylets...")
    
    try:
        response = requests.post("http://localhost:8000/author/populate?target_count=25")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {data['message']}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error populating database: {e}")

def get_stats():
    """Get current storylet statistics."""
    print("\n📊 Current storylet statistics...")
    
    try:
        response = requests.get("http://localhost:8000/author/debug")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📚 Total storylets: {data['total_storylets']}")
            print(f"� Available storylets: {data['available_storylets']}")
            print(f"🔑 API Status: Working properly")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting stats: {e}")

if __name__ == "__main__":
    print("🎮 WorldWeaver AI Setup & Test Tool")
    print("=" * 40)
    
    if check_api_setup():
        get_stats()
        
        print("\nWhat would you like to do?")
        print("1. Test storylet generation")
        print("2. Populate database with AI storylets")
        print("3. Both")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice in ["1", "3"]:
            test_storylet_generation()
            
        if choice in ["2", "3"]:
            populate_database()
            get_stats()
            
        print("\n🎉 Done! Your Twine story should now have AI-generated content!")
        print("💡 The system will automatically generate new storylets as you play!")
    else:
        print("\n🛠️ Please fix the setup issues above and try again.")
