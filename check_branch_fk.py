import psycopg2

conn = psycopg2.connect(database='118', user='postgres', password='pnnl')
cur = conn.cursor()

# Check the foreign key constraint on contingencybranchdata
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
    AND tc.table_name = 'contingencybranchdata'
""")
fks = cur.fetchall()
print("Foreign key constraints for contingencybranchdata:")
for fk in fks:
    print(f"  {fk[0]}: {fk[1]}.{fk[2]} -> {fk[3]}.{fk[4]}")

conn.close()
