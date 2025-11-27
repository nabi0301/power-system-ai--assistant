import psycopg2

# Connect to database
conn = psycopg2.connect(database='118', user='postgres', password='pnnl')
cur = conn.cursor()

# Check all table names with 'case' in them
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name LIKE '%case%'
    ORDER BY table_name
""")
tables = cur.fetchall()
print("Tables with 'case' in name:")
for table in tables:
    print(f"  {table[0]}")

# Check foreign key constraints for contingencycases
cur.execute("""
    SELECT 
        tc.constraint_name,
        tc.table_name,
        kcu.column_name,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_name = 'contingencycases'
""")
fks = cur.fetchall()
print("\nForeign key constraints for contingencycases:")
for fk in fks:
    print(f"  {fk[0]}: {fk[1]}.{fk[2]} -> {fk[3]}.{fk[4]}")

conn.close()