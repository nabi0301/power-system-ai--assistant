import psycopg2

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': '118',
    'user': 'postgres',
    'password': 'pnnl'
}

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Check existing tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    
    tables = cursor.fetchall()
    print("📊 Existing tables in 118 database:")
    for table in tables:
        print(f"   - {table[0]}")
    
    # Check for base case related tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name ILIKE '%base%'
        ORDER BY table_name
    """)
    
    base_tables = cursor.fetchall()
    print("\n🏗️ Base case related tables:")
    for table in base_tables:
        print(f"   - {table[0]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")