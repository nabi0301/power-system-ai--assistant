#!/usr/bin/env python3
"""
Check contingency branch table structure and compare with base branches
"""

import psycopg2

def check_table_structures():
    try:
        conn = psycopg2.connect(
            dbname="118", 
            user="postgres", 
            password="pnnl", 
            host="localhost", 
            port="5432"
        )
        cursor = conn.cursor()
        
        # Check contingency branch table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'contingencybranchdata' 
            ORDER BY ordinal_position
        """)
        contingency_columns = cursor.fetchall()
        
        print("🔍 Contingency Branch Table Columns:")
        for col_name, data_type, nullable in contingency_columns:
            print(f"  {col_name}: {data_type} ({'NULL' if nullable == 'YES' else 'NOT NULL'})")
        
        # Check base branch table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'base_branches' 
            ORDER BY ordinal_position
        """)
        base_columns = cursor.fetchall()
        
        print("\n📋 Base Branch Table Columns:")
        for col_name, data_type, nullable in base_columns:
            print(f"  {col_name}: {data_type} ({'NULL' if nullable == 'YES' else 'NOT NULL'})")
        
        # Find missing columns
        contingency_col_names = [col[0] for col in contingency_columns]
        base_col_names = [col[0] for col in base_columns]
        
        missing_in_contingency = set(base_col_names) - set(contingency_col_names)
        print(f"\n❌ Missing columns in contingency table: {missing_in_contingency}")
        
        # Check sample data to see current state
        cursor.execute("SELECT COUNT(*) FROM contingencybranchdata")
        total_count = cursor.fetchone()[0]
        print(f"\n📊 Current contingency branch records: {total_count:,}")
        
        # Check if PF/QF columns exist and have data
        if 'pf' in contingency_col_names:
            cursor.execute("SELECT COUNT(*) FROM contingencybranchdata WHERE pf != 0")
            pf_count = cursor.fetchone()[0]
            print(f"Records with non-zero PF: {pf_count:,}")
        else:
            print("PF column does not exist")
            
        if 'qf' in contingency_col_names:
            cursor.execute("SELECT COUNT(*) FROM contingencybranchdata WHERE qf != 0")
            qf_count = cursor.fetchone()[0]
            print(f"Records with non-zero QF: {qf_count:,}")
        else:
            print("QF column does not exist")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_table_structures()