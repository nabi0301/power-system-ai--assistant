#!/usr/bin/env python3
"""
Start Power System Visualization with LangChain RAG
This script installs required dependencies and launches the application
"""

import os
import subprocess
import sys
import importlib.util
import time

def check_dependencies():
    """Check if LangChain dependencies are installed"""
    required_packages = [
        "langchain",
        "langchain_core",
        "langchain_community",
        "chromadb",
        "sentence_transformers"
    ]
    
    missing = []
    for package in required_packages:
        if importlib.util.find_spec(package) is None:
            missing.append(package)
    
    return missing

def main():
    """Main function to check dependencies and start the application"""
    print("\n" + "="*50)
    print("Power System Visualization with LangChain RAG")
    print("="*50 + "\n")
    
    # Check for missing dependencies
    missing_deps = check_dependencies()
    if missing_deps:
        print(f"Missing dependencies: {', '.join(missing_deps)}")
        print("Installing required dependencies...\n")
        
        # Run dependency installer
        try:
            subprocess.check_call([sys.executable, "install_langchain_dependencies.py"])
        except subprocess.CalledProcessError as e:
            print(f"Error installing dependencies: {e}")
            print("Please run 'python install_langchain_dependencies.py' manually.")
            return
        
        print("\nDependencies installed successfully.")
    else:
        print("✅ All LangChain dependencies are installed.")
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        try:
            # Try to load from config.py
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from config import AI_CONFIG
            if 'openai_api_key' in AI_CONFIG and AI_CONFIG['openai_api_key']:
                os.environ["OPENAI_API_KEY"] = AI_CONFIG['openai_api_key']
                print("OpenAI API key loaded from config successfully.")
            else:
                api_key = input("\nEnter your OpenAI API key (leave blank to continue without): ")
                if api_key.strip():
                    os.environ["OPENAI_API_KEY"] = api_key
                    print("OpenAI API key set successfully.")
                else:
                    print("No API key provided. Some LangChain features may be limited.")
        except ImportError:
            api_key = input("\nEnter your OpenAI API key (leave blank to continue without): ")
            if api_key.strip():
                os.environ["OPENAI_API_KEY"] = api_key
                print("OpenAI API key set successfully.")
            else:
                print("No API key provided. Some LangChain features may be limited.")
    
    # Start the application
    print("\nStarting Power System Visualization with LangChain RAG...\n")
    time.sleep(1)  # Small delay for better UX
    
    try:
        subprocess.check_call([sys.executable, "power_viz_with_database.py"])
    except subprocess.CalledProcessError as e:
        print(f"Error starting application: {e}")
        return

if __name__ == "__main__":
    main()