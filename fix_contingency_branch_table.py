"""
Fix ContingencyBranchData table to match base_branches format
- Add missing from_bus, to_bus, circuit_id data from base case
- Remove unnecessary columns
- Match the format with base_branches table
"""

import psycopg2
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fix_contingency_branch_table():
    """Fix the contingency branch table structure and data"""
    
    DB_CONFIG = {
        'host': 'localhost',
        'port': '5432',
        'database': '118',
        'user': 'postgres',
        'password': 'pnnl'
    }
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        logging.info("🔧 Starting ContingencyBranchData table fix...")
        
        # Step 1: Create new simplified table structure
        logging.info("Creating new contingency_branches table...")
        cursor.execute("""
            DROP TABLE IF EXISTS contingency_branches CASCADE;
            
            CREATE TABLE contingency_branches (
                branch_data_id SERIAL PRIMARY KEY,
                contingency_case_id INTEGER NOT NULL,
                base_case_id INTEGER NOT NULL,
                from_bus INTEGER NOT NULL,
                to_bus INTEGER NOT NULL,
                circuit_id INTEGER NOT NULL,
                pf DECIMAL(10,4),  -- Real power flow from bus (MW)
                qf DECIMAL(10,4),  -- Reactive power flow from bus (MVAr)
                mva DECIMAL(10,4), -- MVA flow 
                rate DECIMAL(10,4), -- MVA rating
                vio DECIMAL(10,4),  -- Violation amount
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (contingency_case_id) REFERENCES contingencycases(contingency_case_id) ON DELETE CASCADE,
                FOREIGN KEY (base_case_id) REFERENCES base_cases(case_id),
                UNIQUE(contingency_case_id, from_bus, to_bus, circuit_id)
            );
        """)
        
        # Step 2: Populate the new table with corrected data
        logging.info("Populating new table with data from base case inheritance...")
        cursor.execute("""
            INSERT INTO contingency_branches 
            (contingency_case_id, base_case_id, from_bus, to_bus, circuit_id, pf, qf, mva, rate, vio)
            SELECT 
                cbd.contingency_case_id,
                cbd.base_case_id,
                bb.from_bus,
                bb.to_bus, 
                bb.circuit_id,
                cbd.pf,
                cbd.qf,
                CASE 
                    WHEN cbd.pf IS NOT NULL AND cbd.qf IS NOT NULL 
                    THEN SQRT(cbd.pf * cbd.pf + cbd.qf * cbd.qf)
                    ELSE bb.mva 
                END as mva,
                bb.rate,
                CASE 
                    WHEN cbd.pf IS NOT NULL AND cbd.qf IS NOT NULL AND bb.rate IS NOT NULL AND bb.rate > 0
                    THEN GREATEST(0, SQRT(cbd.pf * cbd.pf + cbd.qf * cbd.qf) - bb.rate)
                    ELSE bb.vio
                END as vio
            FROM contingencybranchdata cbd
            JOIN base_branches bb ON (
                cbd.base_case_id = bb.case_id 
                AND cbd.branch_number = (
                    SELECT ROW_NUMBER() OVER (ORDER BY bb2.from_bus, bb2.to_bus, bb2.circuit_id) 
                    FROM base_branches bb2 
                    WHERE bb2.case_id = bb.case_id 
                    AND bb2.from_bus = bb.from_bus 
                    AND bb2.to_bus = bb.to_bus 
                    AND bb2.circuit_id = bb.circuit_id
                )
            )
            ORDER BY cbd.contingency_case_id, bb.from_bus, bb.to_bus, bb.circuit_id;
        """)
        
        affected_rows = cursor.rowcount
        logging.info(f"✅ Inserted {affected_rows} rows into new contingency_branches table")
        
        # Step 3: Create indexes for performance
        logging.info("Creating indexes...")
        cursor.execute("""
            CREATE INDEX idx_contingency_branches_case ON contingency_branches(contingency_case_id);
            CREATE INDEX idx_contingency_branches_base ON contingency_branches(base_case_id);
            CREATE INDEX idx_contingency_branches_line ON contingency_branches(from_bus, to_bus);
            CREATE INDEX idx_contingency_branches_violation ON contingency_branches(vio) WHERE vio > 0;
        """)
        
        # Step 4: Drop the old table and rename the new one
        logging.info("Replacing old table...")
        cursor.execute("""
            DROP TABLE IF EXISTS contingencybranchdata CASCADE;
            ALTER TABLE contingency_branches RENAME TO contingencybranchdata;
        """)
        
        # Step 5: Verify the results
        cursor.execute("SELECT COUNT(*) FROM contingencybranchdata")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM contingencybranchdata WHERE from_bus IS NOT NULL AND to_bus IS NOT NULL")
        valid_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT contingency_case_id) FROM contingencybranchdata")
        case_count = cursor.fetchone()[0]
        
        logging.info(f"✅ Verification Results:")
        logging.info(f"   Total branches: {total_count}")
        logging.info(f"   Valid branches (with from/to bus): {valid_count}")
        logging.info(f"   Contingency cases: {case_count}")
        logging.info(f"   Expected branches per case: {total_count // case_count if case_count > 0 else 0}")
        
        # Step 6: Show sample data
        cursor.execute("""
            SELECT contingency_case_id, from_bus, to_bus, circuit_id, pf, qf, mva, rate, vio
            FROM contingencybranchdata 
            ORDER BY contingency_case_id, from_bus, to_bus 
            LIMIT 5
        """)
        
        sample_data = cursor.fetchall()
        logging.info(f"\n📊 Sample data (first 5 rows):")
        logging.info(f"{'Case':<6} {'From':<5} {'To':<5} {'CKT':<4} {'PF':<8} {'QF':<8} {'MVA':<8} {'Rate':<8} {'Vio':<8}")
        logging.info("-" * 70)
        for row in sample_data:
            logging.info(f"{row[0]:<6} {row[1]:<5} {row[2]:<5} {row[3]:<4} {float(row[4]) if row[4] else 0:<8.2f} {float(row[5]) if row[5] else 0:<8.2f} {float(row[6]) if row[6] else 0:<8.2f} {float(row[7]) if row[7] else 0:<8.2f} {float(row[8]) if row[8] else 0:<8.2f}")
        
        conn.commit()
        logging.info("✅ ContingencyBranchData table fix completed successfully!")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logging.error(f"Error fixing contingency branch table: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False

if __name__ == "__main__":
    print("🔧 Fixing ContingencyBranchData Table")
    print("=" * 50)
    print("Actions:")
    print("1. Create simplified table matching base_branches format")
    print("2. Populate from_bus, to_bus, circuit_id from base case")
    print("3. Remove unnecessary columns")
    print("4. Recalculate MVA and violations")
    
    success = fix_contingency_branch_table()
    
    if success:
        print("\n✅ Table fix completed successfully!")
        print("\nNew table structure matches base_branches:")
        print("- from_bus, to_bus, circuit_id properly populated")
        print("- Only essential columns retained")
        print("- MVA and violations recalculated")
    else:
        print("\n❌ Table fix failed. Check the logs.")