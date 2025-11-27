"""
Corrective Actions Data Loader for 118.db PostgreSQL Database
Processes corrective action CSV files with post-action power flow data
Handles generator and load corrective actions for contingency cases
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
        logging.FileHandler('corrective_actions_import.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class CorrectiveActionsLoader:
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
    
    def create_corrective_actions_schema(self):
        """Create corrective actions tables"""
        try:
            logging.info("Creating corrective actions schema...")
            
            self.cursor.execute("""
                -- Drop existing tables if they exist
                DROP TABLE IF EXISTS PostAction_BranchData CASCADE;
                DROP TABLE IF EXISTS PostAction_BusData CASCADE;
                DROP TABLE IF EXISTS LoadCorrectiveActions CASCADE;
                DROP TABLE IF EXISTS GeneratorCorrectiveActions CASCADE;
                DROP TABLE IF EXISTS ContingencyDetails CASCADE;
                
                -- Contingency Details Table (enhanced)
                CREATE TABLE ContingencyDetails (
                    contingency_detail_id SERIAL PRIMARY KEY,
                    base_case_id INTEGER NOT NULL,
                    contingency_case_id INTEGER,
                    contingency_index INTEGER NOT NULL,
                    tripped_line_index INTEGER NOT NULL,
                    from_bus INTEGER NOT NULL,
                    to_bus INTEGER NOT NULL,
                    line_id TEXT DEFAULT '1',
                    contingency_name TEXT NOT NULL,
                    data_source_folder TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Foreign key constraints
                    FOREIGN KEY (base_case_id) REFERENCES base_cases(case_id) ON DELETE CASCADE,
                    FOREIGN KEY (contingency_case_id) REFERENCES contingency_cases(id) ON DELETE CASCADE,
                    
                    -- Ensure unique contingencies
                    UNIQUE(base_case_id, contingency_index, from_bus, to_bus, line_id)
                );
                
                -- Generator Corrective Actions Table
                CREATE TABLE GeneratorCorrectiveActions (
                    gen_action_id SERIAL PRIMARY KEY,
                    contingency_detail_id INTEGER NOT NULL,
                    bus_number INTEGER NOT NULL,
                    generator_id TEXT DEFAULT 'G1',
                    action_type TEXT DEFAULT 'generation_adjustment',
                    pg_mw REAL,
                    qg_mvar REAL,
                    voltage_setpoint REAL,
                    status INTEGER DEFAULT 1,
                    cost_per_mw REAL,
                    -- Additional columns to store exact CSV data
                    gen_initial_mw REAL,
                    gen_final_mw REAL,
                    gen_adjustment_mw REAL,
                    kv_level REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (contingency_detail_id) REFERENCES ContingencyDetails(contingency_detail_id) ON DELETE CASCADE,
                    UNIQUE(contingency_detail_id, bus_number, generator_id)
                );
                
                -- Load Corrective Actions Table  
                CREATE TABLE LoadCorrectiveActions (
                    load_action_id SERIAL PRIMARY KEY,
                    contingency_detail_id INTEGER NOT NULL,
                    bus_number INTEGER NOT NULL,
                    action_type TEXT DEFAULT 'load_shedding',
                    pd_mw REAL,
                    qd_mvar REAL,
                    load_priority INTEGER DEFAULT 1,
                    shed_amount_mw REAL,
                    shed_amount_mvar REAL,
                    cost_per_mw REAL,
                    -- Additional columns to store exact CSV data
                    load_initial_mw REAL,
                    load_final_mw REAL,
                    load_adjustment_mw REAL,
                    kv_level REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (contingency_detail_id) REFERENCES ContingencyDetails(contingency_detail_id) ON DELETE CASCADE,
                    UNIQUE(contingency_detail_id, bus_number)
                );
                
                -- Post-Action Bus Data Table
                CREATE TABLE PostAction_BusData (
                    post_bus_id SERIAL PRIMARY KEY,
                    contingency_detail_id INTEGER NOT NULL,
                    bus_number INTEGER NOT NULL,
                    vm_pu REAL,
                    va_degrees REAL,
                    base_kv REAL,
                    pg_mw REAL,
                    qg_mvar REAL,
                    pd_mw REAL,
                    qd_mvar REAL,
                    bus_type INTEGER DEFAULT 1,
                    
                    FOREIGN KEY (contingency_detail_id) REFERENCES ContingencyDetails(contingency_detail_id) ON DELETE CASCADE,
                    UNIQUE(contingency_detail_id, bus_number)
                );
                
                -- Post-Action Branch Data Table
                CREATE TABLE PostAction_BranchData (
                    post_branch_id SERIAL PRIMARY KEY,
                    contingency_detail_id INTEGER NOT NULL,
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
                    violation_flag BOOLEAN DEFAULT FALSE,
                    
                    FOREIGN KEY (contingency_detail_id) REFERENCES ContingencyDetails(contingency_detail_id) ON DELETE CASCADE,
                    UNIQUE(contingency_detail_id, from_bus, to_bus, circuit_id)
                );
                
                -- Create indexes for performance
                CREATE INDEX idx_contingency_detail_base ON ContingencyDetails(base_case_id);
                CREATE INDEX idx_contingency_detail_line ON ContingencyDetails(from_bus, to_bus);
                CREATE INDEX idx_gen_action_bus ON GeneratorCorrectiveActions(bus_number);
                CREATE INDEX idx_load_action_bus ON LoadCorrectiveActions(bus_number);
                CREATE INDEX idx_post_bus_number ON PostAction_BusData(bus_number);
                CREATE INDEX idx_post_branch_line ON PostAction_BranchData(from_bus, to_bus);
                
                -- Create summary views for analysis
                CREATE OR REPLACE VIEW CorrectiveActions_Summary AS
                SELECT 
                    cd.contingency_name,
                    cd.from_bus,
                    cd.to_bus,
                    cd.line_id,
                    COUNT(DISTINCT gca.gen_action_id) as generator_actions,
                    COUNT(DISTINCT lca.load_action_id) as load_actions,
                    SUM(lca.shed_amount_mw) as total_load_shed_mw,
                    SUM(lca.shed_amount_mvar) as total_load_shed_mvar,
                    AVG(pbd.loading_percent) as avg_loading_percent,
                    MAX(pbd.loading_percent) as max_loading_percent
                FROM ContingencyDetails cd
                LEFT JOIN GeneratorCorrectiveActions gca ON cd.contingency_detail_id = gca.contingency_detail_id
                LEFT JOIN LoadCorrectiveActions lca ON cd.contingency_detail_id = lca.contingency_detail_id
                LEFT JOIN PostAction_BranchData pbd ON cd.contingency_detail_id = pbd.contingency_detail_id
                GROUP BY cd.contingency_detail_id, cd.contingency_name, cd.from_bus, cd.to_bus, cd.line_id;
                
                CREATE OR REPLACE VIEW ContingencyImprovements AS
                SELECT 
                    cd.contingency_name,
                    cd.from_bus || ' - ' || cd.to_bus as tripped_line,
                    SUM(lca.shed_amount_mw) as load_shed_mw,
                    COUNT(DISTINCT CASE WHEN pbd.violation_flag THEN pbd.post_branch_id END) as violations_remaining,
                    AVG(CASE WHEN pbd.loading_percent > 100 THEN pbd.loading_percent ELSE NULL END) as avg_overload_percent
                FROM ContingencyDetails cd
                LEFT JOIN LoadCorrectiveActions lca ON cd.contingency_detail_id = lca.contingency_detail_id
                LEFT JOIN PostAction_BranchData pbd ON cd.contingency_detail_id = pbd.contingency_detail_id
                GROUP BY cd.contingency_detail_id, cd.contingency_name, cd.from_bus, cd.to_bus;
            """)
            
            self.conn.commit()
            logging.info("✅ Corrective actions schema created successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error creating corrective actions schema: {e}")
            self.conn.rollback()
            return False
    
    def parse_contingency_filename(self, filename):
        """Parse contingency information from filename"""
        try:
            # Pattern: idx_122_line_77_80 or idx_123_line_77_82_1
            match = re.search(r'idx_(\d+)_line_(\d+)_(\d+)(?:_(\d+))?', filename)
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
    
    def get_base_case_42_id(self):
        """Get a base case ID (using first available since we can't identify case 42 specifically)"""
        try:
            self.cursor.execute("""
                SELECT case_id FROM base_cases 
                ORDER BY case_id LIMIT 1
            """)
            result = self.cursor.fetchone()
            if result:
                logging.info(f"Using base case ID: {result[0]} (first available)")
                return result[0]
            return None
        except Exception as e:
            logging.error(f"Error getting base case ID: {e}")
            return None
    
    def create_contingency_detail(self, base_case_id, contingency_info, data_source_folder):
        """Create or get contingency detail record"""
        try:
            # Try to insert, or get existing
            self.cursor.execute("""
                INSERT INTO ContingencyDetails 
                (base_case_id, contingency_index, tripped_line_index, from_bus, to_bus, 
                 line_id, contingency_name, data_source_folder)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (base_case_id, contingency_index, from_bus, to_bus, line_id)
                DO UPDATE SET data_source_folder = EXCLUDED.data_source_folder
                RETURNING contingency_detail_id
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
            logging.error(f"Error creating contingency detail: {e}")
            return None
    
    def import_generator_corrective_actions(self, file_path, contingency_detail_id):
        """Import generator corrective actions from CSV exactly as they appear"""
        try:
            df = pd.read_csv(file_path)
            logging.info(f"Importing {len(df)} generator corrective actions from {file_path.name}")
            
            # Clean column names but preserve original structure
            df.columns = df.columns.str.strip().str.upper()
            
            # Print actual columns for debugging
            logging.info(f"CSV columns: {list(df.columns)}")
            
            imported_count = 0
            for _, row in df.iterrows():
                try:
                    # Use the actual column names from your CSV files
                    bus_number = int(row.get('BUS_NUMBER', 0))
                    if bus_number == 0:
                        continue
                    
                    # Extract values exactly as they appear in CSV
                    gen_ini = float(row.get('GEN-INI', 0)) if pd.notna(row.get('GEN-INI')) else None
                    gen_new = float(row.get('GEN-NEW', 0)) if pd.notna(row.get('GEN-NEW')) else None
                    gen_adj = float(row.get('GEN-ADJ', 0)) if pd.notna(row.get('GEN-ADJ')) else None
                    kv_level = float(row.get('KV_LEVEL', 138.0)) if pd.notna(row.get('KV_LEVEL')) else None
                    
                    self.cursor.execute("""
                        INSERT INTO GeneratorCorrectiveActions
                        (contingency_detail_id, bus_number, generator_id, pg_mw, qg_mvar, 
                         voltage_setpoint, status, gen_initial_mw, gen_final_mw, gen_adjustment_mw, kv_level)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (contingency_detail_id, bus_number, generator_id)
                        DO UPDATE SET
                            pg_mw = EXCLUDED.pg_mw,
                            qg_mvar = EXCLUDED.qg_mvar,
                            voltage_setpoint = EXCLUDED.voltage_setpoint,
                            status = EXCLUDED.status,
                            gen_initial_mw = EXCLUDED.gen_initial_mw,
                            gen_final_mw = EXCLUDED.gen_final_mw,
                            gen_adjustment_mw = EXCLUDED.gen_adjustment_mw,
                            kv_level = EXCLUDED.kv_level
                    """, (
                        contingency_detail_id,
                        bus_number,
                        'G1',  # Default generator ID
                        gen_new,  # Use final generation as PG
                        0.0,      # Default QG
                        kv_level, # Use KV level as voltage setpoint
                        1,        # Active status
                        gen_ini,  # Store initial generation
                        gen_new,  # Store final generation
                        gen_adj,  # Store adjustment
                        kv_level  # Store voltage level
                    ))
                    imported_count += 1
                    
                except Exception as e:
                    logging.warning(f"Failed to import generator action row {bus_number}: {e}")
            
            logging.info(f"✅ Imported {imported_count} generator corrective actions")
            return imported_count
            
        except Exception as e:
            logging.error(f"Error importing generator corrective actions: {e}")
            return 0
    
    def import_load_corrective_actions(self, file_path, contingency_detail_id):
        """Import load corrective actions from CSV exactly as they appear"""
        try:
            df = pd.read_csv(file_path)
            logging.info(f"Importing {len(df)} load corrective actions from {file_path.name}")
            
            # Clean column names but preserve original structure
            df.columns = df.columns.str.strip().str.upper()
            
            # Print actual columns for debugging
            logging.info(f"CSV columns: {list(df.columns)}")
            
            imported_count = 0
            for _, row in df.iterrows():
                try:
                    # Use the actual column names from your CSV files
                    bus_number = int(row.get('BUS_NUMBER', 0))
                    if bus_number == 0:
                        continue
                    
                    # Extract values exactly as they appear in CSV
                    load_ini = float(row.get('LOAD-INI', 0)) if pd.notna(row.get('LOAD-INI')) else 0
                    load_new = float(row.get('LOAD-NEW', 0)) if pd.notna(row.get('LOAD-NEW')) else 0
                    load_adj = float(row.get('LOAD-ADJ', 0)) if pd.notna(row.get('LOAD-ADJ')) else 0
                    kv_level = float(row.get('KV_LEVEL', 138.0)) if pd.notna(row.get('KV_LEVEL')) else None
                    
                    # Load adjustment is the shed amount
                    shed_mw = load_adj  # Direct from CSV
                    
                    self.cursor.execute("""
                        INSERT INTO LoadCorrectiveActions
                        (contingency_detail_id, bus_number, pd_mw, qd_mvar, 
                         shed_amount_mw, shed_amount_mvar, load_priority, 
                         load_initial_mw, load_final_mw, load_adjustment_mw, kv_level)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (contingency_detail_id, bus_number)
                        DO UPDATE SET
                            pd_mw = EXCLUDED.pd_mw,
                            qd_mvar = EXCLUDED.qd_mvar,
                            shed_amount_mw = EXCLUDED.shed_amount_mw,
                            shed_amount_mvar = EXCLUDED.shed_amount_mvar,
                            load_priority = EXCLUDED.load_priority,
                            load_initial_mw = EXCLUDED.load_initial_mw,
                            load_final_mw = EXCLUDED.load_final_mw,
                            load_adjustment_mw = EXCLUDED.load_adjustment_mw,
                            kv_level = EXCLUDED.kv_level
                    """, (
                        contingency_detail_id,
                        bus_number,
                        load_new,  # Final load as PD
                        0.0,       # Default QD
                        shed_mw,   # Shed amount from CSV
                        0.0,       # Default MVAR shed
                        1,         # Default priority
                        load_ini,  # Store initial load
                        load_new,  # Store final load
                        load_adj,  # Store adjustment
                        kv_level   # Store voltage level
                    ))
                    imported_count += 1
                    
                except Exception as e:
                    logging.warning(f"Failed to import load action row {bus_number}: {e}")
            
            logging.info(f"✅ Imported {imported_count} load corrective actions")
            return imported_count
            
        except Exception as e:
            logging.error(f"Error importing load corrective actions: {e}")
            return 0
    
    def import_post_action_bus_data(self, file_path, contingency_detail_id):
        """Import post-action bus data from CSV"""
        try:
            df = pd.read_csv(file_path)
            logging.info(f"Importing {len(df)} post-action bus records")
            
            # Clean column names
            df.columns = df.columns.str.strip().str.upper()
            
            imported_count = 0
            for _, row in df.iterrows():
                try:
                    bus_number = int(row.get('BUS', row.get('BUS_NUMBER', 0)))
                    if bus_number == 0:
                        continue
                    
                    self.cursor.execute("""
                        INSERT INTO PostAction_BusData
                        (contingency_detail_id, bus_number, vm_pu, va_degrees, base_kv,
                         pg_mw, qg_mvar, pd_mw, qd_mvar, bus_type)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (contingency_detail_id, bus_number)
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
                        contingency_detail_id,
                        bus_number,
                        float(row.get('VM', 1.0)) if pd.notna(row.get('VM')) else None,
                        float(row.get('VA', 0.0)) if pd.notna(row.get('VA')) else None,
                        float(row.get('BASE_KV', 138.0)) if pd.notna(row.get('BASE_KV')) else None,
                        float(row.get('PG', 0.0)) if pd.notna(row.get('PG')) else None,
                        float(row.get('QG', 0.0)) if pd.notna(row.get('QG')) else None,
                        float(row.get('PD', 0.0)) if pd.notna(row.get('PD')) else None,
                        float(row.get('QD', 0.0)) if pd.notna(row.get('QD')) else None,
                        int(row.get('TYPE', 1))
                    ))
                    imported_count += 1
                    
                except Exception as e:
                    logging.warning(f"Failed to import post-action bus row: {e}")
            
            logging.info(f"✅ Imported {imported_count} post-action bus records")
            return imported_count
            
        except Exception as e:
            logging.error(f"Error importing post-action bus data: {e}")
            return 0
    
    def import_post_action_branch_data(self, file_path, contingency_detail_id):
        """Import post-action branch data from CSV"""
        try:
            df = pd.read_csv(file_path)
            logging.info(f"Importing {len(df)} post-action branch records")
            
            # Clean column names
            df.columns = df.columns.str.strip().str.upper()
            
            imported_count = 0
            for _, row in df.iterrows():
                try:
                    from_bus = int(row.get('FROM', row.get('F_BUS', 0)))
                    to_bus = int(row.get('TO', row.get('T_BUS', 0)))
                    if from_bus == 0 or to_bus == 0:
                        continue
                    
                    pf = float(row.get('PF', 0)) if pd.notna(row.get('PF')) else None
                    qf = float(row.get('QF', 0)) if pd.notna(row.get('QF')) else None
                    rating = float(row.get('RATE', row.get('MVA_RATING', 0))) if pd.notna(row.get('RATE', row.get('MVA_RATING'))) else None
                    
                    # Calculate MVA flow and loading
                    mva_flow = None
                    loading_percent = None
                    violation = False
                    
                    if pf is not None and qf is not None:
                        mva_flow = (pf**2 + qf**2)**0.5
                        if rating and rating > 0:
                            loading_percent = (mva_flow / rating) * 100
                            violation = loading_percent > 100
                    
                    self.cursor.execute("""
                        INSERT INTO PostAction_BranchData
                        (contingency_detail_id, from_bus, to_bus, circuit_id, pf_mw, qf_mvar,
                         pt_mw, qt_mvar, mva_flow, mva_rating, loading_percent, violation_flag)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (contingency_detail_id, from_bus, to_bus, circuit_id)
                        DO UPDATE SET
                            pf_mw = EXCLUDED.pf_mw,
                            qf_mvar = EXCLUDED.qf_mvar,
                            pt_mw = EXCLUDED.pt_mw,
                            qt_mvar = EXCLUDED.qt_mvar,
                            mva_flow = EXCLUDED.mva_flow,
                            mva_rating = EXCLUDED.mva_rating,
                            loading_percent = EXCLUDED.loading_percent,
                            violation_flag = EXCLUDED.violation_flag
                    """, (
                        contingency_detail_id,
                        from_bus,
                        to_bus,
                        str(row.get('CKT', row.get('ID', '1'))),
                        pf,
                        qf,
                        float(row.get('PT', 0)) if pd.notna(row.get('PT')) else None,
                        float(row.get('QT', 0)) if pd.notna(row.get('QT')) else None,
                        mva_flow,
                        rating,
                        loading_percent,
                        violation
                    ))
                    imported_count += 1
                    
                except Exception as e:
                    logging.warning(f"Failed to import post-action branch row: {e}")
            
            logging.info(f"✅ Imported {imported_count} post-action branch records")
            return imported_count
            
        except Exception as e:
            logging.error(f"Error importing post-action branch data: {e}")
            return 0
    
    def import_corrective_actions_folder(self, folder_path):
        """Import all corrective action CSV files from flat file structure"""
        if not self.connect_database():
            return False
        
        try:
            # Create schema
            if not self.create_corrective_actions_schema():
                return False
            
            # Get base case 42 ID
            base_case_id = self.get_base_case_42_id()
            if base_case_id is None:
                logging.error("Could not find any base case in database!")
                return False
            
            logging.info(f"Using base case ID: {base_case_id}")
            
            folder_path = Path(folder_path)
            total_contingencies = 0
            contingency_details = {}
            
            # Get all CSV files and group by contingency
            csv_files = list(folder_path.glob("*.csv"))
            logging.info(f"Found {len(csv_files)} CSV files")
            
            # Group files by contingency pattern
            for csv_file in csv_files:
                filename = csv_file.name
                
                # Parse contingency info from filename (dlr_idx_122_line_77_80_2_branches.csv)
                match = re.search(r'(?:dlr_|slr_)?idx_(\d+)_line_(\d+)_(\d+)(?:_(\d+))?', filename)
                if not match:
                    logging.warning(f"Could not parse contingency from filename: {filename}")
                    continue
                
                idx = int(match.group(1))
                from_bus = int(match.group(2))
                to_bus = int(match.group(3))
                line_id = match.group(4) if match.group(4) else '1'
                
                contingency_key = f"idx_{idx}_line_{from_bus}_{to_bus}_{line_id}"
                
                if contingency_key not in contingency_details:
                    # Create contingency info
                    contingency_info = {
                        'contingency_index': idx,
                        'tripped_line_index': idx + 1,
                        'from_bus': from_bus,
                        'to_bus': to_bus,
                        'line_id': line_id,
                        'contingency_name': f"Line_{from_bus}_{to_bus}_{line_id}"
                    }
                    
                    # Create contingency detail record
                    contingency_detail_id = self.create_contingency_detail(
                        base_case_id, contingency_info, str(folder_path)
                    )
                    
                    if contingency_detail_id:
                        contingency_details[contingency_key] = {
                            'id': contingency_detail_id,
                            'info': contingency_info,
                            'files': []
                        }
                        total_contingencies += 1
                        logging.info(f"\n--- Created Contingency: {contingency_info['contingency_name']} ---")
                
                # Add file to contingency
                if contingency_key in contingency_details:
                    contingency_details[contingency_key]['files'].append(csv_file)
            
            # Process files for each contingency
            for contingency_key, contingency_data in contingency_details.items():
                contingency_detail_id = contingency_data['id']
                files = contingency_data['files']
                
                logging.info(f"\nProcessing {len(files)} files for {contingency_data['info']['contingency_name']}")
                
                for csv_file in files:
                    try:
                        filename = csv_file.name.lower()
                        
                        if 'cor_gen' in filename:
                            self.import_generator_corrective_actions(csv_file, contingency_detail_id)
                        elif 'cor_load' in filename:
                            self.import_load_corrective_actions(csv_file, contingency_detail_id)
                        elif 'bus' in filename:
                            self.import_post_action_bus_data(csv_file, contingency_detail_id)
                        elif 'branch' in filename:
                            self.import_post_action_branch_data(csv_file, contingency_detail_id)
                        else:
                            logging.info(f"Skipping unrecognized file: {csv_file.name}")
                    
                    except Exception as e:
                        logging.error(f"Error processing {csv_file}: {e}")
                        continue
                
                self.conn.commit()
            
            logging.info(f"\n🎉 Import Complete!")
            logging.info(f"   Total contingencies processed: {total_contingencies}")
            
            # Show summary
            self.show_import_summary()
            
            return True
            
        except Exception as e:
            logging.error(f"Error during corrective actions import: {e}")
            return False
        finally:
            self.disconnect_database()
    
    def show_import_summary(self):
        """Show summary of imported corrective actions data"""
        try:
            # Summary statistics
            self.cursor.execute("SELECT COUNT(*) FROM ContingencyDetails")
            contingency_count = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM GeneratorCorrectiveActions")
            gen_actions = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM LoadCorrectiveActions")
            load_actions = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT SUM(shed_amount_mw) FROM LoadCorrectiveActions")
            total_shed = self.cursor.fetchone()[0] or 0
            
            self.cursor.execute("""
                SELECT contingency_name, total_load_shed_mw, max_loading_percent 
                FROM CorrectiveActions_Summary 
                ORDER BY total_load_shed_mw DESC 
                LIMIT 5
            """)
            top_contingencies = self.cursor.fetchall()
            
            logging.info(f"\n📊 Import Summary:")
            logging.info(f"   Contingencies: {contingency_count}")
            logging.info(f"   Generator Actions: {gen_actions}")
            logging.info(f"   Load Actions: {load_actions}")
            logging.info(f"   Total Load Shed: {total_shed:.2f} MW")
            
            logging.info(f"\n🔥 Top Contingencies by Load Shed:")
            for contingency in top_contingencies:
                logging.info(f"   {contingency[0]}: {contingency[1]:.2f} MW shed, {contingency[2]:.1f}% max loading")
            
        except Exception as e:
            logging.error(f"Error showing summary: {e}")

def main():
    """Main function to run corrective actions import"""
    
    # Database configuration
    DB_CONFIG = {
        'host': 'localhost',
        'port': '5432',
        'database': '118',  # Your 118.db database
        'user': 'postgres',
        'password': 'pnnl'
    }
    
    # Path to your corrective actions data folder containing contingency subfolders
    CORRECTIVE_ACTIONS_FOLDER = r"C:\Users\nira771\slr_dlr_cor_action"
    
    # Verify folder exists
    if not os.path.exists(CORRECTIVE_ACTIONS_FOLDER):
        print(f"❌ Error: Folder '{CORRECTIVE_ACTIONS_FOLDER}' does not exist!")
        print("Please update the CORRECTIVE_ACTIONS_FOLDER path in the script.")
        return
    
    print("⚡ Corrective Actions Data Loader for Base Case 42")
    print("=" * 50)
    print(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    print(f"Data folder: {CORRECTIVE_ACTIONS_FOLDER}")
    print(f"Log file: corrective_actions_import.log")
    print("Target: idx_122_line_77_80 and idx_123_line_77_82_1 contingencies")
    
    # Create loader and run
    loader = CorrectiveActionsLoader(DB_CONFIG)
    
    print(f"\n🚀 Starting corrective actions import at {datetime.now()}")
    success = loader.import_corrective_actions_folder(CORRECTIVE_ACTIONS_FOLDER)
    
    if success:
        print("\n✅ Corrective actions import completed successfully!")
        print("\n📊 Ready for Figures 3 and 4 generation!")
        print("Key contingencies loaded: idx_122_line_77_80, idx_123_line_77_82_1")
        print("Data includes: Generator actions, Load shedding, Post-action power flows")
    else:
        print("\n⚠️ Import completed with errors. Check the log file.")
    
    print(f"Finished at {datetime.now()}")

if __name__ == "__main__":
    main()