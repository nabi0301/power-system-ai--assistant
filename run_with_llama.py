#!/usr/bin/env python3
"""
Launcher script for Power System Visualization with Llama AI Integration.

This script:
1. Checks if Ollama is installed and running
2. Verifies if Llama model is available
3. Launches the power visualization with Llama integration
"""

import os
import sys
import subprocess
import requests
import time

def check_ollama():
    """Check if Ollama is running and Llama model is available"""
    print("Checking Ollama service...")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m.get('name', '') for m in models]
            
            print(f"✅ Ollama is running with {len(model_names)} models")
            
            # Check for Llama models
            llama_models = [m for m in model_names if 'llama' in m.lower()]
            
            if llama_models:
                print(f"✅ Llama models available: {', '.join(llama_models)}")
                return True
            else:
                print("❌ No Llama models found. Pulling llama3.2:8b...")
                try:
                    # Try to pull llama3.2:8b
                    pull_response = requests.post(
                        "http://localhost:11434/api/pull",
                        json={"name": "llama3.2:8b"},
                        timeout=30
                    )
                    if pull_response.status_code == 200:
                        print("✅ Successfully started downloading llama3.2:8b")
                        print("⚠️ Note: This may take several minutes in the background.")
                        print("⚠️ The application will start but may use Claude as fallback until download completes.")
                        return True
                except Exception as e:
                    print(f"❌ Error pulling model: {e}")
                    
                return False
        else:
            print(f"❌ Ollama is not responding properly: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        
        # Check if Ollama is installed
        try:
            if os.name == 'nt':  # Windows
                result = subprocess.run(["where", "ollama"], capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ Ollama is installed but not running")
                    print("⚠️ Please start Ollama and try again")
                else:
                    print("❌ Ollama is not installed")
                    print("⚠️ Install Ollama from: https://ollama.ai/download")
            else:  # Unix-like
                result = subprocess.run(["which", "ollama"], capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ Ollama is installed but not running")
                    print("⚠️ Please start Ollama and try again")
                else:
                    print("❌ Ollama is not installed")
                    print("⚠️ Install Ollama from: https://ollama.ai/download")
        except Exception:
            print("❌ Could not determine if Ollama is installed")
            
        return False

def run_application():
    """Run the power visualization application"""
    print("\n==== Starting Power System Visualization with Llama AI Integration ====\n")
    
    # Check Ollama and models
    check_ollama()
    
    # Run the application
    print("\n🚀 Launching Power System Visualization...\n")
    subprocess.run([sys.executable, "power_viz_with_database.py"])

if __name__ == "__main__":
    run_application()