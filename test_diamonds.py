"""Test script to verify diamond generation for SLR/DLR networks"""
import sqlite3
import pandas as pd
import sys

# Add current directory to path
sys.path.insert(0, '.')

def test_generator_loading():
    """Test loading generator data for case 42"""
    conn = sqlite3.connect('data.db')
    
    case_id = 42
    actual_slr_id = 56  # First contingency maps to this
    actual_dlr_id = 56
    
    print(f"=== Testing Generator Data Loading ===")
    print(f"Case ID: {case_id}, SLR Contingency: {actual_slr_id}, DLR Contingency: {actual_dlr_id}\n")
    
    # Load SLR generator data
    slr_gen_df = pd.read_sql_query(
        f"SELECT BUS_NUMBER, GEN_INI, GEN_NEW, GEN_ADJ FROM SLR_Generator WHERE base_case_id = {case_id} AND contingency_case_id = {actual_slr_id}", 
        conn
    )
    print(f"✅ SLR Generator Data:")
    print(f"   Rows: {len(slr_gen_df)}")
    if not slr_gen_df.empty:
        print(f"   Columns: {slr_gen_df.columns.tolist()}")
        print(f"   Bus numbers: {slr_gen_df['BUS_NUMBER'].tolist()}")
        print(f"   GEN_ADJ values: {slr_gen_df['GEN_ADJ'].tolist()}")
    else:
        print(f"   ⚠️ NO DATA - This is expected for contingency 56")
    
    print()
    
    # Load DLR generator data
    dlr_gen_df = pd.read_sql_query(
        f"SELECT BUS_NUMBER, GEN_INI, GEN_NEW, GEN_ADJ FROM DLR_Generator WHERE base_case_id = {case_id} AND contingency_case_id = {actual_dlr_id}", 
        conn
    )
    print(f"✅ DLR Generator Data:")
    print(f"   Rows: {len(dlr_gen_df)}")
    if not dlr_gen_df.empty:
        print(f"   Columns: {dlr_gen_df.columns.tolist()}")
        print(f"   Bus numbers: {dlr_gen_df['BUS_NUMBER'].tolist()}")
        print(f"   GEN_ADJ values: {dlr_gen_df['GEN_ADJ'].tolist()}")
    else:
        print(f"   ⚠️ NO DATA")
    
    print()
    
    # Load bus data for DLR
    dlr_buses_df = pd.read_sql_query(
        f"SELECT bus_number as BUS_NUMBER, VM, VA, base_kv as BASE_KV, 0 as PG, 0 as QG, PD, QD FROM DLR_Buses WHERE base_case_id = {case_id} AND contingency_case_id = {actual_dlr_id}", 
        conn
    )
    print(f"✅ DLR Bus Data: {len(dlr_buses_df)} buses")
    
    # Simulate merge
    if not dlr_gen_df.empty:
        print(f"\n=== Testing Merge Operation ===")
        print(f"Before merge - dlr_buses_df shape: {dlr_buses_df.shape}")
        print(f"Before merge - dlr_gen_df shape: {dlr_gen_df.shape}")
        
        merged_df = dlr_buses_df.merge(
            dlr_gen_df[['BUS_NUMBER', 'GEN_INI', 'GEN_NEW', 'GEN_ADJ']], 
            on='BUS_NUMBER', 
            how='left',
            suffixes=('', '_gen')
        )
        
        print(f"After merge - merged_df shape: {merged_df.shape}")
        merged_df['HAS_GEN'] = ~merged_df['GEN_ADJ'].isna()
        merged_df['SHOW_GEN_ADJ'] = merged_df['HAS_GEN']
        
        gen_count = merged_df['HAS_GEN'].sum()
        print(f"\n✅ Generators with GEN_ADJ: {gen_count}")
        print(f"   Buses with generators: {merged_df[merged_df['HAS_GEN']]['BUS_NUMBER'].tolist()}")
        print(f"   GEN_ADJ values: {merged_df[merged_df['HAS_GEN']]['GEN_ADJ'].tolist()}")
    
    conn.close()
    
    print(f"\n=== Conclusion ===")
    print(f"SLR Case 56: {len(slr_gen_df)} generators (expected 0)")
    print(f"DLR Case 56: {len(dlr_gen_df)} generators (expected 3)")
    print(f"\nTo see diamonds, select contingency 2 (case 90) or higher!")

if __name__ == '__main__':
    test_generator_loading()
