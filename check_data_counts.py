import sqlite3
import pandas as pd

conn = sqlite3.connect('data.db')

contingencies = [55, 89, 122, 123, 157]

for cont_id in contingencies:
    print(f"\n{'='*60}")
    print(f"Contingency {cont_id}")
    print(f"{'='*60}")
    
    # Check SLR branch count
    slr_df = pd.read_sql_query(
        f"SELECT COUNT(*) as count FROM SLRBranchData WHERE base_case_id=43 AND contingency_case_id={cont_id}", 
        conn
    )
    print(f"  SLR Branches: {slr_df['count'].iloc[0]}")
    
    # Check DLR branch count
    dlr_df = pd.read_sql_query(
        f"SELECT COUNT(*) as count FROM DLRBranchData WHERE base_case_id=43 AND contingency_case_id={cont_id}", 
        conn
    )
    print(f"  DLR Branches: {dlr_df['count'].iloc[0]}")
    
    # Check SLR generator count
    slr_gen_df = pd.read_sql_query(
        f"SELECT COUNT(*) as count FROM SLR_Generator WHERE base_case_id=43 AND contingency_case_id={cont_id}", 
        conn
    )
    print(f"  SLR Generators: {slr_gen_df['count'].iloc[0]}")
    
    # Check DLR generator count
    dlr_gen_df = pd.read_sql_query(
        f"SELECT COUNT(*) as count FROM DLR_Generator WHERE base_case_id=43 AND contingency_case_id={cont_id}", 
        conn
    )
    print(f"  DLR Generators: {dlr_gen_df['count'].iloc[0]}")

conn.close()
