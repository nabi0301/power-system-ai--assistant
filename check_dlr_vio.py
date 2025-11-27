import sqlite3
import pandas as pd

conn = sqlite3.connect(r'C:\Projects\dlr-database-project\data.db')

# Check DLR branch data for case 43, contingency 123
print("="*80)
print("DLR Branch Data - Case 43, Contingency 123")
print("="*80)

dlr_df = pd.read_sql_query(
    "SELECT From_Bus, To_Bus, PF, QF, MVA, RATE, VIO FROM DLRBranchData WHERE base_case_id=43 AND contingency_case_id=123 ORDER BY VIO DESC LIMIT 20", 
    conn
)

print("\nTop 20 branches by VIO:")
print(dlr_df.to_string())

print("\n" + "="*80)
print("VIO Statistics:")
print("="*80)
print(f"Max VIO: {dlr_df['VIO'].max()}")
print(f"Min VIO: {dlr_df['VIO'].min()}")
print(f"Mean VIO: {dlr_df['VIO'].mean():.2f}")
print(f"Branches with VIO >= 100: {len(dlr_df[dlr_df['VIO'] >= 100])}")
print(f"Branches with VIO >= 99: {len(dlr_df[dlr_df['VIO'] >= 99])}")

# Check all VIO values
all_vio_df = pd.read_sql_query(
    "SELECT VIO FROM DLRBranchData WHERE base_case_id=43 AND contingency_case_id=123", 
    conn
)
print(f"\nTotal branches: {len(all_vio_df)}")
print(f"VIO >= 100 count: {len(all_vio_df[all_vio_df['VIO'] >= 100])}")

conn.close()
