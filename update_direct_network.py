#!/usr/bin/env python3
"""
Helper script to update the fetch_case_data function in direct_network_integration.py
"""

def update_fetch_case_data():
    """Update fetch_case_data function to use dynamic case management"""
    file_path = "direct_network_integration.py"
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Find the fetch_case_data function
    start_marker = "def fetch_case_data(case_id, contingency_id=None):"
    start_pos = content.find(start_marker)
    
    if start_pos < 0:
        print("❌ Could not find fetch_case_data function")
        return False
        
    # Find the position of the code for case_id validation
    validate_marker = "        # Validate case_id"
    validate_pos = content.find(validate_marker, start_pos)
    
    if validate_pos < 0:
        print("❌ Could not find case_id validation code")
        return False
        
    # Find where to stop replacing
    stop_marker = "        # Validate contingency_id if provided"
    stop_pos = content.find(stop_marker, validate_pos)
    
    if stop_pos < 0:
        print("❌ Could not find end of case_id validation code")
        return False
    
    # Create new validation code
    new_validation_code = """        # Validate case_id
        if DYNAMIC_CASE_MANAGEMENT_AVAILABLE:
            try:
                case_id = validate_case_id(case_id)
            except ValueError as e:
                print(f"ERROR: {e}")
                if case_id is None:
                    first_available = get_first_available_case_id()
                    if first_available:
                        print(f"INFO: Using first available case ID: {first_available}")
                        case_id = first_available
                    else:
                        raise ValueError("No valid case IDs available in the database")
                else:
                    raise
        else:
            # Validate case_id without the helper module
            if case_id is None:
                print("ERROR: case_id is None, no default will be used")
                raise ValueError("case_id must be specified - no default value will be used")
            else:
                try:
                    case_id = int(case_id)
                except (ValueError, TypeError):
                    print(f"ERROR: Invalid case_id '{case_id}'")
                    raise ValueError(f"Invalid case_id: {case_id} - must be a valid integer")
"""
    
    # Replace the validation code
    new_content = content[:validate_pos] + new_validation_code + content[stop_pos:]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ Successfully updated fetch_case_data function in {file_path}")
    return True

if __name__ == "__main__":
    print("Updating direct_network_integration.py...")
    update_fetch_case_data()
    print("Done!")