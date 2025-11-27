#!/usr/bin/env python3
"""
Test the database structure and generator analysis functionality
"""

import sqlite3
import pandas as pd

def test_database_structure():
    """Check database tables and structure"""
    try:
        conn = sqlite3.connect('data.db')
        
        # Check all tables
        tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
        tables_df = pd.read_sql_query(tables_query, conn)
        print(f"📊 Available tables: {tables_df['name'].tolist()}")
        
        # Check if SLR_Generator exists
        if 'SLR_Generator' in tables_df['name'].values:
            print("\n✅ SLR_Generator table found")
            
            # Get schema
            schema = pd.read_sql_query("PRAGMA table_info(SLR_Generator)", conn)
            print(f"📋 SLR_Generator columns: {schema['name'].tolist()}")
            
            # Get count
            count = pd.read_sql_query("SELECT COUNT(*) as count FROM SLR_Generator", conn)
            print(f"📈 SLR_Generator rows: {count.iloc[0]['count']}")
            
            # Get sample data
            if count.iloc[0]['count'] > 0:
                sample = pd.read_sql_query("SELECT * FROM SLR_Generator LIMIT 3", conn)
                print(f"📋 Sample data:\n{sample.to_string()}")
            
        else:
            print("❌ SLR_Generator table not found")
        
        # Check if DLR_Generator exists
        if 'DLR_Generator' in tables_df['name'].values:
            print("\n✅ DLR_Generator table found")
            
            # Get schema
            schema = pd.read_sql_query("PRAGMA table_info(DLR_Generator)", conn)
            print(f"📋 DLR_Generator columns: {schema['name'].tolist()}")
            
            # Get count
            count = pd.read_sql_query("SELECT COUNT(*) as count FROM DLR_Generator", conn)
            print(f"📈 DLR_Generator rows: {count.iloc[0]['count']}")
            
        else:
            print("❌ DLR_Generator table not found")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_query_with_case_42():
    """Test querying for case 42 specifically"""
    try:
        conn = sqlite3.connect('data.db')
        
        # Test different column names that might be used
        column_names_to_try = ['case_id', 'base_case_id', 'Case_ID', 'Base_Case_ID']
        
        for col_name in column_names_to_try:
            try:
                query = f"SELECT * FROM SLR_Generator WHERE {col_name} = 42 LIMIT 3"
                result = pd.read_sql_query(query, conn)
                print(f"✅ Query with {col_name} worked: {len(result)} rows")
                if not result.empty:
                    print(f"📋 Sample data:\n{result.to_string()}")
                    break
            except Exception as e:
                print(f"❌ Query with {col_name} failed: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Query test error: {e}")

if __name__ == "__main__":
    print("🧪 Testing database structure...")
    test_database_structure()
    
    print("\n🧪 Testing case 42 queries...")
    test_query_with_case_42()