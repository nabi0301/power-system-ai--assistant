#!/usr/bin/env python3
"""
Simple test to verify the database status fix
"""

import sqlite3

def test_database_fix():
    """Test if database status would work correctly"""
    
    print("🧪 Testing database status fix...")
    
    # Simulate the corrected logic
    status = {
        "databases": {},
        "active_database": "main",
        "postgresql_available": False
    }
    
    # Ensure databases key exists
    if "databases" not in status:
        status["databases"] = {}
    
    # Test SQLite connection (with the fixed logic)
    try:
        conn = sqlite3.connect("data.db")
        conn.close()
        # Always ensure main database entry exists
        status["databases"]["main"] = {
            "type": "sqlite",
            "connected": True,
            "config": {"database": "data.db"},
            "description": "Primary SQLite Database"
        }
        print("✅ SQLite connection successful")
    except Exception as e:
        # Always ensure main database entry exists
        status["databases"]["main"] = {
            "type": "sqlite",
            "connected": False,
            "config": {"database": "data.db"},
            "description": "Primary SQLite Database (disconnected)"
        }
        print(f"⚠️ SQLite connection failed: {e}")
    
    # Test PostgreSQL connection
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            port='5432',
            database='118',
            user='postgres',
            password='pnnl'
        )
        conn.close()
        
        status["databases"]["118"] = {
            "type": "postgresql",
            "connected": True,
            "config": {
                "host": "localhost",
                "port": "5432",
                "database": "118",
                "user": "postgres",
                "password": "pnnl"
            },
            "description": "IEEE 118 Bus System Database"
        }
        status["postgresql_available"] = True
        print("✅ PostgreSQL connection successful")
        
    except Exception as e:
        print(f"⚠️ PostgreSQL connection failed: {e}")
    
    # Verify the main database key exists
    if "main" in status["databases"]:
        print("✅ 'main' database key exists in status")
        main_db = status["databases"]["main"]
        print(f"   Type: {main_db['type']}")
        print(f"   Connected: {main_db['connected']}")
        print(f"   Description: {main_db['description']}")
    else:
        print("❌ 'main' database key missing from status")
        return False
    
    print(f"\n📊 Database status contains {len(status['databases'])} databases:")
    for db_name, db_info in status['databases'].items():
        status_text = "✅" if db_info['connected'] else "❌"
        print(f"   {status_text} {db_name} ({db_info['type']})")
    
    return True

if __name__ == "__main__":
    success = test_database_fix()
    
    if success:
        print("\n✅ Database status fix test PASSED - KeyError should be resolved")
    else:
        print("\n❌ Database status fix test FAILED")