import pandas as pd
import psycopg2
import os
import time
from pathlib import Path
import logging
from datetime import datetime
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('contingency_import_text.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class TextContingencyImporter:
    def __init__(self, db_config):
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
    
    def disconnect_database(self):
        """Disconnect from database"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logging.info("Database connection closed")
    
    def get_base_case_id(self):
        """Get a base case ID - we'll use case_id = 42 to match the corrective actions"""
        try:
            # First try to get case_id = 42 (matches the corrective actions we imported)
            self.cursor.execute("SELECT case_id FROM base_cases WHERE case_id = 42")
            result = self.cursor.fetchone()
            if result:
                logging.info(f"Using base case ID 42 for contingency analysis")
                return result[0]
            
            # If case 42 doesn't exist, get any available base case
            self.cursor.execute("SELECT case_id FROM base_cases ORDER BY case_id LIMIT 1")
            result = self.cursor.fetchone()
            if result:
                logging.info(f"Using base case ID {result[0]} for contingency analysis")
                return result[0]
            else:
                logging.error("No base case found in database!")
                return None
        except Exception as e:
            logging.error(f"Error getting base case ID: {e}")
            return None
    
    def contingency_case_exists(self, base_case_id, case_number):
        """Check if a contingency case already exists and is completed"""
        try:
            self.cursor.execute("""
                SELECT contingency_case_id, processing_status 
                FROM ContingencyCases 
                WHERE base_case_id = %s AND case_number = %s
            """, (base_case_id, case_number))
            
            result = self.cursor.fetchone()
            if result:
                case_id, status = result
                return True, case_id, status
            return False, None, None
            
        except Exception as e:
            logging.error(f"Error checking contingency case existence: {e}")
            return False, None, None

    def parse_contingency_text_file(self, file_path):
        """Parse the text file format and extract bus and branch data"""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Skip the first line (just contains "1")
            data_lines = [line.strip() for line in lines[1:] if line.strip()]
            
            buses_data = []
            branches_data = []
            
            # First 118 lines are bus data
            for i in range(min(118, len(data_lines))):
                line = data_lines[i]
                # Parse space-separated values
                parts = line.split()
                if len(parts) >= 7:
                    buses_data.append({
                        'bus_number': int(parts[0]),
                        'vm': float(parts[1]),
                        'va': float(parts[2]),
                        'pg': float(parts[3]),
                        'qg': float(parts[4]),
                        'pd': float(parts[5]),
                        'qd': float(parts[6])
                    })
            
            # Next 186 lines are branch data (starting from line 119, taking only first 186 branches)
            branch_start = 118
            expected_branches = 186
            for i in range(branch_start, min(branch_start + expected_branches, len(data_lines))):
                line = data_lines[i]
                parts = line.split()
                if len(parts) >= 3:
                    branches_data.append({
                        'branch_number': int(parts[0]),
                        'pf': float(parts[1]),
                        'qf': float(parts[2])
                    })
            
            logging.info(f"Parsed {len(buses_data)} bus records and {len(branches_data)} branch records from {Path(file_path).name}")
            return buses_data, branches_data
            
        except Exception as e:
            logging.error(f"Error parsing text file {file_path}: {e}")
            return [], []

    def create_contingency_case(self, base_case_id, case_number, file_path):
        """Create contingency case and import data from text file"""
        filename = os.path.basename(file_path)
        
        # Check if case already exists and is completed
        exists, existing_id, status = self.contingency_case_exists(base_case_id, case_number)
        if exists and status == 'completed':
            logging.info(f"Contingency case {filename} already exists and is completed - skipping")
            return True, (118, 186)
        
        try:
            case_name = f"Contingency Case {case_number}"
            contingency_element = f"Contingency {case_number}"
            
            # Parse the text file
            buses_data, branches_data = self.parse_contingency_text_file(file_path)
            
            if not buses_data and not branches_data:
                logging.error(f"No valid data found in {filename}")
                return False, (0, 0)
            
            # Create case record
            self.cursor.execute("""
                INSERT INTO contingencycases 
                (base_case_id, case_number, filename, case_name, contingency_element, processing_status) 
                VALUES (%s, %s, %s, %s, %s, %s) 
                ON CONFLICT (base_case_id, case_number) DO UPDATE SET
                    filename = EXCLUDED.filename,
                    case_name = EXCLUDED.case_name,
                    contingency_element = EXCLUDED.contingency_element,
                    processing_status = EXCLUDED.processing_status
                RETURNING contingency_case_id
            """, (base_case_id, case_number, filename, case_name, contingency_element, 'processing'))
            
            contingency_case_id = self.cursor.fetchone()[0]
            
            # Import bus data
            buses_imported = self.import_bus_data(contingency_case_id, base_case_id, buses_data)
            
            # Import branch data
            branches_imported = self.import_branch_data(contingency_case_id, base_case_id, branches_data)
            
            # Populate complete data with base case inheritance and calculate violations
            self.cursor.execute("""
                SELECT populate_complete_contingency_data(%s, %s)
            """, (contingency_case_id, base_case_id))
            
            # Identify contingency element (removed branch)
            self.cursor.execute("""
                SELECT identify_contingency_element(%s, %s)
            """, (contingency_case_id, base_case_id))
            
            contingency_element = self.cursor.fetchone()[0]
            
            # Update case with final counts and contingency element
            self.cursor.execute("""
                UPDATE contingencycases 
                SET buses_count = 118, 
                    branches_count = %s,
                    contingency_element = %s,
                    processing_status = 'completed'
                WHERE contingency_case_id = %s
            """, (branches_imported, contingency_element, contingency_case_id))
            
            self.conn.commit()
            logging.info(f"Successfully imported {filename}: {buses_imported} buses, {branches_imported} branches")
            return True, (buses_imported, branches_imported)
            
        except Exception as e:
            logging.error(f"Error importing contingency case {filename}: {e}")
            self.conn.rollback()
            return False, (0, 0)
    
    def import_bus_data(self, contingency_case_id, base_case_id, buses_data):
        """Import bus data into ContingencyBusData table"""
        inserted_count = 0
        
        for bus_data in buses_data:
            try:
                self.cursor.execute("""
                    INSERT INTO contingencybusdata 
                    (contingency_case_id, base_case_id, bus_number, vm, va, base_kv, pg, qg, pd, qd) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (contingency_case_id, bus_number) DO UPDATE SET
                        vm = EXCLUDED.vm,
                        va = EXCLUDED.va,
                        base_kv = EXCLUDED.base_kv,
                        pg = EXCLUDED.pg,
                        qg = EXCLUDED.qg,
                        pd = EXCLUDED.pd,
                        qd = EXCLUDED.qd
                """, (
                    contingency_case_id, base_case_id, bus_data['bus_number'],
                    bus_data['vm'], bus_data['va'], bus_data.get('base_kv', 138.0),
                    bus_data['pg'], bus_data['qg'], bus_data['pd'], bus_data['qd']
                ))
                inserted_count += 1
            except Exception as e:
                logging.warning(f"Failed to insert bus {bus_data['bus_number']}: {e}")
        
        return inserted_count
    
    def import_branch_data(self, contingency_case_id, base_case_id, branches_data):
        """Import branch data into ContingencyBranchData table"""
        inserted_count = 0
        
        for branch_data in branches_data:
            try:
                # Map branch number to from_bus, to_bus, circuit_id using base case data
                self.cursor.execute("""
                    SELECT from_bus, to_bus, circuit_id 
                    FROM base_branches 
                    WHERE case_id = %s 
                    ORDER BY from_bus, to_bus, circuit_id 
                    LIMIT 1 OFFSET %s
                """, (base_case_id, branch_data['branch_number'] - 1))
                
                result = self.cursor.fetchone()
                if not result:
                    logging.warning(f"Could not find base branch for branch number {branch_data['branch_number']}")
                    continue
                
                from_bus, to_bus, circuit_id = result
                
                # Calculate MVA flow
                pf = branch_data['pf'] or 0
                qf = branch_data['qf'] or 0
                mva = (pf**2 + qf**2)**0.5 if pf != 0 or qf != 0 else 0
                
                self.cursor.execute("""
                    UPDATE contingencybranchdata 
                    SET pf = %s, qf = %s, mva = %s
                    WHERE contingency_case_id = %s 
                    AND from_bus = %s AND to_bus = %s AND circuit_id = %s
                """, (pf, qf, mva, contingency_case_id, from_bus, to_bus, circuit_id))
                
                if self.cursor.rowcount > 0:
                    inserted_count += 1
                else:
                    logging.warning(f"No existing record found to update for branch {from_bus}-{to_bus}-{circuit_id}")
                    
            except Exception as e:
                logging.warning(f"Failed to update branch {branch_data['branch_number']}: {e}")
        
        return inserted_count
    
    def import_all_contingency_files(self, contingency_folder):
        """Import all contingency text files"""
        if not self.connect_database():
            return False
        
        try:
            # Get base case ID
            base_case_id = self.get_base_case_id()
            if not base_case_id:
                logging.error("No base case found!")
                return False
            
            # Get all text files
            text_files = list(Path(contingency_folder).glob('CA_0_bus118_*.txt'))
            total_files = len(text_files)
            
            logging.info(f"Found {total_files} contingency files to process")
            
            successful_cases = 0
            failed_cases = 0
            start_time = time.time()
            
            for i, file_path in enumerate(text_files, 1):
                filename = file_path.name
                
                # Extract case number from filename (CA_0_bus118_42.txt -> 42)
                match = re.search(r'CA_0_bus118_(\d+)\.txt', filename)
                if not match:
                    logging.warning(f"Could not extract case number from {filename}")
                    failed_cases += 1
                    continue
                
                case_number = int(match.group(1))
                
                logging.info(f"Processing {i}/{total_files}: {filename} (Case {case_number})")
                
                success, (buses, branches) = self.create_contingency_case(
                    base_case_id, case_number, file_path
                )
                
                if success:
                    successful_cases += 1
                else:
                    failed_cases += 1
                
                # Progress update every 50 files
                if i % 50 == 0:
                    elapsed = time.time() - start_time
                    estimated_total = elapsed * total_files / i
                    remaining = estimated_total - elapsed
                    
                    logging.info(f"\n[PROGRESS UPDATE]")
                    logging.info(f"   Files: {i}/{total_files} ({i/total_files*100:.1f}%)")
                    logging.info(f"   Successful: {successful_cases}")
                    logging.info(f"   Failed: {failed_cases}")
                    logging.info(f"   Time elapsed: {elapsed/60:.1f} minutes")
                    logging.info(f"   Estimated remaining: {remaining/60:.1f} minutes")
            
            # Final summary
            total_time = time.time() - start_time
            logging.info(f"\n=== CONTINGENCY IMPORT COMPLETE ===")
            logging.info(f"   Total files: {total_files}")
            logging.info(f"   Successful: {successful_cases}")
            logging.info(f"   Failed: {failed_cases}")
            logging.info(f"   Success rate: {successful_cases/total_files*100:.1f}%")
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
                WHERE processing_status = 'completed'
            """)
            
            analysis_result = self.cursor.fetchone()
            if analysis_result:
                voltage_viol, thermal_viol, worst_voltage, worst_thermal = analysis_result
                logging.info(f"\n=== VIOLATION ANALYSIS ===")
                logging.info(f"   Cases with voltage violations: {voltage_viol}")
                logging.info(f"   Cases with thermal violations: {thermal_viol}")
                logging.info(f"   Worst voltage violation: {worst_voltage:.4f} pu")
                logging.info(f"   Worst thermal violation: {worst_thermal:.2f} MVA")
            
            return successful_cases == total_files
            
        except Exception as e:
            logging.error(f"Error during contingency import: {e}")
            return False
        finally:
            self.disconnect_database()

def main():
    """Main function to run text contingency import"""
    
    # Database configuration
    DB_CONFIG = {
        'host': 'localhost',
        'port': '5432',
        'database': '118',
        'user': 'postgres',
        'password': 'pnnl'
    }
    
    # Path to contingency text files
    CONTINGENCY_FOLDER = r"C:\Projects\dlr-database-project\contingency_118"
    
    # Verify folder exists
    if not os.path.exists(CONTINGENCY_FOLDER):
        print(f"❌ Error: Folder '{CONTINGENCY_FOLDER}' does not exist!")
        return
    
    # Show configuration
    print("⚡ IEEE 118 Text Contingency Data Import")
    print("=" * 45)
    print(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    print(f"Contingency files: {CONTINGENCY_FOLDER}")
    print(f"Log file: contingency_import_text.log")
    print("Features: Text file parsing + Base case inheritance + Violation analysis")
    
    # Count contingency files
    text_files = list(Path(CONTINGENCY_FOLDER).glob('CA_0_bus118_*.txt'))
    print(f"Found {len(text_files)} contingency text files")
    
    if len(text_files) == 0:
        print("❌ No contingency text files found! Please check the folder path.")
        return
    
    # Show what will happen
    print(f"\nThis will:")
    print(f"  ✓ Parse {len(text_files)} text files with bus/branch data")
    print(f"  ✓ Import contingency data with complete 118-bus, 186-branch datasets")
    print(f"  ✓ Inherit missing data from base case automatically")
    print(f"  ✓ Calculate voltage violations (0.95-1.05 pu limits)")
    print(f"  ✓ Calculate thermal violations (MVA > rating)")
    print(f"  ✓ Identify contingency elements (removed branches)")
    
    # Confirm before starting (auto-confirm for batch processing)
    print(f"\n🚀 Starting import of {len(text_files)} contingency files automatically...")
    # response = input(f"\n🚀 Start importing {len(text_files)} contingency files? (y/n): ")
    # if response.lower() != 'y':
    #     print("Import cancelled.")
    #     return
    
    # Create importer and run
    importer = TextContingencyImporter(DB_CONFIG)
    
    print(f"\n📊 Starting text contingency import at {datetime.now()}")
    print("Check 'contingency_import_text.log' for detailed progress...")
    print("This may take 10-20 minutes for 577 files...")
    
    success = importer.import_all_contingency_files(CONTINGENCY_FOLDER)
    
    if success:
        print("\n✅ All contingency files imported successfully!")
        print("Your IEEE 118 contingency analysis database is ready!")
    else:
        print("\n⚠️ Import completed with some errors. Check the log file.")
    
    print(f"Finished at {datetime.now()}")
    
    # Show next steps
    print(f"\n=== NEXT STEPS ===")
    print(f"You can now analyze your data using:")
    print(f"  • SELECT * FROM ContingencyViolationSummary LIMIT 10;")
    print(f"  • SELECT * FROM WorstContingencies LIMIT 10;")
    print(f"  • SELECT case_number, contingency_element, max_thermal_violation")
    print(f"    FROM ContingencyCases WHERE max_thermal_violation > 0")
    print(f"    ORDER BY max_thermal_violation DESC LIMIT 10;")

if __name__ == "__main__":
    main()