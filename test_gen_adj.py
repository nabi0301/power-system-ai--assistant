#!/usr/bin/env python3
"""
Test script to verify generator adjustment display in SLR/DLR network graphs
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_viz_fall import load_slr_case_from_db, load_dlr_case_from_db

def test_generator_adjustments():
    """Test that generator adjustments are loaded and available in bus data"""
    print("🔍 Testing Generator Adjustment Loading")
    print("=" * 50)
    
    # Test SLR case
    print("\n📊 Testing SLR Case Generator Adjustments:")
    try:
        slr_buses, slr_branches = load_slr_case_from_db(contingency_case_id=90, base_case_id=42)
        print(f"✅ SLR Case 90: {len(slr_buses)} buses, {len(slr_branches)} branches")
        
        # Check if GEN_ADJ column exists and has data
        if 'GEN_ADJ' in slr_buses.columns:
            gen_adj_buses = slr_buses[slr_buses['GEN_ADJ'] != 0]
            print(f"   Buses with generator adjustments: {len(gen_adj_buses)}")
            if len(gen_adj_buses) > 0:
                print("   Generator adjustments found:")
                for _, bus in gen_adj_buses.iterrows():
                    print(f"     Bus {bus['BUS_NUMBER']}: {bus['GEN_ADJ']:+.1f} MW")
        else:
            print("   ❌ GEN_ADJ column not found in SLR bus data")
    except Exception as e:
        print(f"❌ SLR Case 90 failed: {e}")
    
    # Test DLR case  
    print("\n📊 Testing DLR Case Generator Adjustments:")
    try:
        dlr_buses, dlr_branches = load_dlr_case_from_db(contingency_case_id=90, base_case_id=42)
        print(f"✅ DLR Case 90: {len(dlr_buses)} buses, {len(dlr_branches)} branches")
        
        # Check if GEN_ADJ column exists and has data
        if 'GEN_ADJ' in dlr_buses.columns:
            gen_adj_buses = dlr_buses[dlr_buses['GEN_ADJ'] != 0]
            print(f"   Buses with generator adjustments: {len(gen_adj_buses)}")
            if len(gen_adj_buses) > 0:
                print("   Generator adjustments found:")
                for _, bus in gen_adj_buses.iterrows():
                    print(f"     Bus {bus['BUS_NUMBER']}: {bus['GEN_ADJ']:+.1f} MW")
        else:
            print("   ❌ GEN_ADJ column not found in DLR bus data")
    except Exception as e:
        print(f"❌ DLR Case 90 failed: {e}")
    
    print("\n🎯 Generator Adjustment Test Complete!")

if __name__ == "__main__":
    test_generator_adjustments()