import sqlite3
import pandas as pd

conn = sqlite3.connect(r'C:\Projects\dlr-database-project\data.db')

# Check DLR branch data for branches with VIO >= 100
print("="*80)
print("DLR Branches with VIO >= 100 - Case 43, Contingency 123")
print("="*80)

dlr_df = pd.read_sql_query(
    """SELECT From_Bus, To_Bus, PF, QF, MVA, RATE, VIO,
       ROUND((MVA / RATE * 100), 2) as Calculated_Loading
       FROM DLRBranchData 
       WHERE base_case_id=43 AND contingency_case_id=123 AND VIO >= 100
       ORDER BY VIO DESC""", 
    conn
)

print("\nBranches with database VIO >= 100:")
print(dlr_df.to_string())

print("\n" + "="*80)
print("Analysis:")
print("="*80)
print(f"Total branches with VIO >= 100 in database: {len(dlr_df)}")
print("\nCalculated Loading vs Database VIO:")
for idx, row in dlr_df.iterrows():
    print(f"  Branch {int(row['From_Bus'])}->{int(row['To_Bus'])}: "
          f"DB_VIO={row['VIO']:.2f}%  vs  Calculated_Loading={row['Calculated_Loading']:.2f}%")
    print(f"    MVA={row['MVA']:.2f}, RATE={row['RATE']:.2f}")

conn.close()
