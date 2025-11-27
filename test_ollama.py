#!/usr/bin/env python3
"""
Test script to check Ollama availability and models
"""
import requests
import json

try:
    response = requests.get('http://localhost:11434/api/tags', timeout=5)
    if response.status_code == 200:
        data = response.json()
        models = data.get('models', [])
        print(f"✅ Ollama is running (status: {response.status_code})")
        print(f"Available models ({len(models)}):")
        for model in models:
            print(f"  - {model.get('name', 'Unknown')}")
        
        # Check if llama3.2:8b is available
        model_names = [m.get('name', '') for m in models]
        target_model = "llama3.2:8b"
        
        if target_model in model_names:
            print(f"✅ Target model '{target_model}' is available")
        else:
            print(f"❌ Target model '{target_model}' is NOT available")
            # Check for similar models
            similar = [name for name in model_names if 'llama3' in name.lower()]
            if similar:
                print(f"Similar models found: {similar}")
    else:
        print(f"❌ Ollama returned status: {response.status_code}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ Cannot connect to Ollama: {e}")
except Exception as e:
    print(f"❌ Error: {e}")