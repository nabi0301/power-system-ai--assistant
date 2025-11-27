"""
Demo script to run the integrated power visualization in data_viz_fall.py
------------------------------------------------------------------------
This script runs the integrated application after the integration has been completed.
"""

import os
import importlib
import sys

def check_integration_status():
    """Check if the integration has been completed"""
    try:
        # Check if the required files exist
        required_files = [
            "data_viz_fall.py", 
            "power_viz_component.py",
            "power_viz_integration.py"
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            print("❌ Integration incomplete. Missing files:")
            for file in missing_files:
                print(f" - {file}")
            return False
        
        # Check if power_viz_integration import is in data_viz_fall.py
        with open("data_viz_fall.py", "r") as f:
            content = f.read()
            
        if "from power_viz_integration import" not in content:
            print("❌ Integration incomplete. power_viz_integration import not found in data_viz_fall.py")
            return False
            
        print("✅ Integration status check passed")
        return True
        
    except Exception as e:
        print(f"❌ Error checking integration status: {e}")
        return False

def run_integrated_app():
    """Run the integrated application"""
    try:
        print("Launching integrated application...")
        
        # Add the current directory to sys.path to ensure imports work
        sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
        
        # Import the data_viz_fall module dynamically
        data_viz_fall = importlib.import_module("data_viz_fall")
        
        # Run the application
        if hasattr(data_viz_fall, "app"):
            print("Starting server...")
            data_viz_fall.app.run_server(debug=True)
        else:
            print("❌ Could not find app object in data_viz_fall.py")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error running integrated application: {e}")
        return False

def main():
    """Main function to run the demo"""
    print("="*60)
    print(" Power Visualization Integration Demo")
    print("="*60)
    
    if not check_integration_status():
        print("\nIntegration check failed. Please run integrate_power_viz.py first.")
        return
        
    print("\nStarting integrated application with Power Visualization tab...")
    run_integrated_app()

if __name__ == "__main__":
    main()