#!/usr/bin/env python3
"""
Test script to verify branch deduplication logic for DLR/SLR network graphs
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_viz_fall import load_slr_case_from_db, load_dlr_case_from_db

def test_deduplication():
    """Test the deduplication logic for SLR and DLR cases"""
    print("🔍 Testing Branch Deduplication Logic")
    print("=" * 50)
    
    # Test SLR case (use base_case_id=42 as seen in database)
    print("\n📊 Testing SLR Case Deduplication:")
    try:
        slr_buses, slr_branches = load_slr_case_from_db(base_case_id=42, contingency_case_id=90)
        print(f"✅ SLR Case 90: {len(slr_buses)} buses, {len(slr_branches)} branches")
    except Exception as e:
        print(f"❌ SLR Case 90 failed: {e}")
    
    try:
        slr_buses, slr_branches = load_slr_case_from_db(base_case_id=42, contingency_case_id=123)
        print(f"✅ SLR Case 123: {len(slr_buses)} buses, {len(slr_branches)} branches")
    except Exception as e:
        print(f"❌ SLR Case 123 failed: {e}")
    
    # Test DLR case (use base_case_id=42 as seen in database)
    print("\n📊 Testing DLR Case Deduplication:")
    try:
        dlr_buses, dlr_branches = load_dlr_case_from_db(base_case_id=42, contingency_case_id=90)
        print(f"✅ DLR Case 90: {len(dlr_buses)} buses, {len(dlr_branches)} branches")
    except Exception as e:
        print(f"❌ DLR Case 90 failed: {e}")
    
    try:
        dlr_buses, dlr_branches = load_dlr_case_from_db(base_case_id=42, contingency_case_id=123)
        print(f"✅ DLR Case 123: {len(dlr_buses)} buses, {len(dlr_branches)} branches")
    except Exception as e:
        print(f"❌ DLR Case 123 failed: {e}")
    
    print("\n🎯 Deduplication Test Complete!")

if __name__ == "__main__":
    test_deduplication()