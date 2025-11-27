import pandas as pd
import psycopg2
from pathlib import Path
import re
import logging
from datetime import datetime
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production_loader.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class ProductionContingencyLoader:
    def __init__(self, data_folder, db_config):
        self.data_folder = Path(data_folder)
        self.db_config = db_config
        self.conn = None
        self.cursor = None
        
    def connect_database(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            logging.info("Database connection established")
            return True
        except Exception as e:
            logging.error(f"Database connection failed: {e}")
            return False
    
    def create_schema(self):
        """Create database schema if it doesn't exist"""
        try:
            logging.info("Creating database schema...")
            
            # Create BaseCases table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS BaseCases (
                    base_case_id SERIAL PRIMARY KEY,
                    case_number INTEGER UNIQUE NOT NULL,
                    filename VARCHAR(255),
                    case_name VARCHAR(255),
                    folder_name VARCHAR(255),
                    buses_count INTEGER DEFAULT 0,
                    processing_status VARCHAR(50) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create BaseBusData table
            self.cursor.execute("""
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
            
            # Create ContingencyCases table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS ContingencyCases (
                    contingency_case_id SERIAL PRIMARY KEY,
                    base_case_id INTEGER REFERENCES BaseCases(base_case_id),
                    case_number INTEGER NOT NULL,
                    filename VARCHAR(255),
                    case_name VARCHAR(255),
                    contingency_element VARCHAR(255),
                    folder_name VARCHAR(255),
                    buses_count INTEGER DEFAULT 0,
                    processing_status VARCHAR(50) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(base_case_id, case_number)
                )
            """)
            
            # Create ContingencyBusData table
            self.cursor.execute("""
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
            
            self.conn.commit()
            logging.info("Database schema created successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error creating schema: {e}")
            self.conn.rollback()
            return False

    def parse_base_case_file(self, file_path):
        """Parse a base case file"""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Skip first two lines (headers)
            data_lines = [line.strip() for line in lines[2:] if line.strip()]
            
            if not data_lines:
                return None
            
            # Parse and handle duplicates
            data_dict = {}
            for line in data_lines:
                parts = line.split()
                if len(parts) >= 8:
                    try:
                        bus_number = int(float(parts[0]))
                        row = [float(p) for p in parts[:8]]
                        data_dict[bus_number] = row
                    except ValueError:
                        continue
            
            if not data_dict:
                return None
                
            return pd.DataFrame(list(data_dict.values()), 
                              columns=['BUS_NUMBER', 'VM', 'VA', 'BASE_KV', 'PG', 'QG', 'PD', 'QD'])
            
        except Exception as e:
            logging.error(f"Error parsing base case file {file_path}: {e}")
            return None

    def parse_contingency_file(self, file_path):
        """Parse a contingency case file"""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Skip first line only for contingency files
            data_lines = [line.strip() for line in lines[1:] if line.strip()]
            
            if not data_lines:
                return None
            
            # Parse and handle duplicates
            data_dict = {}
            for line in data_lines:
                parts = line.split()
                if len(parts) >= 7:
                    try:
                        bus_number = int(float(parts[0]))
                        if len(parts) >= 8:
                            row = [float(p) for p in parts[:8]]
                        else:
                            # Insert default BASE_KV if missing
                            row = [float(parts[0]), float(parts[1]), float(parts[2]), 138.0,
                                   float(parts[3]), float(parts[4]), float(parts[5]), float(parts[6])]
                        data_dict[bus_number] = row
                    except ValueError:
                        continue
            
            if not data_dict:
                return None
                
            return pd.DataFrame(list(data_dict.values()), 
                              columns=['BUS_NUMBER', 'VM', 'VA', 'BASE_KV', 'PG', 'QG', 'PD', 'QD'])
            
        except Exception as e:
            logging.error(f"Error parsing contingency file {file_path}: {e}")
            return None

    def import_base_cases(self):
        """Import all base case files"""
        base_folder = self.data_folder / "Base_118"
        if not base_folder.exists():
            logging.warning(f"Base folder {base_folder} does not exist")
            return False
        
        base_files = list(base_folder.glob("*.txt"))
        total_files = len(base_files)
        
        if total_files == 0:
            logging.warning("No base case files found")
            return True
        
        logging.info(f"Found {total_files} base case files to import")
        
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        for i, file_path in enumerate(base_files, 1):
            try:
                # Extract case number from filename (it's the last number before .txt)
                match = re.search(r'BASE_\d+_bus\d+_(\d+)\.txt', file_path.name, re.IGNORECASE)
                if not match:
                    # Try alternative pattern
                    match = re.search(r'BASE.*?_(\d+)\.txt', file_path.name, re.IGNORECASE)
                if not match:
                    logging.warning(f"Could not extract case number from {file_path.name}")
                    error_count += 1
                    continue
                
                case_number = int(match.group(1))
                
                # Check if already completed
                self.cursor.execute("""
                    SELECT processing_status FROM BaseCases WHERE case_number = %s
                """, (case_number,))
                result = self.cursor.fetchone()
                if result and result[0] == 'completed':
                    logging.info(f"Base case {case_number} already completed - skipping")
                    skipped_count += 1
                    continue
                
                # Parse file
                df = self.parse_base_case_file(file_path)
                if df is None:
                    logging.error(f"Failed to parse {file_path.name}")
                    error_count += 1
                    continue
                
                # Create/update base case record
                self.cursor.execute("""
                    INSERT INTO BaseCases (case_number, filename, case_name, folder_name, processing_status)
                    VALUES (%s, %s, %s, %s, 'processing')
                    ON CONFLICT (case_number) DO UPDATE SET
                        filename = EXCLUDED.filename,
                        processing_status = EXCLUDED.processing_status
                    RETURNING base_case_id
                """, (case_number, file_path.name, f"Base Case {case_number}", "Base_118"))
                
                base_case_id = self.cursor.fetchone()[0]
                
                # Import bus data
                bus_records = []
                for _, row in df.iterrows():
                    bus_records.append((
                        base_case_id,
                        int(row['BUS_NUMBER']),
                        float(row['VM']),
                        float(row['VA']),
                        float(row['BASE_KV']),
                        float(row['PG']),
                        float(row['QG']),
                        float(row['PD']),
                        float(row['QD'])
                    ))
                
                # Clear and insert
                self.cursor.execute("DELETE FROM BaseBusData WHERE base_case_id = %s", (base_case_id,))
                self.cursor.executemany("""
                    INSERT INTO BaseBusData 
                    (base_case_id, bus_number, vm, va, base_kv, pg, qg, pd, qd)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, bus_records)
                
                # Update status
                self.cursor.execute("""
                    UPDATE BaseCases 
                    SET buses_count = %s, processing_status = 'completed'
                    WHERE base_case_id = %s
                """, (len(bus_records), base_case_id))
                
                self.conn.commit()
                imported_count += 1
                
                if i % 50 == 0 or i == total_files:
                    logging.info(f"Progress: {i}/{total_files} files processed "
                               f"(imported: {imported_count}, skipped: {skipped_count}, errors: {error_count})")
                
            except Exception as e:
                logging.error(f"Error processing base case {file_path.name}: {e}")
                self.conn.rollback()
                error_count += 1
                continue
        
        logging.info(f"Base case import completed: {imported_count} imported, {skipped_count} skipped, {error_count} errors")
        return True

    def import_contingency_cases(self):
        """Import all contingency case files"""
        contingency_folder = self.data_folder / "contingency_118"
        if not contingency_folder.exists():
            logging.warning(f"Contingency folder {contingency_folder} does not exist")
            return False
        
        contingency_files = list(contingency_folder.glob("*.txt"))
        total_files = len(contingency_files)
        
        if total_files == 0:
            logging.warning("No contingency case files found")
            return True
        
        # Get all base cases for linking
        self.cursor.execute("SELECT case_number, base_case_id FROM BaseCases WHERE processing_status = 'completed'")
        base_cases = dict(self.cursor.fetchall())
        if not base_cases:
            logging.error("No completed base cases found. Please import base cases first.")
            return False
        
        logging.info(f"Found {total_files} contingency case files to import")
        logging.info(f"Available base cases: {list(base_cases.keys())}")
        
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        for i, file_path in enumerate(contingency_files, 1):
            try:
                # Extract case number from filename (it's the last number before .txt)
                match = re.search(r'CA_\d+_bus\d+_(\d+)\.txt', file_path.name, re.IGNORECASE)
                if not match:
                    # Try alternative pattern
                    match = re.search(r'CA.*?_(\d+)\.txt', file_path.name, re.IGNORECASE)
                if not match:
                    logging.warning(f"Could not extract case number from {file_path.name}")
                    error_count += 1
                    continue
                
                case_number = int(match.group(1))
                
                # Find matching base case
                if case_number not in base_cases:
                    logging.warning(f"No matching base case found for contingency case {case_number}")
                    error_count += 1
                    continue
                
                base_case_id = base_cases[case_number]
                
                # Check if already completed
                self.cursor.execute("""
                    SELECT processing_status FROM ContingencyCases 
                    WHERE base_case_id = %s AND case_number = %s
                """, (base_case_id, case_number))
                result = self.cursor.fetchone()
                if result and result[0] == 'completed':
                    logging.info(f"Contingency case {case_number} already completed - skipping")
                    skipped_count += 1
                    continue
                
                # Parse file
                df = self.parse_contingency_file(file_path)
                if df is None:
                    logging.error(f"Failed to parse {file_path.name}")
                    error_count += 1
                    continue
                
                # Create/update contingency case record
                self.cursor.execute("""
                    INSERT INTO ContingencyCases 
                    (base_case_id, case_number, filename, case_name, contingency_element, folder_name, processing_status)
                    VALUES (%s, %s, %s, %s, %s, %s, 'processing')
                    ON CONFLICT (base_case_id, case_number) DO UPDATE SET
                        filename = EXCLUDED.filename,
                        processing_status = EXCLUDED.processing_status
                    RETURNING contingency_case_id
                """, (base_case_id, case_number, file_path.name, f"Contingency Case {case_number}", 
                      f"Contingency {case_number}", "contingency_118"))
                
                contingency_case_id = self.cursor.fetchone()[0]
                
                # Import bus data
                bus_records = []
                for _, row in df.iterrows():
                    bus_records.append((
                        contingency_case_id,
                        int(row['BUS_NUMBER']),
                        float(row['VM']),
                        float(row['VA']),
                        float(row['BASE_KV']),
                        float(row['PG']),
                        float(row['QG']),
                        float(row['PD']),
                        float(row['QD'])
                    ))
                
                # Clear and insert
                self.cursor.execute("DELETE FROM ContingencyBusData WHERE contingency_case_id = %s", (contingency_case_id,))
                self.cursor.executemany("""
                    INSERT INTO ContingencyBusData 
                    (contingency_case_id, bus_number, vm, va, base_kv, pg, qg, pd, qd)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, bus_records)
                
                # Update status
                self.cursor.execute("""
                    UPDATE ContingencyCases 
                    SET buses_count = %s, processing_status = 'completed'
                    WHERE contingency_case_id = %s
                """, (len(bus_records), contingency_case_id))
                
                self.conn.commit()
                imported_count += 1
                
                if i % 25 == 0 or i == total_files:
                    logging.info(f"Progress: {i}/{total_files} files processed "
                               f"(imported: {imported_count}, skipped: {skipped_count}, errors: {error_count})")
                
            except Exception as e:
                logging.error(f"Error processing contingency case {file_path.name}: {e}")
                self.conn.rollback()
                error_count += 1
                continue
        
        logging.info(f"Contingency case import completed: {imported_count} imported, {skipped_count} skipped, {error_count} errors")
        return True

    def get_import_summary(self):
        """Get summary of imported data"""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM BaseCases WHERE processing_status = 'completed'")
            base_cases = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM ContingencyCases WHERE processing_status = 'completed'")
            contingency_cases = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM BaseBusData")
            base_bus_data = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM ContingencyBusData")
            contingency_bus_data = self.cursor.fetchone()[0]
            
            return {
                'base_cases': base_cases,
                'contingency_cases': contingency_cases,
                'base_bus_data': base_bus_data,
                'contingency_bus_data': contingency_bus_data
            }
        except Exception as e:
            logging.error(f"Error getting summary: {e}")
            return None

    def run_full_import(self):
        """Run the complete import process"""
        start_time = time.time()
        logging.info("Starting full import process...")
        
        try:
            # Connect to database
            if not self.connect_database():
                return False
            
            # Create schema
            if not self.create_schema():
                return False
            
            # Import base cases
            logging.info("=" * 50)
            logging.info("STARTING BASE CASE IMPORT")
            logging.info("=" * 50)
            if not self.import_base_cases():
                logging.error("Base case import failed")
                return False
            
            # Import contingency cases
            logging.info("=" * 50)
            logging.info("STARTING CONTINGENCY CASE IMPORT")
            logging.info("=" * 50)
            if not self.import_contingency_cases():
                logging.error("Contingency case import failed")
                return False
            
            # Get final summary
            summary = self.get_import_summary()
            if summary:
                elapsed_time = time.time() - start_time
                logging.info("=" * 50)
                logging.info("IMPORT COMPLETED SUCCESSFULLY!")
                logging.info("=" * 50)
                logging.info(f"Base cases imported: {summary['base_cases']}")
                logging.info(f"Contingency cases imported: {summary['contingency_cases']}")
                logging.info(f"Base bus data records: {summary['base_bus_data']}")
                logging.info(f"Contingency bus data records: {summary['contingency_bus_data']}")
                logging.info(f"Total elapsed time: {elapsed_time:.2f} seconds")
            
            return True
            
        except Exception as e:
            logging.error(f"Error in full import: {e}")
            return False
        finally:
            if self.conn:
                self.conn.close()
                logging.info("Database connection closed")

if __name__ == "__main__":
    # Database configuration
    DB_CONFIG = {
        'host': 'localhost',
        'database': '118',
        'user': 'postgres',
        'password': 'pnnl'
    }
    
    # Data folder path
    DATA_FOLDER = r"C:\Projects\dlr-database-project"
    
    # Create and run the loader
    loader = ProductionContingencyLoader(DATA_FOLDER, DB_CONFIG)
    success = loader.run_full_import()
    
    if success:
        print("\n🎉 ALL DATA LOADED SUCCESSFULLY!")
        print("Check production_loader.log for detailed progress information")
    else:
        print("\n❌ Import failed. Check production_loader.log for error details")