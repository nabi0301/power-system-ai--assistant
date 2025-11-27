"""
DLR/SLR Data Loader for 118.db PostgreSQL Database
Processes DLR and SLR corrective action CSV files with minimal table structure
Creates separate schemas for DLR and SLR data based on actual file contents
"""

import pandas as pd
import psycopg2
import os
import re
import time
from pathlib import Path
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dlr_slr_import.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class DLR_SLR_Loader:
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
    
    def create_dlr_slr_schema(self):
        """Create DLR and SLR tables with minimal structure"""
        try:
            logging.info("Creating DLR/SLR schema...")
            
            self.cursor.execute("""
                -- Drop existing tables if they exist
                DROP TABLE IF EXISTS dlr_buses CASCADE;
                DROP TABLE IF EXISTS dlr_branches CASCADE;
                DROP TABLE IF EXISTS dlr_generators CASCADE;
                DROP TABLE IF EXISTS dlr_loads CASCADE;
                DROP TABLE IF EXISTS dlr_cases CASCADE;
                
                DROP TABLE IF EXISTS slr_buses CASCADE;
                DROP TABLE IF EXISTS slr_branches CASCADE;
                DROP TABLE IF EXISTS slr_generators CASCADE;
                DROP TABLE IF EXISTS slr_loads CASCADE;
                DROP TABLE IF EXISTS slr_cases CASCADE;
                
                -- DLR Tables
                CREATE TABLE dlr_cases (
                    dlr_case_id SERIAL PRIMARY KEY,
                    base_case_id INTEGER NOT NULL,
                    contingency_index INTEGER NOT NULL,
                    tripped_line_index INTEGER NOT NULL,
                    from_bus INTEGER NOT NULL,
                    to_bus INTEGER NOT NULL,
                    line_id TEXT DEFAULT '1',
                    contingency_name TEXT NOT NULL,
                    data_source_folder TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (base_case_id) REFERENCES base_cases(case_id) ON DELETE CASCADE,
                    UNIQUE(base_case_id, contingency_index, from_bus, to_bus, line_id)
                );
                
                CREATE TABLE dlr_buses (
                    dlr_bus_id SERIAL PRIMARY KEY,
                    dlr_case_id INTEGER NOT NULL,
                    bus_number INTEGER NOT NULL,
                    vm_pu REAL,
                    va_degrees REAL,
                    base_kv REAL,
                    pg_mw REAL,
                    qg_mvar REAL,
                    pd_mw REAL,
                    qd_mvar REAL,
                    bus_type INTEGER,
                    
                    FOREIGN KEY (dlr_case_id) REFERENCES dlr_cases(dlr_case_id) ON DELETE CASCADE,
                    UNIQUE(dlr_case_id, bus_number)
                );
                
                CREATE TABLE dlr_branches (
                    dlr_branch_id SERIAL PRIMARY KEY,
                    dlr_case_id INTEGER NOT NULL,
                    from_bus INTEGER NOT NULL,
                    to_bus INTEGER NOT NULL,
                    circuit_id TEXT DEFAULT '1',
                    pf_mw REAL,
                    qf_mvar REAL,
                    pt_mw REAL,
                    qt_mvar REAL,
                    mva_flow REAL,
                    mva_rating REAL,
                    loading_percent REAL,
                    
                    FOREIGN KEY (dlr_case_id) REFERENCES dlr_cases(dlr_case_id) ON DELETE CASCADE,
                    UNIQUE(dlr_case_id, from_bus, to_bus, circuit_id)
                );
                
                CREATE TABLE dlr_generators (
                    dlr_gen_id SERIAL PRIMARY KEY,
                    dlr_case_id INTEGER NOT NULL,
                    bus_number INTEGER NOT NULL,
                    gen_ini REAL,
                    gen_new REAL,
                    gen_adj REAL,
                    kv_level REAL,
                    
                    FOREIGN KEY (dlr_case_id) REFERENCES dlr_cases(dlr_case_id) ON DELETE CASCADE,
                    UNIQUE(dlr_case_id, bus_number)
                );
                
                CREATE TABLE dlr_loads (
                    dlr_load_id SERIAL PRIMARY KEY,
                    dlr_case_id INTEGER NOT NULL,
                    bus_number INTEGER NOT NULL,
                    load_ini REAL,
                    load_new REAL,
                    load_adj REAL,
                    kv_level REAL,
                    
                    FOREIGN KEY (dlr_case_id) REFERENCES dlr_cases(dlr_case_id) ON DELETE CASCADE,
                    UNIQUE(dlr_case_id, bus_number)
                );
                
                -- SLR Tables (identical structure)
                CREATE TABLE slr_cases (
                    slr_case_id SERIAL PRIMARY KEY,
                    base_case_id INTEGER NOT NULL,
                    contingency_index INTEGER NOT NULL,
                    tripped_line_index INTEGER NOT NULL,
                    from_bus INTEGER NOT NULL,
                    to_bus INTEGER NOT NULL,
                    line_id TEXT DEFAULT '1',
                    contingency_name TEXT NOT NULL,
                    data_source_folder TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (base_case_id) REFERENCES base_cases(case_id) ON DELETE CASCADE,
                    UNIQUE(base_case_id, contingency_index, from_bus, to_bus, line_id)
                );
                
                CREATE TABLE slr_buses (
                    slr_bus_id SERIAL PRIMARY KEY,
                    slr_case_id INTEGER NOT NULL,
                    bus_number INTEGER NOT NULL,
                    vm_pu REAL,
                    va_degrees REAL,
                    base_kv REAL,
                    pg_mw REAL,
                    qg_mvar REAL,
                    pd_mw REAL,
                    qd_mvar REAL,
                    bus_type INTEGER,
                    
                    FOREIGN KEY (slr_case_id) REFERENCES slr_cases(slr_case_id) ON DELETE CASCADE,
                    UNIQUE(slr_case_id, bus_number)
                );
                
                CREATE TABLE slr_branches (
                    slr_branch_id SERIAL PRIMARY KEY,
                    slr_case_id INTEGER NOT NULL,
                    from_bus INTEGER NOT NULL,
                    to_bus INTEGER NOT NULL,
                    circuit_id TEXT DEFAULT '1',
                    pf_mw REAL,
                    qf_mvar REAL,
                    pt_mw REAL,
                    qt_mvar REAL,
                    mva_flow REAL,
                    mva_rating REAL,
                    loading_percent REAL,
                    
                    FOREIGN KEY (slr_case_id) REFERENCES slr_cases(slr_case_id) ON DELETE CASCADE,
                    UNIQUE(slr_case_id, from_bus, to_bus, circuit_id)
                );
                
                CREATE TABLE slr_generators (
                    slr_gen_id SERIAL PRIMARY KEY,
                    slr_case_id INTEGER NOT NULL,
                    bus_number INTEGER NOT NULL,
                    gen_ini REAL,
                    gen_new REAL,
                    gen_adj REAL,
                    kv_level REAL,
                    
                    FOREIGN KEY (slr_case_id) REFERENCES slr_cases(slr_case_id) ON DELETE CASCADE,
                    UNIQUE(slr_case_id, bus_number)
                );
                
                CREATE TABLE slr_loads (
                    slr_load_id SERIAL PRIMARY KEY,
                    slr_case_id INTEGER NOT NULL,
                    bus_number INTEGER NOT NULL,
                    load_ini REAL,
                    load_new REAL,
                    load_adj REAL,
                    kv_level REAL,
                    
                    FOREIGN KEY (slr_case_id) REFERENCES slr_cases(slr_case_id) ON DELETE CASCADE,
                    UNIQUE(slr_case_id, bus_number)
                );
                
                -- Create indexes for performance
                CREATE INDEX idx_dlr_cases_base ON dlr_cases(base_case_id);
                CREATE INDEX idx_dlr_cases_line ON dlr_cases(from_bus, to_bus);
                CREATE INDEX idx_dlr_buses_number ON dlr_buses(bus_number);
                CREATE INDEX idx_dlr_branches_line ON dlr_branches(from_bus, to_bus);
                CREATE INDEX idx_dlr_generators_bus ON dlr_generators(bus_number);
                CREATE INDEX idx_dlr_loads_bus ON dlr_loads(bus_number);
                
                CREATE INDEX idx_slr_cases_base ON slr_cases(base_case_id);
                CREATE INDEX idx_slr_cases_line ON slr_cases(from_bus, to_bus);
                CREATE INDEX idx_slr_buses_number ON slr_buses(bus_number);
                CREATE INDEX idx_slr_branches_line ON slr_branches(from_bus, to_bus);
                CREATE INDEX idx_slr_generators_bus ON slr_generators(bus_number);
                CREATE INDEX idx_slr_loads_bus ON slr_loads(bus_number);
            """)
            
            self.conn.commit()
            logging.info("✅ DLR/SLR schema created successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error creating DLR/SLR schema: {e}")
            self.conn.rollback()
            return False
    
    def parse_contingency_filename(self, filename):
        """Parse contingency information from filename"""
        try:
            # Pattern: dlr_idx_122_line_77_80_2_branches.csv or slr_idx_123_line_77_82_1_cor_gen.csv
            match = re.search(r'(?:dlr_|slr_)?idx_(\d+)_line_(\d+)_(\d+)(?:_(\d+))?', filename)
            if match:
                idx = int(match.group(1))
                from_bus = int(match.group(2))
                to_bus = int(match.group(3))
                line_id = match.group(4) if match.group(4) else '1'
                
                # Tripped line index is idx + 1 (as per your note)
                tripped_line_index = idx + 1
                
                contingency_name = f"Line_{from_bus}_{to_bus}_{line_id}"
                
                return {
                    'contingency_index': idx,
                    'tripped_line_index': tripped_line_index,
                    'from_bus': from_bus,
                    'to_bus': to_bus,
                    'line_id': line_id,
                    'contingency_name': contingency_name
                }
            
            return None
            
        except Exception as e:
            logging.error(f"Error parsing filename {filename}: {e}")
            return None
    
    def get_base_case_id(self):
        """Get first available base case ID"""
        try:
            self.cursor.execute("""
                SELECT case_id FROM base_cases 
                ORDER BY case_id LIMIT 1
            """)
            result = self.cursor.fetchone()
            if result:
                logging.info(f"Using base case ID: {result[0]}")
                return result[0]
            return None
        except Exception as e:
            logging.error(f"Error getting base case ID: {e}")
            return None
    
    def create_case_record(self, data_type, base_case_id, contingency_info, data_source_folder):
        """Create or get case record for DLR/SLR"""
        try:
            table_name = f"{data_type}_cases"
            id_column = f"{data_type}_case_id"
            
            # Try to insert, or get existing
            self.cursor.execute(f"""
                INSERT INTO {table_name} 
                (base_case_id, contingency_index, tripped_line_index, from_bus, to_bus, 
                 line_id, contingency_name, data_source_folder)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (base_case_id, contingency_index, from_bus, to_bus, line_id)
                DO UPDATE SET data_source_folder = EXCLUDED.data_source_folder
                RETURNING {id_column}
            """, (
                base_case_id,
                contingency_info['contingency_index'],
                contingency_info['tripped_line_index'],
                contingency_info['from_bus'],
                contingency_info['to_bus'],
                contingency_info['line_id'],
                contingency_info['contingency_name'],
                data_source_folder
            ))
            
            return self.cursor.fetchone()[0]
            
        except Exception as e:
            logging.error(f"Error creating {data_type} case record: {e}")
            return None
    
    def import_bus_data(self, data_type, file_path, case_id):
        """Import bus data from CSV"""
        try:
            df = pd.read_csv(file_path)
            logging.info(f"Importing {len(df)} {data_type} bus records from {file_path.name}")
            
            # Clean column names
            df.columns = df.columns.str.strip().str.upper()
            logging.info(f"Bus CSV columns: {list(df.columns)}")
            
            table_name = f"{data_type}_buses"
            case_id_column = f"{data_type}_case_id"
            
            imported_count = 0
            for _, row in df.iterrows():
                try:
                    bus_number = int(row.get('BUS', row.get('BUS_NUMBER', 0)))
                    if bus_number == 0:
                        continue
                    
                    self.cursor.execute(f"""
                        INSERT INTO {table_name}
                        ({case_id_column}, bus_number, vm_pu, va_degrees, base_kv,
                         pg_mw, qg_mvar, pd_mw, qd_mvar, bus_type)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT ({case_id_column}, bus_number)
                        DO UPDATE SET
                            vm_pu = EXCLUDED.vm_pu,
                            va_degrees = EXCLUDED.va_degrees,
                            base_kv = EXCLUDED.base_kv,
                            pg_mw = EXCLUDED.pg_mw,
                            qg_mvar = EXCLUDED.qg_mvar,
                            pd_mw = EXCLUDED.pd_mw,
                            qd_mvar = EXCLUDED.qd_mvar,
                            bus_type = EXCLUDED.bus_type
                    """, (
                        case_id,
                        bus_number,
                        float(row.get('VM', 1.0)) if pd.notna(row.get('VM')) else None,
                        float(row.get('VA', 0.0)) if pd.notna(row.get('VA')) else None,
                        float(row.get('BASE_KV', 138.0)) if pd.notna(row.get('BASE_KV')) else None,
                        float(row.get('PG', 0.0)) if pd.notna(row.get('PG')) else None,
                        float(row.get('QG', 0.0)) if pd.notna(row.get('QG')) else None,
                        float(row.get('PD', 0.0)) if pd.notna(row.get('PD')) else None,
                        float(row.get('QD', 0.0)) if pd.notna(row.get('QD')) else None,
                        int(row.get('TYPE', 1)) if pd.notna(row.get('TYPE')) else None
                    ))
                    imported_count += 1
                    
                except Exception as e:
                    logging.warning(f"Failed to import {data_type} bus row: {e}")
            
            logging.info(f"✅ Imported {imported_count} {data_type} bus records")
            return imported_count
            
        except Exception as e:
            logging.error(f"Error importing {data_type} bus data: {e}")
            return 0
    
    def import_branch_data(self, data_type, file_path, case_id):
        """Import branch data from CSV"""
        try:
            df = pd.read_csv(file_path)
            logging.info(f"Importing {len(df)} {data_type} branch records from {file_path.name}")
            
            # Clean column names
            df.columns = df.columns.str.strip().str.upper()
            logging.info(f"Branch CSV columns: {list(df.columns)}")
            
            table_name = f"{data_type}_branches"
            case_id_column = f"{data_type}_case_id"
            
            imported_count = 0
            for _, row in df.iterrows():
                try:
                    from_bus = int(row.get('FROM_BUS', row.get('FROM', row.get('F_BUS', 0))))
                    to_bus = int(row.get('TO_BUS', row.get('TO', row.get('T_BUS', 0))))
                    if from_bus == 0 or to_bus == 0:
                        continue
                    
                    pf = float(row.get('PF', 0)) if pd.notna(row.get('PF')) else None
                    qf = float(row.get('QF', 0)) if pd.notna(row.get('QF')) else None
                    rating = float(row.get('RATE', row.get('MVA_RATING', 0))) if pd.notna(row.get('RATE', row.get('MVA_RATING'))) else None
                    
                    # Calculate MVA flow and loading
                    mva_flow = None
                    loading_percent = None
                    
                    if pf is not None and qf is not None:
                        mva_flow = (pf**2 + qf**2)**0.5
                        if rating and rating > 0:
                            loading_percent = (mva_flow / rating) * 100
                    
                    self.cursor.execute(f"""
                        INSERT INTO {table_name}
                        ({case_id_column}, from_bus, to_bus, circuit_id, pf_mw, qf_mvar,
                         pt_mw, qt_mvar, mva_flow, mva_rating, loading_percent)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT ({case_id_column}, from_bus, to_bus, circuit_id)
                        DO UPDATE SET
                            pf_mw = EXCLUDED.pf_mw,
                            qf_mvar = EXCLUDED.qf_mvar,
                            pt_mw = EXCLUDED.pt_mw,
                            qt_mvar = EXCLUDED.qt_mvar,
                            mva_flow = EXCLUDED.mva_flow,
                            mva_rating = EXCLUDED.mva_rating,
                            loading_percent = EXCLUDED.loading_percent
                    """, (
                        case_id,
                        from_bus,
                        to_bus,
                        str(row.get('CKT', row.get('ID', '1'))),
                        pf,
                        qf,
                        float(row.get('PT', 0)) if pd.notna(row.get('PT')) else None,
                        float(row.get('QT', 0)) if pd.notna(row.get('QT')) else None,
                        mva_flow,
                        rating,
                        loading_percent
                    ))
                    imported_count += 1
                    
                except Exception as e:
                    logging.warning(f"Failed to import {data_type} branch row: {e}")
            
            logging.info(f"✅ Imported {imported_count} {data_type} branch records")
            return imported_count
            
        except Exception as e:
            logging.error(f"Error importing {data_type} branch data: {e}")
            return 0
    
    def import_generator_data(self, data_type, file_path, case_id):
        """Import generator corrective action data from CSV"""
        try:
            df = pd.read_csv(file_path)
            logging.info(f"Importing {len(df)} {data_type} generator records from {file_path.name}")
            
            # Clean column names
            df.columns = df.columns.str.strip().str.upper()
            logging.info(f"Generator CSV columns: {list(df.columns)}")
            
            table_name = f"{data_type}_generators"
            case_id_column = f"{data_type}_case_id"
            
            imported_count = 0
            for _, row in df.iterrows():
                try:
                    bus_number = int(row.get('BUS_NUMBER', 0))
                    if bus_number == 0:
                        continue
                    
                    self.cursor.execute(f"""
                        INSERT INTO {table_name}
                        ({case_id_column}, bus_number, gen_ini, gen_new, gen_adj, kv_level)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT ({case_id_column}, bus_number)
                        DO UPDATE SET
                            gen_ini = EXCLUDED.gen_ini,
                            gen_new = EXCLUDED.gen_new,
                            gen_adj = EXCLUDED.gen_adj,
                            kv_level = EXCLUDED.kv_level
                    """, (
                        case_id,
                        bus_number,
                        float(row.get('GEN-INI', 0)) if pd.notna(row.get('GEN-INI')) else None,
                        float(row.get('GEN-NEW', 0)) if pd.notna(row.get('GEN-NEW')) else None,
                        float(row.get('GEN-ADJ', 0)) if pd.notna(row.get('GEN-ADJ')) else None,
                        float(row.get('KV_LEVEL', 138.0)) if pd.notna(row.get('KV_LEVEL')) else None
                    ))
                    imported_count += 1
                    
                except Exception as e:
                    logging.warning(f"Failed to import {data_type} generator row: {e}")
            
            logging.info(f"✅ Imported {imported_count} {data_type} generator records")
            return imported_count
            
        except Exception as e:
            logging.error(f"Error importing {data_type} generator data: {e}")
            return 0
    
    def import_load_data(self, data_type, file_path, case_id):
        """Import load corrective action data from CSV"""
        try:
            df = pd.read_csv(file_path)
            logging.info(f"Importing {len(df)} {data_type} load records from {file_path.name}")
            
            # Clean column names
            df.columns = df.columns.str.strip().str.upper()
            logging.info(f"Load CSV columns: {list(df.columns)}")
            
            table_name = f"{data_type}_loads"
            case_id_column = f"{data_type}_case_id"
            
            imported_count = 0
            for _, row in df.iterrows():
                try:
                    bus_number = int(row.get('BUS_NUMBER', 0))
                    if bus_number == 0:
                        continue
                    
                    self.cursor.execute(f"""
                        INSERT INTO {table_name}
                        ({case_id_column}, bus_number, load_ini, load_new, load_adj, kv_level)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT ({case_id_column}, bus_number)
                        DO UPDATE SET
                            load_ini = EXCLUDED.load_ini,
                            load_new = EXCLUDED.load_new,
                            load_adj = EXCLUDED.load_adj,
                            kv_level = EXCLUDED.kv_level
                    """, (
                        case_id,
                        bus_number,
                        float(row.get('LOAD-INI', 0)) if pd.notna(row.get('LOAD-INI')) else None,
                        float(row.get('LOAD-NEW', 0)) if pd.notna(row.get('LOAD-NEW')) else None,
                        float(row.get('LOAD-ADJ', 0)) if pd.notna(row.get('LOAD-ADJ')) else None,
                        float(row.get('KV_LEVEL', 138.0)) if pd.notna(row.get('KV_LEVEL')) else None
                    ))
                    imported_count += 1
                    
                except Exception as e:
                    logging.warning(f"Failed to import {data_type} load row: {e}")
            
            logging.info(f"✅ Imported {imported_count} {data_type} load records")
            return imported_count
            
        except Exception as e:
            logging.error(f"Error importing {data_type} load data: {e}")
            return 0
    
    def import_dlr_slr_folder(self, folder_path):
        """Import all DLR and SLR CSV files from folder"""
        if not self.connect_database():
            return False
        
        try:
            # Create schema
            if not self.create_dlr_slr_schema():
                return False
            
            # Get base case ID
            base_case_id = self.get_base_case_id()
            if base_case_id is None:
                logging.error("Could not find any base case in database!")
                return False
            
            logging.info(f"Using base case ID: {base_case_id}")
            
            folder_path = Path(folder_path)
            dlr_cases = {}
            slr_cases = {}
            
            # Get all CSV files
            csv_files = list(folder_path.glob("*.csv"))
            logging.info(f"Found {len(csv_files)} CSV files")
            
            # Group files by data type (DLR/SLR) and contingency
            for csv_file in csv_files:
                filename = csv_file.name.lower()
                
                # Determine data type
                if filename.startswith('dlr_'):
                    data_type = 'dlr'
                    cases_dict = dlr_cases
                elif filename.startswith('slr_'):
                    data_type = 'slr'
                    cases_dict = slr_cases
                else:
                    logging.warning(f"Unknown file type: {csv_file.name}")
                    continue
                
                # Parse contingency info
                contingency_info = self.parse_contingency_filename(filename)
                if not contingency_info:
                    logging.warning(f"Could not parse contingency from: {csv_file.name}")
                    continue
                
                contingency_key = f"idx_{contingency_info['contingency_index']}_line_{contingency_info['from_bus']}_{contingency_info['to_bus']}_{contingency_info['line_id']}"
                
                if contingency_key not in cases_dict:
                    # Create case record
                    case_id = self.create_case_record(
                        data_type, base_case_id, contingency_info, str(folder_path)
                    )
                    
                    if case_id:
                        cases_dict[contingency_key] = {
                            'id': case_id,
                            'info': contingency_info,
                            'files': []
                        }
                        logging.info(f"\n--- Created {data_type.upper()} Case: {contingency_info['contingency_name']} ---")
                
                # Add file to case
                if contingency_key in cases_dict:
                    cases_dict[contingency_key]['files'].append((csv_file, data_type))
            
            # Process DLR files
            for contingency_key, case_data in dlr_cases.items():
                case_id = case_data['id']
                files = case_data['files']
                
                logging.info(f"\nProcessing {len(files)} DLR files for {case_data['info']['contingency_name']}")
                
                for csv_file, data_type in files:
                    self.process_file(data_type, csv_file, case_id)
                
                self.conn.commit()
            
            # Process SLR files
            for contingency_key, case_data in slr_cases.items():
                case_id = case_data['id']
                files = case_data['files']
                
                logging.info(f"\nProcessing {len(files)} SLR files for {case_data['info']['contingency_name']}")
                
                for csv_file, data_type in files:
                    self.process_file(data_type, csv_file, case_id)
                
                self.conn.commit()
            
            logging.info(f"\n🎉 DLR/SLR Import Complete!")
            logging.info(f"   DLR contingencies: {len(dlr_cases)}")
            logging.info(f"   SLR contingencies: {len(slr_cases)}")
            
            # Show summary
            self.show_import_summary()
            
            return True
            
        except Exception as e:
            logging.error(f"Error during DLR/SLR import: {e}")
            return False
        finally:
            self.disconnect_database()
    
    def process_file(self, data_type, csv_file, case_id):
        """Process a single CSV file based on its type"""
        try:
            filename = csv_file.name.lower()
            
            if 'cor_gen' in filename:
                self.import_generator_data(data_type, csv_file, case_id)
            elif 'cor_load' in filename:
                self.import_load_data(data_type, csv_file, case_id)
            elif 'bus' in filename:
                self.import_bus_data(data_type, csv_file, case_id)
            elif 'branch' in filename:
                self.import_branch_data(data_type, csv_file, case_id)
            else:
                logging.info(f"Skipping unrecognized file: {csv_file.name}")
        
        except Exception as e:
            logging.error(f"Error processing {csv_file}: {e}")
    
    def show_import_summary(self):
        """Show summary of imported DLR/SLR data"""
        try:
            # DLR Summary
            self.cursor.execute("SELECT COUNT(*) FROM dlr_cases")
            dlr_cases_count = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM dlr_generators")
            dlr_gen_count = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM dlr_loads")
            dlr_load_count = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM dlr_buses")
            dlr_bus_count = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM dlr_branches")
            dlr_branch_count = self.cursor.fetchone()[0]
            
            # SLR Summary
            self.cursor.execute("SELECT COUNT(*) FROM slr_cases")
            slr_cases_count = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM slr_generators")
            slr_gen_count = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM slr_loads")
            slr_load_count = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM slr_buses")
            slr_bus_count = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM slr_branches")
            slr_branch_count = self.cursor.fetchone()[0]
            
            logging.info(f"\n📊 DLR/SLR Import Summary:")
            logging.info(f"\n🔥 DLR Data:")
            logging.info(f"   Cases: {dlr_cases_count}")
            logging.info(f"   Generators: {dlr_gen_count}")
            logging.info(f"   Loads: {dlr_load_count}")
            logging.info(f"   Buses: {dlr_bus_count}")
            logging.info(f"   Branches: {dlr_branch_count}")
            
            logging.info(f"\n🔥 SLR Data:")
            logging.info(f"   Cases: {slr_cases_count}")
            logging.info(f"   Generators: {slr_gen_count}")
            logging.info(f"   Loads: {slr_load_count}")
            logging.info(f"   Buses: {slr_bus_count}")
            logging.info(f"   Branches: {slr_branch_count}")
            
        except Exception as e:
            logging.error(f"Error showing summary: {e}")

def main():
    """Main function to run DLR/SLR import"""
    
    # Database configuration
    DB_CONFIG = {
        'host': 'localhost',
        'port': '5432',
        'database': '118',
        'user': 'postgres',
        'password': 'pnnl'
    }
    
    # Path to your DLR/SLR data folder
    DLR_SLR_FOLDER = r"C:\Users\nira771\slr_dlr_cor_action"
    
    # Verify folder exists
    if not os.path.exists(DLR_SLR_FOLDER):
        print(f"❌ Error: Folder '{DLR_SLR_FOLDER}' does not exist!")
        print("Please update the DLR_SLR_FOLDER path in the script.")
        return
    
    print("⚡ DLR/SLR Data Loader for 118.db")
    print("=" * 40)
    print(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    print(f"Data folder: {DLR_SLR_FOLDER}")
    print(f"Log file: dlr_slr_import.log")
    print("Features: Minimal table structure + Exact CSV data preservation")
    
    # Create loader and run
    loader = DLR_SLR_Loader(DB_CONFIG)
    
    print(f"\n🚀 Starting DLR/SLR import at {datetime.now()}")
    success = loader.import_dlr_slr_folder(DLR_SLR_FOLDER)
    
    if success:
        print("\n✅ DLR/SLR import completed successfully!")
        print("Tables created: dlr_cases, dlr_buses, dlr_branches, dlr_generators, dlr_loads")
        print("               slr_cases, slr_buses, slr_branches, slr_generators, slr_loads")
    else:
        print("\n⚠️ Import completed with errors. Check the log file.")
    
    print(f"Finished at {datetime.now()}")

if __name__ == "__main__":
    main()