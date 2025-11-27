"""
Fix ContingencyBusData table to match base_buses format
- Remove unnecessary columns (bus_data_id and all extra columns)
- Match the exact format of base_buses table
- Fix the base_case_id issue if needed
"""

import psycopg2
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fix_contingency_bus_table():
    """Fix the contingency bus table structure and data"""
    
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
        
        logging.info("🔧 Starting ContingencyBusData table fix...")
        
        # Step 1: Create new simplified table structure matching base_buses exactly
        logging.info("Creating new contingency_buses table with base_buses format...")
        cursor.execute("""
            DROP TABLE IF EXISTS contingency_buses CASCADE;
            
            CREATE TABLE contingency_buses (
                contingency_case_id INTEGER NOT NULL,
                base_case_id INTEGER NOT NULL,
                bus_number INTEGER NOT NULL,
                vm DECIMAL(10,6),          -- Voltage magnitude (pu) 
                va DECIMAL(10,4),          -- Voltage angle (degrees)
                base_kv DECIMAL(10,3),     -- Base voltage (kV)
                pg DECIMAL(10,4),          -- Generator real power (MW)
                qg DECIMAL(10,4),          -- Generator reactive power (MVAr)
                pd DECIMAL(10,4),          -- Load real power (MW)
                qd DECIMAL(10,4),          -- Load reactive power (MVAr)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (contingency_case_id) REFERENCES contingencycases(contingency_case_id) ON DELETE CASCADE,
                FOREIGN KEY (base_case_id) REFERENCES base_cases(case_id),
                UNIQUE(contingency_case_id, bus_number)
            );
        """)
        
        # Step 2: Populate the new table with simplified data
        logging.info("Populating new table with essential bus data...")
        cursor.execute("""
            INSERT INTO contingency_buses 
            (contingency_case_id, base_case_id, bus_number, vm, va, base_kv, pg, qg, pd, qd)
            SELECT 
                contingency_case_id,
                base_case_id,
                bus_number,
                vm,
                va,
                base_kv,
                pg,
                qg,
                pd,
                qd
            FROM contingencybusdata
            ORDER BY contingency_case_id, bus_number;
        """)
        
        affected_rows = cursor.rowcount
        logging.info(f"✅ Inserted {affected_rows} rows into new contingency_buses table")
        
        # Step 3: Create indexes for performance
        logging.info("Creating indexes...")
        cursor.execute("""
            CREATE INDEX idx_contingency_buses_case ON contingency_buses(contingency_case_id);
            CREATE INDEX idx_contingency_buses_base ON contingency_buses(base_case_id);
            CREATE INDEX idx_contingency_buses_number ON contingency_buses(bus_number);
            CREATE INDEX idx_contingency_buses_case_bus ON contingency_buses(contingency_case_id, bus_number);
        """)
        
        # Step 4: Drop the old table and rename the new one
        logging.info("Replacing old table...")
        cursor.execute("""
            DROP TABLE IF EXISTS contingencybusdata CASCADE;
            ALTER TABLE contingency_buses RENAME TO contingencybusdata;
        """)
        
        # Step 5: Verify the results
        cursor.execute("SELECT COUNT(*) FROM contingencybusdata")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT contingency_case_id) FROM contingencybusdata")
        case_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT bus_number) FROM contingencybusdata")
        bus_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT base_case_id, COUNT(*) as count
            FROM contingencybusdata 
            GROUP BY base_case_id 
            ORDER BY base_case_id
        """)
        base_case_counts = cursor.fetchall()
        
        logging.info(f"✅ Verification Results:")
        logging.info(f"   Total bus records: {total_count}")
        logging.info(f"   Contingency cases: {case_count}")
        logging.info(f"   Unique buses: {bus_count}")
        logging.info(f"   Expected records per case: {total_count // case_count if case_count > 0 else 0}")
        
        logging.info(f"   Base case distribution:")
        for case_id, count in base_case_counts:
            logging.info(f"     Base case {case_id}: {count} records")
        
        # Step 6: Show sample data
        cursor.execute("""
            SELECT contingency_case_id, base_case_id, bus_number, vm, va, base_kv, pg, qg, pd, qd
            FROM contingencybusdata 
            ORDER BY contingency_case_id, bus_number 
            LIMIT 5
        """)
        
        sample_data = cursor.fetchall()
        logging.info(f"\nSample data (first 5 rows):")
        logging.info(f"{'Case':<6} {'Base':<5} {'Bus':<4} {'VM':<8} {'VA':<8} {'BaseKV':<8} {'PG':<8} {'QG':<8} {'PD':<8} {'QD':<8}")
        logging.info("-" * 80)
        for row in sample_data:
            logging.info(f"{row[0]:<6} {row[1]:<5} {row[2]:<4} {float(row[3]) if row[3] else 0:<8.3f} {float(row[4]) if row[4] else 0:<8.2f} {float(row[5]) if row[5] else 0:<8.1f} {float(row[6]) if row[6] else 0:<8.2f} {float(row[7]) if row[7] else 0:<8.2f} {float(row[8]) if row[8] else 0:<8.2f} {float(row[9]) if row[9] else 0:<8.2f}")
        
        # Step 7: Check table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'contingencybusdata' 
            ORDER BY ordinal_position
        """)
        
        new_columns = cursor.fetchall()
        logging.info(f"\nNew table structure:")
        for col in new_columns:
            logging.info(f"   {col[0]:<25} {col[1]:<15} {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
        
        conn.commit()
        logging.info("✅ ContingencyBusData table fix completed successfully!")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logging.error(f"Error fixing contingency bus table: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False

if __name__ == "__main__":
    print("🔧 Fixing ContingencyBusData Table")
    print("=" * 50)
    print("Actions:")
    print("1. Remove bus_data_id and all unnecessary columns")
    print("2. Match base_buses table format exactly")
    print("3. Keep only essential bus data columns")
    print("4. Maintain contingency_case_id and base_case_id relationships")
    
    success = fix_contingency_bus_table()
    
    if success:
        print("\n✅ Table fix completed successfully!")
        print("\nNew table structure matches base_buses:")
        print("- Removed bus_data_id and all extra columns")
        print("- Only essential bus data columns retained")
        print("- Same format as base_buses table")
    else:
        print("\n❌ Table fix failed. Check the logs.")