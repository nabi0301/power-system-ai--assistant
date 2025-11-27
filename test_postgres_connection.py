#!/usr/bin/env python3
"""
Test PostgreSQL connection with provided credentials
"""

try:
    import psycopg2
    
    # Your connection details
    conn_params = {
        "host": "localhost",
        "port": "5432",
        "database": "118",
        "user": "postgres",
        "password": "pnnl"
    }
    
    print("🔗 Testing PostgreSQL connection...")
    print(f"   Host: {conn_params['host']}")
    print(f"   Port: {conn_params['port']}")
    print(f"   Database: {conn_params['database']}")
    print(f"   User: {conn_params['user']}")
    
    # Test connection
    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Connection successful!")
        print(f"   PostgreSQL version: {version[0]}")
        
        # Check available tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"📊 Found {len(tables)} tables:")
            for table in tables[:10]:  # Show first 10 tables
                print(f"   • {table[0]}")
            if len(tables) > 10:
                print(f"   ... and {len(tables) - 10} more tables")
        else:
            print("⚠️ No tables found in public schema")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Connection failed: {e}")
        print(f"   Error code: {e.pgcode}")
        
        # Try connecting to default postgres database
        print("\n🔄 Trying default 'postgres' database...")
        try:
            default_params = conn_params.copy()
            default_params["database"] = "postgres"
            
            conn = psycopg2.connect(**default_params)
            cursor = conn.cursor()
            
            print("✅ Connected to default postgres database")
            
            # List all databases
            cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
            databases = cursor.fetchall()
            
            print(f"📋 Available databases:")
            for db in databases:
                print(f"   • {db[0]}")
            
            cursor.close()
            conn.close()
            
        except psycopg2.Error as e2:
            print(f"❌ Default database connection also failed: {e2}")
            
except ImportError:
    print("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
except Exception as e:
    print(f"❌ Unexpected error: {e}")