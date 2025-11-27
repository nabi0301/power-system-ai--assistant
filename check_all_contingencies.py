#!/usr/bin/env python3
"""
Check branch counts across all contingency cases
"""

import sqlite3
import pandas as pd

def check_all_contingencies():
    """Check branch counts for all 5 contingency cases"""
    
    conn = sqlite3.connect('data.db')
    base_case_id = 42
    
    print("Branch counts across contingency cases:")
    print("=" * 50)
    
    for cont_id in [56, 90, 123, 124, 158]:
        # SLR branches
        slr_df = pd.read_sql_query(
            'SELECT From_Bus, To_Bus FROM SLR_Branches WHERE base_case_id = ? AND contingency_case_id = ?', 
            conn, params=(base_case_id, cont_id)
        )
        
        # DLR branches  
        dlr_df = pd.read_sql_query(
            'SELECT From_Bus, To_Bus FROM DLR_Branches WHERE base_case_id = ? AND contingency_case_id = ?', 
            conn, params=(base_case_id, cont_id)
        )
        
        print(f"Contingency {cont_id}:")
        print(f"  SLR: {len(slr_df)} branches")
        print(f"  DLR: {len(dlr_df)} branches")
        
        # Apply deduplication to get unique connections
        def deduplicate_branches(df):
            if df.empty:
                return df
            df = df.copy()
            df['BUS_MIN'] = df[['From_Bus', 'To_Bus']].min(axis=1)
            df['BUS_MAX'] = df[['From_Bus', 'To_Bus']].max(axis=1)
            df['CONNECTION_ID'] = df['BUS_MIN'].astype(str) + '-' + df['BUS_MAX'].astype(str)
            df_unique = df.drop_duplicates(subset=['CONNECTION_ID'], keep='first')
            return df_unique
        
        slr_unique = deduplicate_branches(slr_df)
        dlr_unique = deduplicate_branches(dlr_df)
        
        print(f"  After deduplication - SLR: {len(slr_unique)}, DLR: {len(dlr_unique)}")
        print()
    
    conn.close()

if __name__ == "__main__":
    check_all_contingencies()