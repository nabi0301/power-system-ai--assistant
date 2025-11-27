import sqlite3

# Connect to the database
conn = sqlite3.connect('data.db')
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("All tables in database:")
for table in tables:
    print(f"- {table[0]}")

print("\nLooking for Generator tables:")
generator_tables = [t[0] for t in tables if 'Generator' in t[0] or 'generator' in t[0]]
print(generator_tables)

if generator_tables:
    print("\nSchema for Generator tables:")
    for table in generator_tables:
        print(f"\nTable: {table}")
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")

# Close the connection
conn.close()