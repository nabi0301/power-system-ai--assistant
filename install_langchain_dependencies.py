#!/usr/bin/env python3
"""
LangChain Dependencies Installer
Installs all required packages for the LangChain-based RAG system
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install all required packages for the LangChain RAG system"""
    print("Installing LangChain dependencies...")
    
    dependencies = [
        "langchain",
        "langchain-core",
        "langchain-community",
        "langchain-text-splitters",
        "langchainhub",
        "chromadb",
        "sentence-transformers",
        "openai",
        "tiktoken",
        "faiss-cpu",
        "pysqlite3"
    ]
    
    for dep in dependencies:
        print(f"Installing {dep}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✅ Successfully installed {dep}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {dep}")
    
    print("\nVerifying installations...")
    try:
        import langchain
        import langchain_core
        import langchain_community
        import chromadb
        import sentence_transformers
        
        print("\n✅ All core dependencies verified!")
        print("\nLangChain dependencies installed successfully.")
        print("You can now run the power system visualization with LangChain RAG.")
    except ImportError as e:
        print(f"\n❌ Verification failed: {e}")
        print("Please check the error and try installing the missing package manually.")

if __name__ == "__main__":
    install_dependencies()