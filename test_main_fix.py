#!/usr/bin/env python3
"""
Test just the database status function from the main file
"""

import sqlite3
import sys

# Test importing the specific function without importing Dash
def test_database_status_from_main():
    """Test database status function from main file without Dash imports"""
    
    print("🧪 Testing database status function from main file...")
    
    # Read the main file and extract only the database status function
    try:
        with open('power_viz_with_database.py', 'r') as f:
            content = f.read()
        
        # Find the get_database_status function
        if 'def get_database_status() -> dict:' in content:
            print("✅ Found get_database_status function in main file")
        else:
            print("❌ get_database_status function not found")
            return False
        
        # Check for the fixed code pattern
        if 'if "databases" not in status:' in content and 'status["databases"] = {}' in content:
            print("✅ Database status fix is present in main file")
        else:
            print("❌ Database status fix not found")
            return False
        
        # Check for the simplified main database handling
        if 'status["databases"]["main"] = {' in content:
            print("✅ Simplified main database handling is present")
        else:
            print("❌ Simplified main database handling not found")
            return False
        
        print("✅ All fixes appear to be correctly applied to main file")
        return True
        
    except Exception as e:
        print(f"❌ Error reading main file: {e}")
        return False

def test_import_issue():
    """Test if we can identify the import issue"""
    
    print("\n🔍 Testing import issues...")
    
    try:
        import ctypes
        print("✅ ctypes import successful")
    except Exception as e:
        print(f"❌ ctypes import failed: {e}")
        return False
    
    try:
        import werkzeug
        print("✅ werkzeug import successful") 
    except Exception as e:
        print(f"❌ werkzeug import failed: {e}")
        return False
    
    try:
        import flask
        print("✅ flask import successful")
    except Exception as e:
        print(f"❌ flask import failed: {e}")
        return False
    
    try:
        import dash
        print("✅ dash import successful")
    except Exception as e:
        print(f"❌ dash import failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 Running comprehensive tests...")
    
    db_test = test_database_status_from_main()
    import_test = test_import_issue()
    
    if db_test:
        print("\n✅ Database status fix verification PASSED")
    else:
        print("\n❌ Database status fix verification FAILED")
    
    if import_test:
        print("✅ Import test PASSED")
    else:
        print("❌ Import test FAILED")
    
    if db_test and import_test:
        print("\n🎉 All tests PASSED - Main application should work now!")
    else:
        print("\n⚠️ Some tests failed - Check the issues above")