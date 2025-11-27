import pandas as pd
import psycopg2
import os
import time
from pathlib import Path
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ieee118_import.log'),
        logging.StreamHandler()
    ]
)

class IEEE118DataImporter:
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
    
    def validate_excel_file(self, file_path):
        """Validate Excel file structure"""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return False, "File does not exist"
            
            # Try to read Excel file
            excel_file = pd.ExcelFile(file_path)
            
            # Check for required sheets (adjust names if different)
            required_sheets = ['buses', 'branches']  # Change these if your sheet names are different
            available_sheets = excel_file.sheet_names
            
            # Try common variations of sheet names
            buses_sheet = None
            branches_sheet = None
            
            for sheet in available_sheets:
                sheet_lower = sheet.lower()
                if 'bus' in sheet_lower:
                    buses_sheet = sheet
                elif 'branch' in sheet_lower or 'line' in sheet_lower:
                    branches_sheet = sheet
            
            if buses_sheet is None:
                return False, f"No buses sheet found. Available: {available_sheets}"
            if branches_sheet is None:
                return False, f"No branches sheet found. Available: {available_sheets}"
            
            return True, (buses_sheet, branches_sheet)
            
        except Exception as e:
            return False, f"Excel validation error: {e}"
    
    def import_single_file(self, file_path, scenario_id):
        """Import a single Excel file"""
        filename = os.path.basename(file_path)
        start_time = time.time()
        
        try:
            # Validate file
            is_valid, result = self.validate_excel_file(file_path)
            if not is_valid:
                logging.error(f"Validation failed for {filename}: {result}")
                return False
            
            buses_sheet, branches_sheet = result
            logging.info(f"Processing {filename} - Buses: '{buses_sheet}', Branches: '{branches_sheet}'")
            
            # Insert base case file record
            case_name = f"IEEE 118 Case {scenario_id}"
            self.cursor.execute("""
                INSERT INTO BaseCaseFiles (filename, scenario_id, case_name, file_path, processing_status) 
                VALUES (%s, %s, %s, %s, 'processing') 
                RETURNING Id
            """, (filename, scenario_id, case_name, str(file_path)))
            
            file_id = self.cursor.fetchone()[0]
            self.conn.commit()
            
            # Read and import buses data
            buses_count = self.import_buses_data(file_path, buses_sheet, file_id)
            if buses_count == 0:
                raise Exception("No buses data imported")
            
            # Read and import branches data
            branches_count = self.import_branches_data(file_path, branches_sheet, file_id)
            if branches_count == 0:
                raise Exception("No branches data imported")
            
            # Update case statistics
            processing_time = time.time() - start_time
            self.cursor.execute("SELECT update_case_statistics(%s)", (file_id,))
            self.cursor.execute("""
                UPDATE BaseCaseFiles 
                SET processing_time = %s, processing_status = 'completed' 
                WHERE Id = %s
            """, (processing_time, file_id))
            
            self.conn.commit()
            
            logging.info(f"✅ {filename} - Buses: {buses_count}, Branches: {branches_count}, Time: {processing_time:.2f}s")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to process {filename}: {e}")
            self.conn.rollback()
            
            # Mark as failed
            try:
                self.cursor.execute("""
                    UPDATE BaseCaseFiles 
                    SET processing_status = 'failed' 
                    WHERE filename = %s
                """, (filename,))
                self.conn.commit()
            except:
                pass
            
            return False
    
    def import_buses_data(self, file_path, sheet_name, file_id):
        """Import buses data from Excel sheet"""
        try:
            # Read buses sheet
            buses_df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Clean column names (remove spaces, make uppercase)
            buses_df.columns = buses_df.columns.str.strip().str.upper()
            
            # Map possible column name variations
            column_mapping = {
                'BUS_NUMBER': ['BUS_NUMBER', 'BUS', 'BUS_NUM', 'BUSNUM', 'BUS NUMBER'],
                'VM': ['VM', 'V_MAG', 'VMAG', 'VOLTAGE_MAG', 'V'],
                'VA': ['VA', 'V_ANG', 'VANG', 'VOLTAGE_ANG', 'ANGLE'],
                'BASE_KV': ['BASE_KV', 'BASEKV', 'BASE_VOLTAGE', 'KV', 'BASE KV'],
                'PG': ['PG', 'P_GEN', 'PGEN', 'GEN_P', 'P_GENERATION'],
                'QG': ['QG', 'Q_GEN', 'QGEN', 'GEN_Q', 'Q_GENERATION'],
                'PD': ['PD', 'P_LOAD', 'PLOAD', 'LOAD_P', 'P_DEMAND'],
                'QD': ['QD', 'Q_LOAD', 'QLOAD', 'LOAD_Q', 'Q_DEMAND']
            }
            
            # Standardize column names
            for standard_col, variations in column_mapping.items():
                for col in buses_df.columns:
                    if col in variations:
                        buses_df.rename(columns={col: standard_col}, inplace=True)
                        break
            
            # Ensure required columns exist
            required_cols = ['BUS_NUMBER']
            for col in required_cols:
                if col not in buses_df.columns:
                    raise Exception(f"Required column '{col}' not found in buses sheet")
            
            # Fill missing columns with defaults
            default_values = {
                'VM': 1.0, 'VA': 0.0, 'BASE_KV': 138.0,
                'PG': 0.0, 'QG': 0.0, 'PD': 0.0, 'QD': 0.0
            }
            
            for col, default_val in default_values.items():
                if col not in buses_df.columns:
                    buses_df[col] = default_val
                else:
                    buses_df[col] = buses_df[col].fillna(default_val)
            
            # Insert data
            inserted_count = 0
            for idx, row in buses_df.iterrows():
                try:
                    self.cursor.execute("""
                        INSERT INTO BaseBusData 
                        (file_id, Id, BUS_NUMBER, VM, VA, BASE_KV, PG, QG, PD, QD) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        file_id,
                        idx + 1,  # Use row index as Id
                        int(row['BUS_NUMBER']),
                        float(row['VM']),
                        float(row['VA']),
                        float(row['BASE_KV']),
                        float(row['PG']),
                        float(row['QG']),
                        float(row['PD']),
                        float(row['QD'])
                    ))
                    inserted_count += 1
                except Exception as e:
                    logging.warning(f"Failed to insert bus {row['BUS_NUMBER']}: {e}")
            
            return inserted_count
            
        except Exception as e:
            logging.error(f"Error importing buses data: {e}")
            return 0
    
    def import_branches_data(self, file_path, sheet_name, file_id):
        """Import branches data from Excel sheet"""
        try:
            # Read branches sheet
            branches_df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Clean column names
            branches_df.columns = branches_df.columns.str.strip().str.upper()
            
            # Map possible column name variations
            column_mapping = {
                'FROM': ['FROM', 'FROM_BUS', 'FROMBUS', 'F_BUS', 'FROM BUS'],
                'TO': ['TO', 'TO_BUS', 'TOBUS', 'T_BUS', 'TO BUS'],
                'ID': ['ID', 'CKT', 'CIRCUIT', 'CKT_ID'],
                'PF': ['PF', 'P_FROM', 'PFROM', 'MW_FROM', 'P'],
                'QF': ['QF', 'Q_FROM', 'QFROM', 'MVAR_FROM', 'Q'],
                'MVA': ['MVA', 'S', 'APPARENT_POWER', 'S_MVA'],
                'RATE': ['RATE', 'RATING', 'MVA_RATING', 'THERMAL_RATING'],
                'VIO': ['VIO', 'VIOLATION', 'OVERLOAD', 'VIOL']
            }
            
            # Standardize column names
            for standard_col, variations in column_mapping.items():
                for col in branches_df.columns:
                    if col in variations:
                        branches_df.rename(columns={col: standard_col}, inplace=True)
                        break
            
            # Ensure required columns exist
            required_cols = ['FROM', 'TO']
            for col in required_cols:
                if col not in branches_df.columns:
                    raise Exception(f"Required column '{col}' not found in branches sheet")
            
            # Fill missing columns with defaults
            default_values = {
                'ID': '1', 'PF': 0.0, 'QF': 0.0, 'MVA': 0.0, 'RATE': 0.0, 'VIO': 0.0
            }
            
            for col, default_val in default_values.items():
                if col not in branches_df.columns:
                    branches_df[col] = default_val
                else:
                    if col == 'ID':
                        branches_df[col] = branches_df[col].fillna(default_val).astype(str)
                    else:
                        branches_df[col] = branches_df[col].fillna(default_val)
            
            # Insert data
            inserted_count = 0
            for idx, row in branches_df.iterrows():
                try:
                    self.cursor.execute("""
                        INSERT INTO BaseBranchData 
                        (file_id, branch_number, From_Bus, To_Bus, ID, PF, QF, MVA, RATE, VIO) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        file_id,
                        idx + 1,  # Use row index as branch_number
                        int(row['FROM']),
                        int(row['TO']),
                        str(row['ID']),
                        float(row['PF']),
                        float(row['QF']),
                        float(row['MVA']),
                        float(row['RATE']),
                        float(row['VIO'])
                    ))
                    inserted_count += 1
                except Exception as e:
                    logging.warning(f"Failed to insert branch {idx+1}: {e}")
            
            return inserted_count
            
        except Exception as e:
            logging.error(f"Error importing branches data: {e}")
            return 0
    
    def import_all_files(self, excel_folder):
        """Import all Excel files from folder"""
        if not self.connect_database():
            return False
        
        try:
            # Get all Excel files
            excel_files = []
            for ext in ['*.xlsx', '*.xls']:
                excel_files.extend(list(Path(excel_folder).glob(ext)))
            
            total_files = len(excel_files)
            logging.info(f"Found {total_files} Excel files in {excel_folder}")
            
            if total_files == 0:
                logging.error("No Excel files found!")
                return False
            
            # Process files
            successful = 0
            failed = 0
            start_time = time.time()
            
            for i, file_path in enumerate(excel_files, 1):
                logging.info(f"\n--- Processing {i}/{total_files}: {file_path.name} ---")
                
                if self.import_single_file(file_path, i):
                    successful += 1
                else:
                    failed += 1
                
                # Progress update every 50 files
                if i % 50 == 0:
                    elapsed = time.time() - start_time
                    estimated_total = elapsed * total_files / i
                    remaining = estimated_total - elapsed
                    
                    logging.info(f"\n📊 Progress Update:")
                    logging.info(f"   Processed: {i}/{total_files} ({i/total_files*100:.1f}%)")
                    logging.info(f"   Successful: {successful}")
                    logging.info(f"   Failed: {failed}")
                    logging.info(f"   Time elapsed: {elapsed/60:.1f} minutes")
                    logging.info(f"   Estimated remaining: {remaining/60:.1f} minutes")
            
            # Final summary
            total_time = time.time() - start_time
            logging.info(f"\n🎉 Import Complete!")
            logging.info(f"   Total files: {total_files}")
            logging.info(f"   Successful: {successful}")
            logging.info(f"   Failed: {failed}")
            logging.info(f"   Success rate: {successful/total_files*100:.1f}%")
            logging.info(f"   Total time: {total_time/60:.1f} minutes")
            
            # Database summary
            self.cursor.execute("SELECT COUNT(*) FROM BaseCaseFiles")
            total_cases = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM BaseBusData")
            total_buses = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM BaseBranchData")
            total_branches = self.cursor.fetchone()[0]
            
            logging.info(f"\n📈 Database Summary:")
            logging.info(f"   Total cases in database: {total_cases}")
            logging.info(f"   Total bus records: {total_buses}")
            logging.info(f"   Total branch records: {total_branches}")
            
            return successful == total_files
            
        except Exception as e:
            logging.error(f"Error during bulk import: {e}")
            return False
        finally:
            self.disconnect_database()

def main():
    """Main function to run the import"""
    
    # Database configuration - UPDATE THESE VALUES
    DB_CONFIG = {
        'host': 'localhost',        # Your PostgreSQL host
        'port': '5432',            # Your PostgreSQL port
        'database': '118',  # Your database name
        'user': 'postgres',        # Your username
        'password': 'pnnl' # Your password
    }
    
    # Path to your Excel files folder - UPDATE THIS PATH
    EXCEL_FOLDER = r"C:\\Users\\nira771\\Data\\base_case"
    
    # Verify folder exists
    if not os.path.exists(EXCEL_FOLDER):
        print(f"❌ Error: Folder '{EXCEL_FOLDER}' does not exist!")
        print("Please update the EXCEL_FOLDER path in the script.")
        return
    
    # Show configuration
    print("🔧 IEEE 118 Bus System Data Import")
    print("=" * 50)
    print(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    print(f"Excel folder: {EXCEL_FOLDER}")
    print(f"Log file: ieee118_import.log")
    
    # Count Excel files
    excel_files = []
    for ext in ['*.xlsx', '*.xls']:
        excel_files.extend(list(Path(EXCEL_FOLDER).glob(ext)))
    
    print(f"Found {len(excel_files)} Excel files")
    
    if len(excel_files) == 0:
        print("❌ No Excel files found! Please check the folder path.")
        return
    
    # Confirm before starting
    response = input(f"\n🚀 Start importing {len(excel_files)} files? (y/n): ")
    if response.lower() != 'y':
        print("Import cancelled.")
        return
    
    # Create importer and run
    importer = IEEE118DataImporter(DB_CONFIG)
    
    print(f"\n📊 Starting import at {datetime.now()}")
    print("Check 'ieee118_import.log' for detailed progress...")
    
    success = importer.import_all_files(EXCEL_FOLDER)
    
    if success:
        print("\n✅ All files imported successfully!")
    else:
        print("\n⚠️ Import completed with some errors. Check the log file.")
    
    print(f"Finished at {datetime.now()}")

def test_single_file():
    """Test function to import just one file"""
    
    DB_CONFIG = {
        'host': 'localhost',
        'port': '5432',
        'database': 'ieee118_db',  # Your database name
        'user': 'postgres',        # Your username
        'password': 'your_password' # Your password
    }
    
    # Test with one file - UPDATE THIS PATH
    TEST_FILE = r"C:\path\to\one\test\file.xlsx"
    
    if not os.path.exists(TEST_FILE):
        print(f"❌ Test file '{TEST_FILE}' does not exist!")
        return
    
    print(f"🧪 Testing with single file: {TEST_FILE}")
    
    importer = IEEE118DataImporter(DB_CONFIG)
    
    if importer.connect_database():
        success = importer.import_single_file(TEST_FILE, 999)  # Use scenario_id 999 for test
        importer.disconnect_database()
        
        if success:
            print("✅ Test file imported successfully!")
        else:
            print("❌ Test file import failed!")
    else:
        print("❌ Database connection failed!")

def check_database_status():
    """Check current database status"""
    
    DB_CONFIG = {
        'host': 'localhost',
        'port': '5432',
        'database': 'ieee118_db',  # Your database name
        'user': 'postgres',        # Your username
        'password': 'your_password' # Your password
    }
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("📊 Database Status Check")
        print("=" * 30)
        
        # Check tables exist
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        print(f"Tables: {[t[0] for t in tables]}")
        
        # Check record counts
        cursor.execute("SELECT COUNT(*) FROM BaseCaseFiles")
        case_count = cursor.fetchone()[0]
        print(f"Base case files: {case_count}")
        
        cursor.execute("SELECT COUNT(*) FROM BaseBusData")
        bus_count = cursor.fetchone()[0]
        print(f"Bus records: {bus_count}")
        
        cursor.execute("SELECT COUNT(*) FROM BaseBranchData")
        branch_count = cursor.fetchone()[0]
        print(f"Branch records: {branch_count}")
        
        # Check processing status
        cursor.execute("""
            SELECT processing_status, COUNT(*) 
            FROM BaseCaseFiles 
            GROUP BY processing_status
        """)
        status_counts = cursor.fetchall()
        print(f"Processing status: {dict(status_counts)}")
        
        # Show sample data
        cursor.execute("SELECT * FROM SystemSummary LIMIT 3")
        samples = cursor.fetchall()
        if samples:
            print(f"\nSample cases:")
            for sample in samples:
                print(f"  Case {sample[0]}: {sample[1]} - {sample[4]} buses, {sample[5]} branches")
        
        cursor.close()
        conn.close()
        
        print("✅ Database status check complete!")
        
    except Exception as e:
        print(f"❌ Database status check failed: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_single_file()
        elif sys.argv[1] == "status":
            check_database_status()
        else:
            print("Usage:")
            print("  python import_script.py        # Import all files")
            print("  python import_script.py test   # Test with one file")
            print("  python import_script.py status # Check database status")
    else:
        main()