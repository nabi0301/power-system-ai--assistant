import sqlite3

conn = sqlite3.connect('data.db')
cursor = conn.cursor()

# Check SLR data
cursor.execute('SELECT DISTINCT base_case_id, contingency_case_id FROM SLRBranchData WHERE base_case_id=43 ORDER BY contingency_case_id')
print('SLR data for case 43:')
for row in cursor.fetchall():
    print(f'  Contingency {row[1]}')

# Check DLR data
cursor.execute('SELECT DISTINCT base_case_id, contingency_case_id FROM DLRBranchData WHERE base_case_id=43 ORDER BY contingency_case_id')
print('\nDLR data for case 43:')
for row in cursor.fetchall():
    print(f'  Contingency {row[1]}')

conn.close()
