import sqlite3

# Connect to SQLite database
sqlite_conn = sqlite3.connect(r"C:\Users\nira771\data - Copy.db")
sqlite_cur = sqlite_conn.cursor()

# Get all tables
sqlite_cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = sqlite_cur.fetchall()

print("=" * 70)
print("SQLite Database Tables:")
print("=" * 70)

for table in tables:
    table_name = table[0]
    print(f"\n{table_name}:")
    
    # Get table schema
    sqlite_cur.execute(f"PRAGMA table_info({table_name});")
    columns = sqlite_cur.fetchall()
    
    for col in columns:
        col_id, col_name, col_type, not_null, default_val, is_pk = col
        nullable = "NOT NULL" if not_null else "NULL"
        pk = " PRIMARY KEY" if is_pk else ""
        print(f"  {col_name}: {col_type} ({nullable}){pk}")
    
    # Get row count
    sqlite_cur.execute(f"SELECT COUNT(*) FROM {table_name};")
    count = sqlite_cur.fetchone()[0]
    print(f"  → Row count: {count:,}")

sqlite_conn.close()
