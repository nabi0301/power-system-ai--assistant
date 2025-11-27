import psycopg2

# Connect to database
conn = psycopg2.connect(database='118', user='postgres', password='pnnl')
cur = conn.cursor()

# Check if base_case_id 625 exists
cur.execute("SELECT COUNT(*) FROM basecases WHERE base_case_id = 625")
base_case_exists = cur.fetchone()[0]
print(f"base_case_id 625 exists: {base_case_exists > 0}")

# Check case 132
cur.execute("SELECT base_case_id FROM basecases WHERE case_number = 132")
result = cur.fetchone()
print(f"Case 132 has base_case_id: {result[0] if result else 'Not found'}")

# Check foreign key constraint
cur.execute("""
    SELECT constraint_name, table_name, column_name 
    FROM information_schema.key_column_usage 
    WHERE table_name = 'contingencycases' AND column_name = 'base_case_id'
""")
constraints = cur.fetchall()
print(f"Foreign key constraints: {constraints}")

# Check table names
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%cases%'")
tables = cur.fetchall()
print(f"Tables with 'cases': {[t[0] for t in tables]}")

conn.close()