#!/usr/bin/env python3
"""
Force reload PF/QF data by clearing completion status and re-running import
"""

import psycopg2
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def force_reload_power_flow_data():
    """Clear completion status and force reload of power flow data"""
    try:
        conn = psycopg2.connect(
            dbname="118", 
            user="postgres", 
            password="pnnl", 
            host="localhost", 
            port="5432"
        )
        cursor = conn.cursor()
        
        logging.info("Connected to database successfully")
        
        # Clear completion status for first 10 cases to force reload
        cursor.execute("""
            UPDATE contingencycases 
            SET processing_status = 'pending' 
            WHERE contingency_case_id <= 10
        """)
        
        affected_rows = cursor.rowcount
        conn.commit()
        
        logging.info(f"Cleared completion status for {affected_rows} contingency cases")
        
        # Check current PF/QF status
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN pf != 0 OR qf != 0 THEN 1 END) as with_power_flow,
                COUNT(CASE WHEN contingency_case_id <= 10 THEN 1 END) as test_records
            FROM contingencybranchdata
        """)
        
        stats = cursor.fetchone()
        logging.info(f"Current state - Total: {stats[0]}, Power Flow: {stats[1]}, Test Records: {stats[2]}")
        
        cursor.close()
        conn.close()
        
        logging.info("✅ Ready for reload. Run text_contingency_loader.py now to populate power flow data.")
        return True
        
    except Exception as e:
        logging.error(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    force_reload_power_flow_data()