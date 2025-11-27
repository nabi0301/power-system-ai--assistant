#!/usr/bin/env python3
"""
This script launches the power visualization tool with AI assistant integration
and ensures the network graph visualization is working properly.

Usage:
    python start_power_viz.py
"""

import os
import sys
import subprocess
import importlib.util
import time

def check_module_exists(module_name):
    """Check if a module exists and can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✅ Module '{module_name}' is available")
        return True
    except ImportError:
        print(f"❌ Module '{module_name}' is not available")
        return False

def check_network_graph_integration():
    """Test if network graph integration is working"""
    print("Testing network graph integration...")
    
    try:
        # Import direct_network_integration module
        from direct_network_integration import create_network_graph
        
        # Try to create a simple graph
        fig = create_network_graph(42)  # Use default case
        
        if fig is not None:
            print("✅ Network graph integration is working!")
            return True
        else:
            print("❌ Network graph integration failed!")
            return False
    except Exception as e:
        print(f"❌ Network graph integration failed: {e}")
        return False

def main():
    """Main entry point of the script"""
    print("=" * 80)
    print("POWER SYSTEM VISUALIZATION WITH AI ASSISTANT".center(80, " "))
    print("=" * 80)
    print()
    
    # Check required modules
    required_modules = ["dash", "plotly", "pandas", "sqlite3", "networkx"]
    all_modules_available = True
    
    for module in required_modules:
        if not check_module_exists(module):
            all_modules_available = False
    
    if not all_modules_available:
        print("Some required modules are missing. Please install them with:")
        print("pip install dash plotly pandas networkx")
        return
    
    # Check network graph integration
    if not check_network_graph_integration():
        print("Network graph integration is not working correctly.")
        print("AI assistant may not be able to show network graphs.")
        user_input = input("Do you want to continue anyway? (y/n): ")
        if user_input.lower() != 'y':
            print("Exiting...")
            return
    
    # Start the power visualization tool
    print("\nStarting power visualization tool with AI assistant...")
    subprocess.run([sys.executable, "power_viz_with_database.py"])

if __name__ == "__main__":
    main()