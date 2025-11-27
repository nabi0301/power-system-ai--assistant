import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    dbname='118',
    user='postgres',
    password='pnnl'
)
cur = conn.cursor()

print("=" * 70)
print("Tables migrated from SQLite (with '_sqlite' suffix):")
print("=" * 70)

cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema='public' AND table_name LIKE '%sqlite%'
    ORDER BY table_name;
""")
sqlite_tables = cur.fetchall()

for table in sqlite_tables:
    table_name = table[0]
    cur.execute(f'SELECT COUNT(*) FROM "{table_name}";')
    count = cur.fetchone()[0]
    print(f"  {table_name}: {count:,} rows")

print("\n" + "=" * 70)
print("All tables from original SQLite (without suffix):")
print("=" * 70)

# Check for tables that might have been created without suffix
original_tables = [
    'BaseCaseFiles', 'ContingencyScenarios', 'sqlite_stat1', 'sqlite_stat4',
    'CircularProcessingLog'
]

for table_name in original_tables:
    try:
        cur.execute(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table_name.lower()}');")
        if cur.fetchone()[0]:
            cur.execute(f'SELECT COUNT(*) FROM "{table_name}";')
            count = cur.fetchone()[0]
            print(f"  {table_name}: {count:,} rows")
    except:
        pass

conn.close()
