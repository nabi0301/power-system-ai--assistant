#!/usr/bin/env python3
"""
Launch script for Power System Visualization with Network Graph capabilities.
This script ensures all required modules are properly initialized before starting the app.

Usage:
    python launch_with_network_graphs.py
"""

import os
import sys
import importlib
import time
import subprocess

def check_module_exists(module_name):
    """Check if a module exists and can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✅ Module '{module_name}' is available")
        return True
    except ImportError:
        print(f"❌ Module '{module_name}' is not available")
        return False

def check_file_exists(file_path):
    """Check if a file exists"""
    exists = os.path.exists(file_path)
    print(f"{'✅' if exists else '❌'} File '{file_path}' {'exists' if exists else 'does not exist'}")
    return exists

def print_banner():
    """Print a nice banner"""
    print("\n" + "=" * 80)
    print(" 🔌 POWER SYSTEM VISUALIZATION WITH NETWORK GRAPHS 🔌 ".center(80, "="))
    print("=" * 80)
    print("\nInitializing system components...")

def main():
    """Main function to check dependencies and launch the app"""
    print_banner()
    
    # Check for required files
    required_files = [
        "power_viz_with_database.py",
        "data_viz_fall.py",
        "network_comparison.py",
        "data_availability.py",
        "direct_network_integration.py"  # Add the new direct integration module
    ]
    
    all_files_exist = True
    for file in required_files:
        if not check_file_exists(file):
            all_files_exist = False
    
    if not all_files_exist:
        print("\n⚠️ Some required files are missing. The application may not function correctly.")
        user_input = input("Do you want to continue anyway? (y/n): ")
        if user_input.lower() != 'y':
            print("Aborting launch.")
            return
    
    # Check for required modules
    required_modules = [
        "dash",
        "plotly",
        "pandas",
        "sqlite3",
        "networkx",  # Required by data_viz_fall.py
        "importlib"  # Required for dynamic imports
    ]
    
    all_modules_available = True
    for module in required_modules:
        if not check_module_exists(module):
            all_modules_available = False
    
    if not all_modules_available:
        print("\n⚠️ Some required modules are missing. Please install them with:")
        print("pip install dash plotly pandas networkx")
        user_input = input("Do you want to continue anyway? (y/n): ")
        if user_input.lower() != 'y':
            print("Aborting launch.")
            return
    
    # Check database
    if not check_file_exists("data.db"):
        print("\n⚠️ Database file 'data.db' is missing. The application won't have any data to display.")
        user_input = input("Do you want to continue anyway? (y/n): ")
        if user_input.lower() != 'y':
            print("Aborting launch.")
            return
    
    # All checks passed or user chose to continue
    print("\n✅ System check complete. Launching visualization application...")
    
    try:
        # Test direct network integration
        print("\n" + "=" * 80)
        print(" 🧪 TESTING DIRECT NETWORK INTEGRATION 🧪 ".center(80, "="))
        print("=" * 80)
        
        try:
            print("\nTesting direct_network_integration module...")
            from direct_network_integration import test_network_graph
            test_result = test_network_graph()
            if test_result:
                print("\n✅ Direct network integration test passed!")
            else:
                print("\n⚠️ Direct network integration test failed. Application may have visualization issues.")
                user_input = input("Do you want to continue anyway? (y/n): ")
                if user_input.lower() != 'y':
                    print("Aborting launch.")
                    return
        except Exception as e:
            print(f"\n❌ Error testing network integration: {e}")
            user_input = input("Do you want to continue anyway? (y/n): ")
            if user_input.lower() != 'y':
                print("Aborting launch.")
                return
        
        # Launch the application
        print("\n" + "=" * 80)
        print(" 🚀 LAUNCHING APPLICATION 🚀 ".center(80, "="))
        print("=" * 80 + "\n")
        
        # Execute the main application script
        subprocess.run([sys.executable, "power_viz_with_database.py"])
        
    except Exception as e:
        print(f"\n❌ Error launching application: {e}")
        print("\nPlease check the error message and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()