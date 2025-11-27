import pandas as pdimport pandas as pdimport pandas as pdimport pandas as pd

import psycopg2

from pathlib import Pathimport psycopg2

import logging

from pathlib import Pathimport psycopg2import psycopg2

# Database configuration

DB_CONFIG = {import logging

    'host': 'localhost',

    'database': '118',from datetime import datetimefrom pathlib import Pathimport os

    'user': 'postgres',

    'password': 'postgres'import re

}

import loggingimport time

def create_schema():

    """Create database schema"""# Set up logging

    try:

        conn = psycopg2.connect(**DB_CONFIG)logging.basicConfig(from datetime import datetimefrom pathlib import Path

        cursor = conn.cursor()

            level=logging.INFO,

        print("Creating database schema...")

            format='%(asctime)s - %(levelname)s - %(message)s',import reimport logging

        # Create BaseCases table

        cursor.execute("""    handlers=[

            CREATE TABLE IF NOT EXISTS BaseCases (

                base_case_id SERIAL PRIMARY KEY,        logging.FileHandler('contingency_case_loader.log', encoding='utf-8'),from datetime import datetime

                case_number INTEGER UNIQUE NOT NULL,

                filename VARCHAR(255),        logging.StreamHandler()

                case_name VARCHAR(255),

                folder_name VARCHAR(255),    ]# Set up logging

                buses_count INTEGER DEFAULT 0,

                processing_status VARCHAR(50) DEFAULT 'pending',)

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

            )logging.basicConfig(# Set up logging

        """)

        class ContingencyCaseLoader:

        # Create BaseBusData table

        cursor.execute("""    def __init__(self, base_folder_path, db_config):    level=logging.INFO,logging.basicConfig(

            CREATE TABLE IF NOT EXISTS BaseBusData (

                bus_data_id SERIAL PRIMARY KEY,        """

                base_case_id INTEGER REFERENCES BaseCases(base_case_id) ON DELETE CASCADE,

                bus_number INTEGER NOT NULL,        Initialize the ContingencyCaseLoader    format='%(asctime)s - %(levelname)s - %(message)s',    level=logging.INFO,

                vm FLOAT,

                va FLOAT,        

                base_kv FLOAT,

                pg FLOAT,        Args:    handlers=[    format='%(asctime)s - %(levelname)s - %(message)s',

                qg FLOAT,

                pd FLOAT,            base_folder_path: Path to the folder containing Base_118 and contingency_118 subfolders

                qd FLOAT,

                UNIQUE(base_case_id, bus_number)            db_config: Database configuration dictionary        logging.FileHandler('contingency_case_loader.log', encoding='utf-8'),    handlers=[

            )

        """)        """

        

        # Create ContingencyCases table        self.base_folder_path = Path(base_folder_path)        logging.StreamHandler()        logging.FileHandler('contingency_import_optimized.log', encoding='utf-8'),

        cursor.execute("""

            CREATE TABLE IF NOT EXISTS ContingencyCases (        self.db_config = db_config

                contingency_case_id SERIAL PRIMARY KEY,

                base_case_id INTEGER REFERENCES BaseCases(base_case_id),        self.conn = None    ]        logging.StreamHandler()

                case_number INTEGER NOT NULL,

                filename VARCHAR(255),        self.cursor = None

                case_name VARCHAR(255),

                contingency_element VARCHAR(255),        )    ]

                folder_name VARCHAR(255),

                buses_count INTEGER DEFAULT 0,    def connect_database(self):

                processing_status VARCHAR(50) DEFAULT 'pending',

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,        """Connect to PostgreSQL database""")

                UNIQUE(base_case_id, case_number)

            )        try:

        """)

                    self.conn = psycopg2.connect(**self.db_config)class ContingencyCaseLoader:

        # Create ContingencyBusData table

        cursor.execute("""            self.cursor = self.conn.cursor()

            CREATE TABLE IF NOT EXISTS ContingencyBusData (

                bus_data_id SERIAL PRIMARY KEY,            logging.info("Database connection established")    def __init__(self, base_folder_path, db_config):class OptimizedContingencyImporter:

                contingency_case_id INTEGER REFERENCES ContingencyCases(contingency_case_id) ON DELETE CASCADE,

                bus_number INTEGER NOT NULL,            return True

                vm FLOAT,

                va FLOAT,        except Exception as e:        """    def __init__(self, db_config):

                base_kv FLOAT,

                pg FLOAT,            logging.error(f"Database connection failed: {e}")

                qg FLOAT,

                pd FLOAT,            return False        Initialize the ContingencyCaseLoader        self.db_config = db_config

                qd FLOAT,

                UNIQUE(contingency_case_id, bus_number)    

            )

        """)    def create_database_schema(self):                self.conn = None

        

        conn.commit()        """Create the required database schema"""

        print("Database schema created successfully!")

        cursor.close()        try:        Args:        self.cursor = None

        conn.close()

        return True            logging.info("Creating database schema...")

        

    except Exception as e:                        base_folder_path: Path to the folder containing Base_118 and contingency_118 subfolders        

        print(f"Error creating schema: {e}")

        return False            # Create BaseCases table



def test_file_reading():            self.cursor.execute("""            db_config: Database configuration dictionary    def connect_database(self):

    """Test reading a few files to understand the format"""

    try:                CREATE TABLE IF NOT EXISTS BaseCases (

        base_folder = Path(r"C:\Projects\dlr-database-project\Base_118")

        contingency_folder = Path(r"C:\Projects\dlr-database-project\contingency_118")                    base_case_id SERIAL PRIMARY KEY,        """        """Connect to PostgreSQL database"""

        

        print(f"Base folder exists: {base_folder.exists()}")                    case_number INTEGER UNIQUE NOT NULL,

        print(f"Contingency folder exists: {contingency_folder.exists()}")

                            filename VARCHAR(255),        self.base_folder_path = Path(base_folder_path)        try:

        if base_folder.exists():

            base_files = list(base_folder.glob("*.txt"))                    case_name VARCHAR(255),

            print(f"Found {len(base_files)} base case files")

                                folder_name VARCHAR(255),        self.db_config = db_config            self.conn = psycopg2.connect(**self.db_config)

            if base_files:

                # Try to read the first file                    buses_count INTEGER DEFAULT 0,

                first_file = base_files[0]

                print(f"\nReading first base file: {first_file.name}")                    branches_count INTEGER DEFAULT 0,        self.conn = None            self.cursor = self.conn.cursor()

                

                df = pd.read_csv(first_file, sep=r'\s+', comment='#')                    processing_status VARCHAR(50) DEFAULT 'pending',

                print(f"Columns: {list(df.columns)}")

                print(f"Shape: {df.shape}")                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP        self.cursor = None            logging.info("Database connection established")

                print(f"First 3 rows:\n{df.head(3)}")

                        )

        if contingency_folder.exists():

            contingency_files = list(contingency_folder.glob("*.txt"))            """)                    return True

            print(f"\nFound {len(contingency_files)} contingency case files")

                        

            if contingency_files:

                # Try to read the first file            # Create BaseBusData table    def connect_database(self):        except Exception as e:

                first_file = contingency_files[0]

                print(f"\nReading first contingency file: {first_file.name}")            self.cursor.execute("""

                

                df = pd.read_csv(first_file, sep=r'\s+', comment='#')                CREATE TABLE IF NOT EXISTS BaseBusData (        """Connect to PostgreSQL database"""            logging.error(f"Database connection failed: {e}")

                print(f"Columns: {list(df.columns)}")

                print(f"Shape: {df.shape}")                    bus_data_id SERIAL PRIMARY KEY,

                print(f"First 3 rows:\n{df.head(3)}")

                            base_case_id INTEGER REFERENCES BaseCases(base_case_id) ON DELETE CASCADE,        try:            return False

    except Exception as e:

        print(f"Error testing file reading: {e}")                    bus_number INTEGER NOT NULL,



def import_single_base_case():                    vm FLOAT,            self.conn = psycopg2.connect(**self.db_config)    

    """Import one base case as a test"""

    try:                    va FLOAT,

        conn = psycopg2.connect(**DB_CONFIG)

        cursor = conn.cursor()                    base_kv FLOAT,            self.cursor = self.conn.cursor()    def create_database_schema(self):

        

        base_folder = Path(r"C:\Projects\dlr-database-project\Base_118")                    pg FLOAT,

        base_files = list(base_folder.glob("*.txt"))

                            qg FLOAT,            logging.info("Database connection established")        """Create the required database schema"""

        if not base_files:

            print("No base case files found")                    pd FLOAT,

            return False

                                qd FLOAT,            return True        try:

        # Take the first file

        file_path = base_files[0]                    UNIQUE(base_case_id, bus_number)

        print(f"Importing base case: {file_path.name}")

                        )        except Exception as e:            logging.info("Creating database schema...")

        # Extract case number from filename

        import re            """)

        match = re.search(r'BASE_(\d+)\.txt', file_path.name, re.IGNORECASE)

        if not match:                        logging.error(f"Database connection failed: {e}")            

            print(f"Could not extract case number from {file_path.name}")

            return False            # Create BaseBranchData table

            

        case_number = int(match.group(1))            self.cursor.execute("""            return False            # Create BaseCases table

        

        # Read the file                CREATE TABLE IF NOT EXISTS BaseBranchData (

        df = pd.read_csv(file_path, sep=r'\s+', comment='#')

        df.columns = [col.upper() for col in df.columns]                    branch_data_id SERIAL PRIMARY KEY,                self.cursor.execute("""

        

        # Create base case record                    base_case_id INTEGER REFERENCES BaseCases(base_case_id) ON DELETE CASCADE,

        cursor.execute("""

            INSERT INTO BaseCases (case_number, filename, case_name, folder_name, processing_status)                    from_bus INTEGER NOT NULL,    def create_database_schema(self):                CREATE TABLE IF NOT EXISTS BaseCases (

            VALUES (%s, %s, %s, %s, 'processing')

            ON CONFLICT (case_number) DO UPDATE SET                    to_bus INTEGER NOT NULL,

                filename = EXCLUDED.filename,

                case_name = EXCLUDED.case_name,                    circuit_id INTEGER DEFAULT 1,        """Create the required database schema"""                    base_case_id SERIAL PRIMARY KEY,

                processing_status = EXCLUDED.processing_status

            RETURNING base_case_id                    pf FLOAT,

        """, (case_number, file_path.name, f"Base Case {case_number}", "Base_118"))

                            qf FLOAT,        try:                    case_number INTEGER UNIQUE NOT NULL,

        base_case_id = cursor.fetchone()[0]

                            rate FLOAT,

        # Import bus data

        bus_records = []                    UNIQUE(base_case_id, from_bus, to_bus, circuit_id)            logging.info("Creating database schema...")                    filename VARCHAR(255),

        for _, row in df.iterrows():

            bus_number = int(row['BUS_NUMBER'])                )

            vm = row.get('VM', 1.0) if pd.notna(row.get('VM')) else 1.0

            va = row.get('VA', 0.0) if pd.notna(row.get('VA')) else 0.0            """)                                case_name VARCHAR(255),

            base_kv = row.get('BASE_KV', 138.0) if pd.notna(row.get('BASE_KV')) else 138.0

            pg = row.get('PG', 0.0) if pd.notna(row.get('PG')) else 0.0            

            qg = row.get('QG', 0.0) if pd.notna(row.get('QG')) else 0.0

            pd_val = row.get('PD', 0.0) if pd.notna(row.get('PD')) else 0.0            # Create ContingencyCases table            # Create BaseCases table                    folder_name VARCHAR(255),

            qd = row.get('QD', 0.0) if pd.notna(row.get('QD')) else 0.0

                        self.cursor.execute("""

            bus_records.append((base_case_id, bus_number, vm, va, base_kv, pg, qg, pd_val, qd))

                        CREATE TABLE IF NOT EXISTS ContingencyCases (            self.cursor.execute("""                    buses_count INTEGER DEFAULT 0,

        # Clear existing data and insert new

        cursor.execute("DELETE FROM BaseBusData WHERE base_case_id = %s", (base_case_id,))                    contingency_case_id SERIAL PRIMARY KEY,

        

        cursor.executemany("""                    base_case_id INTEGER REFERENCES BaseCases(base_case_id),                CREATE TABLE IF NOT EXISTS BaseCases (                    branches_count INTEGER DEFAULT 0,

            INSERT INTO BaseBusData 

            (base_case_id, bus_number, vm, va, base_kv, pg, qg, pd, qd)                    case_number INTEGER NOT NULL,

            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)

        """, bus_records)                    filename VARCHAR(255),                    base_case_id SERIAL PRIMARY KEY,                    processing_status VARCHAR(50) DEFAULT 'pending',

        

        # Update base case status                    case_name VARCHAR(255),

        cursor.execute("""

            UPDATE BaseCases                     contingency_element VARCHAR(255),                    case_number INTEGER UNIQUE NOT NULL,                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

            SET buses_count = %s, processing_status = 'completed'

            WHERE base_case_id = %s                    folder_name VARCHAR(255),

        """, (len(bus_records), base_case_id))

                            buses_count INTEGER DEFAULT 0,                    filename VARCHAR(255),                )

        conn.commit()

        print(f"Successfully imported base case {case_number} with {len(bus_records)} buses")                    branches_count INTEGER DEFAULT 0,

        

        cursor.close()                    processing_status VARCHAR(50) DEFAULT 'pending',                    case_name VARCHAR(255),            """)

        conn.close()

        return True                    max_voltage_violation FLOAT DEFAULT 0,

        

    except Exception as e:                    max_thermal_violation FLOAT DEFAULT 0,                    folder_name VARCHAR(255),            

        print(f"Error importing base case: {e}")

        return False                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,



if __name__ == "__main__":                    UNIQUE(base_case_id, case_number)                    buses_count INTEGER DEFAULT 0,            # Create BaseBusData table

    print("🔧 Testing Contingency Case Loader")

    print("=" * 40)                )

    

    # Step 1: Create schema            """)                    branches_count INTEGER DEFAULT 0,            self.cursor.execute("""

    if create_schema():

        print("✅ Schema creation successful")            

    else:

        print("❌ Schema creation failed")            # Create ContingencyBusData table                    processing_status VARCHAR(50) DEFAULT 'pending',                CREATE TABLE IF NOT EXISTS BaseBusData (

        exit(1)

                self.cursor.execute("""

    # Step 2: Test file reading

    print("\n📁 Testing file reading...")                CREATE TABLE IF NOT EXISTS ContingencyBusData (                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP                    bus_data_id SERIAL PRIMARY KEY,

    test_file_reading()

                        bus_data_id SERIAL PRIMARY KEY,

    # Step 3: Import single base case

    print("\n⬆️ Testing single base case import...")                    contingency_case_id INTEGER REFERENCES ContingencyCases(contingency_case_id) ON DELETE CASCADE,                )                    base_case_id INTEGER REFERENCES BaseCases(base_case_id) ON DELETE CASCADE,

    if import_single_base_case():

        print("✅ Base case import successful")                    bus_number INTEGER NOT NULL,

    else:

        print("❌ Base case import failed")                    vm FLOAT,            """)                    bus_number INTEGER NOT NULL,

        

    print("\n🎉 Test completed!")                    va FLOAT,

                    base_kv FLOAT,                                vm FLOAT,

                    pg FLOAT,

                    qg FLOAT,            # Create BaseBusData table                    va FLOAT,

                    pd FLOAT,

                    qd FLOAT,            self.cursor.execute("""                    base_kv FLOAT,

                    voltage_violation FLOAT DEFAULT 0,

                    UNIQUE(contingency_case_id, bus_number)                CREATE TABLE IF NOT EXISTS BaseBusData (                    pg FLOAT,

                )

            """)                    bus_data_id SERIAL PRIMARY KEY,                    qg FLOAT,

            

            # Create ContingencyBranchData table                    base_case_id INTEGER REFERENCES BaseCases(base_case_id) ON DELETE CASCADE,                    pd FLOAT,

            self.cursor.execute("""

                CREATE TABLE IF NOT EXISTS ContingencyBranchData (                    bus_number INTEGER NOT NULL,                    qd FLOAT,

                    branch_data_id SERIAL PRIMARY KEY,

                    contingency_case_id INTEGER REFERENCES ContingencyCases(contingency_case_id) ON DELETE CASCADE,                    vm FLOAT,                    UNIQUE(base_case_id, bus_number)

                    from_bus INTEGER NOT NULL,

                    to_bus INTEGER NOT NULL,                    va FLOAT,                )

                    circuit_id INTEGER DEFAULT 1,

                    pf FLOAT,                    base_kv FLOAT,            """)

                    qf FLOAT,

                    mva FLOAT,                    pg FLOAT,            

                    rate FLOAT,

                    vio FLOAT DEFAULT 0,                    qg FLOAT,            # Create BaseBranchData table

                    UNIQUE(contingency_case_id, from_bus, to_bus, circuit_id)

                )                    pd FLOAT,            self.cursor.execute("""

            """)

                                qd FLOAT,                CREATE TABLE IF NOT EXISTS BaseBranchData (

            self.conn.commit()

            logging.info("Database schema created successfully")                    UNIQUE(base_case_id, bus_number)                    branch_data_id SERIAL PRIMARY KEY,

            return True

                            )                    base_case_id INTEGER REFERENCES BaseCases(base_case_id) ON DELETE CASCADE,

        except Exception as e:

            logging.error(f"Error creating database schema: {e}")            """)                    from_bus INTEGER NOT NULL,

            self.conn.rollback()

            return False                                to_bus INTEGER NOT NULL,



    def import_base_cases_from_text(self, base_folder):            # Create BaseBranchData table                    circuit_id INTEGER DEFAULT 1,

        """Import base cases from text files in Base_118 folder"""

        try:            self.cursor.execute("""                    pf FLOAT,

            logging.info(f"Importing base cases from: {base_folder}")

                            CREATE TABLE IF NOT EXISTS BaseBranchData (                    qf FLOAT,

            # Get all text files in the base folder

            text_files = list(base_folder.glob("*.txt"))                    branch_data_id SERIAL PRIMARY KEY,                    rate FLOAT,

            total_files = len(text_files)

                                base_case_id INTEGER REFERENCES BaseCases(base_case_id) ON DELETE CASCADE,                    UNIQUE(base_case_id, from_bus, to_bus, circuit_id)

            if total_files == 0:

                logging.warning(f"No text files found in {base_folder}")                    from_bus INTEGER NOT NULL,                )

                return True

                                    to_bus INTEGER NOT NULL,            """)

            logging.info(f"Found {total_files} base case files to process")

                                circuit_id INTEGER DEFAULT 1,            

            imported_count = 0

            for i, file_path in enumerate(text_files, 1):                    pf FLOAT,            # Create ContingencyCases table

                logging.info(f"Processing base case {i}/{total_files}: {file_path.name}")

                                    qf FLOAT,            self.cursor.execute("""

                # Extract case number from filename (e.g., BASE_1.txt -> 1)

                filename = file_path.name                    rate FLOAT,                CREATE TABLE IF NOT EXISTS ContingencyCases (

                match = re.search(r'BASE_(\d+)\.txt', filename, re.IGNORECASE)

                if not match:                    UNIQUE(base_case_id, from_bus, to_bus, circuit_id)                    contingency_case_id SERIAL PRIMARY KEY,

                    logging.warning(f"Could not extract case number from {filename}")

                    continue                )                    base_case_id INTEGER REFERENCES BaseCases(base_case_id),

                    

                case_number = int(match.group(1))            """)                    case_number INTEGER NOT NULL,

                

                # Check if already imported                                filename VARCHAR(255),

                self.cursor.execute("""

                    SELECT base_case_id, processing_status FROM BaseCases             # Create ContingencyCases table                    case_name VARCHAR(255),

                    WHERE case_number = %s

                """, (case_number,))            self.cursor.execute("""                    contingency_element VARCHAR(255),

                

                existing_case = self.cursor.fetchone()                CREATE TABLE IF NOT EXISTS ContingencyCases (                    folder_name VARCHAR(255),

                if existing_case and existing_case[1] == 'completed':

                    logging.info(f"Base case {case_number} already imported - skipping")                    contingency_case_id SERIAL PRIMARY KEY,                    buses_count INTEGER DEFAULT 0,

                    continue

                                    base_case_id INTEGER REFERENCES BaseCases(base_case_id),                    branches_count INTEGER DEFAULT 0,

                try:

                    # Read the text file as CSV                    case_number INTEGER NOT NULL,                    processing_status VARCHAR(50) DEFAULT 'pending',

                    df = pd.read_csv(file_path, sep=r'\s+', comment='#')

                                        filename VARCHAR(255),                    max_voltage_violation FLOAT DEFAULT 0,

                    # Standardize column names (case insensitive)

                    df.columns = [col.upper() for col in df.columns]                    case_name VARCHAR(255),                    max_thermal_violation FLOAT DEFAULT 0,

                    

                    # Check if we have the essential columns                    contingency_element VARCHAR(255),                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    if 'BUS_NUMBER' not in df.columns:

                        logging.error(f"Missing BUS_NUMBER column in {filename}")                    folder_name VARCHAR(255),                    UNIQUE(base_case_id, case_number)

                        continue

                                        buses_count INTEGER DEFAULT 0,                )

                    # Create or update base case record

                    case_name = f"Base Case {case_number}"                    branches_count INTEGER DEFAULT 0,            """)

                    folder_name = base_folder.name

                                        processing_status VARCHAR(50) DEFAULT 'pending',            

                    if existing_case:

                        base_case_id = existing_case[0]                    max_voltage_violation FLOAT DEFAULT 0,            # Create ContingencyBusData table

                        self.cursor.execute("""

                            UPDATE BaseCases                     max_thermal_violation FLOAT DEFAULT 0,            self.cursor.execute("""

                            SET filename = %s, case_name = %s, folder_name = %s, 

                                processing_status = 'processing'                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,                CREATE TABLE IF NOT EXISTS ContingencyBusData (

                            WHERE base_case_id = %s

                        """, (filename, case_name, folder_name, base_case_id))                    UNIQUE(base_case_id, case_number)                    bus_data_id SERIAL PRIMARY KEY,

                    else:

                        self.cursor.execute("""                )                    contingency_case_id INTEGER REFERENCES ContingencyCases(contingency_case_id) ON DELETE CASCADE,

                            INSERT INTO BaseCases (case_number, filename, case_name, folder_name, processing_status)

                            VALUES (%s, %s, %s, %s, 'processing')            """)                    bus_number INTEGER NOT NULL,

                            RETURNING base_case_id

                        """, (case_number, filename, case_name, folder_name))                                vm FLOAT,

                        base_case_id = self.cursor.fetchone()[0]

                                # Create ContingencyBusData table                    va FLOAT,

                    # Import bus data

                    bus_records = []            self.cursor.execute("""                    base_kv FLOAT,

                    for _, row in df.iterrows():

                        bus_number = int(row['BUS_NUMBER'])                CREATE TABLE IF NOT EXISTS ContingencyBusData (                    pg FLOAT,

                        vm = row.get('VM', 1.0) if pd.notna(row.get('VM')) else 1.0

                        va = row.get('VA', 0.0) if pd.notna(row.get('VA')) else 0.0                    bus_data_id SERIAL PRIMARY KEY,                    qg FLOAT,

                        base_kv = row.get('BASE_KV', 138.0) if pd.notna(row.get('BASE_KV')) else 138.0

                        pg = row.get('PG', 0.0) if pd.notna(row.get('PG')) else 0.0                    contingency_case_id INTEGER REFERENCES ContingencyCases(contingency_case_id) ON DELETE CASCADE,                    pd FLOAT,

                        qg = row.get('QG', 0.0) if pd.notna(row.get('QG')) else 0.0

                        pd_val = row.get('PD', 0.0) if pd.notna(row.get('PD')) else 0.0                    bus_number INTEGER NOT NULL,                    qd FLOAT,

                        qd = row.get('QD', 0.0) if pd.notna(row.get('QD')) else 0.0

                                            vm FLOAT,                    voltage_violation FLOAT DEFAULT 0,

                        bus_records.append((base_case_id, bus_number, vm, va, base_kv, pg, qg, pd_val, qd))

                                        va FLOAT,                    UNIQUE(contingency_case_id, bus_number)

                    # Batch insert bus data

                    if bus_records:                    base_kv FLOAT,                )

                        self.cursor.execute("DELETE FROM BaseBusData WHERE base_case_id = %s", (base_case_id,))

                                            pg FLOAT,            """)

                        self.cursor.executemany("""

                            INSERT INTO BaseBusData                     qg FLOAT,            

                            (base_case_id, bus_number, vm, va, base_kv, pg, qg, pd, qd)

                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)                    pd FLOAT,            # Create ContingencyBranchData table

                        """, bus_records)

                                        qd FLOAT,            self.cursor.execute("""

                    # Update base case status

                    self.cursor.execute("""                    voltage_violation FLOAT DEFAULT 0,                CREATE TABLE IF NOT EXISTS ContingencyBranchData (

                        UPDATE BaseCases 

                        SET buses_count = %s, processing_status = 'completed'                    UNIQUE(contingency_case_id, bus_number)                    branch_data_id SERIAL PRIMARY KEY,

                        WHERE base_case_id = %s

                    """, (len(bus_records), base_case_id))                )                    contingency_case_id INTEGER REFERENCES ContingencyCases(contingency_case_id) ON DELETE CASCADE,

                    

                    self.conn.commit()            """)                    from_bus INTEGER NOT NULL,

                    imported_count += 1

                    logging.info(f"Successfully imported base case {case_number} with {len(bus_records)} buses")                                to_bus INTEGER NOT NULL,

                    

                except Exception as e:            # Create ContingencyBranchData table                    circuit_id INTEGER DEFAULT 1,

                    logging.error(f"Error processing base case file {filename}: {e}")

                    self.conn.rollback()            self.cursor.execute("""                    pf FLOAT,

                    continue

                            CREATE TABLE IF NOT EXISTS ContingencyBranchData (                    qf FLOAT,

            logging.info(f"Base case import completed: {imported_count}/{total_files} files imported successfully")

            return True                    branch_data_id SERIAL PRIMARY KEY,                    mva FLOAT,

            

        except Exception as e:                    contingency_case_id INTEGER REFERENCES ContingencyCases(contingency_case_id) ON DELETE CASCADE,                    rate FLOAT,

            logging.error(f"Error importing base cases: {e}")

            return False                    from_bus INTEGER NOT NULL,                    vio FLOAT DEFAULT 0,



    def import_contingency_files_flat(self, contingency_folder):                    to_bus INTEGER NOT NULL,                    UNIQUE(contingency_case_id, from_bus, to_bus, circuit_id)

        """Import contingency cases from text files in flat directory structure"""

        try:                    circuit_id INTEGER DEFAULT 1,                )

            logging.info(f"Importing contingency cases from: {contingency_folder}")

                                pf FLOAT,            """)

            # Get all text files in the contingency folder

            text_files = list(contingency_folder.glob("*.txt"))                    qf FLOAT,            

            total_files = len(text_files)

                                mva FLOAT,            # Create some useful functions for data inheritance

            if total_files == 0:

                logging.warning(f"No text files found in {contingency_folder}")                    rate FLOAT,            self.cursor.execute("""

                return True

                                    vio FLOAT DEFAULT 0,                CREATE OR REPLACE FUNCTION populate_complete_contingency_data(

            logging.info(f"Found {total_files} contingency case files to process")

                                UNIQUE(contingency_case_id, from_bus, to_bus, circuit_id)                    p_contingency_case_id INTEGER,

            # Get base case ID for linking contingencies

            self.cursor.execute("SELECT base_case_id FROM BaseCases ORDER BY case_number LIMIT 1")                )                    p_base_case_id INTEGER

            base_case_result = self.cursor.fetchone()

            if not base_case_result:            """)                ) RETURNS VOID AS $$

                logging.error("No base case found. Please import base cases first.")

                return False                            BEGIN

            

            base_case_id = base_case_result[0]            # Create some useful functions for data inheritance                    -- Insert missing bus data from base case

            imported_count = 0

                        self.cursor.execute("""                    INSERT INTO ContingencyBusData (

            for i, file_path in enumerate(text_files, 1):

                logging.info(f"Processing contingency case {i}/{total_files}: {file_path.name}")                CREATE OR REPLACE FUNCTION populate_complete_contingency_data(                        contingency_case_id, bus_number, vm, va, base_kv, pg, qg, pd, qd

                

                # Extract case number from filename (e.g., CA_1.txt -> 1)                    p_contingency_case_id INTEGER,                    )

                filename = file_path.name

                match = re.search(r'CA_(\d+)\.txt', filename, re.IGNORECASE)                    p_base_case_id INTEGER                    SELECT 

                if not match:

                    logging.warning(f"Could not extract case number from {filename}")                ) RETURNS VOID AS $$                        p_contingency_case_id, bus_number, vm, va, base_kv, pg, qg, pd, qd

                    continue

                                    BEGIN                    FROM BaseBusData 

                case_number = int(match.group(1))

                                    -- Insert missing bus data from base case                    WHERE base_case_id = p_base_case_id

                # Check if already imported

                self.cursor.execute("""                    INSERT INTO ContingencyBusData (                    AND bus_number NOT IN (

                    SELECT contingency_case_id, processing_status FROM ContingencyCases 

                    WHERE base_case_id = %s AND case_number = %s                        contingency_case_id, bus_number, vm, va, base_kv, pg, qg, pd, qd                        SELECT bus_number FROM ContingencyBusData 

                """, (base_case_id, case_number))

                                    )                        WHERE contingency_case_id = p_contingency_case_id

                existing_case = self.cursor.fetchone()

                if existing_case and existing_case[1] == 'completed':                    SELECT                     );

                    logging.info(f"Contingency case {case_number} already imported - skipping")

                    continue                        p_contingency_case_id, bus_number, vm, va, base_kv, pg, qg, pd, qd                    

                

                try:                    FROM BaseBusData                     -- Insert missing branch data from base case  

                    # Read the text file as CSV

                    df = pd.read_csv(file_path, sep=r'\s+', comment='#')                    WHERE base_case_id = p_base_case_id                    INSERT INTO ContingencyBranchData (

                    

                    # Standardize column names (case insensitive)                    AND bus_number NOT IN (                        contingency_case_id, from_bus, to_bus, circuit_id, pf, qf, rate

                    df.columns = [col.upper() for col in df.columns]

                                            SELECT bus_number FROM ContingencyBusData                     )

                    # Check if we have the essential columns

                    if 'BUS_NUMBER' not in df.columns:                        WHERE contingency_case_id = p_contingency_case_id                    SELECT 

                        logging.error(f"Missing BUS_NUMBER column in {filename}")

                        continue                    );                        p_contingency_case_id, from_bus, to_bus, circuit_id, pf, qf, rate

                    

                    # Create or update contingency case record                                        FROM BaseBranchData 

                    case_name = f"Contingency Case {case_number}"

                    contingency_element = f"Contingency {case_number}"                    -- Insert missing branch data from base case                      WHERE base_case_id = p_base_case_id

                    folder_name = contingency_folder.name

                                        INSERT INTO ContingencyBranchData (                    AND (from_bus, to_bus, circuit_id) NOT IN (

                    if existing_case:

                        contingency_case_id = existing_case[0]                        contingency_case_id, from_bus, to_bus, circuit_id, pf, qf, rate                        SELECT from_bus, to_bus, circuit_id FROM ContingencyBranchData 

                        self.cursor.execute("""

                            UPDATE ContingencyCases                     )                        WHERE contingency_case_id = p_contingency_case_id

                            SET filename = %s, case_name = %s, contingency_element = %s, 

                                folder_name = %s, processing_status = 'processing'                    SELECT                     );

                            WHERE contingency_case_id = %s

                        """, (filename, case_name, contingency_element, folder_name, contingency_case_id))                        p_contingency_case_id, from_bus, to_bus, circuit_id, pf, qf, rate                END;

                    else:

                        self.cursor.execute("""                    FROM BaseBranchData                 $$ LANGUAGE plpgsql;

                            INSERT INTO ContingencyCases 

                            (base_case_id, case_number, filename, case_name, contingency_element, folder_name, processing_status)                    WHERE base_case_id = p_base_case_id            """)

                            VALUES (%s, %s, %s, %s, %s, %s, 'processing')

                            RETURNING contingency_case_id                    AND (from_bus, to_bus, circuit_id) NOT IN (            

                        """, (base_case_id, case_number, filename, case_name, contingency_element, folder_name))

                        contingency_case_id = self.cursor.fetchone()[0]                        SELECT from_bus, to_bus, circuit_id FROM ContingencyBranchData             self.conn.commit()

                    

                    # Import bus data                        WHERE contingency_case_id = p_contingency_case_id            logging.info("Database schema created successfully")

                    bus_records = []

                    for _, row in df.iterrows():                    );            return True

                        bus_number = int(row['BUS_NUMBER'])

                        vm = row.get('VM', 1.0) if pd.notna(row.get('VM')) else 1.0                END;            

                        va = row.get('VA', 0.0) if pd.notna(row.get('VA')) else 0.0

                        base_kv = row.get('BASE_KV', 138.0) if pd.notna(row.get('BASE_KV')) else 138.0                $$ LANGUAGE plpgsql;        except Exception as e:

                        pg = row.get('PG', 0.0) if pd.notna(row.get('PG')) else 0.0

                        qg = row.get('QG', 0.0) if pd.notna(row.get('QG')) else 0.0            """)            logging.error(f"Error creating database schema: {e}")

                        pd_val = row.get('PD', 0.0) if pd.notna(row.get('PD')) else 0.0

                        qd = row.get('QD', 0.0) if pd.notna(row.get('QD')) else 0.0                        self.conn.rollback()

                        

                        bus_records.append((contingency_case_id, bus_number, vm, va, base_kv, pg, qg, pd_val, qd))            self.conn.commit()            return False

                    

                    # Batch insert bus data            logging.info("Database schema created successfully")    

                    if bus_records:

                        self.cursor.execute("DELETE FROM ContingencyBusData WHERE contingency_case_id = %s", (contingency_case_id,))            return True    def disconnect_database(self):

                        

                        self.cursor.executemany("""                    """Disconnect from database"""

                            INSERT INTO ContingencyBusData 

                            (contingency_case_id, bus_number, vm, va, base_kv, pg, qg, pd, qd)        except Exception as e:        if self.cursor:

                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)

                        """, bus_records)            logging.error(f"Error creating database schema: {e}")            self.cursor.close()

                    

                    # Update contingency case status            self.conn.rollback()        if self.conn:

                    self.cursor.execute("""

                        UPDATE ContingencyCases             return False            self.conn.close()

                        SET buses_count = %s, processing_status = 'completed'

                        WHERE contingency_case_id = %s        logging.info("Database connection closed")

                    """, (len(bus_records), contingency_case_id))

                        def import_base_cases_from_text(self, base_folder):    

                    self.conn.commit()

                    imported_count += 1        """Import base cases from text files in Base_118 folder"""    def get_base_case_mapping(self):

                    logging.info(f"Successfully imported contingency case {case_number} with {len(bus_records)} buses")

                            try:        """Get mapping of base case filenames to IDs"""

                except Exception as e:

                    logging.error(f"Error processing contingency case file {filename}: {e}")            logging.info(f"Importing base cases from: {base_folder}")        try:

                    self.conn.rollback()

                    continue                        self.cursor.execute("""

            

            logging.info(f"Contingency case import completed: {imported_count}/{total_files} files imported successfully")            # Get all text files in the base folder                SELECT base_case_id, filename 

            return True

                        text_files = list(base_folder.glob("*.txt"))                FROM BaseCaseFiles 

        except Exception as e:

            logging.error(f"Error importing contingency cases: {e}")            total_files = len(text_files)                ORDER BY base_case_id

            return False

                        """)

    def main(self):

        """Main processing function"""            if total_files == 0:            

        try:

            # Connect to database                logging.warning(f"No text files found in {base_folder}")            base_cases = {}

            if not self.connect_database():

                return False                return True            for base_case_id, filename in self.cursor.fetchall():

                

            # Create database schema                                if 'BASE_0_bus118_' in filename:

            if not self.create_database_schema():

                return False            logging.info(f"Found {total_files} base case files to process")                    parts = filename.split('BASE_0_bus118_')

            

            # First, import base cases from text files                                if len(parts) > 1:

            base_118_folder = self.base_folder_path / "Base_118"

            logging.info(f"Looking for base case files in: {base_118_folder}")            imported_count = 0                        number = parts[1].replace('.txt', '')

            

            if base_118_folder.exists():            for i, file_path in enumerate(text_files, 1):                        contingency_folder = f'CA_0_bus118_{number}'

                base_files = list(base_118_folder.glob("*.txt"))

                logging.info(f"Found {len(base_files)} base case files")                logging.info(f"Processing base case {i}/{total_files}: {file_path.name}")                        base_cases[contingency_folder] = base_case_id

                

                if base_files:                                        

                    if not self.import_base_cases_from_text(base_118_folder):

                        logging.error("Failed to import base cases")                # Extract case number from filename (e.g., BASE_1.txt -> 1)                        base_name = filename.replace('.txt', '').replace('BASE_', '')

                        return False

            else:                filename = file_path.name                        base_cases[base_name] = base_case_id

                logging.warning(f"Base case folder {base_118_folder} does not exist")

                            match = re.search(r'BASE_(\d+)\.txt', filename, re.IGNORECASE)                

            # Now import contingency cases from text files

            contingency_118_folder = self.base_folder_path / "contingency_118"                if not match:            logging.info(f"Found {len(base_cases)} base cases for contingency mapping")

            logging.info(f"Looking for contingency case files in: {contingency_118_folder}")

                                logging.warning(f"Could not extract case number from {filename}")            return base_cases

            if contingency_118_folder.exists():

                contingency_files = list(contingency_118_folder.glob("*.txt"))                    continue            

                logging.info(f"Found {len(contingency_files)} contingency case files")

                                            except Exception as e:

                if contingency_files:

                    if not self.import_contingency_files_flat(contingency_118_folder):                case_number = int(match.group(1))            logging.error(f"Error getting base case mapping: {e}")

                        logging.error("Failed to import contingency cases")

                        return False                            return {}

            else:

                logging.warning(f"Contingency case folder {contingency_118_folder} does not exist")                # Check if already imported    

            

            # Process SLR/DLR Excel files                self.cursor.execute("""    def contingency_case_exists(self, base_case_id, case_number):

            try:

                slr_dlr_folder = self.base_folder_path / "SLR_DLR_Data"                    SELECT base_case_id, processing_status FROM BaseCases         """Check if a contingency case already exists and is completed"""

                if slr_dlr_folder.exists():

                    logging.info("Processing SLR/DLR Excel files...")                    WHERE case_number = %s        try:

                    

                    # Import SLR files (Static Load Relief)                """, (case_number,))            self.cursor.execute("""

                    slr_files = list(slr_dlr_folder.glob("*SLR*.xlsx"))

                    if slr_files:                                SELECT contingency_case_id, processing_status 

                        logging.info(f"Found {len(slr_files)} SLR files")

                        for slr_file in slr_files:                existing_case = self.cursor.fetchone()                FROM ContingencyCases 

                            try:

                                from slr_dlr_loader import process_slr_file                if existing_case and existing_case[1] == 'completed':                WHERE base_case_id = %s AND case_number = %s

                                process_slr_file(str(slr_file), self.db_config)

                                logging.info(f"Processed SLR file: {slr_file.name}")                    logging.info(f"Base case {case_number} already imported - skipping")            """, (base_case_id, case_number))

                            except Exception as e:

                                logging.warning(f"Error processing SLR file {slr_file}: {e}")                    continue            

                    

                    # Import DLR files (Dynamic Load Relief)                              result = self.cursor.fetchone()

                    dlr_files = list(slr_dlr_folder.glob("*DLR*.xlsx"))

                    if dlr_files:                try:            if result:

                        logging.info(f"Found {len(dlr_files)} DLR files")

                        for dlr_file in dlr_files:                    # Read the text file as CSV                case_id, status = result

                            try:

                                from dlr_slr_loader import process_dlr_file                    df = pd.read_csv(file_path, sep=r'\s+', comment='#')                return True, case_id, status

                                process_dlr_file(str(dlr_file), self.db_config)

                                logging.info(f"Processed DLR file: {dlr_file.name}")                                return False, None, None

                            except Exception as e:

                                logging.warning(f"Error processing DLR file {dlr_file}: {e}")                    # Standardize column names (case insensitive)            

                else:

                    logging.info("No SLR/DLR folder found - skipping Excel file processing")                    df.columns = [col.upper() for col in df.columns]        except Exception as e:

                    

            except Exception as e:                                logging.error(f"Error checking contingency case existence: {e}")

                logging.warning(f"Error processing SLR/DLR files: {e}")

                                # Map expected columns            return False, None, None

            logging.info("Processing completed successfully")

            return True                    expected_cols = ['BUS_NUMBER', 'VM', 'VA', 'BASE_KV', 'PG', 'QG', 'PD', 'QD']

            

        except Exception as e:                        def create_contingency_case(self, base_case_id, case_number, file_path, folder_name):

            logging.error(f"Error in main processing: {e}")

            return False                    # Check if we have the essential columns        """Create contingency case and import sparse data"""

        finally:

            if self.conn:                    if 'BUS_NUMBER' not in df.columns:        filename = os.path.basename(file_path)

                self.conn.close()

                logging.info("Database connection closed")                        logging.error(f"Missing BUS_NUMBER column in {filename}")        



                        continue        # Check if case already exists and is completed

if __name__ == "__main__":

    # Database configuration for '118' database                            exists, existing_id, status = self.contingency_case_exists(base_case_id, case_number)

    DB_CONFIG = {

        'host': 'localhost',                    # Create or update base case record        if exists and status == 'completed':

        'database': '118',

        'user': 'postgres',                    case_name = f"Base Case {case_number}"            logging.info(f"Contingency case {filename} already exists and is completed - skipping")

        'password': 'postgres'

    }                    folder_name = base_folder.name            return True, (118, 0)  # Assume standard bus count, no new branches imported

    

    # Path to your data folder                            

    DATA_FOLDER = r"C:\Projects\dlr-database-project"

                        if existing_case:        try:

    # Create and run the loader

    loader = ContingencyCaseLoader(DATA_FOLDER, DB_CONFIG)                        base_case_id = existing_case[0]            case_name = f"Contingency Case {case_number}"

    success = loader.main()

                            self.cursor.execute("""            contingency_element = f"Contingency {case_number} - {folder_name}"

    if success:

        print("✅ Contingency case loading completed successfully!")                            UPDATE BaseCases             

    else:

        print("❌ Contingency case loading failed. Check the logs for details.")                            SET filename = %s, case_name = %s, folder_name = %s,             # Create case record (skip if already exists)

                                processing_status = 'processing'            self.cursor.execute("""

                            WHERE base_case_id = %s                INSERT INTO ContingencyCases 

                        """, (filename, case_name, folder_name, base_case_id))                (base_case_id, case_number, filename, case_name, contingency_element, folder_name, processing_status) 

                    else:                VALUES (%s, %s, %s, %s, %s, %s, %s) 

                        self.cursor.execute("""                ON CONFLICT (base_case_id, case_number) DO UPDATE SET

                            INSERT INTO BaseCases (case_number, filename, case_name, folder_name, processing_status)                    filename = EXCLUDED.filename,

                            VALUES (%s, %s, %s, %s, 'processing')                    case_name = EXCLUDED.case_name,

                            RETURNING base_case_id                    contingency_element = EXCLUDED.contingency_element,

                        """, (case_number, filename, case_name, folder_name))                    folder_name = EXCLUDED.folder_name,

                        base_case_id = self.cursor.fetchone()[0]                    processing_status = EXCLUDED.processing_status

                                    RETURNING contingency_case_id

                    # Import bus data            """, (base_case_id, case_number, filename, case_name, contingency_element, folder_name, 'processing'))

                    bus_records = []            

                    for _, row in df.iterrows():            contingency_case_id = self.cursor.fetchone()[0]

                        bus_number = int(row['BUS_NUMBER'])            

                        vm = row.get('VM', 1.0) if pd.notna(row.get('VM')) else 1.0            # Import sparse contingency data

                        va = row.get('VA', 0.0) if pd.notna(row.get('VA')) else 0.0            buses_imported = self.import_sparse_buses(file_path, contingency_case_id, base_case_id)

                        base_kv = row.get('BASE_KV', 138.0) if pd.notna(row.get('BASE_KV')) else 138.0            branches_imported = self.import_sparse_branches(file_path, contingency_case_id, base_case_id)

                        pg = row.get('PG', 0.0) if pd.notna(row.get('PG')) else 0.0            

                        qg = row.get('QG', 0.0) if pd.notna(row.get('QG')) else 0.0            # Populate complete data with base case inheritance

                        pd_val = row.get('PD', 0.0) if pd.notna(row.get('PD')) else 0.0            self.cursor.execute("""

                        qd = row.get('QD', 0.0) if pd.notna(row.get('QD')) else 0.0                SELECT populate_complete_contingency_data(%s, %s)

                                    """, (contingency_case_id, base_case_id))

                        bus_records.append((base_case_id, bus_number, vm, va, base_kv, pg, qg, pd_val, qd))            

                                # Update case status

                    # Batch insert bus data            self.cursor.execute("""

                    if bus_records:                UPDATE ContingencyCases 

                        self.cursor.execute("DELETE FROM BaseBusData WHERE base_case_id = %s", (base_case_id,))                SET buses_count = 118, branches_count = (

                                            SELECT COUNT(*) FROM ContingencyBranchData 

                        self.cursor.executemany("""                    WHERE contingency_case_id = %s

                            INSERT INTO BaseBusData                 ), processing_status = 'completed'

                            (base_case_id, bus_number, vm, va, base_kv, pg, qg, pd, qd)                WHERE contingency_case_id = %s

                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)            """, (contingency_case_id, contingency_case_id))

                        """, bus_records)            

                                self.conn.commit()

                    # Update base case status            return True, (118, branches_imported)

                    self.cursor.execute("""            

                        UPDATE BaseCases         except Exception as e:

                        SET buses_count = %s, processing_status = 'completed'            logging.error(f"Error importing contingency case {filename}: {e}")

                        WHERE base_case_id = %s            self.conn.rollback()

                    """, (len(bus_records), base_case_id))            return False, (0, 0)

                        

                    self.conn.commit()    def import_sparse_buses(self, file_path, contingency_case_id, base_case_id):

                    imported_count += 1        """Import only the bus data that exists in contingency file"""

                    logging.info(f"Successfully imported base case {case_number} with {len(bus_records)} buses")        try:

                                # Read text file as CSV with proper parsing

                except Exception as e:            # Expected format: Bus_Number, VM, VA, BASE_KV, PG, QG, PD, QD

                    logging.error(f"Error processing base case file {filename}: {e}")            buses_df = pd.read_csv(file_path, skipinitialspace=True)

                    self.conn.rollback()            

                    continue            if buses_df is None or buses_df.empty:

                            logging.info(f"No bus data found in {Path(file_path).name} - will use base case data")

            logging.info(f"Base case import completed: {imported_count}/{total_files} files imported successfully")                return 0

            return True            

                        # Clean and standardize column names - handle the header format

        except Exception as e:            buses_df.columns = buses_df.columns.str.strip().str.upper()

            logging.error(f"Error importing base cases: {e}")            

            return False            # Map column variations to standard names

            column_mapping = {

    def import_contingency_files_flat(self, contingency_folder):                'BUS_NUMBER': ['BUS_NUMBER', 'BUS', 'BUS_NUM'],

        """Import contingency cases from text files in flat directory structure"""                'VM': ['VM', 'V_MAG', 'VMAG'],

        try:                'VA': ['VA', 'V_ANG', 'VANG'], 

            logging.info(f"Importing contingency cases from: {contingency_folder}")                'PG': ['PG', 'P_GEN', 'PGEN'],

                            'QG': ['QG', 'Q_GEN', 'QGEN'],

            # Get all text files in the contingency folder                'PD': ['PD', 'P_LOAD', 'PLOAD'],

            text_files = list(contingency_folder.glob("*.txt"))                'QD': ['QD', 'Q_LOAD', 'QLOAD'],

            total_files = len(text_files)                'BASE_KV': ['BASE_KV', 'BASEKV', 'KV']

                        }

            if total_files == 0:            

                logging.warning(f"No text files found in {contingency_folder}")            for standard_col, variations in column_mapping.items():

                return True                for col in buses_df.columns:

                                    if col in variations:

            logging.info(f"Found {total_files} contingency case files to process")                        buses_df.rename(columns={col: standard_col}, inplace=True)

                                    break

            # Get base case ID for linking contingencies            

            self.cursor.execute("SELECT base_case_id FROM BaseCases ORDER BY case_number LIMIT 1")            # Insert sparse bus data

            base_case_result = self.cursor.fetchone()            inserted_count = 0

            if not base_case_result:            for _, row in buses_df.iterrows():

                logging.error("No base case found. Please import base cases first.")                if 'BUS_NUMBER' not in row or pd.isna(row['BUS_NUMBER']):

                return False                    continue

                                

            base_case_id = base_case_result[0]                # Build dynamic insert based on available data

            imported_count = 0                columns = ['contingency_case_id', 'base_case_id', 'bus_number']

                            values = [contingency_case_id, base_case_id, int(row['BUS_NUMBER'])]

            for i, file_path in enumerate(text_files, 1):                

                logging.info(f"Processing contingency case {i}/{total_files}: {file_path.name}")                # Add only non-null values

                                for col in ['VM', 'VA', 'PG', 'QG', 'PD', 'QD']:

                # Extract case number from filename (e.g., CA_1.txt -> 1)                    if col in row and pd.notna(row[col]):

                filename = file_path.name                        columns.append(col)

                match = re.search(r'CA_(\d+)\.txt', filename, re.IGNORECASE)                        values.append(float(row[col]))

                if not match:                

                    logging.warning(f"Could not extract case number from {filename}")                if len(columns) > 3:  # Only insert if we have actual data

                    continue                    placeholders = ', '.join(['%s'] * len(values))

                                        columns_str = ', '.join(columns)

                case_number = int(match.group(1))                    

                                    self.cursor.execute(f"""

                # Check if already imported                        INSERT INTO ContingencyBusData ({columns_str}) 

                self.cursor.execute("""                        VALUES ({placeholders})

                    SELECT contingency_case_id, processing_status FROM ContingencyCases                         ON CONFLICT (contingency_case_id, bus_number) DO NOTHING

                    WHERE base_case_id = %s AND case_number = %s                    """, values)

                """, (base_case_id, case_number))                    inserted_count += 1

                            

                existing_case = self.cursor.fetchone()            logging.info(f"Imported {inserted_count} sparse bus records from {Path(file_path).name}")

                if existing_case and existing_case[1] == 'completed':            return inserted_count

                    logging.info(f"Contingency case {case_number} already imported - skipping")            

                    continue        except Exception as e:

                            logging.error(f"Error importing sparse bus data from {file_path}: {e}")

                try:            return 0

                    # Read the text file as CSV    

                    df = pd.read_csv(file_path, sep=r'\s+', comment='#')    def import_sparse_branches(self, file_path, contingency_case_id, base_case_id):

                            """Import only the branch data that exists in contingency file"""

                    # Standardize column names (case insensitive)        try:

                    df.columns = [col.upper() for col in df.columns]            # Read as text file to parse power flow data

                                if not file_path.endswith('.txt'):

                    # Check if we have the essential columns                logging.info(f"Skipping non-text file: {file_path}")

                    if 'BUS_NUMBER' not in df.columns:                return 0

                        logging.error(f"Missing BUS_NUMBER column in {filename}")            

                        continue            with open(file_path, 'r') as f:

                                    content = f.read()

                    # Create or update contingency case record            

                    case_name = f"Contingency Case {case_number}"            # Parse branch data from text file

                    contingency_element = f"Contingency {case_number}"            branch_data = []

                    folder_name = contingency_folder.name            lines = content.strip().split('\n')

                                

                    if existing_case:            # Find branch data section (usually marked by "BRA" or similar)

                        contingency_case_id = existing_case[0]            in_branch_section = False

                        self.cursor.execute("""            for line in lines:

                            UPDATE ContingencyCases                 line = line.strip()

                            SET filename = %s, case_name = %s, contingency_element = %s,                 if not line:

                                folder_name = %s, processing_status = 'processing'                    continue

                            WHERE contingency_case_id = %s                

                        """, (filename, case_name, contingency_element, folder_name, contingency_case_id))                # Skip header lines and look for branch data

                    else:                if 'BRA' in line.upper() or 'BRANCH' in line.upper():

                        self.cursor.execute("""                    in_branch_section = True

                            INSERT INTO ContingencyCases                     continue

                            (base_case_id, case_number, filename, case_name, contingency_element, folder_name, processing_status)                

                            VALUES (%s, %s, %s, %s, %s, %s, 'processing')                if in_branch_section and line.replace('-', '').replace('.', '').replace(' ', '').isdigit() == False:

                            RETURNING contingency_case_id                    # Try to parse branch data line

                        """, (base_case_id, case_number, filename, case_name, contingency_element, folder_name))                    parts = line.split()

                        contingency_case_id = self.cursor.fetchone()[0]                    if len(parts) >= 9:  # Typical branch data format

                                            try:

                    # Import bus data                            branch_num = int(parts[0])

                    bus_records = []                            from_bus = int(parts[1])

                    for _, row in df.iterrows():                            to_bus = int(parts[2])

                        bus_number = int(row['BUS_NUMBER'])                            circuit_id = int(parts[3]) if len(parts) > 3 else 1

                        vm = row.get('VM', 1.0) if pd.notna(row.get('VM')) else 1.0                            pf = float(parts[4]) if len(parts) > 4 else 0.0

                        va = row.get('VA', 0.0) if pd.notna(row.get('VA')) else 0.0                            qf = float(parts[5]) if len(parts) > 5 else 0.0

                        base_kv = row.get('BASE_KV', 138.0) if pd.notna(row.get('BASE_KV')) else 138.0                            

                        pg = row.get('PG', 0.0) if pd.notna(row.get('PG')) else 0.0                            branch_data.append({

                        qg = row.get('QG', 0.0) if pd.notna(row.get('QG')) else 0.0                                'branch_num': branch_num,

                        pd_val = row.get('PD', 0.0) if pd.notna(row.get('PD')) else 0.0                                'from_bus': from_bus,

                        qd = row.get('QD', 0.0) if pd.notna(row.get('QD')) else 0.0                                'to_bus': to_bus,

                                                        'circuit_id': circuit_id,

                        bus_records.append((contingency_case_id, bus_number, vm, va, base_kv, pg, qg, pd_val, qd))                                'pf': pf,

                                                    'qf': qf

                    # Batch insert bus data                            })

                    if bus_records:                        except (ValueError, IndexError):

                        self.cursor.execute("DELETE FROM ContingencyBusData WHERE contingency_case_id = %s", (contingency_case_id,))                            continue

                                    

                        self.cursor.executemany("""            # Update existing contingency branch data with power flow values

                            INSERT INTO ContingencyBusData             updated_count = 0

                            (contingency_case_id, bus_number, vm, va, base_kv, pg, qg, pd, qd)            for branch in branch_data:

                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)                try:

                        """, bus_records)                    self.cursor.execute("""

                                            UPDATE contingencybranchdata 

                    # Update contingency case status                        SET pf = %s, qf = %s,

                    self.cursor.execute("""                            mva = SQRT(%s * %s + %s * %s),

                        UPDATE ContingencyCases                             vio = CASE 

                        SET buses_count = %s, processing_status = 'completed'                                WHEN rate > 0 THEN 

                        WHERE contingency_case_id = %s                                    GREATEST(0, SQRT(%s * %s + %s * %s) - rate)

                    """, (len(bus_records), contingency_case_id))                                ELSE 0 

                                                END

                    self.conn.commit()                        WHERE contingency_case_id = %s 

                    imported_count += 1                            AND from_bus = %s 

                    logging.info(f"Successfully imported contingency case {case_number} with {len(bus_records)} buses")                            AND to_bus = %s 

                                                AND circuit_id = %s

                except Exception as e:                    """, (

                    logging.error(f"Error processing contingency case file {filename}: {e}")                        branch['pf'], branch['qf'],

                    self.conn.rollback()                        branch['pf'], branch['pf'], branch['qf'], branch['qf'],  # for mva calculation

                    continue                        branch['pf'], branch['pf'], branch['qf'], branch['qf'],  # for vio calculation

                                    contingency_case_id,

            logging.info(f"Contingency case import completed: {imported_count}/{total_files} files imported successfully")                        branch['from_bus'],

            return True                        branch['to_bus'], 

                                    branch['circuit_id']

        except Exception as e:                    ))

            logging.error(f"Error importing contingency cases: {e}")                    

            return False                    if self.cursor.rowcount > 0:

                        updated_count += 1

    def main(self):                        

        """Main processing function"""                except Exception as e:

        try:                    logging.warning(f"Failed to update branch {branch['from_bus']}-{branch['to_bus']}-{branch['circuit_id']}: {e}")

            # Connect to database            

            if not self.connect_database():            logging.info(f"Updated {updated_count} branch records with power flow data from {Path(file_path).name}")

                return False            return updated_count

                            

            # Create database schema        except Exception as e:

            if not self.create_database_schema():            logging.error(f"Error importing branch data from {file_path}: {e}")

                return False            return 0

                

            # First, import base cases from text files    def import_base_cases_from_text(self, base_cases_folder):

            base_118_folder = self.base_folder_path / "Base_118"        """Import base cases from text files"""

            logging.info(f"Looking for base case files in: {base_118_folder}")        try:

                        base_cases_path = Path(base_cases_folder)

            if base_118_folder.exists():            if not base_cases_path.exists():

                base_files = list(base_118_folder.glob("*.txt"))                logging.error(f"Base cases folder not found: {base_cases_folder}")

                logging.info(f"Found {len(base_files)} base case files")                return False

                            

                if base_files:            # Get all base case text files

                    if not self.import_base_cases_from_text(base_118_folder):            text_files = list(base_cases_path.glob('BASE_*.txt'))

                        logging.error("Failed to import base cases")            

                        return False            logging.info(f"Found {len(text_files)} base case files to import")

            else:            

                logging.warning(f"Base case folder {base_118_folder} does not exist")            for file_path in text_files:

                            try:

            # Now import contingency cases from text files                    # Extract case number from filename

            contingency_118_folder = self.base_folder_path / "contingency_118"                    filename = file_path.name

            logging.info(f"Looking for contingency case files in: {contingency_118_folder}")                    case_number = None

                                if 'BASE_0_bus118_' in filename:

            if contingency_118_folder.exists():                        parts = filename.split('BASE_0_bus118_')

                contingency_files = list(contingency_118_folder.glob("*.txt"))                        if len(parts) > 1:

                logging.info(f"Found {len(contingency_files)} contingency case files")                            case_number = int(parts[1].replace('.txt', ''))

                                    

                if contingency_files:                    if case_number is None:

                    if not self.import_contingency_files_flat(contingency_118_folder):                        logging.warning(f"Could not extract case number from {filename}")

                        logging.error("Failed to import contingency cases")                        continue

                        return False                    

            else:                    # Check if base case already exists

                logging.warning(f"Contingency case folder {contingency_118_folder} does not exist")                    self.cursor.execute("""

                                    SELECT base_case_id FROM BaseCases 

            # Process SLR/DLR Excel files                        WHERE case_number = %s

            try:                    """, (case_number,))

                slr_dlr_folder = self.base_folder_path / "SLR_DLR_Data"                    

                if slr_dlr_folder.exists():                    existing = self.cursor.fetchone()

                    logging.info("Processing SLR/DLR Excel files...")                    if existing:

                                            logging.info(f"Base case {case_number} already exists, skipping")

                    # Import SLR files (Static Load Relief)                        continue

                    slr_files = list(slr_dlr_folder.glob("*SLR*.xlsx"))                    

                    if slr_files:                    # Read the text file as CSV

                        logging.info(f"Found {len(slr_files)} SLR files")                    buses_df = pd.read_csv(file_path, skipinitialspace=True)

                        for slr_file in slr_files:                    

                            try:                    # Create base case record

                                from slr_dlr_loader import process_slr_file                    self.cursor.execute("""

                                process_slr_file(str(slr_file), self.db_config)                        INSERT INTO BaseCases (case_number, filename, case_name, folder_name)

                                logging.info(f"Processed SLR file: {slr_file.name}")                        VALUES (%s, %s, %s, %s)

                            except Exception as e:                        RETURNING base_case_id

                                logging.warning(f"Error processing SLR file {slr_file}: {e}")                    """, (case_number, filename, f"Base Case {case_number}", "Base_118"))

                                        

                    # Import DLR files (Dynamic Load Relief)                      base_case_id = self.cursor.fetchone()[0]

                    dlr_files = list(slr_dlr_folder.glob("*DLR*.xlsx"))                    

                    if dlr_files:                    # Import bus data

                        logging.info(f"Found {len(dlr_files)} DLR files")                    bus_count = 0

                        for dlr_file in dlr_files:                    for _, row in buses_df.iterrows():

                            try:                        try:

                                from dlr_slr_loader import process_dlr_file                            self.cursor.execute("""

                                process_dlr_file(str(dlr_file), self.db_config)                                INSERT INTO BaseBusData 

                                logging.info(f"Processed DLR file: {dlr_file.name}")                                (base_case_id, bus_number, vm, va, base_kv, pg, qg, pd, qd)

                            except Exception as e:                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)

                                logging.warning(f"Error processing DLR file {dlr_file}: {e}")                            """, (

                else:                                base_case_id,

                    logging.info("No SLR/DLR folder found - skipping Excel file processing")                                int(row['Bus_Number']),

                                                    float(row['VM']),

            except Exception as e:                                float(row['VA']),

                logging.warning(f"Error processing SLR/DLR files: {e}")                                float(row['BASE_KV']),

                                            float(row['PG']),

            logging.info("Processing completed successfully")                                float(row['QG']),

            return True                                float(row['PD']),

                                            float(row['QD'])

        except Exception as e:                            ))

            logging.error(f"Error in main processing: {e}")                            bus_count += 1

            return False                        except Exception as e:

        finally:                            logging.warning(f"Error importing bus data for case {case_number}: {e}")

            if self.conn:                    

                self.conn.close()                    # Update base case with bus count

                logging.info("Database connection closed")                    self.cursor.execute("""

                        UPDATE BaseCases 

                        SET buses_count = %s, processing_status = 'completed'

if __name__ == "__main__":                        WHERE base_case_id = %s

    # Database configuration for '118' database                    """, (bus_count, base_case_id))

    DB_CONFIG = {                    

        'host': 'localhost',                    self.conn.commit()

        'database': '118',                    logging.info(f"Imported base case {case_number} with {bus_count} buses")

        'user': 'postgres',                    

        'password': 'postgres'                except Exception as e:

    }                    logging.error(f"Error importing base case from {file_path}: {e}")

                        self.conn.rollback()

    # Path to your data folder                    continue

    DATA_FOLDER = r"C:\Projects\dlr-database-project"            

                return True

    # Create and run the loader            

    loader = ContingencyCaseLoader(DATA_FOLDER, DB_CONFIG)        except Exception as e:

    success = loader.main()            logging.error(f"Error in base case import: {e}")

                return False

    if success:

        print("✅ Contingency case loading completed successfully!")    def import_contingency_folder(self, folder_path, base_case_id):

    else:        """Import all contingency files from a folder"""

        print("❌ Contingency case loading failed. Check the logs for details.")        folder_name = os.path.basename(folder_path)
        
        # Get all text files in folder (changed from Excel files)
        text_files = list(Path(folder_path).glob('*.txt'))
        
        total_files = len(text_files)
        logging.info(f"Processing {total_files} contingency files in {folder_name} for base case {base_case_id}")
        
        successful_cases = 0
        failed_cases = 0
        
        for i, file_path in enumerate(text_files, 1):
            case_number = i
            success, (buses, branches) = self.create_contingency_case(
                base_case_id, case_number, file_path, folder_name
            )
            
            if success:
                successful_cases += 1
                if i % 25 == 0:  # Progress every 25 files
                    logging.info(f"  Progress: {i}/{total_files} files processed")
            else:
                failed_cases += 1
        
        logging.info(f"Completed {folder_name}: {successful_cases} successful, {failed_cases} failed")
        return successful_cases > 0
    
    def import_contingency_files_flat(self, folder_path, base_case_mapping):
        """Import contingency files from a flat directory structure"""
        try:
            folder_path = Path(folder_path)
            
            # Get all contingency text files in folder
            text_files = list(folder_path.glob('CA_*.txt'))
            
            logging.info(f"Found {len(text_files)} contingency files in flat structure")
            
            successful_cases = 0
            failed_cases = 0
            start_time = time.time()
            
            for i, file_path in enumerate(text_files, 1):
                try:
                    filename = file_path.name
                    
                    # Extract case number from filename: CA_0_bus118_X.txt
                    case_number = None
                    if 'CA_0_bus118_' in filename:
                        parts = filename.split('CA_0_bus118_')
                        if len(parts) > 1:
                            case_number = int(parts[1].replace('.txt', ''))
                    
                    if case_number is None:
                        logging.warning(f"Could not extract case number from {filename}")
                        failed_cases += 1
                        continue
                    
                    # Find corresponding base case
                    base_case_id = None
                    base_case_key = f"0_bus118_{case_number}"
                    
                    for key, case_id in base_case_mapping.items():
                        if base_case_key in key:
                            base_case_id = case_id
                            break
                    
                    if base_case_id is None:
                        logging.warning(f"No matching base case found for contingency {case_number}")
                        failed_cases += 1
                        continue
                    
                    # Create contingency case
                    success, (buses, branches) = self.create_contingency_case(
                        base_case_id, case_number, file_path, "contingency_118"
                    )
                    
                    if success:
                        successful_cases += 1
                        if i % 25 == 0:  # Progress every 25 files
                            elapsed = time.time() - start_time
                            logging.info(f"   Processed {i}/{len(text_files)} files ({i/len(text_files)*100:.1f}%) - Elapsed: {elapsed/60:.1f} min")
                    else:
                        failed_cases += 1
                        
                except Exception as e:
                    logging.error(f"Error processing file {file_path}: {e}")
                    failed_cases += 1
                    continue
            
            total_time = time.time() - start_time
            logging.info(f"Flat file import complete: {successful_cases} successful, {failed_cases} failed in {total_time/60:.1f} minutes")
            return successful_cases > 0
            
        except Exception as e:
            logging.error(f"Error in flat file import: {e}")
            return False

    def import_all_contingency_folders(self, contingency_root_folder):
        """Import all contingency folders with optimized schema"""
        if not self.connect_database():
            return False
        
        try:
            # Get base case mapping
            base_case_mapping = self.get_base_case_mapping()
            if not base_case_mapping:
                logging.error("No base case mapping found!")
                return False
            
            # Check if we have subdirectories or flat file structure
            contingency_folders = [f for f in Path(contingency_root_folder).iterdir() if f.is_dir()]
            
            # If no subdirectories, handle as flat file structure
            if len(contingency_folders) == 0:
                logging.info("No subdirectories found, treating as flat file structure")
                return self.import_contingency_files_flat(contingency_root_folder, base_case_mapping)
            
            # Original folder-based processing
            total_folders = len(contingency_folders)
            
            logging.info(f"Found {total_folders} contingency folders")
            
            successful_folders = 0
            failed_folders = 0
            start_time = time.time()
            
            for i, folder_path in enumerate(contingency_folders, 1):
                folder_name = folder_path.name
                
                # Match folder to base case
                base_case_id = None
                for base_name, case_id in base_case_mapping.items():
                    if base_name in folder_name:
                        base_case_id = case_id
                        break
                
                if not base_case_id:
                    logging.warning(f"Could not match folder {folder_name} to base case")
                    failed_folders += 1
                    continue
                
                logging.info(f"\n--- Processing folder {i}/{total_folders}: {folder_name} (Base Case {base_case_id}) ---")
                
                if self.import_contingency_folder(folder_path, base_case_id):
                    successful_folders += 1
                else:
                    failed_folders += 1
                
                # Progress update every 5 folders
                if i % 5 == 0:
                    elapsed = time.time() - start_time
                    estimated_total = elapsed * total_folders / i
                    remaining = estimated_total - elapsed
                    
                    logging.info(f"\n[PROGRESS UPDATE]")
                    logging.info(f"   Folders: {i}/{total_folders} ({i/total_folders*100:.1f}%)")
                    logging.info(f"   Successful: {successful_folders}")
                    logging.info(f"   Failed: {failed_folders}")
                    logging.info(f"   Time elapsed: {elapsed/60:.1f} minutes")
                    logging.info(f"   Estimated remaining: {remaining/60:.1f} minutes")
            
            # Final summary
            total_time = time.time() - start_time
            logging.info(f"\n=== CONTINGENCY IMPORT COMPLETE ===")
            logging.info(f"   Total folders: {total_folders}")
            logging.info(f"   Successful: {successful_folders}")
            logging.info(f"   Failed: {failed_folders}")
            logging.info(f"   Success rate: {successful_folders/total_folders*100:.1f}%")
            logging.info(f"   Total time: {total_time/60:.1f} minutes")
            
            # Database summary
            self.cursor.execute("SELECT COUNT(*) FROM ContingencyCases")
            total_cases = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM ContingencyBusData")
            total_bus_records = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM ContingencyBranchData")
            total_branch_records = self.cursor.fetchone()[0]
            
            logging.info(f"\n=== DATABASE SUMMARY ===")
            logging.info(f"   Total contingency cases: {total_cases}")
            logging.info(f"   Total bus records: {total_bus_records:,}")
            logging.info(f"   Total branch records: {total_branch_records:,}")
            
            # Analysis summary
            self.cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN max_voltage_violation > 0 THEN 1 END) as voltage_violations,
                    COUNT(CASE WHEN max_thermal_violation > 0 THEN 1 END) as thermal_violations,
                    MAX(max_voltage_violation) as worst_voltage,
                    MAX(max_thermal_violation) as worst_thermal
                FROM ContingencyCases
            """)
            
            analysis_result = self.cursor.fetchone()
            if analysis_result:
                voltage_viol, thermal_viol, worst_voltage, worst_thermal = analysis_result
                logging.info(f"   Cases with voltage violations: {voltage_viol}")
                logging.info(f"   Cases with thermal violations: {thermal_viol}")
                logging.info(f"   Worst voltage violation: {worst_voltage:.4f} pu")
                logging.info(f"   Worst thermal violation: {worst_thermal:.2f} MVA")
            
            return successful_folders == total_folders
            
        except Exception as e:
            logging.error(f"Error during contingency import: {e}")
            return False
        finally:
            self.disconnect_database()

def main():
    """Main function to run optimized contingency import"""
    
    # Database configuration - UPDATE THESE VALUES
    DB_CONFIG = {
        'host': 'localhost',
        'port': '5432',
        'database': '118',  # Your database name
        'user': 'postgres',
        'password': 'pnnl'  # Your password
    }
    
    # Path to your contingency folders - UPDATE THIS PATH
    CONTINGENCY_ROOT_FOLDER = r"C:\Projects\dlr-database-project\contingency_118"
    
    # Verify folder exists
    if not os.path.exists(CONTINGENCY_ROOT_FOLDER):
        print(f"❌ Error: Folder '{CONTINGENCY_ROOT_FOLDER}' does not exist!")
        print("Please update the CONTINGENCY_ROOT_FOLDER path in the script.")
        return
    
    # Show configuration
    print("⚡ IEEE 118 Optimized Contingency Data Import")
    print("=" * 55)
    print(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    print(f"Contingency folders: {CONTINGENCY_ROOT_FOLDER}")
    print(f"Log file: contingency_import_optimized.log")
    print("Features: Sparse data import + Base case inheritance")
    
    # Count contingency folders/files
    contingency_folders = [f for f in Path(CONTINGENCY_ROOT_FOLDER).iterdir() if f.is_dir()]
    text_files = []
    
    if len(contingency_folders) == 0:
        # Check for flat file structure
        text_files = list(Path(CONTINGENCY_ROOT_FOLDER).glob('CA_*.txt'))
        if len(text_files) > 0:
            print(f"Found {len(text_files)} contingency files (flat structure)")
        else:
            print("❌ No contingency folders or files found! Please check the folder path.")
            return
    else:
        print(f"Found {len(contingency_folders)} contingency folders")
    
    if len(contingency_folders) == 0 and len(text_files) == 0:
        print("❌ No contingency folders or files found! Please check the folder path.")
        return
    
    # Show what will happen
    print(f"\nThis will:")
    print(f"  ✓ Import base cases from text files in Base_118 folder")
    print(f"  ✓ Import sparse contingency data from text files")
    print(f"  ✓ Inherit missing data from base cases automatically")
    print(f"  ✓ Calculate voltage/thermal violations")
    print(f"  ✓ Create complete dataset with all 118 buses per case")
    print(f"  ✓ Identify contingency elements (removed branches)")
    
    # Confirm before starting
    total_items = len(contingency_folders) if len(contingency_folders) > 0 else len(text_files)
    item_type = "contingency folders" if len(contingency_folders) > 0 else "contingency files"
    
    response = input(f"\n🚀 Start importing {total_items} {item_type}? (y/n): ")
    if response.lower() != 'y':
        print("Import cancelled.")
        return
    
    # Create importer and run
    importer = OptimizedContingencyImporter(DB_CONFIG)
    
    if not importer.connect_database():
        print("❌ Failed to connect to database")
        return
    
    # First, import base cases from Base_118 folder
    base_cases_folder = r"C:\Projects\dlr-database-project\Base_118"
    print(f"\n📊 Step 1: Loading base cases from {base_cases_folder}")
    
    if importer.import_base_cases_from_text(base_cases_folder):
        print("✅ Base cases loaded successfully!")
    else:
        print("❌ Failed to load base cases")
        importer.disconnect_database()
        return
    
    print(f"\n📊 Step 2: Starting contingency import at {datetime.now()}")
    print("Check 'contingency_import_optimized.log' for detailed progress...")
    print("This may take 30-60 minutes for 577 folders...")
    
    success = importer.import_all_contingency_folders(CONTINGENCY_ROOT_FOLDER)
    
    if success:
        print("\n✅ All contingency folders imported successfully!")
        
        # Step 3: Import SLR/DLR data if available
        slr_dlr_folder = r"C:\Projects\dlr-database-project\SLR_DLR_Data"  # Update this path
        if os.path.exists(slr_dlr_folder):
            print(f"\n📊 Step 3: Loading SLR/DLR Excel data from {slr_dlr_folder}")
            try:
                # Import the SLR/DLR loader
                from slr_dlr_loader import SLRDLRDataLoader
                
                slr_loader = SLRDLRDataLoader(DB_CONFIG)
                if slr_loader.connect_database():
                    slr_success = slr_loader.import_slr_dlr_folder(slr_dlr_folder)
                    slr_loader.disconnect_database()
                    
                    if slr_success:
                        print("✅ SLR/DLR data loaded successfully!")
                    else:
                        print("⚠️ SLR/DLR import had some issues. Check logs.")
                else:
                    print("❌ Failed to connect for SLR/DLR import")
            except ImportError as e:
                print(f"⚠️ SLR/DLR loader not available: {e}")
            except Exception as e:
                print(f"⚠️ Error loading SLR/DLR data: {e}")
        else:
            print(f"\n📝 Note: SLR/DLR folder not found at {slr_dlr_folder}")
            print("   Create this folder and add your SLR/DLR Excel files to include them in the import")
        
        print("\nYour IEEE 118 contingency analysis database is ready!")
    else:
        print("\n⚠️ Import completed with some errors. Check the log file.")
    
    importer.disconnect_database()
    print(f"Finished at {datetime.now()}")
    
    # Show next steps
    print(f"\n=== NEXT STEPS ===")
    print(f"You can now analyze your data using:")
    print(f"  • SELECT * FROM ContingencyImpactSummary;")
    print(f"  • SELECT * FROM MostVulnerableBuses;")
    print(f"  • SELECT * FROM MostCriticalBranches;")
    print(f"  • SELECT * FROM WorstCaseContingencies;")

def check_contingency_status():
    """Check current contingency data status"""
    
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
        
        print("📊 Contingency Data Status Check")
        print("=" * 40)
        
        # Check basic counts
        cursor.execute("""
            SELECT 
                'Contingency Cases' as metric,
                COUNT(*) as count
            FROM ContingencyCases
            UNION ALL
            SELECT 
                'Bus Records',
                COUNT(*)
            FROM ContingencyBusData
            UNION ALL
            SELECT 
                'Branch Records',
                COUNT(*)
            FROM ContingencyBranchData
        """)
        
        for metric, count in cursor.fetchall():
            print(f"{metric}: {count:,}")
        
        # Check processing status
        cursor.execute("""
            SELECT 
                processing_status,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ContingencyCases), 1) as percentage
            FROM ContingencyCases
            GROUP BY processing_status
            ORDER BY count DESC
        """)
        
        print(f"\nProcessing Status:")
        for status, count, percentage in cursor.fetchall():
            print(f"  {status}: {count:,} ({percentage}%)")
        
        # Check violations
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN max_voltage_violation > 0 THEN 1 END) as voltage_violations,
                COUNT(CASE WHEN max_thermal_violation > 0 THEN 1 END) as thermal_violations,
                ROUND(MAX(max_voltage_violation), 4) as worst_voltage,
                ROUND(MAX(max_thermal_violation), 2) as worst_thermal
            FROM ContingencyCases
        """)
        
        result = cursor.fetchone()
        if result:
            voltage_viol, thermal_viol, worst_voltage, worst_thermal = result
            print(f"\nViolation Summary:")
            print(f"  Cases with voltage violations: {voltage_viol:,}")
            print(f"  Cases with thermal violations: {thermal_viol:,}")
            print(f"  Worst voltage violation: {worst_voltage} pu")
            print(f"  Worst thermal violation: {worst_thermal} MVA")
        
        # Check base case coverage
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT base_case_id) as base_cases_with_contingencies,
                (SELECT COUNT(*) FROM BaseCaseFiles) as total_base_cases
        """)
        
        contingency_bases, total_bases = cursor.fetchone()
        print(f"\nBase Case Coverage:")
        print(f"  Base cases with contingencies: {contingency_bases}/{total_bases}")
        print(f"  Coverage: {contingency_bases/total_bases*100:.1f}%")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking status: {e}")

def test_contingency_views():
    """Test the contingency analysis views"""
    
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
        
        print("🔍 Testing Contingency Analysis Views")
        print("=" * 45)
        
        # Test ContingencyImpactSummary
        cursor.execute("SELECT * FROM ContingencyImpactSummary LIMIT 5")
        results = cursor.fetchall()
        print(f"ContingencyImpactSummary: {len(results)} base cases")
        
        # Test MostVulnerableBuses
        cursor.execute("SELECT * FROM MostVulnerableBuses LIMIT 5")
        results = cursor.fetchall()
        print(f"MostVulnerableBuses: {len(results)} vulnerable buses found")
        
        # Test MostCriticalBranches
        cursor.execute("SELECT * FROM MostCriticalBranches LIMIT 5")
        results = cursor.fetchall()
        print(f"MostCriticalBranches: {len(results)} critical branches found")
        
        # Test WorstCaseContingencies
        cursor.execute("SELECT * FROM WorstCaseContingencies LIMIT 5")
        results = cursor.fetchall()
        print(f"WorstCaseContingencies: {len(results)} worst cases identified")
        
        print("\n✅ All views are working correctly!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error testing views: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            check_contingency_status()
        elif sys.argv[1] == "test":
            test_contingency_views()
        else:
            print("Usage:")
            print("  python optimized_contingency_import.py        # Import all contingency data")
            print("  python optimized_contingency_import.py status # Check current data status")
            print("  python optimized_contingency_import.py test   # Test analysis views")
    else:
        main()