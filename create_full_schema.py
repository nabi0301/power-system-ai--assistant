import psycopg2

def create_full_schema():
    """Create complete database schema including branch data tables"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='118', 
            user='postgres',
            password='pnnl'
        )
        cursor = conn.cursor()
        
        print("🏗️  Creating complete database schema...")
        
        # Create BaseCases table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS BaseCases (
                base_case_id SERIAL PRIMARY KEY,
                case_number INTEGER UNIQUE NOT NULL,
                filename VARCHAR(255),
                case_name VARCHAR(255),
                folder_name VARCHAR(255),
                buses_count INTEGER DEFAULT 0,
                branches_count INTEGER DEFAULT 0,
                processing_status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create BaseBusData table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS BaseBusData (
                bus_data_id SERIAL PRIMARY KEY,
                base_case_id INTEGER REFERENCES BaseCases(base_case_id) ON DELETE CASCADE,
                bus_number INTEGER NOT NULL,
                vm FLOAT,
                va FLOAT,
                base_kv FLOAT,
                pg FLOAT,
                qg FLOAT,
                pd FLOAT,
                qd FLOAT,
                UNIQUE(base_case_id, bus_number)
            )
        """)
        
        # Create BaseBranchData table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS BaseBranchData (
                branch_data_id SERIAL PRIMARY KEY,
                base_case_id INTEGER REFERENCES BaseCases(base_case_id) ON DELETE CASCADE,
                branch_number INTEGER NOT NULL,
                from_bus INTEGER NOT NULL,
                to_bus INTEGER NOT NULL,
                line_id INTEGER NOT NULL,
                pf FLOAT,
                qf FLOAT,
                mva FLOAT,
                rate FLOAT,
                vio FLOAT,
                UNIQUE(base_case_id, branch_number)
            )
        """)
        
        # Create ContingencyCases table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ContingencyCases (
                contingency_case_id SERIAL PRIMARY KEY,
                base_case_id INTEGER REFERENCES BaseCases(base_case_id),
                case_number INTEGER NOT NULL,
                filename VARCHAR(255),
                case_name VARCHAR(255),
                contingency_element VARCHAR(255),
                folder_name VARCHAR(255),
                buses_count INTEGER DEFAULT 0,
                branches_count INTEGER DEFAULT 0,
                processing_status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(base_case_id, case_number)
            )
        """)
        
        # Create ContingencyBusData table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ContingencyBusData (
                bus_data_id SERIAL PRIMARY KEY,
                contingency_case_id INTEGER REFERENCES ContingencyCases(contingency_case_id) ON DELETE CASCADE,
                bus_number INTEGER NOT NULL,
                vm FLOAT,
                va FLOAT,
                base_kv FLOAT,
                pg FLOAT,
                qg FLOAT,
                pd FLOAT,
                qd FLOAT,
                UNIQUE(contingency_case_id, bus_number)
            )
        """)
        
        # Create ContingencyBranchData table with the exact columns you specified
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ContingencyBranchData (
                branch_data_id SERIAL PRIMARY KEY,
                base_case_id INTEGER REFERENCES BaseCases(base_case_id),
                contingency_case_id INTEGER REFERENCES ContingencyCases(contingency_case_id) ON DELETE CASCADE,
                branch_number INTEGER NOT NULL,
                from_bus INTEGER NOT NULL,
                to_bus INTEGER NOT NULL,
                line_id INTEGER NOT NULL,
                pf FLOAT,
                qf FLOAT,
                mva FLOAT,
                rate FLOAT,
                vio FLOAT,
                UNIQUE(contingency_case_id, branch_number)
            )
        """)
        
        conn.commit()
        print("✅ Complete database schema created successfully")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating schema: {e}")
        return False

if __name__ == "__main__":
    create_full_schema()