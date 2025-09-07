#!/usr/bin/env python3
"""Test the intelligent AI storylet generation system."""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_storylet_analysis():
    """Test the storylet analysis endpoint."""
    print("=== STORYLET ANALYSIS ===")
    try:
        response = requests.get(f"{BASE_URL}/author/storylet-analysis")
        if response.status_code == 200:
            data = response.json()
            print("Analysis Summary:")
            summary = data.get("summary", {})
            print(f"- Total gaps: {summary.get('total_gaps', 0)}")
            print(f"- Top priority: {summary.get('top_priority', 'None')}")
            print(f"- Connectivity health: {summary.get('connectivity_health', 0):.1%}")
            
            print("\nTop 3 Improvement Priorities:")
            for i, rec in enumerate(data.get("recommendations", [])[:3], 1):
                print(f"{i}. {rec.get('suggestion', 'Unknown')}")
            
            return data
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None

def test_intelligent_generation():
    """Test the intelligent storylet generation."""
    print("\n=== INTELLIGENT GENERATION ===")
    try:
        payload = {
            "count": 3,
            "themes": ["exploration", "mystery"],
            "intelligent": True
        }
        response = requests.post(f"{BASE_URL}/author/generate-intelligent", 
                               json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"Generated {len(data.get('storylets', []))} intelligent storylets:")
            for i, storylet in enumerate(data.get("storylets", []), 1):
                print(f"\n{i}. {storylet.get('title', 'Untitled')}")
                print(f"   Text: {storylet.get('text_template', '')[:100]}...")
                print(f"   Choices: {len(storylet.get('choices', []))}")
            return data
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None

def test_targeted_generation():
    """Test the targeted storylet generation."""
    print("\n=== TARGETED GENERATION ===")
    try:
        response = requests.post(f"{BASE_URL}/author/generate-targeted")
        if response.status_code == 200:
            data = response.json()
            if "storylets" in data:
                print(f"Generated {len(data.get('storylets', []))} targeted storylets:")
                for i, storylet in enumerate(data.get("storylets", []), 1):
                    print(f"\n{i}. {storylet.get('title', 'Untitled')}")
                    print(f"   Text: {storylet.get('text_template', '')[:100]}...")
            else:
                print(f"Response: {data.get('message', 'Unknown result')}")
            return data
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None

def test_debug_info():
    """Test the debug endpoint."""
    print("\n=== DEBUG INFO ===")
    try:
        response = requests.get(f"{BASE_URL}/author/debug")
        if response.status_code == 200:
            data = response.json()
            print(f"Total storylets: {data.get('total_storylets', 0)}")
            print(f"Available storylets: {data.get('available_storylets', 0)}")
            print("Sample titles:")
            for title in data.get("sample_storylet_titles", []):
                print(f"  - {title}")
            return data
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None

if __name__ == "__main__":
    print("Testing Intelligent AI Storylet Generation System")
    print("=" * 50)
    
    # Run all tests
    debug_data = test_debug_info()
    analysis_data = test_storylet_analysis()
    intelligent_data = test_intelligent_generation()
    targeted_data = test_targeted_generation()
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    if debug_data:
        print(f"✅ Debug endpoint working - {debug_data.get('total_storylets', 0)} storylets in database")
    if analysis_data:
        print(f"✅ Analysis endpoint working - {len(analysis_data.get('recommendations', []))} recommendations")
    if intelligent_data:
        print(f"✅ Intelligent generation working - created {len(intelligent_data.get('storylets', []))} storylets")
    if targeted_data:
        if 'storylets' in targeted_data:
            print(f"✅ Targeted generation working - created {len(targeted_data.get('storylets', []))} storylets")
        else:
            print(f"ℹ️ Targeted generation: {targeted_data.get('message', 'No gaps to fill')}")
