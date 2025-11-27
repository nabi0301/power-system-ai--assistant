import sqlite3

conn = sqlite3.connect('data.db')
cursor = conn.cursor()

print('=== SLR_Generator data for base_case_id=42 ===')
cursor.execute('SELECT contingency_case_id, COUNT(*) FROM SLR_Generator WHERE base_case_id = 42 GROUP BY contingency_case_id ORDER BY contingency_case_id')
for row in cursor.fetchall():
    print(f'Contingency {row[0]}: {row[1]} generators')

print('\n=== DLR_Generator data for base_case_id=42 ===')
cursor.execute('SELECT contingency_case_id, COUNT(*) FROM DLR_Generator WHERE base_case_id = 42 GROUP BY contingency_case_id ORDER BY contingency_case_id')
for row in cursor.fetchall():
    print(f'Contingency {row[0]}: {row[1]} generators')

print('\n=== Sample SLR generator data (first available) ===')
cursor.execute('SELECT * FROM SLR_Generator WHERE base_case_id = 42 LIMIT 5')
for row in cursor.fetchall():
    print(f'{row}')

conn.close()
