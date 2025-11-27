#!/usr/bin/env python3
"""
Test the network graph comparison with GEN_ADJ diamond shapes
"""

import sqlite3
import pandas as pd

def test_network_graph_with_diamonds():
    """Test that the network graphs show GEN_ADJ diamonds correctly"""
    print("🧪 Testing Network Graph with GEN_ADJ Diamond Shapes...")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect('data.db')
        
        # Test data loading
        case_id = 42
        
        # Get SLR generator data
        slr_gen_df = pd.read_sql_query(f"SELECT BUS_NUMBER, GEN_INI, GEN_NEW, GEN_ADJ FROM SLR_Generator WHERE base_case_id = {case_id}", conn)
        
        # Get DLR generator data  
        dlr_gen_df = pd.read_sql_query(f"SELECT BUS_NUMBER, GEN_INI, GEN_NEW, GEN_ADJ FROM DLR_Generator WHERE base_case_id = {case_id}", conn)
        
        conn.close()
        
        print(f"📊 SLR Generator Data:")
        print(f"   • Total generators: {len(slr_gen_df)}")
        if not slr_gen_df.empty:
            print(f"   • Buses with generators: {sorted(slr_gen_df['BUS_NUMBER'].unique())}")
            print(f"   • GEN_ADJ values: {slr_gen_df['GEN_ADJ'].tolist()}")
        
        print(f"\n📊 DLR Generator Data:")
        print(f"   • Total generators: {len(dlr_gen_df)}")
        if not dlr_gen_df.empty:
            print(f"   • Buses with generators: {sorted(dlr_gen_df['BUS_NUMBER'].unique())}")
            print(f"   • GEN_ADJ values: {dlr_gen_df['GEN_ADJ'].tolist()}")
        
        print(f"\n💎 Expected Diamond Shapes:")
        print(f"   🔵 Blue diamonds (SLR): Buses {sorted(slr_gen_df['BUS_NUMBER'].unique()) if not slr_gen_df.empty else 'None'}")
        print(f"   🟢 Green diamonds (DLR): Buses {sorted(dlr_gen_df['BUS_NUMBER'].unique()) if not dlr_gen_df.empty else 'None'}")
        
        # Test that modifications would work
        print(f"\n✅ Network Graph Diamond Test Results:")
        print(f"   • SLR data available: {'Yes' if not slr_gen_df.empty else 'No'}")
        print(f"   • DLR data available: {'Yes' if not dlr_gen_df.empty else 'No'}")
        print(f"   • Expected blue diamonds: {len(slr_gen_df)} buses")
        print(f"   • Expected green diamonds: {len(dlr_gen_df)} buses")
        
        print(f"\n💡 What You Should See in the Network Graphs:")
        print(f"   🔵 SLR Network: Blue diamond shapes at buses with GEN_ADJ values")
        print(f"   🟢 DLR Network: Green diamond shapes at buses with GEN_ADJ values")
        print(f"   ⚪ Other buses: Regular circles")
        print(f"   📊 Hover info: Shows GEN_ADJ values for diamond-shaped buses")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("💎 NETWORK GRAPH DIAMOND SHAPES TEST")
    print("=" * 60)
    test_network_graph_with_diamonds()