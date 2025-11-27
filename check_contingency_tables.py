#!/usr/bin/env python3
"""
Check actual contingency table names and clear status properly
"""

import psycopg2
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_and_fix_contingency_tables():
    """Check actual table names and clear status properly"""
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
        
        # Check actual table names
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%contingency%' 
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        logging.info("Contingency tables found:")
        for table in tables:
            logging.info(f"  {table[0]}")
        
        # Clear completion status from the correct table
        try:
            cursor.execute("UPDATE contingencycases SET processing_status = 'pending' WHERE contingency_case_id <= 10")
            affected_rows = cursor.rowcount
            logging.info(f"Updated contingencycases: {affected_rows} rows")
        except Exception as e:
            logging.info(f"contingencycases table update failed: {e}")
        
        try:
            cursor.execute("UPDATE ContingencyCases SET processing_status = 'pending' WHERE contingency_case_id <= 10")
            affected_rows = cursor.rowcount
            logging.info(f"Updated ContingencyCases: {affected_rows} rows")
        except Exception as e:
            logging.info(f"ContingencyCases table update failed: {e}")
        
        conn.commit()
        
        cursor.close()
        conn.close()
        
        logging.info("✅ Status cleared. Ready for reload.")
        return True
        
    except Exception as e:
        logging.error(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    check_and_fix_contingency_tables()