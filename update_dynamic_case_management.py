#!/usr/bin/env python3
"""
Integration script to update the main power_viz_with_database.py to use the dynamic case management module

This should be run once to add the necessary imports and update the code.
"""

import os
import sys
import re

def update_power_viz_imports():
    """Add dynamic case management imports to power_viz_with_database.py"""
    file_path = 'power_viz_with_database.py'
    
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return False
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find the imports section
    network_comparison_import_pattern = r"# Import network comparison functionality.*?NETWORK_COMPARISON_AVAILABLE = (True|False)"
    network_comparison_import_match = re.search(network_comparison_import_pattern, content, re.DOTALL)
    
    if not network_comparison_import_match:
        print("Could not find network comparison import section")
        return False
    
    # The text we found
    found_text = network_comparison_import_match.group(0)
    
    # The text to add after
    new_import_text = """

# Import dynamic case management
try:
    from dynamic_case_management import validate_case_id, get_available_case_ids, get_first_available_case_id
    DYNAMIC_CASE_MANAGEMENT_AVAILABLE = True
    print("✅ Dynamic case management system loaded successfully")
except ImportError as e:
    print(f"⚠️ Dynamic case management not available: {e}")
    DYNAMIC_CASE_MANAGEMENT_AVAILABLE = False"""
    
    # Replace the found text with itself + our new text
    new_content = content.replace(found_text, found_text + new_import_text)
    
    # Write the file back
    with open(file_path, 'w') as f:
        f.write(new_content)
    
    print(f"✅ Successfully updated {file_path} with dynamic case management imports")
    return True

def update_case_id_validation():
    """Update case_id validation in power_viz_with_database.py"""
    file_path = 'power_viz_with_database.py'
    
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return False
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Update all instances of using 42 as a default case_id with dynamic validation
    replacements = [
        {
            'pattern': r"""    # Handle type conversion for case_id and contingency_id
    if case_id is not None:
        try:
            case_id = int\(case_id\)
        except \(ValueError, TypeError\):
            print\(f"ERROR: Could not convert case_id '{case_id}' to integer"\)
            raise ValueError\(f"Invalid case_id: {case_id} - must be a valid integer"\)""",
            'replacement': """    # Handle type conversion for case_id and contingency_id
    if case_id is not None:
        if DYNAMIC_CASE_MANAGEMENT_AVAILABLE:
            try:
                case_id = validate_case_id(case_id)
            except ValueError as e:
                print(f"ERROR: {e}")
                first_available = get_first_available_case_id()
                if first_available:
                    print(f"INFO: Using first available case ID: {first_available}")
                    case_id = first_available
                else:
                    raise ValueError("No valid case IDs available in the database")
        else:
            try:
                case_id = int(case_id)
            except (ValueError, TypeError):
                print(f"ERROR: Could not convert case_id '{case_id}' to integer")
                raise ValueError(f"Invalid case_id: {case_id} - must be a valid integer")"""
        },
        {
            'pattern': r"""    # Common validation for all network visualizations
    if case_id is None:
        print\("ERROR: case_id is None, no default will be used"\)
        raise ValueError\("case_id must be specified - no default value will be used"\)""",
            'replacement': """    # Common validation for all network visualizations
    if case_id is None:
        if DYNAMIC_CASE_MANAGEMENT_AVAILABLE:
            first_available = get_first_available_case_id()
            if first_available:
                print(f"INFO: Using first available case ID: {first_available}")
                case_id = first_available
            else:
                print("ERROR: case_id is None, and no cases available in database")
                raise ValueError("No valid case IDs available in the database")
        else:
            print("ERROR: case_id is None, no default will be used")
            raise ValueError("case_id must be specified - no default value will be used")"""
        }
    ]
    
    # Apply all replacements
    new_content = content
    for replacement in replacements:
        pattern = replacement['pattern']
        new_text = replacement['replacement']
        match = re.search(pattern, new_content)
        if match:
            old_text = match.group(0)
            new_content = new_content.replace(old_text, new_text)
    
    # Write the file back
    with open(file_path, 'w') as f:
        f.write(new_content)
    
    print(f"✅ Successfully updated case_id validation in {file_path}")
    return True

if __name__ == "__main__":
    print("Updating power_viz_with_database.py to use dynamic case management...")
    
    # Update imports
    update_power_viz_imports()
    
    # Update case_id validation
    update_case_id_validation()
    
    print("Done! Run the application now with 'python power_viz_with_database.py'")