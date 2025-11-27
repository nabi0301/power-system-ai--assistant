#!/usr/bin/env python3
"""
Check the current status of power flow data in contingency tables
"""

import psycopg2
import pandas as pd

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': '118',
    'user': 'postgres',
    'password': 'pnnl'
}

def check_power_flow_status():
    """Check current power flow data status"""
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("📊 Contingency Power Flow Data Status")
        print("=" * 50)
        
        # Check total records and those with power flow data
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN pf IS NOT NULL AND pf != 0 THEN 1 END) as records_with_pf,
                COUNT(CASE WHEN qf IS NOT NULL AND qf != 0 THEN 1 END) as records_with_qf,
                COUNT(CASE WHEN mva IS NOT NULL AND mva > 0 THEN 1 END) as records_with_mva,
                COUNT(CASE WHEN vio IS NOT NULL AND vio > 0 THEN 1 END) as records_with_violations
            FROM contingencybranchdata
        """)
        
        result = cursor.fetchone()
        total, pf_count, qf_count, mva_count, vio_count = result
        
        print(f"Total branch records: {total:,}")
        print(f"Records with PF data: {pf_count:,} ({pf_count/total*100:.1f}%)")
        print(f"Records with QF data: {qf_count:,} ({qf_count/total*100:.1f}%)")
        print(f"Records with MVA data: {mva_count:,} ({mva_count/total*100:.1f}%)")
        print(f"Records with violations: {vio_count:,} ({vio_count/total*100:.1f}%)")
        
        # Check sample data
        cursor.execute("""
            SELECT 
                contingency_case_id,
                from_bus,
                to_bus,
                pf,
                qf,
                mva,
                rate,
                vio
            FROM contingencybranchdata 
            WHERE contingency_case_id <= 5
            ORDER BY contingency_case_id, from_bus, to_bus
            LIMIT 10
        """)
        
        print(f"\nSample Data (first 10 records):")
        print(f"{'Case':<6} {'From':<4} {'To':<4} {'PF':<8} {'QF':<8} {'MVA':<8} {'Rate':<8} {'VIO':<8}")
        print("-" * 60)
        
        for row in cursor.fetchall():
            case_id, from_bus, to_bus, pf, qf, mva, rate, vio = row
            pf = pf if pf is not None else 0
            qf = qf if qf is not None else 0
            mva = mva if mva is not None else 0
            rate = rate if rate is not None else 0
            vio = vio if vio is not None else 0
            print(f"{case_id:<6} {from_bus:<4} {to_bus:<4} {pf:<8.2f} {qf:<8.2f} {mva:<8.2f} {rate:<8.2f} {vio:<8.2f}")
        
        # Check cases processed
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT contingency_case_id) as total_cases,
                MIN(contingency_case_id) as min_case,
                MAX(contingency_case_id) as max_case
            FROM contingencybranchdata
        """)
        
        result = cursor.fetchone()
        total_cases, min_case, max_case = result
        print(f"\nCase Range: {total_cases} cases (ID {min_case} to {max_case})")
        
        # Check if power flow data is missing
        if pf_count == 0 or qf_count == 0:
            print(f"\n⚠️  ISSUE DETECTED: Power flow data (PF/QF) is missing!")
            print(f"   This explains why the import shows 'errors'")
            print(f"   Need to run the power flow data loader to populate PF/QF from text files")
        elif pf_count < total * 0.5:
            print(f"\n⚠️  ISSUE DETECTED: Power flow data is incomplete!")
            print(f"   Only {pf_count/total*100:.1f}% of records have PF data")
        else:
            print(f"\n✅ Power flow data looks good!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking status: {e}")

if __name__ == "__main__":
    check_power_flow_status()