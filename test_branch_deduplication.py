#!/usr/bin/env python3
"""
Test DLR vs SLR branch deduplication
"""

import sqlite3
import pandas as pd

def test_branch_deduplication():
    """Test that branch deduplication reduces to 186 unique branches"""
    
    conn = sqlite3.connect('data.db')
    
    # Test for one scenario
    base_case_id = 42
    contingency_id = 56
    
    # Query SLR data
    slr_query = """
    SELECT From_Bus, To_Bus, VIO, RATE, MVA 
    FROM SLR_Branches 
    WHERE base_case_id = ? AND contingency_case_id = ?
    ORDER BY From_Bus, To_Bus
    """
    slr_df = pd.read_sql_query(slr_query, conn, params=(base_case_id, contingency_id))
    
    print(f"Original SLR branches: {len(slr_df)}")
    print(f"Sample branches:")
    print(slr_df[['From_Bus', 'To_Bus']].head(10))
    
    # Check for duplicates
    print(f"\nChecking for duplicate connections...")
    duplicates = []
    for _, row in slr_df.iterrows():
        from_bus = row['From_Bus']
        to_bus = row['To_Bus']
        
        # Check if reverse connection exists
        reverse_exists = slr_df[(slr_df['From_Bus'] == to_bus) & (slr_df['To_Bus'] == from_bus)]
        if not reverse_exists.empty:
            connection = f"{min(from_bus, to_bus)}-{max(from_bus, to_bus)}"
            if connection not in duplicates:
                duplicates.append(connection)
                print(f"  Found duplicate: {from_bus} -> {to_bus} and {to_bus} -> {from_bus}")
    
    print(f"Found {len(duplicates)} duplicate connection pairs")
    
    # Apply deduplication
    def deduplicate_branches(df):
        """Remove duplicate branch connections"""
        if df.empty:
            return df
        
        df = df.copy()
        df['BUS_MIN'] = df[['From_Bus', 'To_Bus']].min(axis=1)
        df['BUS_MAX'] = df[['From_Bus', 'To_Bus']].max(axis=1)
        df['CONNECTION_ID'] = df['BUS_MIN'].astype(str) + '-' + df['BUS_MAX'].astype(str)
        
        df_sorted = df.sort_values(['From_Bus', 'To_Bus'])
        df_unique = df_sorted.drop_duplicates(subset=['CONNECTION_ID'], keep='first')
        df_unique = df_unique.drop(['BUS_MIN', 'BUS_MAX', 'CONNECTION_ID'], axis=1)
        
        return df_unique.reset_index(drop=True)
    
    slr_deduplicated = deduplicate_branches(slr_df)
    
    print(f"\nAfter deduplication: {len(slr_deduplicated)} branches")
    print(f"Target: 186 branches")
    print(f"Match: {'✅' if len(slr_deduplicated) == 186 else '❌'}")
    
    conn.close()

if __name__ == "__main__":
    test_branch_deduplication()