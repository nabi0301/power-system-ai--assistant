#!/usr/bin/env python3
"""
This script imports dynamic case management into power_viz_with_database.py
"""

import os

def add_dynamic_case_management_import():
    """Add import for dynamic case management to power_viz_with_database.py"""
    file_path = "power_viz_with_database.py"
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find a good place to add our import
    import_idx = -1
    for i, line in enumerate(lines):
        if "# Import" in line and "functionality" in line:
            import_idx = i
    
    if import_idx == -1:
        print("Could not find a good place to insert the import")
        return False
    
    # Prepare our new import block
    new_import_block = """
# Import dynamic case management
try:
    from dynamic_case_management import validate_case_id, get_available_case_ids, get_first_available_case_id
    DYNAMIC_CASE_MANAGEMENT_AVAILABLE = True
    print("✅ Dynamic case management system loaded successfully")
except ImportError as e:
    print(f"⚠️ Dynamic case management not available: {e}")
    DYNAMIC_CASE_MANAGEMENT_AVAILABLE = False
"""
    
    # Insert our import block after the last import block
    lines.insert(import_idx + 10, new_import_block)
    
    # Write the file back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"Added dynamic case management import to {file_path}")
    return True

if __name__ == "__main__":
    add_dynamic_case_management_import()