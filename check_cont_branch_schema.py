import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    dbname='118',
    user='postgres',
    password='pnnl'
)
cur = conn.cursor()

print("ContingencyBranchData columns:")
cur.execute("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns 
    WHERE table_name='contingencybranchdata' 
    ORDER BY ordinal_position;
""")
cols = cur.fetchall()
for col in cols:
    print(f"  {col[0]}: {col[1]} (nullable={col[2]}, default={col[3]})")

conn.close()
