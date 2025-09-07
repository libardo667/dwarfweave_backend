#!/usr/bin/env python3
"""Test intelligent generation directly."""

import requests
import json

print('Testing intelligent generation directly...')
payload = {
    'count': 2,
    'themes': ['exploration', 'mystery'],
    'intelligent': True
}

try:
    response = requests.post('http://localhost:8000/author/generate-intelligent', json=payload)
    print(f'Status: {response.status_code}')
    result = response.json()
    print(f'Response keys: {list(result.keys())}')
    
    if 'storylets' in result:
        print(f'Generated {len(result["storylets"])} storylets')
        for i, storylet in enumerate(result['storylets'][:2], 1):
            print(f'{i}. {storylet.get("title", "Untitled")}')
            print(f'   Text: {storylet.get("text_template", "")[:100]}...')
    
    if 'error' in result:
        print(f'Error: {result["error"]}')
        
    if 'message' in result:
        print(f'Message: {result["message"]}')
        
except Exception as e:
    print(f'Request failed: {e}')
