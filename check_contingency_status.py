#!/usr/bin/env python3
"""
Check the current status of contingency data and identify any issues
"""

import psycopg2
import os
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': '118',
    'user': 'postgres',
    'password': 'pnnl'
}

def check_contingency_status():
    """Check current contingency data status and identify issues"""
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("📊 Contingency Data Status Check - " + str(datetime.now()))
        print("=" * 60)
        
        # Check basic counts
        cursor.execute("""
            SELECT 
                COUNT(*) as total_cases,
                COUNT(CASE WHEN processing_status = 'completed' THEN 1 END) as completed_cases,
                COUNT(CASE WHEN processing_status = 'processing' THEN 1 END) as processing_cases,
                COUNT(CASE WHEN processing_status = 'failed' THEN 1 END) as failed_cases
            FROM ContingencyCases
        """)
        
        result = cursor.fetchone()
        if result:
            total, completed, processing, failed = result
            print(f"Contingency Cases:")
            print(f"  Total: {total}")
            print(f"  Completed: {completed}")
            print(f"  Processing: {processing}")
            print(f"  Failed: {failed}")
        
        # Check branch data status
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
        if result:
            total, pf_count, qf_count, mva_count, vio_count = result
            print(f"\nBranch Data:")
            print(f"  Total records: {total:,}")
            print(f"  Records with PF data: {pf_count:,} ({pf_count/total*100:.1f}%)")
            print(f"  Records with QF data: {qf_count:,} ({qf_count/total*100:.1f}%)")
            print(f"  Records with MVA data: {mva_count:,} ({mva_count/total*100:.1f}%)")
            print(f"  Records with violations: {vio_count:,} ({vio_count/total*100:.1f}%)")
        
        # Check case range
        cursor.execute("""
            SELECT 
                MIN(contingency_case_id) as min_case,
                MAX(contingency_case_id) as max_case,
                COUNT(DISTINCT contingency_case_id) as unique_cases
            FROM contingencybranchdata
        """)
        
        result = cursor.fetchone()
        if result:
            min_case, max_case, unique_cases = result
            print(f"\nCase Range: {unique_cases} unique cases (ID {min_case} to {max_case})")
        
        # Check for recent errors or issues
        cursor.execute("""
            SELECT 
                case_number,
                filename,
                processing_status,
                folder_name
            FROM ContingencyCases 
            WHERE processing_status != 'completed'
            ORDER BY case_number
            LIMIT 10
        """)
        
        incomplete_cases = cursor.fetchall()
        if incomplete_cases:
            print(f"\nIncomplete Cases (first 10):")
            for case_num, filename, status, folder in incomplete_cases:
                print(f"  Case {case_num}: {filename} - {status} ({folder})")
        else:
            print(f"\n✅ All cases are marked as completed")
        
        # Check if power flow data is missing
        if result and pf_count == 0:
            print(f"\n⚠️  POWER FLOW DATA MISSING!")
            print(f"   The contingency cases exist but power flow data (PF/QF) is not populated")
            print(f"   This is likely the source of the 'errors' message")
            print(f"   Solution: Run the power flow data loader to populate PF/QF from text files")
        elif result and pf_count < total * 0.8:
            print(f"\n⚠️  POWER FLOW DATA INCOMPLETE!")
            print(f"   Only {pf_count/total*100:.1f}% of records have power flow data")
        elif result and pf_count > 0:
            print(f"\n✅ Power flow data looks good! ({pf_count/total*100:.1f}% populated)")
        
        # Sample data
        cursor.execute("""
            SELECT 
                contingency_case_id,
                from_bus,
                to_bus,
                ROUND(COALESCE(pf, 0)::numeric, 2) as pf,
                ROUND(COALESCE(qf, 0)::numeric, 2) as qf,
                ROUND(COALESCE(mva, 0)::numeric, 2) as mva,
                ROUND(COALESCE(rate, 0)::numeric, 2) as rate,
                ROUND(COALESCE(vio, 0)::numeric, 2) as vio
            FROM contingencybranchdata 
            ORDER BY contingency_case_id, from_bus, to_bus
            LIMIT 5
        """)
        
        print(f"\nSample Data (first 5 records):")
        print(f"{'Case':<6} {'From':<4} {'To':<4} {'PF':<8} {'QF':<8} {'MVA':<8} {'Rate':<8} {'VIO':<8}")
        print("-" * 60)
        
        for row in cursor.fetchall():
            case_id, from_bus, to_bus, pf, qf, mva, rate, vio = row
            print(f"{case_id:<6} {from_bus:<4} {to_bus:<4} {pf:<8} {qf:<8} {mva:<8} {rate:<8} {vio:<8}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return False

def check_file_structure():
    """Check if contingency text files exist"""
    print(f"\n📁 File Structure Check:")
    print("=" * 30)
    
    contingency_folder = r"C:\Users\nira771\Data\misc\contingency_118"
    
    if os.path.exists(contingency_folder):
        txt_files = [f for f in os.listdir(contingency_folder) if f.endswith('.txt')]
        print(f"Contingency folder: {contingency_folder}")
        print(f"Text files found: {len(txt_files)}")
        
        if len(txt_files) > 0:
            print(f"✅ Contingency text files are available for power flow loading")
        else:
            print(f"❌ No text files found in contingency folder")
    else:
        print(f"❌ Contingency folder not found: {contingency_folder}")

if __name__ == "__main__":
    success = check_contingency_status()
    if success:
        check_file_structure()
        
        print(f"\n🔧 Next Steps:")
        print(f"  1. If power flow data is missing, run: python load_contingency_power_flow_v2.py")
        print(f"  2. If cases are incomplete, check folder paths and file permissions")
        print(f"  3. Review the contingency_case_loader.py configuration")