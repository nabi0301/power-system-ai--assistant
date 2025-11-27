import psycopg2

conn = psycopg2.connect(database='118', user='postgres', password='pnnl')
cur = conn.cursor()

print("Dropping incorrect foreign key constraint...")
cur.execute("ALTER TABLE contingencybranchdata DROP CONSTRAINT contingency_branches_base_case_id_fkey")
conn.commit()

print("Adding correct foreign key constraint...")
cur.execute("ALTER TABLE contingencybranchdata ADD CONSTRAINT contingency_branches_base_case_id_fkey FOREIGN KEY (base_case_id) REFERENCES basecases(base_case_id)")
conn.commit()

print("Foreign key constraint fixed successfully!")

# Verify
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
    AND kcu.column_name = 'base_case_id'
""")
result = cur.fetchone()
print(f"\nVerification: {result[1]}.{result[2]} -> {result[3]}.{result[4]}")

conn.close()
