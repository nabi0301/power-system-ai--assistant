#!/usr/bin/env python3
"""
Dynamic Case Management Helper

This module adds helper functions to handle case IDs more dynamically without
defaulting to case 42, making the application more flexible when working with
different power system cases.
"""

import os
import sqlite3
import pandas as pd
import traceback

def get_available_case_ids():
    """
    Get a list of available case IDs from the database
    
    Returns:
    --------
    list
        List of available base case IDs
    """
    try:
        # Connect to database
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        # Query for available base case IDs
        cursor.execute("SELECT DISTINCT base_case_id FROM BaseBusData")
        case_ids = [row[0] for row in cursor.fetchall()]
        
        # Close connection
        conn.close()
        
        if not case_ids:
            print("WARNING: No case IDs found in database!")
            return []
            
        print(f"Available case IDs: {case_ids}")
        return case_ids
        
    except Exception as e:
        print(f"ERROR: Could not get available case IDs: {e}")
        traceback.print_exc()
        return []

def get_first_available_case_id():
    """
    Get the first available case ID from the database
    
    Returns:
    --------
    int or None
        The first available case ID, or None if no cases are available
    """
    available_ids = get_available_case_ids()
    if available_ids:
        return available_ids[0]
    return None

def case_exists(case_id):
    """
    Check if a case exists in the database
    
    Parameters:
    -----------
    case_id : int
        The case ID to check
        
    Returns:
    --------
    bool
        True if the case exists, False otherwise
    """
    try:
        # Connect to database
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        # Query for the case
        cursor.execute(f"SELECT COUNT(*) FROM BaseBusData WHERE base_case_id = ?", (case_id,))
        count = cursor.fetchone()[0]
        
        # Close connection
        conn.close()
        
        return count > 0
        
    except Exception as e:
        print(f"ERROR: Could not check if case {case_id} exists: {e}")
        traceback.print_exc()
        return False

def validate_case_id(case_id):
    """
    Validate a case ID and ensure it exists in the database
    
    Parameters:
    -----------
    case_id : int or None
        The case ID to validate
        
    Returns:
    --------
    int
        A valid case ID
        
    Raises:
    -------
    ValueError
        If case_id is None or invalid
    """
    if case_id is None:
        raise ValueError("case_id must be specified - no default value will be used")
        
    try:
        case_id = int(case_id)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid case_id: {case_id} - must be a valid integer")
        
    # Check if the case exists
    if not case_exists(case_id):
        available_ids = get_available_case_ids()
        if available_ids:
            available_str = ", ".join(str(id) for id in available_ids)
            raise ValueError(f"Case {case_id} does not exist in the database. Available case IDs: {available_str}")
        else:
            raise ValueError(f"Case {case_id} does not exist, and no other cases are available in the database.")
            
    return case_id

# Test function
def test_case_management():
    """Test the case management functions"""
    print("\n=== Testing Case Management ===")
    
    available_ids = get_available_case_ids()
    print(f"Available case IDs: {available_ids}")
    
    if available_ids:
        first_id = get_first_available_case_id()
        print(f"First available case ID: {first_id}")
        
        # Test if the first case exists
        exists = case_exists(first_id)
        print(f"Case {first_id} exists: {exists}")
        
        # Test validation for a valid case
        try:
            valid_id = validate_case_id(first_id)
            print(f"Validated case ID: {valid_id}")
        except ValueError as e:
            print(f"Error validating case ID {first_id}: {e}")
        
        # Test validation for an invalid case
        try:
            invalid_id = -999
            validate_case_id(invalid_id)
            print(f"Validated case ID {invalid_id} (unexpected!)")
        except ValueError as e:
            print(f"Expected error for invalid case ID {invalid_id}: {e}")
            
    else:
        print("No cases available for testing")
        
    return True

if __name__ == "__main__":
    # Run test when executed directly
    test_case_management()