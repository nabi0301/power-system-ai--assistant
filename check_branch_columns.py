import psycopg2

conn = psycopg2.connect(database='118', user='postgres', password='pnnl')
cur = conn.cursor()

# Check all branch tables
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name LIKE '%branch%'
    ORDER BY table_name
""")
tables = cur.fetchall()
print("Branch tables:")
for table in tables:
    print(f"\n  {table[0]}:")
    cur.execute(f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = '{table[0]}'
        ORDER BY ordinal_position
    """)
    columns = cur.fetchall()
    for col in columns:
        print(f"    - {col[0]}")

conn.close()
