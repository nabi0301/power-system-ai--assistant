#!/usr/bin/env python3
"""
Start Power System Visualization
This script launches the power system visualization application
"""

import subprocess
import sys
import os

def main():
    """Main function to start the application"""
    print("\n" + "="*50)
    print("Power System Visualization")
    print("="*50 + "\n")
    
    print("Starting Power System Visualization...\n")
    
    try:
        subprocess.check_call([sys.executable, "power_viz_with_database.py"])
    except subprocess.CalledProcessError as e:
        print(f"Error starting application: {e}")
        return

if __name__ == "__main__":
    main()