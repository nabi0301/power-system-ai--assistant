import psycopg2

conn = psycopg2.connect(database='118', user='postgres', password='pnnl')
cur = conn.cursor()

# Check how many contingency branch records exist
cur.execute("SELECT COUNT(*) FROM contingencybranchdata")
count = cur.fetchone()[0]
print(f"Existing contingencybranchdata records: {count}")

# Check a sample of the existing records
cur.execute("""
    SELECT contingency_case_id, from_bus, to_bus, circuit_id 
    FROM contingencybranchdata 
    LIMIT 10
""")
print("\nSample records:")
for row in cur.fetchall():
    print(f"  contingency_case_id={row[0]}, from_bus={row[1]}, to_bus={row[2]}, circuit_id={row[3]}")

# Check how many contingency cases exist
cur.execute("SELECT COUNT(*) FROM contingencycases")
count = cur.fetchone()[0]
print(f"\nTotal contingency cases: {count}")

conn.close()
