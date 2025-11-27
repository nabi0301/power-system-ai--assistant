import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    dbname='118',
    user='postgres',
    password='pnnl'
)
cur = conn.cursor()

# Get table names
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE '%branch%' ORDER BY tablename;")
tables = cur.fetchall()
print("Branch tables:")
for table in tables:
    print(f"  {table[0]}")
    
# Get BaseBranchData columns
print("\nBaseBranchData columns:")
cur.execute("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns 
    WHERE table_name='basebranchdata' 
    ORDER BY ordinal_position;
""")
cols = cur.fetchall()
for col in cols:
    print(f"  {col[0]}: {col[1]} (nullable={col[2]}, default={col[3]})")

conn.close()
