#!/usr/bin/env python3
"""
Quick verification script to check the power flow data loading results.
"""

import sqlite3

DATABASE_PATH = "data.db"

def main():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Check sample data for Case 1
    print("Sample power flow data for Case ID 1:")
    cursor.execute("""
        SELECT contingency_case_id, branch_number, PF, QF, MVA, RATE, VIO 
        FROM contingencybranchdata 
        WHERE contingency_case_id = 1 AND PF != 0 
        LIMIT 10
    """)
    
    for row in cursor.fetchall():
        case_id, branch_num, pf, qf, mva, rate, vio = row
        print(f"  Case {case_id}, Branch {branch_num}: PF={pf:.2f}, QF={qf:.2f}, MVA={mva:.2f}, RATE={rate:.2f}, VIO={vio:.2f}")
    
    # Check summary statistics
    print("\nSummary Statistics:")
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT contingency_case_id) as case_count,
            COUNT(*) as total_records,
            SUM(CASE WHEN PF != 0 OR QF != 0 THEN 1 ELSE 0 END) as with_power_flow,
            SUM(CASE WHEN VIO > 0 THEN 1 ELSE 0 END) as with_violations,
            MAX(VIO) as max_violation
        FROM contingencybranchdata
    """)
    
    result = cursor.fetchone()
    case_count, total_records, with_power_flow, with_violations, max_violation = result
    
    print(f"  Cases with data: {case_count}")
    print(f"  Total branch records: {total_records}")
    print(f"  Records with power flow: {with_power_flow}")
    print(f"  Records with violations: {with_violations}")
    print(f"  Maximum violation: {max_violation:.2f} MVA")
    
    # Check a few more cases
    print("\nPower flow data status by case:")
    cursor.execute("""
        SELECT 
            contingency_case_id,
            COUNT(*) as total_branches,
            SUM(CASE WHEN PF != 0 OR QF != 0 THEN 1 ELSE 0 END) as with_power_flow
        FROM contingencybranchdata 
        WHERE contingency_case_id IN (1, 2, 3, 10, 100, 186)
        GROUP BY contingency_case_id
        ORDER BY contingency_case_id
    """)
    
    for row in cursor.fetchall():
        case_id, total, with_pf = row
        print(f"  Case {case_id}: {with_pf}/{total} branches have power flow data")
    
    conn.close()
    print("\n✅ Verification complete!")

if __name__ == "__main__":
    main()