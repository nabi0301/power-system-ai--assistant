#!/usr/bin/env python3
"""
Test script to verify power flow-based branch thickness calculation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_viz_fall import get_branch_width_by_power_flow

def test_power_flow_thickness():
    """Test the power flow-based thickness calculation"""
    print("🔍 Testing Power Flow-Based Branch Thickness")
    print("=" * 50)
    
    # Test cases with different power flow scenarios
    test_cases = [
        # [PF, QF, RATE, VIO, Expected Description]
        [0, 0, 100, 0, "Zero power flow"],
        [20, 15, 100, 0, "Low loading (25%)"],
        [40, 30, 100, 0, "Medium loading (50%)"],
        [60, 80, 100, 0, "High loading (100%)"],
        [80, 60, 100, 0, "High loading (100%)"],
        [90, 60, 100, 0, "Overloaded (108%)"],
        [100, 50, 100, 110, "Critical violation (VIO=110)"],
        [150, 0, None, 0, "High absolute power (no rate)"],
        [50, 0, None, 0, "Medium absolute power (no rate)"],
        [10, 0, None, 0, "Low absolute power (no rate)"],
    ]
    
    print("\n📊 Testing Branch Width Calculations:")
    print("PF(MW) | QF(MVAr) | RATE(MVA) | VIO | S(MVA) | Loading% | Width | Description")
    print("-" * 85)
    
    for pf, qf, rate, vio, description in test_cases:
        width = get_branch_width_by_power_flow(pf, qf, rate, vio)
        apparent_power = (pf**2 + qf**2)**0.5
        
        if rate:
            loading_pct = (apparent_power / rate) * 100
            loading_str = f"{loading_pct:6.1f}%"
        else:
            loading_str = "   N/A "
        
        print(f"{pf:6.0f} | {qf:8.0f} | {rate if rate else 'None':9} | {vio:3.0f} | {apparent_power:6.1f} | {loading_str} | {width:5.0f} | {description}")
    
    print("\n🎯 Branch Thickness Legend:")
    print("Width 2: Very light loading (<20% or <25 MVA)")
    print("Width 3: Light loading (20-50% or 25-75 MVA)")
    print("Width 4: Medium loading (50-80% or 75-150 MVA)")
    print("Width 6: High loading (80-100% or >150 MVA)")
    print("Width 8: Critical violation (>100% or VIO≥100)")
    
    print("\n🎯 Power Flow Thickness Test Complete!")

if __name__ == "__main__":
    test_power_flow_thickness()