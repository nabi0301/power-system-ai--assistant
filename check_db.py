import sqlite3

conn = sqlite3.connect('data.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("📊 Database: data.db")
print(f"📍 Location: C:\\Projects\\dlr-database-project\\data.db")
print(f"\n📋 Tables ({len(tables)} total):")
for table in tables[:15]:  # Show first 15
    print(f"  - {table[0]}")

# Check BaseBusData schema
print("\n📐 BaseBusData Schema:")
cursor.execute("PRAGMA table_info(BaseBusData)")
cols = cursor.fetchall()
for col in cols:
    print(f"  {col[1]} ({col[2]})")

# Check if base_case_id column exists
has_base_case_id = any(col[1] == 'base_case_id' for col in cols)
print(f"\n❓ Has 'base_case_id' column: {has_base_case_id}")

# Check what data exists
cursor.execute("SELECT COUNT(*) FROM BaseBusData")
row_count = cursor.fetchone()[0]
print(f"\n📊 BaseBusData rows: {row_count}")

# Show sample column names if base_case_id doesn't exist
if not has_base_case_id:
    print("\n⚠️ 'base_case_id' column NOT FOUND!")
    print("   Available columns:", [col[1] for col in cols])

conn.close()
