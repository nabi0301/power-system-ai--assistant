#!/usr/bin/env python3
"""
Populate MVA, RATE from base case and calculate VIO for contingency branch data
"""

import psycopg2
import logging
import math

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def populate_contingency_branch_data():
    """Populate MVA, RATE from base case and calculate VIO"""
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
        
        # First, check current state
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN pf != 0 OR qf != 0 THEN 1 END) as with_power_flow,
                COUNT(CASE WHEN mva != 0 THEN 1 END) as with_mva,
                COUNT(CASE WHEN rate != 0 THEN 1 END) as with_rate,
                COUNT(CASE WHEN vio != 0 THEN 1 END) as with_violations
            FROM contingencybranchdata
        """)
        
        stats = cursor.fetchone()
        logging.info(f"Current state - Total: {stats[0]}, Power Flow: {stats[1]}, MVA: {stats[2]}, Rate: {stats[3]}, Violations: {stats[4]}")
        
        # Update contingency branch data with base case MVA and RATE, calculate new MVA and VIO
        logging.info("Updating contingency branch data with base case inheritance...")
        
        cursor.execute("""
            UPDATE contingencybranchdata AS cbd
            SET 
                mva = SQRT(cbd.pf * cbd.pf + cbd.qf * cbd.qf),
                rate = bb.rate,
                vio = CASE 
                    WHEN bb.rate > 0 THEN 
                        GREATEST(0, SQRT(cbd.pf * cbd.pf + cbd.qf * cbd.qf) - bb.rate)
                    ELSE 0 
                END
            FROM base_branches AS bb
            WHERE bb.case_id = cbd.base_case_id
                AND bb.from_bus = cbd.from_bus 
                AND bb.to_bus = cbd.to_bus 
                AND bb.circuit_id = cbd.circuit_id
        """)
        
        updated_count = cursor.rowcount
        conn.commit()
        
        logging.info(f"Updated {updated_count} contingency branch records with base case data")
        
        # Check results
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN pf != 0 OR qf != 0 THEN 1 END) as with_power_flow,
                COUNT(CASE WHEN mva != 0 THEN 1 END) as with_mva,
                COUNT(CASE WHEN rate != 0 THEN 1 END) as with_rate,
                COUNT(CASE WHEN vio > 0 THEN 1 END) as with_violations,
                MAX(vio) as max_violation,
                AVG(vio) as avg_violation
            FROM contingencybranchdata
        """)
        
        final_stats = cursor.fetchone()
        logging.info(f"Final state - Total: {final_stats[0]}, Power Flow: {final_stats[1]}, MVA: {final_stats[2]}, Rate: {final_stats[3]}")
        logging.info(f"Violations: {final_stats[4]}, Max Violation: {final_stats[5]:.2f} MVA, Avg Violation: {final_stats[6]:.2f} MVA")
        
        # Show sample of populated data
        cursor.execute("""
            SELECT 
                contingency_case_id,
                from_bus, 
                to_bus, 
                circuit_id,
                ROUND(pf::numeric, 2) as pf,
                ROUND(qf::numeric, 2) as qf,
                ROUND(mva::numeric, 2) as mva,
                ROUND(rate::numeric, 2) as rate,
                ROUND(vio::numeric, 2) as vio
            FROM contingencybranchdata 
            WHERE vio > 0 
            ORDER BY vio DESC 
            LIMIT 5
        """)
        
        sample_violations = cursor.fetchall()
        logging.info("Sample violations:")
        for record in sample_violations:
            logging.info(f"  Case {record[0]}: Bus {record[1]}-{record[2]}-{record[3]}, PF={record[4]}, QF={record[5]}, MVA={record[6]}, Rate={record[7]}, Violation={record[8]}")
        
        cursor.close()
        conn.close()
        
        logging.info("✅ Successfully populated contingency branch data!")
        return True
        
    except Exception as e:
        logging.error(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    populate_contingency_branch_data()