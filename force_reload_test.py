#!/usr/bin/env python3
"""
Force reload contingency data to test the fixes
"""

import psycopg2
import logging
import os
import sys
from pathlib import Path

# Add the current directory to path for imports
sys.path.append(str(Path(__file__).parent))

def get_db_connection():
    """Try different connection methods"""
    connection_configs = [
        {"dbname": "118", "user": "postgres", "password": "admin", "host": "localhost", "port": "5432"},
        {"dbname": "118", "user": "postgres", "password": "postgres", "host": "localhost", "port": "5432"},
        {"dbname": "118", "user": "postgres", "password": "", "host": "localhost", "port": "5432"},
        {"dbname": "118", "user": "postgres", "host": "localhost", "port": "5432"},
    ]
    
    for config in connection_configs:
        try:
            conn = psycopg2.connect(**config)
            print(f"✓ Connected successfully with config: {config}")
            return conn
        except Exception as e:
            print(f"✗ Failed with config {config}: {e}")
    
    return None

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Try to connect to database
    conn = get_db_connection()
    if not conn:
        print("❌ Could not connect to database with any configuration")
        return
    
    cursor = conn.cursor()
    
    # Check current state
    cursor.execute("SELECT COUNT(*) FROM contingencybranchdata WHERE pf != 0 OR qf != 0")
    power_flow_count = cursor.fetchone()[0]
    print(f"Current power flow records: {power_flow_count}")
    
    cursor.execute("SELECT COUNT(*) FROM contingencybranchdata")
    total_branch_count = cursor.fetchone()[0]
    print(f"Total branch records: {total_branch_count}")
    
    cursor.execute("SELECT COUNT(*) FROM contingencybusdata")
    total_bus_count = cursor.fetchone()[0]
    print(f"Total bus records: {total_bus_count}")
    
    if power_flow_count == 0:
        print("🔄 No power flow data found. Need to reload with updated loader.")
        
        # Clear one test case
        cursor.execute("DELETE FROM contingencycases WHERE contingency_case_id = 1")
        conn.commit()
        print("✓ Cleared test case 1 for reload")
        
        # Try to import the updated loader
        try:
            from text_contingency_loader import TextContingencyImporter
            loader = TextContingencyImporter(conn)
            
            test_file = r"C:\Projects\contingency files\contingency_case_0.txt"
            if os.path.exists(test_file):
                print(f"📥 Loading test file: {test_file}")
                success = loader.load_contingency_file(test_file)
                print(f"Load result: {success}")
                
                # Check if power flow data was loaded
                cursor.execute("SELECT COUNT(*) FROM contingencybranchdata WHERE contingency_case_id = 1 AND (pf != 0 OR qf != 0)")
                new_power_flow_count = cursor.fetchone()[0]
                print(f"New power flow records for case 1: {new_power_flow_count}")
                
                if new_power_flow_count > 0:
                    print("✅ Power flow data loading is working!")
                    
                    # Show sample data
                    cursor.execute("""
                        SELECT from_bus, to_bus, circuit_id, pf, qf 
                        FROM contingencybranchdata 
                        WHERE contingency_case_id = 1 AND pf != 0 
                        LIMIT 3
                    """)
                    sample_data = cursor.fetchall()
                    print(f"Sample power flow data: {sample_data}")
                else:
                    print("❌ Power flow data still not loading")
            else:
                print(f"❌ Test file not found: {test_file}")
                
        except ImportError as e:
            print(f"❌ Could not import loader: {e}")
        except Exception as e:
            print(f"❌ Error during test load: {e}")
    else:
        print("✅ Power flow data already exists")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()