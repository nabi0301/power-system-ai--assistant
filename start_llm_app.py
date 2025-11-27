#!/usr/bin/env python3
"""
Simplified startup script for Power System Visualization with LLM Integration
This script sets environment variables and then runs the main application
"""

import os
import sys
import subprocess
import argparse

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Start Power System Visualization with LLM')
    parser.add_argument('--db-path', default='C:/Projects/dlr-database-project/data.db', 
                      help='Path to SQLite database')
    parser.add_argument('--port', type=int, default=8050, 
                      help='Port for the web application')
    parser.add_argument('--model', default='gpt-3.5-turbo', 
                      help='LLM model to use (if API key available)')
    parser.add_argument('--no-llm', action='store_true',
                      help='Disable LLM integration even if API key is available')
    parser.add_argument('--mock-llm', action='store_true', 
                      help='Use mock LLM (rule-based enhanced) without API key')
    parser.add_argument('--expertise', default='expert',
                      help='Expertise level (beginner, intermediate, expert)')
    parser.add_argument('--use-llama', action='store_true',
                      help='Use Llama LLM instead of OpenAI')
    parser.add_argument('--llama-api-url', default='http://localhost:8000/v1',
                      help='URL for the Llama API endpoint')
    parser.add_argument('--llama-model', default='llama-3-70b-chat',
                      help='Llama model to use')
    
    args = parser.parse_args()
    
    # Set environment variables for the child process
    env = os.environ.copy()
    env["DLR_DATABASE_PATH"] = args.db_path
    env["DLR_PORT"] = str(args.port)
    env["DLR_LLM_MODEL"] = args.model
    env["DLR_EXPERTISE_LEVEL"] = args.expertise
    
    # Handle LLM settings
    if args.no_llm:
        if "OPENAI_API_KEY" in env:
            del env["OPENAI_API_KEY"]  # Remove API key to disable OpenAI LLM
        env["DLR_DISABLE_LLM"] = "1"
    
    # Handle Llama settings
    if args.use_llama:
        env["DLR_USE_LLAMA"] = "1"
        env["LLAMA_API_URL"] = args.llama_api_url
        env["LLAMA_MODEL"] = args.llama_model
        # If API key is provided in env but not explicitly set here, keep it
    
    if args.mock_llm:
        env["DLR_MOCK_LLM"] = "1"  # Use mock LLM without API key
    
    print("=" * 70)
    print("Power System Visualization Tool with AI Assistant")
    print("=" * 70)
    print(f"Database: {args.db_path}")
    print(f"Port: {args.port}")
    
    if args.use_llama:
        print("LLM Integration: ENABLED (LLAMA)")
        print(f"Llama Model: {args.llama_model}")
        print(f"Llama API URL: {args.llama_api_url}")
    elif "OPENAI_API_KEY" in env and not args.no_llm:
        print("LLM Integration: ENABLED (OPENAI)")
        print(f"Model: {args.model}")
    elif args.mock_llm:
        print("LLM Integration: MOCK MODE (using enhanced rules without API)")
    else:
        print("LLM Integration: DISABLED")
        print("Using standard rule-based AI Assistant")
    
    print(f"Expertise Level: {args.expertise}")
    print("=" * 70)
    
    # Get the path to data_viz_fall.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, 'data_viz_fall.py')
    
    # Launch the application using subprocess
    try:
        subprocess.run([sys.executable, script_path], env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting application: {e}")
        return 1
    except KeyboardInterrupt:
        print("Application terminated by user")
        return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main())