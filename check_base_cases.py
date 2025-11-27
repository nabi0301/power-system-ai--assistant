import psycopg2

conn = psycopg2.connect(host='localhost', port='5432', database='118', user='postgres', password='pnnl')
cursor = conn.cursor()

# Check base_cases structure
cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'base_cases' ORDER BY ordinal_position")
columns = cursor.fetchall()
print('base_cases table columns:')
for col in columns:
    print(f'  - {col[0]} ({col[1]})')

# Sample data
cursor.execute("SELECT * FROM base_cases LIMIT 3")
sample = cursor.fetchall()
print('\nSample data:')
for row in sample:
    print(f'  {row}')

cursor.close()
conn.close()