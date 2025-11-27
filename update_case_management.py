#!/usr/bin/env python3
"""
Helper script to update the power_viz_with_database.py to use dynamic case management
"""

import re

def insert_import():
    """Insert dynamic case management import into power_viz_with_database.py"""
    file_path = "power_viz_with_database.py"
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Define the import block to add
    import_block = """
# Import dynamic case management
try:
    from dynamic_case_management import validate_case_id, get_available_case_ids, get_first_available_case_id
    DYNAMIC_CASE_MANAGEMENT_AVAILABLE = True
    print("✅ Dynamic case management system loaded successfully")
except ImportError as e:
    print(f"⚠️ Dynamic case management not available: {e}")
    DYNAMIC_CASE_MANAGEMENT_AVAILABLE = False
"""
    
    # Find a place to insert the import
    insertion_point = content.find("# AI Integration with API")
    
    if insertion_point > 0:
        new_content = content[:insertion_point] + import_block + content[insertion_point:]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ Successfully inserted dynamic case management import")
        return True
    else:
        print("❌ Could not find insertion point")
        return False

def update_case_id_validation():
    """Update case ID validation to use dynamic case management"""
    file_path = "power_viz_with_database.py"
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Pattern 1: Update in update_dynamic_plot function
    pattern1 = re.compile(r"""(\s+# Handle type conversion for case_id and contingency_id\s+if case_id is not None:\s+try:\s+case_id = int\(case_id\)\s+except \(ValueError, TypeError\):\s+print\(f"ERROR: Could not convert case_id '[^']*' to integer"\)\s+raise ValueError\(f"Invalid case_id: {case_id} - must be a valid integer"\))""")
    
    replacement1 = """    # Handle type conversion for case_id and contingency_id
    if case_id is not None:
        try:
            # Use dynamic case management if available
            if 'DYNAMIC_CASE_MANAGEMENT_AVAILABLE' in globals() and DYNAMIC_CASE_MANAGEMENT_AVAILABLE:
                case_id = validate_case_id(case_id)
            else:
                case_id = int(case_id)
        except (ValueError, TypeError) as e:
            print(f"ERROR: Could not convert case_id '{case_id}' to integer: {e}")
            
            # Try to use first available case
            if 'DYNAMIC_CASE_MANAGEMENT_AVAILABLE' in globals() and DYNAMIC_CASE_MANAGEMENT_AVAILABLE:
                first_available = get_first_available_case_id()
                if first_available:
                    print(f"INFO: Using first available case ID: {first_available}")
                    case_id = first_available
                else:
                    raise ValueError("No valid case IDs available in database")
            else:
                raise ValueError(f"Invalid case_id: {case_id} - must be a valid integer")"""
    
    # Pattern 2: Update in debug_visualization function
    pattern2 = re.compile(r"""(\s+# Common validation for all network visualizations\s+if case_id is None:\s+print\("ERROR: case_id is None, no default will be used"\)\s+raise ValueError\("case_id must be specified - no default value will be used"\))""")
    
    replacement2 = """    # Common validation for all network visualizations
    if case_id is None:
        # Try to use dynamic case management
        if 'DYNAMIC_CASE_MANAGEMENT_AVAILABLE' in globals() and DYNAMIC_CASE_MANAGEMENT_AVAILABLE:
            first_available = get_first_available_case_id()
            if first_available:
                print(f"INFO: Using first available case ID: {first_available}")
                case_id = first_available
            else:
                print("ERROR: case_id is None and no cases available in database")
                raise ValueError("No valid case IDs available in database")
        else:
            print("ERROR: case_id is None, no default will be used")
            raise ValueError("case_id must be specified - no default value will be used")"""
    
    # Apply replacements
    new_content = pattern1.sub(replacement1, content)
    new_content = pattern2.sub(replacement2, new_content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ Successfully updated case ID validation")
    return True

if __name__ == "__main__":
    print("Updating power_viz_with_database.py with dynamic case management...")
    
    # Insert import
    insert_import()
    
    # Update validation
    update_case_id_validation()
    
    print("✅ Done updating power_viz_with_database.py")