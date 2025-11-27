import psycopg2
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_contingency_schema():
    """Create the complete contingency analysis schema"""
    
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
        
        # Create ContingencyCases table
        logging.info("Creating ContingencyCases table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ContingencyCases (
                contingency_case_id SERIAL PRIMARY KEY,
                base_case_id INTEGER NOT NULL REFERENCES base_cases(case_id),
                case_number INTEGER NOT NULL,
                filename VARCHAR(255),
                case_name VARCHAR(255),
                contingency_element VARCHAR(500),
                folder_name VARCHAR(255),
                processing_status VARCHAR(50) DEFAULT 'pending',
                buses_count INTEGER DEFAULT 118,
                branches_count INTEGER DEFAULT 186,
                max_voltage_violation DECIMAL(10,6) DEFAULT 0,
                max_thermal_violation DECIMAL(10,2) DEFAULT 0,
                violation_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(base_case_id, case_number)
            );
        """)
        
        # Create ContingencyBusData table
        logging.info("Creating ContingencyBusData table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ContingencyBusData (
                bus_data_id SERIAL PRIMARY KEY,
                contingency_case_id INTEGER NOT NULL REFERENCES ContingencyCases(contingency_case_id) ON DELETE CASCADE,
                base_case_id INTEGER NOT NULL REFERENCES base_cases(case_id),
                bus_number INTEGER NOT NULL,
                bus_type INTEGER,
                vm DECIMAL(10,6),  -- Voltage magnitude (pu)
                va DECIMAL(10,4),  -- Voltage angle (degrees)
                pg DECIMAL(10,4),  -- Generator real power (MW)
                qg DECIMAL(10,4),  -- Generator reactive power (MVAr)
                pd DECIMAL(10,4),  -- Load real power (MW)
                qd DECIMAL(10,4),  -- Load reactive power (MVAr)
                gs DECIMAL(10,6),  -- Shunt conductance (MW at 1.0 pu voltage)
                bs DECIMAL(10,6),  -- Shunt susceptance (MVAr at 1.0 pu voltage)
                area INTEGER,
                vm_max DECIMAL(10,6),
                vm_min DECIMAL(10,6),
                base_kv DECIMAL(10,3),
                zone INTEGER,
                vmax DECIMAL(10,6),
                vmin DECIMAL(10,6),
                -- Violation tracking
                voltage_violation DECIMAL(10,6) DEFAULT 0,  -- Violation amount (pu)
                violation_type VARCHAR(20),  -- 'high', 'low', 'none'
                inherited_from_base BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(contingency_case_id, bus_number)
            );
        """)
        
        # Create ContingencyBranchData table
        logging.info("Creating ContingencyBranchData table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ContingencyBranchData (
                branch_data_id SERIAL PRIMARY KEY,
                contingency_case_id INTEGER NOT NULL REFERENCES ContingencyCases(contingency_case_id) ON DELETE CASCADE,
                base_case_id INTEGER NOT NULL REFERENCES base_cases(case_id),
                branch_number INTEGER NOT NULL,
                from_bus INTEGER,
                to_bus INTEGER,
                pf DECIMAL(10,4),  -- Real power flow from bus (MW)
                qf DECIMAL(10,4),  -- Reactive power flow from bus (MVAr)
                pt DECIMAL(10,4),  -- Real power flow to bus (MW)
                qt DECIMAL(10,4),  -- Reactive power flow to bus (MVAr)
                -- Inherited from base case
                r DECIMAL(10,8),   -- Resistance (pu)
                x DECIMAL(10,8),   -- Reactance (pu)
                b DECIMAL(10,8),   -- Susceptance (pu)
                rate_a DECIMAL(10,2), -- MVA rating A (normal)
                rate_b DECIMAL(10,2), -- MVA rating B (short term)
                rate_c DECIMAL(10,2), -- MVA rating C (emergency)
                ratio DECIMAL(10,6), -- Transformer ratio
                angle DECIMAL(10,4), -- Transformer phase angle
                status INTEGER,    -- Branch status (1=in-service, 0=out-of-service)
                angmin DECIMAL(10,4),
                angmax DECIMAL(10,4),
                -- Calculated values
                mva_from DECIMAL(10,4), -- MVA flow from bus
                mva_to DECIMAL(10,4),   -- MVA flow to bus
                thermal_violation DECIMAL(10,4) DEFAULT 0, -- Violation amount (MVA)
                violation_percentage DECIMAL(10,2) DEFAULT 0, -- Percentage of rating
                is_contingency_element BOOLEAN DEFAULT FALSE, -- True if this branch was removed in contingency
                inherited_from_base BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(contingency_case_id, branch_number)
            );
        """)
        
        # Create indexes for performance
        logging.info("Creating indexes...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_contingency_cases_base_case 
            ON ContingencyCases(base_case_id);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_contingency_bus_case_bus 
            ON ContingencyBusData(contingency_case_id, bus_number);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_contingency_branch_case_branch 
            ON ContingencyBranchData(contingency_case_id, branch_number);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_contingency_branch_violation 
            ON ContingencyBranchData(thermal_violation) WHERE thermal_violation > 0;
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_contingency_bus_violation 
            ON ContingencyBusData(voltage_violation) WHERE voltage_violation > 0;
        """)
        
        # Create update trigger for ContingencyCases
        logging.info("Creating update triggers...")
        cursor.execute("""
            CREATE OR REPLACE FUNCTION update_contingency_case_timestamp()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        cursor.execute("""
            DROP TRIGGER IF EXISTS trigger_update_contingency_case_timestamp ON ContingencyCases;
            CREATE TRIGGER trigger_update_contingency_case_timestamp
                BEFORE UPDATE ON ContingencyCases
                FOR EACH ROW
                EXECUTE FUNCTION update_contingency_case_timestamp();
        """)
        
        conn.commit()
        logging.info("✅ Contingency schema created successfully!")
        
        # Check what we created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%contingency%'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        logging.info(f"Created {len(tables)} contingency tables:")
        for table in tables:
            logging.info(f"  - {table[0]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logging.error(f"Error creating contingency schema: {e}")
        return False

if __name__ == "__main__":
    print("🏗️  Creating IEEE 118 Contingency Analysis Schema")
    print("=" * 50)
    
    success = create_contingency_schema()
    
    if success:
        print("\n✅ Schema creation completed successfully!")
        print("\nNext steps:")
        print("1. Create the populate_complete_contingency_data() function")
        print("2. Run the contingency data loader")
    else:
        print("\n❌ Schema creation failed. Check the logs.")