#!/usr/bin/env python3
"""
Quick verification of what you should see in Datasette
"""

import sqlite3
import requests
import json

def test_datasette_connection():
    """Test if Datasette is responding and showing data"""
    
    print("🔍 Testing Datasette Interface at http://127.0.0.1:8001")
    print("=" * 55)
    
    try:
        # Test if Datasette homepage loads
        response = requests.get("http://127.0.0.1:8001", timeout=5)
        if response.status_code == 200:
            print("✅ Datasette homepage loads successfully")
        else:
            print(f"❌ Datasette homepage error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Datasette: {e}")
        return False
    
    try:
        # Test database listing
        db_response = requests.get("http://127.0.0.1:8001/data.json", timeout=5)
        if db_response.status_code == 200:
            db_info = db_response.json()
            print(f"✅ Database accessible with {len(db_info.get('tables', []))} tables")
        else:
            print(f"❌ Database not accessible: {db_response.status_code}")
    except Exception as e:
        print(f"⚠️ Error testing database access: {e}")
    
    # Show what tables should be visible
    print("\n📊 Tables you should see in Datasette:")
    print("-" * 40)
    
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        print(f"• {table_name}: {count:,} records")
    
    print("\n📈 Sample data from key tables:")
    print("-" * 35)
    
    # Show sample from BaseBusData
    cursor.execute("SELECT BUS_NUMBER, VM, PD, BASE_KV FROM BaseBusData LIMIT 5;")
    bus_data = cursor.fetchall()
    print("\n🏠 BaseBusData (first 5 rows):")
    print("Bus | Voltage | Load MW | Base kV")
    for row in bus_data:
        print(f"{row[0]:3d} | {row[1]:7.3f} | {row[2]:7.1f} | {row[3]:7.0f}")
    
    # Show sample from BaseBranchData
    cursor.execute("SELECT From_Bus, To_Bus, MVA, RATE FROM BaseBranchData LIMIT 5;")
    branch_data = cursor.fetchall()
    print("\n🔌 BaseBranchData (first 5 rows):")
    print("From | To | MVA Flow | Rating")
    for row in branch_data:
        print(f"{row[0]:4d} | {row[1]:2d} | {row[2]:8.1f} | {row[3]:6.1f}")
    
    conn.close()
    
    print("\n🌐 WHAT YOU SHOULD SEE IN DATASETTE:")
    print("-" * 40)
    print("1. Homepage with 'data' database link")
    print("2. List of all tables (BaseBusData, BaseBranchData, etc.)")
    print("3. Click any table to browse data")
    print("4. Use 'SQL' tab to run custom queries")
    print("5. Export buttons for JSON/CSV download")
    
    print("\n🚀 Try these direct URLs:")
    print("• Main page: http://127.0.0.1:8001")
    print("• Database: http://127.0.0.1:8001/data")
    print("• Bus data: http://127.0.0.1:8001/data/BaseBusData")
    print("• Branch data: http://127.0.0.1:8001/data/BaseBranchData")
    print("• SQL query: http://127.0.0.1:8001/data?sql=SELECT+*+FROM+BaseBusData+LIMIT+10")
    
    return True

if __name__ == "__main__":
    test_datasette_connection()