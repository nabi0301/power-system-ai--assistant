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
        logging.FileHandler('full_loader.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class FullDataLoader:
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

    def parse_base_case_file(self, file_path):
        """Parse a base case file - returns bus_data and branch_data"""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Skip first two lines (headers), then find bus data (118 lines)
            data_lines = [line.strip() for line in lines[2:] if line.strip()]
            
            if len(data_lines) < 118:
                logging.error(f"Not enough data lines in {file_path.name}")
                return None, None
            
            # Parse bus data (first 118 lines)
            bus_data_dict = {}
            for i, line in enumerate(data_lines[:118]):
                parts = line.split()
                if len(parts) >= 8:
                    try:
                        bus_number = int(float(parts[0]))
                        row = [float(p) for p in parts[:8]]
                        bus_data_dict[bus_number] = row
                    except ValueError:
                        continue
            
            bus_df = pd.DataFrame(list(bus_data_dict.values()), 
                                columns=['BUS_NUMBER', 'VM', 'VA', 'BASE_KV', 'PG', 'QG', 'PD', 'QD'])
            
            # Parse branch data (after "From, To, ID, PF, QF, MVA, RATE, VIO" header)
            branch_data = []
            branch_started = False
            branch_number = 1
            
            for line in data_lines[118:]:
                if "From, To, ID, PF, QF, MVA, RATE, VIO" in line or "From,To,ID,PF,QF,MVA,RATE,VIO" in line:
                    branch_started = True
                    continue
                    
                if branch_started:
                    parts = line.split()
                    if len(parts) >= 8:
                        try:
                            from_bus = int(float(parts[0]))
                            to_bus = int(float(parts[1]))
                            line_id = int(float(parts[2]))
                            pf = float(parts[3])
                            qf = float(parts[4])
                            mva = float(parts[5])
                            rate = float(parts[6])
                            vio = float(parts[7])
                            
                            branch_data.append([branch_number, from_bus, to_bus, line_id, pf, qf, mva, rate, vio])
                            branch_number += 1
                        except ValueError:
                            continue
            
            branch_df = pd.DataFrame(branch_data, 
                                   columns=['BRANCH_NUMBER', 'FROM_BUS', 'TO_BUS', 'LINE_ID', 'PF', 'QF', 'MVA', 'RATE', 'VIO'])
            
            logging.info(f"Parsed {file_path.name}: {len(bus_df)} buses, {len(branch_df)} branches")
            return bus_df, branch_df
            
        except Exception as e:
            logging.error(f"Error parsing base case file {file_path}: {e}")
            return None, None

    def parse_contingency_file(self, file_path):
        """
        Parse a contingency file that contains 186 contingency cases.
        Each case has: 118 bus lines + 186 branch lines
        Format: Case number on its own line, followed by bus data, then branch data
        """
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Remove empty lines and strip whitespace
            data_lines = [line.strip() for line in lines if line.strip()]
            
            if not data_lines:
                logging.error(f"No data in {file_path.name}")
                return []
            
            # Each contingency case has 118 bus lines + 186 branch lines = 304 lines
            LINES_PER_CASE = 304
            cases = []
            
            i = 0
            while i < len(data_lines):
                # Check if this line is a case number (1-3 digits, standalone)
                if data_lines[i].isdigit() and len(data_lines[i]) <= 3:
                    case_number = int(data_lines[i])
                    i += 1
                    
                    # Extract 118 bus lines
                    if i + 118 > len(data_lines):
                        break
                    
                    bus_lines = data_lines[i:i+118]
                    i += 118
                    
                    # Extract 186 branch lines
                    if i + 186 > len(data_lines):
                        break
                    
                    branch_lines = data_lines[i:i+186]
                    i += 186
                    
                    # Parse bus data
                    bus_data = []
                    for line in bus_lines:
                        parts = line.split()
                        if len(parts) >= 7:
                            try:
                                bus_number = int(float(parts[0]))
                                vm = float(parts[1])
                                va = float(parts[2])
                                pg = float(parts[3])
                                qg = float(parts[4])
                                pd_val = float(parts[5])
                                qd_val = float(parts[6])
                                bus_data.append([bus_number, vm, va, 138.0, pg, qg, pd_val, qd_val])
                            except ValueError:
                                continue
                    
                    # Parse branch data (branch_number, pf, qf)
                    branch_data = []
                    for line in branch_lines:
                        parts = line.split()
                        if len(parts) >= 3:
                            try:
                                branch_num = int(float(parts[0]))
                                pf = float(parts[1])
                                qf = float(parts[2])
                                branch_data.append([branch_num, pf, qf])
                            except ValueError:
                                continue
                    
                    if bus_data and branch_data:
                        bus_df = pd.DataFrame(bus_data, columns=['BUS_NUMBER', 'VM', 'VA', 'BASE_KV', 'PG', 'QG', 'PD', 'QD'])
                        branch_df = pd.DataFrame(branch_data, columns=['BRANCH_NUMBER', 'PF', 'QF'])
                        cases.append((case_number, bus_df, branch_df))
                else:
                    i += 1
            
            logging.info(f"Parsed {file_path.name}: Found {len(cases)} contingency cases")
            return cases
            
        except Exception as e:
            logging.error(f"Error parsing contingency file {file_path}: {e}")
            return []

    def import_base_cases(self):
        """Import all base case files with bus and branch data"""
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
        error_count = 0
        
        for i, file_path in enumerate(base_files, 1):
            try:
                # Extract case number from filename
                match = re.search(r'BASE_\d+_bus\d+_(\d+)\.txt', file_path.name, re.IGNORECASE)
                if not match:
                    match = re.search(r'BASE.*?_(\d+)\.txt', file_path.name, re.IGNORECASE)
                if not match:
                    logging.warning(f"Could not extract case number from {file_path.name}")
                    error_count += 1
                    continue
                
                case_number = int(match.group(1))
                
                # Parse file
                bus_df, branch_df = self.parse_base_case_file(file_path)
                if bus_df is None or branch_df is None:
                    logging.error(f"Failed to parse {file_path.name}")
                    error_count += 1
                    continue
                
                # Create/update base case record
                self.cursor.execute("""
                    INSERT INTO BaseCases (case_number, filename, case_name, folder_name, buses_count, branches_count, processing_status)
                    VALUES (%s, %s, %s, %s, %s, %s, 'processing')
                    ON CONFLICT (case_number) DO UPDATE SET
                        filename = EXCLUDED.filename,
                        buses_count = EXCLUDED.buses_count,
                        branches_count = EXCLUDED.branches_count,
                        processing_status = EXCLUDED.processing_status
                    RETURNING base_case_id
                """, (case_number, file_path.name, f"Base Case {case_number}", "Base_118", len(bus_df), len(branch_df)))
                
                base_case_id = self.cursor.fetchone()[0]
                
                # Import bus data
                bus_records = []
                for _, row in bus_df.iterrows():
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
                
                # Clear and insert bus data
                self.cursor.execute("DELETE FROM BaseBusData WHERE base_case_id = %s", (base_case_id,))
                self.cursor.executemany("""
                    INSERT INTO BaseBusData 
                    (base_case_id, bus_number, vm, va, base_kv, pg, qg, pd, qd)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, bus_records)
                
                # Import branch data
                branch_records = []
                for _, row in branch_df.iterrows():
                    branch_records.append((
                        base_case_id,
                        int(row['BRANCH_NUMBER']),
                        int(row['FROM_BUS']),
                        int(row['TO_BUS']),
                        int(row['LINE_ID']),
                        float(row['PF']),
                        float(row['QF']),
                        float(row['MVA']),
                        float(row['RATE']),
                        float(row['VIO'])
                    ))
                
                # Clear and insert branch data
                self.cursor.execute("DELETE FROM BaseBranchData WHERE base_case_id = %s", (base_case_id,))
                self.cursor.executemany("""
                    INSERT INTO BaseBranchData 
                    (base_case_id, branch_number, from_bus, to_bus, line_id, pf, qf, mva, rate, vio)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, branch_records)
                
                # Update status
                self.cursor.execute("""
                    UPDATE BaseCases 
                    SET processing_status = 'completed'
                    WHERE base_case_id = %s
                """, (base_case_id,))
                
                self.conn.commit()
                imported_count += 1
                
                if i % 50 == 0 or i == total_files:
                    logging.info(f"Progress: {i}/{total_files} base cases processed (imported: {imported_count}, errors: {error_count})")
                
            except Exception as e:
                logging.error(f"Error processing base case {file_path.name}: {e}")
                self.conn.rollback()
                error_count += 1
                continue
        
        logging.info(f"Base case import completed: {imported_count} imported, {error_count} errors")
        return True

    def import_contingency_cases(self):
        """Import all contingency case files with bus and branch data"""
        contingency_folder = self.data_folder / "contingency_118"
        if not contingency_folder.exists():
            logging.warning(f"Contingency folder {contingency_folder} does not exist")
            return False
        
        contingency_files = list(contingency_folder.glob("*.txt"))
        total_files = len(contingency_files)
        
        if total_files == 0:
            logging.warning("No contingency case files found")
            return True
        
        # Get all base cases with their branch data for reference
        self.cursor.execute("""
            SELECT bc.case_number, bc.base_case_id, bb.branch_number, bb.from_bus, bb.to_bus, bb.line_id, bb.mva, bb.rate
            FROM BaseCases bc
            JOIN BaseBranchData bb ON bc.base_case_id = bb.base_case_id
            WHERE bc.processing_status = 'completed'
            ORDER BY bc.case_number, bb.branch_number
        """)
        
        base_branch_data = {}
        for row in self.cursor.fetchall():
            case_num, base_case_id, branch_num, from_bus, to_bus, line_id, mva, rate = row
            if case_num not in base_branch_data:
                base_branch_data[case_num] = {}
            base_branch_data[case_num][branch_num] = {
                'base_case_id': base_case_id,
                'from_bus': from_bus,
                'to_bus': to_bus,
                'line_id': line_id,
                'mva': mva,
                'rate': rate
            }
        
        logging.info(f"Found {total_files} contingency case files to import")
        logging.info(f"Base cases available for linking: {list(base_branch_data.keys())}")
        
        imported_count = 0
        error_count = 0
        
        for i, file_path in enumerate(contingency_files, 1):
            try:
                # Extract case number from filename
                match = re.search(r'CA_\d+_bus\d+_(\d+)\.txt', file_path.name, re.IGNORECASE)
                if not match:
                    match = re.search(r'CA.*?_(\d+)\.txt', file_path.name, re.IGNORECASE)
                if not match:
                    logging.warning(f"Could not extract case number from {file_path.name}")
                    error_count += 1
                    continue
                
                case_number = int(match.group(1))
                
                # Find matching base case
                if case_number not in base_branch_data:
                    logging.warning(f"No matching base case found for contingency case {case_number}")
                    error_count += 1
                    continue
                
                # Get base_case_id from first available branch
                first_branch_num = list(base_branch_data[case_number].keys())[0]
                base_case_id = base_branch_data[case_number][first_branch_num]['base_case_id']
                
                # Parse file - returns list of (case_num, bus_df, branch_df) tuples
                cases = self.parse_contingency_file(file_path)
                if not cases:
                    logging.error(f"Failed to parse any cases from {file_path.name}")
                    error_count += 1
                    continue
                
                # Process each contingency case from the file
                for cont_case_num, bus_df, branch_df in cases:
                    try:
                        # Create contingency case record
                        self.cursor.execute("""
                            INSERT INTO ContingencyCases 
                            (base_case_id, case_number, filename, case_name, contingency_element, folder_name, buses_count, branches_count, processing_status)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'processing')
                            ON CONFLICT (base_case_id, case_number) DO UPDATE SET
                                filename = EXCLUDED.filename,
                                buses_count = EXCLUDED.buses_count,
                                branches_count = EXCLUDED.branches_count,
                                processing_status = EXCLUDED.processing_status
                            RETURNING contingency_case_id
                        """, (base_case_id, cont_case_num, file_path.name, f"Contingency Case {cont_case_num}", 
                              f"Contingency {cont_case_num}", "contingency_118", len(bus_df), len(branch_df)))
                        
                        contingency_case_id = self.cursor.fetchone()[0]
                        
                        # Import bus data
                        bus_records = []
                        for _, row in bus_df.iterrows():
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
                        
                        # Clear and insert bus data
                        self.cursor.execute("DELETE FROM ContingencyBusData WHERE contingency_case_id = %s", (contingency_case_id,))
                        self.cursor.executemany("""
                            INSERT INTO ContingencyBusData 
                            (contingency_case_id, bus_number, vm, va, base_kv, pg, qg, pd, qd)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, bus_records)
                        
                        # Import branch data with base case linking
                        branch_records = []
                        for _, row in branch_df.iterrows():
                            branch_num = int(row['BRANCH_NUMBER'])
                            pf = float(row['PF'])
                            qf = float(row['QF'])
                            
                            # Get base case branch info
                            if branch_num in base_branch_data[case_number]:
                                base_info = base_branch_data[case_number][branch_num]
                                from_bus = base_info['from_bus']
                                to_bus = base_info['to_bus']
                                line_id = base_info['line_id']
                                rate = base_info['rate']
                                
                                # Calculate MVA and VIO using contingency PF/QF
                                import numpy as np
                                mva = np.sqrt(pf**2 + qf**2)
                                vio = max(0.0, mva - rate) if rate > 0 else 0.0
                                
                                branch_records.append((
                                    contingency_case_id,
                                    base_case_id,
                                    from_bus,
                                    to_bus,
                                    line_id,  # This will map to circuit_id
                                    pf,
                                    qf,
                                    mva,
                                    rate,
                                    vio
                                ))
                        
                        # Clear and insert branch data
                        self.cursor.execute("DELETE FROM ContingencyBranchData WHERE contingency_case_id = %s", (contingency_case_id,))
                        self.cursor.executemany("""
                            INSERT INTO ContingencyBranchData 
                            (contingency_case_id, base_case_id, from_bus, to_bus, circuit_id, pf, qf, mva, rate, vio)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, branch_records)
                        
                        # Update status
                        self.cursor.execute("""
                            UPDATE ContingencyCases 
                            SET processing_status = 'completed'
                            WHERE contingency_case_id = %s
                        """, (contingency_case_id,))
                        
                        imported_count += 1
                        
                    except Exception as e:
                        logging.error(f"Error processing case {cont_case_num} from {file_path.name}: {e}")
                        error_count += 1
                        continue
                
                self.conn.commit()
                
                if i % 10 == 0 or i == total_files:
                    logging.info(f"Progress: {i}/{total_files} files processed ({imported_count} cases imported, {error_count} errors)")
                
            except Exception as e:
                logging.error(f"Error processing contingency file {file_path.name}: {e}")
                self.conn.rollback()
                error_count += 1
                continue
        
        logging.info(f"Contingency case import completed: {imported_count} cases imported from {total_files} files, {error_count} errors")
        return True

    def get_import_summary(self):
        """Get summary of imported data"""
        try:
            summary = {}
            
            self.cursor.execute("SELECT COUNT(*) FROM BaseCases WHERE processing_status = 'completed'")
            summary['base_cases'] = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM ContingencyCases WHERE processing_status = 'completed'")
            summary['contingency_cases'] = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM BaseBusData")
            summary['base_bus_data'] = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM BaseBranchData")
            summary['base_branch_data'] = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM ContingencyBusData")
            summary['contingency_bus_data'] = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM ContingencyBranchData")
            summary['contingency_branch_data'] = self.cursor.fetchone()[0]
            
            return summary
        except Exception as e:
            logging.error(f"Error getting summary: {e}")
            return None

    def run_full_import(self):
        """Run the complete import process"""
        start_time = time.time()
        logging.info("Starting full import process with bus and branch data...")
        
        try:
            # Connect to database
            if not self.connect_database():
                return False
            
            # Import base cases
            logging.info("=" * 60)
            logging.info("STARTING BASE CASE IMPORT (BUS + BRANCH DATA)")
            logging.info("=" * 60)
            if not self.import_base_cases():
                logging.error("Base case import failed")
                return False
            
            # Import contingency cases
            logging.info("=" * 60)
            logging.info("STARTING CONTINGENCY CASE IMPORT (BUS + BRANCH DATA)")
            logging.info("=" * 60)
            if not self.import_contingency_cases():
                logging.error("Contingency case import failed")
                return False
            
            # Get final summary
            summary = self.get_import_summary()
            if summary:
                elapsed_time = time.time() - start_time
                logging.info("=" * 60)
                logging.info("FULL IMPORT COMPLETED SUCCESSFULLY!")
                logging.info("=" * 60)
                logging.info(f"Base cases imported: {summary['base_cases']}")
                logging.info(f"Contingency cases imported: {summary['contingency_cases']}")
                logging.info(f"Base bus data records: {summary['base_bus_data']}")
                logging.info(f"Base branch data records: {summary['base_branch_data']}")
                logging.info(f"Contingency bus data records: {summary['contingency_bus_data']}")
                logging.info(f"Contingency branch data records: {summary['contingency_branch_data']}")
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
    loader = FullDataLoader(DATA_FOLDER, DB_CONFIG)
    success = loader.run_full_import()
    
    if success:
        print("\n🎉 ALL DATA (BUS + BRANCH) LOADED SUCCESSFULLY!")
        print("Check full_loader.log for detailed progress information")
    else:
        print("\n❌ Import failed. Check full_loader.log for error details")