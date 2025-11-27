#!/usr/bin/env python3
"""
Test contingency import with the updated table structure
"""

import psycopg2
import logging
import os
from text_contingency_loader import TextContingencyImporter

def test_import():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Database connection
    try:
        conn = psycopg2.connect(
            dbname="118", 
            user="postgres", 
            password="12345", 
            host="localhost", 
            port="5432"
        )
        logging.info("Connected to database successfully")
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return
    
    # Delete a few test cases to reload them
    cursor = conn.cursor()
    cursor.execute("DELETE FROM contingencycases WHERE contingency_case_id <= 3")
    conn.commit()
    logging.info("Deleted first 3 contingency cases for testing")
    
    # Initialize loader
    loader = TextContingencyImporter(conn)
    
    # Test loading first 3 files
    test_files = [
        r"C:\Projects\contingency files\contingency_case_0.txt",
        r"C:\Projects\contingency files\contingency_case_1.txt", 
        r"C:\Projects\contingency files\contingency_case_2.txt"
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            logging.info(f"Loading {file_path}")
            success = loader.load_contingency_file(file_path)
            logging.info(f"Load result: {success}")
        else:
            logging.warning(f"File not found: {file_path}")
    
    # Check results
    cursor.execute("""
        SELECT COUNT(*) as total, 
               COUNT(CASE WHEN pf != 0 OR qf != 0 THEN 1 END) as with_power 
        FROM contingencybranchdata 
        WHERE contingency_case_id <= 3
    """)
    result = cursor.fetchone()
    logging.info(f"Branch data for first 3 cases: {result[0]} total records, {result[1]} with power flow data")
    
    cursor.execute("SELECT COUNT(*) FROM contingencybusdata WHERE contingency_case_id <= 3")
    bus_count = cursor.fetchone()[0]
    logging.info(f"Bus data for first 3 cases: {bus_count} records")
    
    # Check a sample of actual values
    cursor.execute("""
        SELECT from_bus, to_bus, circuit_id, pf, qf 
        FROM contingencybranchdata 
        WHERE contingency_case_id = 1 AND (pf != 0 OR qf != 0)
        LIMIT 5
    """)
    sample_data = cursor.fetchall()
    logging.info(f"Sample power flow data: {sample_data}")
    
    cursor.close()
    conn.close()
    logging.info("Test completed")

if __name__ == "__main__":
    test_import()