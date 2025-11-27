#!/usr/bin/env python3
"""
Test the DLR vs SLR comparison function with deduplication
"""

import sqlite3
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def test_slr_dlr_comparison():
    """Test the SLR vs DLR comparison with deduplication"""
    
    conn = sqlite3.connect('data.db')
    base_case_id = 42
    scenarios = [56, 90, 123, 124, 158]
    
    print("Testing SLR vs DLR comparison with deduplication:")
    print("=" * 60)
    
    for i, contingency_id in enumerate(scenarios):
        print(f"\nScenario {i+1} - Contingency {contingency_id}:")
        
        # SLR query
        slr_query = """
        SELECT From_Bus, To_Bus, PF, QF, MVA, RATE, VIO
        FROM SLR_Branches 
        WHERE base_case_id = ? AND contingency_case_id = ?
        ORDER BY From_Bus, To_Bus
        """
        slr_df = pd.read_sql_query(slr_query, conn, params=(base_case_id, contingency_id))
        
        # DLR query  
        dlr_query = """
        SELECT From_Bus, To_Bus, PF, QF, MVA, RATE, VIO
        FROM DLR_Branches 
        WHERE base_case_id = ? AND contingency_case_id = ?
        ORDER BY From_Bus, To_Bus
        """
        dlr_df = pd.read_sql_query(dlr_query, conn, params=(base_case_id, contingency_id))
        
        print(f"  Original - SLR: {len(slr_df)}, DLR: {len(dlr_df)} branches")
        
        # Apply deduplication
        def deduplicate_branches(df):
            """Remove duplicate branch connections (e.g., 72->12 and 12->72)"""
            if df.empty:
                return df
            
            # Create a standardized connection identifier (smaller bus first)
            df = df.copy()
            df['BUS_MIN'] = df[['From_Bus', 'To_Bus']].min(axis=1)
            df['BUS_MAX'] = df[['From_Bus', 'To_Bus']].max(axis=1)
            df['CONNECTION_ID'] = df['BUS_MIN'].astype(str) + '-' + df['BUS_MAX'].astype(str)
            
            # Keep only the first occurrence of each unique connection
            df_sorted = df.sort_values(['From_Bus', 'To_Bus'])
            df_unique = df_sorted.drop_duplicates(subset=['CONNECTION_ID'], keep='first')
            
            # Remove the helper columns
            df_unique = df_unique.drop(['BUS_MIN', 'BUS_MAX', 'CONNECTION_ID'], axis=1)
            
            return df_unique.reset_index(drop=True)
        
        # Apply deduplication to both SLR and DLR data
        if not slr_df.empty:
            slr_df = deduplicate_branches(slr_df)
        if not dlr_df.empty:
            dlr_df = deduplicate_branches(dlr_df)
            
        print(f"  After deduplication - SLR: {len(slr_df)}, DLR: {len(dlr_df)} branches")
        
        if not slr_df.empty and not dlr_df.empty:
            # Calculate violation percentages
            slr_df['VIO_PCT'] = (slr_df['MVA'] / slr_df['RATE']) * 100
            dlr_df['VIO_PCT'] = (dlr_df['MVA'] / dlr_df['RATE']) * 100
            
            # Calculate statistics
            slr_violations = (slr_df['VIO_PCT'] > 100).sum()
            dlr_violations = (dlr_df['VIO_PCT'] > 100).sum()
            
            print(f"  Violations - SLR: {slr_violations}, DLR: {dlr_violations}")
            print(f"  Max loading - SLR: {slr_df['VIO_PCT'].max():.1f}%, DLR: {dlr_df['VIO_PCT'].max():.1f}%")
            
            # Sample a few branch comparisons
            sample_branches = slr_df.head(3)
            print(f"  Sample branches:")
            for _, branch in sample_branches.iterrows():
                from_bus = int(branch['From_Bus'])
                to_bus = int(branch['To_Bus'])
                slr_loading = branch['VIO_PCT']
                
                # Find corresponding DLR branch
                dlr_branch = dlr_df[(dlr_df['From_Bus'] == from_bus) & (dlr_df['To_Bus'] == to_bus)]
                if not dlr_branch.empty:
                    dlr_loading = dlr_branch['VIO_PCT'].iloc[0]
                    print(f"    Branch {from_bus}-{to_bus}: SLR {slr_loading:.1f}% vs DLR {dlr_loading:.1f}%")
    
    conn.close()
    print(f"\n✅ Test completed successfully!")
    print(f"The deduplication ensures only unique connections are analyzed,")
    print(f"eliminating bidirectional duplicates like 72→12 and 12→72.")

if __name__ == "__main__":
    test_slr_dlr_comparison()