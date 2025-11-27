import psycopg2

# Connect to PostgreSQL database
conn = psycopg2.connect(database='118', user='postgres', password='pnnl')
cur = conn.cursor()

print("=" * 70)
print("CHECKING TABLE SCHEMAS")
print("=" * 70)

# Check BaseCases table structure
print("\nBaseCases table columns:")
cur.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'basecases'
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} (nullable: {row[2]})")

# Check primary key
cur.execute("""
    SELECT a.attname
    FROM pg_index i
    JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
    WHERE i.indrelid = 'basecases'::regclass AND i.indisprimary
""")
pk = cur.fetchone()
if pk:
    print(f"\n  Primary Key: {pk[0]}")

# Check ContingencyCases table structure
print("\n\nContingencyCases table columns:")
cur.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'contingencycases'
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} (nullable: {row[2]})")

# Check primary key
cur.execute("""
    SELECT a.attname
    FROM pg_index i
    JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
    WHERE i.indrelid = 'contingencycases'::regclass AND i.indisprimary
""")
pk = cur.fetchone()
if pk:
    print(f"\n  Primary Key: {pk[0]}")

conn.close()
