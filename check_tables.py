import psycopg2

conn = psycopg2.connect(host='localhost', database='118', user='postgres', password='pnnl')
cursor = conn.cursor()

# Check contingency tables
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema='public' 
    AND table_name LIKE '%contingency%'
""")
tables = cursor.fetchall()
print("Contingency tables:", [t[0] for t in tables])

# Check first table structure
if tables:
    table_name = tables[0][0]
    cursor.execute(f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position
    """)
    columns = cursor.fetchall()
    print(f"\nColumns in {table_name}:")
    for col in columns:
        print(f"  {col[0]}: {col[1]}")

# Check for case_number or similar
cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
sample = cursor.fetchall()
print(f"\nSample rows from {table_name}:")
for row in sample:
    print(row)

conn.close()