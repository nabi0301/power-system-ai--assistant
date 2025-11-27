"""
Data Availability Testing Module

This module provides functionality for testing the data availability checking features
in the network comparison visualization system.
"""

import sys
import os
import json
from data_availability import check_data_availability, get_available_cases

def test_data_availability():
    """Test the data availability checking functionality"""
    
    print("=" * 60)
    print("NETWORK COMPARISON DATA AVAILABILITY TEST")
    print("=" * 60)
    
    # Test cases to check
    test_cases = [
        (1, None),    # Base case 1, no contingency
        (5, None),    # Base case 5, no contingency
        (1, 1),       # Base case 1, contingency 1
        (5, 2),       # Base case 5, contingency 2
        (999, None),  # Non-existent base case
    ]
    
    print("\nTesting specific case availability:")
    print("-" * 60)
    
    for case in test_cases:
        base_id, cont_id = case
        case_desc = f"Base Case {base_id}" + (f", Contingency {cont_id}" if cont_id is not None else "")
        
        # Check data availability
        availability = check_data_availability(base_id, cont_id)
        
        # Count available data sets
        available_count = sum(1 for available in availability.values() if available)
        missing_data = [key.replace('_case', '').upper() for key, available in availability.items() if not available]
        available_data = [key.replace('_case', '').upper() for key, available in availability.items() if available]
        
        # Print results
        print(f"Case: {case_desc}")
        print(f"  Available datasets: {available_count}/4")
        print(f"  Available: {', '.join(available_data) if available_data else 'None'}")
        print(f"  Missing: {', '.join(missing_data) if missing_data else 'None'}")
        print("-" * 60)
    
    # Get and display cases with complete data
    print("\nFinding cases with complete data:")
    print("-" * 60)
    
    complete_cases = get_available_cases()
    
    if complete_cases:
        print(f"Found {len(complete_cases)} cases with complete data.")
        print("\nFirst 5 cases with complete data:")
        for i, case in enumerate(complete_cases[:5]):
            base_id = case['base_case_id']
            cont_id = case['contingency_case_id']
            print(f"  {i+1}. {case['description']}")
    else:
        print("No cases with complete data were found.")
    
    print("-" * 60)
    print("Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_data_availability()