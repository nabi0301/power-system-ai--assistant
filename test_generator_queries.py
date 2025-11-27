#!/usr/bin/env python3
"""
Test generator analysis database queries to debug the issue
"""

import sqlite3
import pandas as pd

def test_generator_analysis_queries():
    """Test all possible generator analysis database queries"""
    
    print("🧪 Testing Generator Analysis Database Queries...")
    
    try:
        conn = sqlite3.connect('data.db')
        
        # Check what tables exist
        tables_query = "SELECT name FROM sqlite_master WHERE type='table';"
        tables_df = pd.read_sql_query(tables_query, conn)
        print(f"\n📊 Available tables: {tables_df['name'].tolist()}")
        
        # Check SLR_Generator table
        print(f"\n🔍 Testing SLR_Generator table...")
        try:
            slr_structure = pd.read_sql_query("PRAGMA table_info(SLR_Generator)", conn)
            print(f"   SLR_Generator columns: {slr_structure['name'].tolist()}")
            
            slr_count = pd.read_sql_query("SELECT COUNT(*) as count FROM SLR_Generator", conn)
            print(f"   SLR_Generator total rows: {slr_count.iloc[0]['count']}")
            
            if slr_count.iloc[0]['count'] > 0:
                # Check what case IDs are available
                slr_cases = pd.read_sql_query("SELECT DISTINCT case_id FROM SLR_Generator LIMIT 10", conn)
                print(f"   SLR_Generator case_ids: {slr_cases['case_id'].tolist()}")
                
                # Try base_case_id if case_id doesn't work
                try:
                    slr_base_cases = pd.read_sql_query("SELECT DISTINCT base_case_id FROM SLR_Generator LIMIT 10", conn)
                    print(f"   SLR_Generator base_case_ids: {slr_base_cases['base_case_id'].tolist()}")
                except:
                    print("   No base_case_id column in SLR_Generator")
                
                # Show sample data
                sample_slr = pd.read_sql_query("SELECT * FROM SLR_Generator LIMIT 3", conn)
                print(f"   SLR_Generator sample:\n{sample_slr}")
                
        except Exception as e:
            print(f"   ❌ Error with SLR_Generator: {e}")
        
        # Check DLR_Generator table
        print(f"\n🔍 Testing DLR_Generator table...")
        try:
            dlr_structure = pd.read_sql_query("PRAGMA table_info(DLR_Generator)", conn)
            print(f"   DLR_Generator columns: {dlr_structure['name'].tolist()}")
            
            dlr_count = pd.read_sql_query("SELECT COUNT(*) as count FROM DLR_Generator", conn)
            print(f"   DLR_Generator total rows: {dlr_count.iloc[0]['count']}")
            
            if dlr_count.iloc[0]['count'] > 0:
                # Check what case IDs are available
                dlr_cases = pd.read_sql_query("SELECT DISTINCT case_id FROM DLR_Generator LIMIT 10", conn)
                print(f"   DLR_Generator case_ids: {dlr_cases['case_id'].tolist()}")
                
                # Try base_case_id if case_id doesn't work
                try:
                    dlr_base_cases = pd.read_sql_query("SELECT DISTINCT base_case_id FROM DLR_Generator LIMIT 10", conn)
                    print(f"   DLR_Generator base_case_ids: {dlr_base_cases['base_case_id'].tolist()}")
                except:
                    print("   No base_case_id column in DLR_Generator")
                
                # Show sample data
                sample_dlr = pd.read_sql_query("SELECT * FROM DLR_Generator LIMIT 3", conn)
                print(f"   DLR_Generator sample:\n{sample_dlr}")
                
        except Exception as e:
            print(f"   ❌ Error with DLR_Generator: {e}")
        
        # Test specific queries that the generator analysis uses
        print(f"\n🎯 Testing specific generator analysis queries...")
        
        case_id = 42  # Use case 42 as example
        
        test_queries = [
            f"SELECT COUNT(*) as count FROM SLR_Generator WHERE base_case_id = {case_id}",
            f"SELECT COUNT(*) as count FROM DLR_Generator WHERE base_case_id = {case_id}",
            f"SELECT COUNT(*) as count FROM SLR_Generator WHERE case_id = {case_id}",
            f"SELECT COUNT(*) as count FROM DLR_Generator WHERE case_id = {case_id}",
            "SELECT * FROM SLR_Generator LIMIT 5",
            "SELECT * FROM DLR_Generator LIMIT 5"
        ]
        
        for i, query in enumerate(test_queries):
            try:
                result = pd.read_sql_query(query, conn)
                if 'count' in result.columns:
                    print(f"   Query {i+1}: {result.iloc[0]['count']} rows - {query}")
                else:
                    print(f"   Query {i+1}: {len(result)} rows - {query}")
                    if len(result) > 0:
                        print(f"      Sample: {result.iloc[0].to_dict()}")
            except Exception as e:
                print(f"   Query {i+1} FAILED: {query} - {e}")
        
        conn.close()
        
        print(f"\n✅ Generator analysis database test complete!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

if __name__ == "__main__":
    test_generator_analysis_queries()