"""
SLR/DLR Data Loader for 118.db PostgreSQL Database
Loads Static Load Relief (SLR) and Dynamic Line Rating (DLR) data
Links to existing base cases and contingency cases
"""

import pandas as pd
import psycopg2
import os
import time
from pathlib import Path
import logging
from datetime import datetime
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('slr_dlr_import.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class SLRDLRDataLoader:
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
    
    def create_slr_dlr_schema(self):
        """Create SLR/DLR tables linked to existing base and contingency cases"""
        try:
            logging.info("Creating SLR/DLR schema...")
            
            self.cursor.execute("""
                -- Drop existing SLR/DLR tables if they exist
                DROP TABLE IF EXISTS DLR_Actions CASCADE;
                DROP TABLE IF EXISTS SLR_Actions CASCADE;
                
                -- SLR (Static Load Relief) Actions Table
                CREATE TABLE SLR_Actions (
                    slr_action_id SERIAL PRIMARY KEY,
                    base_case_id INTEGER NOT NULL,
                    contingency_case_id INTEGER,
                    action_name TEXT NOT NULL,
                    bus_number INTEGER,
                    load_shed_mw REAL DEFAULT 0,
                    load_shed_mvar REAL DEFAULT 0,
                    action_priority INTEGER DEFAULT 1,
                    action_status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Foreign key constraints
                    FOREIGN KEY (base_case_id) REFERENCES BaseCases(base_case_id) ON DELETE CASCADE,
                    FOREIGN KEY (contingency_case_id) REFERENCES ContingencyCases(contingency_case_id) ON DELETE CASCADE,
                    
                    -- Ensure unique actions per case
                    UNIQUE(base_case_id, contingency_case_id, action_name)
                );
                
                -- DLR (Dynamic Line Rating) Actions Table  
                CREATE TABLE DLR_Actions (
                    dlr_action_id SERIAL PRIMARY KEY,
                    base_case_id INTEGER NOT NULL,
                    contingency_case_id INTEGER,
                    line_name TEXT NOT NULL,
                    from_bus INTEGER,
                    to_bus INTEGER,
                    circuit_id TEXT DEFAULT '1',
                    original_rating_mva REAL,
                    dynamic_rating_mva REAL,
                    temperature_celsius REAL,
                    wind_speed_mps REAL,
                    current_amps REAL,
                    rating_increase_percent REAL,
                    action_status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Foreign key constraints
                    FOREIGN KEY (base_case_id) REFERENCES BaseCases(base_case_id) ON DELETE CASCADE,
                    FOREIGN KEY (contingency_case_id) REFERENCES ContingencyCases(contingency_case_id) ON DELETE CASCADE,
                    
                    -- Ensure unique lines per case
                    UNIQUE(base_case_id, contingency_case_id, line_name, circuit_id)
                );
                
                -- Create indexes for better performance
                CREATE INDEX idx_slr_base_case ON SLR_Actions(base_case_id);
                CREATE INDEX idx_slr_contingency_case ON SLR_Actions(contingency_case_id);
                CREATE INDEX idx_slr_bus ON SLR_Actions(bus_number);
                
                CREATE INDEX idx_dlr_base_case ON DLR_Actions(base_case_id);
                CREATE INDEX idx_dlr_contingency_case ON DLR_Actions(contingency_case_id);
                CREATE INDEX idx_dlr_line ON DLR_Actions(from_bus, to_bus);
                
                -- Create summary views
                CREATE OR REPLACE VIEW SLR_Summary AS
                SELECT 
                    bc.filename as base_case_file,
                    cc.case_number as contingency_case,
                    COUNT(slr.slr_action_id) as slr_actions_count,
                    SUM(slr.load_shed_mw) as total_load_shed_mw,
                    SUM(slr.load_shed_mvar) as total_load_shed_mvar
                FROM SLR_Actions slr
                JOIN BaseCases bc ON slr.base_case_id = bc.base_case_id
                LEFT JOIN ContingencyCases cc ON slr.contingency_case_id = cc.contingency_case_id
                GROUP BY bc.filename, cc.case_number;
                
                CREATE OR REPLACE VIEW DLR_Summary AS
                SELECT 
                    bc.filename as base_case_file,
                    cc.case_number as contingency_case,
                    COUNT(dlr.dlr_action_id) as dlr_actions_count,
                    AVG(dlr.rating_increase_percent) as avg_rating_increase_percent,
                    MAX(dlr.rating_increase_percent) as max_rating_increase_percent
                FROM DLR_Actions dlr
                JOIN BaseCases bc ON dlr.base_case_id = bc.base_case_id
                LEFT JOIN ContingencyCases cc ON dlr.contingency_case_id = cc.contingency_case_id
                GROUP BY bc.filename, cc.case_number;
            """)
            
            self.conn.commit()
            logging.info("✅ SLR/DLR schema created successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error creating SLR/DLR schema: {e}")
            self.conn.rollback()
            return False
    
    def get_case_mapping(self):
        """Get mapping of base cases and contingency cases"""
        try:
            # Get base cases
            self.cursor.execute("""
                SELECT base_case_id, filename, case_number 
                FROM BaseCases 
                WHERE processing_status = 'completed'
                ORDER BY base_case_id
            """)
            base_cases = {row[1]: {'id': row[0], 'case_num': row[2]} for row in self.cursor.fetchall()}
            
            # Get contingency cases
            self.cursor.execute("""
                SELECT cc.contingency_case_id, cc.base_case_id, cc.case_number, bc.filename
                FROM ContingencyCases cc
                JOIN BaseCases bc ON cc.base_case_id = bc.base_case_id
                WHERE cc.processing_status = 'completed'
                ORDER BY cc.base_case_id, cc.case_number
            """)
            contingency_cases = {}
            for row in self.cursor.fetchall():
                key = f"{row[3]}_case_{row[2]}"  # filename_case_number
                contingency_cases[key] = {'id': row[0], 'base_id': row[1], 'case_num': row[2]}
            
            logging.info(f"Found {len(base_cases)} base cases and {len(contingency_cases)} contingency cases")
            return base_cases, contingency_cases
            
        except Exception as e:
            logging.error(f"Error getting case mapping: {e}")
            return {}, {}
    
    def import_slr_data(self, file_path, base_case_id, contingency_case_id=None):
        """Import SLR data from Excel file"""
        filename = os.path.basename(file_path)
        logging.info(f"Importing SLR data from {filename}")
        
        try:
            # Try to read the file with different possible sheet names
            excel_file = pd.ExcelFile(file_path)
            slr_sheet = None
            
            # Look for SLR-related sheet names
            for sheet in excel_file.sheet_names:
                if any(keyword in sheet.lower() for keyword in ['slr', 'load', 'shed', 'relief']):
                    slr_sheet = sheet
                    break
            
            if slr_sheet is None:
                slr_sheet = excel_file.sheet_names[0]  # Use first sheet if no SLR-specific found
            
            df = pd.read_excel(file_path, sheet_name=slr_sheet)
            logging.info(f"Reading SLR data from sheet '{slr_sheet}' with {len(df)} rows")
            
            # Clean column names
            df.columns = df.columns.str.strip().str.upper()
            
            # Map possible column variations
            column_mapping = {
                'ACTION_NAME': ['ACTION_NAME', 'ACTION', 'SLR_ACTION', 'NAME'],
                'BUS_NUMBER': ['BUS_NUMBER', 'BUS', 'BUS_NUM', 'NODE'],
                'LOAD_SHED_MW': ['LOAD_SHED_MW', 'MW_SHED', 'P_SHED', 'LOAD_MW'],
                'LOAD_SHED_MVAR': ['LOAD_SHED_MVAR', 'MVAR_SHED', 'Q_SHED', 'LOAD_MVAR'],
                'PRIORITY': ['PRIORITY', 'ACTION_PRIORITY', 'RANK'],
                'STATUS': ['STATUS', 'ACTION_STATUS', 'STATE']
            }
            
            # Standardize column names
            for standard_col, variations in column_mapping.items():
                for col in df.columns:
                    if col in variations:
                        df.rename(columns={col: standard_col}, inplace=True)
                        break
            
            # Import data
            imported_count = 0
            for idx, row in df.iterrows():
                try:
                    # Extract values with defaults
                    action_name = str(row.get('ACTION_NAME', f'SLR_Action_{idx+1}'))
                    bus_number = int(row['BUS_NUMBER']) if 'BUS_NUMBER' in row and pd.notna(row['BUS_NUMBER']) else None
                    load_shed_mw = float(row.get('LOAD_SHED_MW', 0)) if pd.notna(row.get('LOAD_SHED_MW')) else 0
                    load_shed_mvar = float(row.get('LOAD_SHED_MVAR', 0)) if pd.notna(row.get('LOAD_SHED_MVAR')) else 0
                    priority = int(row.get('PRIORITY', 1)) if pd.notna(row.get('PRIORITY')) else 1
                    status = str(row.get('STATUS', 'active'))
                    
                    self.cursor.execute("""
                        INSERT INTO SLR_Actions 
                        (base_case_id, contingency_case_id, action_name, bus_number, 
                         load_shed_mw, load_shed_mvar, action_priority, action_status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (base_case_id, contingency_case_id, action_name) 
                        DO UPDATE SET
                            bus_number = EXCLUDED.bus_number,
                            load_shed_mw = EXCLUDED.load_shed_mw,
                            load_shed_mvar = EXCLUDED.load_shed_mvar,
                            action_priority = EXCLUDED.action_priority,
                            action_status = EXCLUDED.action_status
                    """, (base_case_id, contingency_case_id, action_name, bus_number,
                          load_shed_mw, load_shed_mvar, priority, status))
                    
                    imported_count += 1
                    
                except Exception as e:
                    logging.warning(f"Failed to import SLR row {idx+1}: {e}")
            
            logging.info(f"✅ Imported {imported_count} SLR actions from {filename}")
            return imported_count
            
        except Exception as e:
            logging.error(f"Error importing SLR data from {filename}: {e}")
            return 0
    
    def import_dlr_data(self, file_path, base_case_id, contingency_case_id=None):
        """Import DLR data from Excel file"""
        filename = os.path.basename(file_path)
        logging.info(f"Importing DLR data from {filename}")
        
        try:
            # Try to read the file with different possible sheet names
            excel_file = pd.ExcelFile(file_path)
            dlr_sheet = None
            
            # Look for DLR-related sheet names
            for sheet in excel_file.sheet_names:
                if any(keyword in sheet.lower() for keyword in ['dlr', 'dynamic', 'rating', 'line']):
                    dlr_sheet = sheet
                    break
            
            if dlr_sheet is None:
                dlr_sheet = excel_file.sheet_names[0]  # Use first sheet if no DLR-specific found
            
            df = pd.read_excel(file_path, sheet_name=dlr_sheet)
            logging.info(f"Reading DLR data from sheet '{dlr_sheet}' with {len(df)} rows")
            
            # Clean column names
            df.columns = df.columns.str.strip().str.upper()
            
            # Map possible column variations
            column_mapping = {
                'LINE_NAME': ['LINE_NAME', 'LINE', 'BRANCH_NAME', 'NAME'],
                'FROM_BUS': ['FROM_BUS', 'FROM', 'F_BUS', 'BUS_FROM'],
                'TO_BUS': ['TO_BUS', 'TO', 'T_BUS', 'BUS_TO'],
                'CIRCUIT_ID': ['CIRCUIT_ID', 'CKT', 'CIRCUIT', 'ID'],
                'ORIGINAL_RATING': ['ORIGINAL_RATING', 'RATING_MVA', 'ORIGINAL_MVA', 'BASE_RATING'],
                'DYNAMIC_RATING': ['DYNAMIC_RATING', 'DLR_MVA', 'NEW_RATING', 'DYNAMIC_MVA'],
                'TEMPERATURE': ['TEMPERATURE', 'TEMP_C', 'TEMPERATURE_C', 'AMBIENT_TEMP'],
                'WIND_SPEED': ['WIND_SPEED', 'WIND_MPS', 'WIND', 'WIND_SPEED_MPS'],
                'CURRENT': ['CURRENT', 'CURRENT_AMPS', 'AMPS', 'I_AMPS'],
                'STATUS': ['STATUS', 'ACTION_STATUS', 'STATE']
            }
            
            # Standardize column names
            for standard_col, variations in column_mapping.items():
                for col in df.columns:
                    if col in variations:
                        df.rename(columns={col: standard_col}, inplace=True)
                        break
            
            # Import data
            imported_count = 0
            for idx, row in df.iterrows():
                try:
                    # Extract values with defaults
                    line_name = str(row.get('LINE_NAME', f'Line_{idx+1}'))
                    from_bus = int(row['FROM_BUS']) if 'FROM_BUS' in row and pd.notna(row['FROM_BUS']) else None
                    to_bus = int(row['TO_BUS']) if 'TO_BUS' in row and pd.notna(row['TO_BUS']) else None
                    circuit_id = str(row.get('CIRCUIT_ID', '1'))
                    original_rating = float(row.get('ORIGINAL_RATING', 0)) if pd.notna(row.get('ORIGINAL_RATING')) else None
                    dynamic_rating = float(row.get('DYNAMIC_RATING', 0)) if pd.notna(row.get('DYNAMIC_RATING')) else None
                    temperature = float(row.get('TEMPERATURE', 0)) if pd.notna(row.get('TEMPERATURE')) else None
                    wind_speed = float(row.get('WIND_SPEED', 0)) if pd.notna(row.get('WIND_SPEED')) else None
                    current = float(row.get('CURRENT', 0)) if pd.notna(row.get('CURRENT')) else None
                    status = str(row.get('STATUS', 'active'))
                    
                    # Calculate rating increase percentage
                    rating_increase = None
                    if original_rating and dynamic_rating and original_rating > 0:
                        rating_increase = ((dynamic_rating - original_rating) / original_rating) * 100
                    
                    self.cursor.execute("""
                        INSERT INTO DLR_Actions 
                        (base_case_id, contingency_case_id, line_name, from_bus, to_bus, 
                         circuit_id, original_rating_mva, dynamic_rating_mva, 
                         temperature_celsius, wind_speed_mps, current_amps, 
                         rating_increase_percent, action_status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (base_case_id, contingency_case_id, line_name, circuit_id) 
                        DO UPDATE SET
                            from_bus = EXCLUDED.from_bus,
                            to_bus = EXCLUDED.to_bus,
                            original_rating_mva = EXCLUDED.original_rating_mva,
                            dynamic_rating_mva = EXCLUDED.dynamic_rating_mva,
                            temperature_celsius = EXCLUDED.temperature_celsius,
                            wind_speed_mps = EXCLUDED.wind_speed_mps,
                            current_amps = EXCLUDED.current_amps,
                            rating_increase_percent = EXCLUDED.rating_increase_percent,
                            action_status = EXCLUDED.action_status
                    """, (base_case_id, contingency_case_id, line_name, from_bus, to_bus,
                          circuit_id, original_rating, dynamic_rating, temperature, 
                          wind_speed, current, rating_increase, status))
                    
                    imported_count += 1
                    
                except Exception as e:
                    logging.warning(f"Failed to import DLR row {idx+1}: {e}")
            
            logging.info(f"✅ Imported {imported_count} DLR actions from {filename}")
            return imported_count
            
        except Exception as e:
            logging.error(f"Error importing DLR data from {filename}: {e}")
            return 0
    
    def import_slr_dlr_folder(self, folder_path):
        """Import all SLR/DLR files from a folder"""
        if not self.connect_database():
            return False
        
        try:
            # Create schema first
            if not self.create_slr_dlr_schema():
                return False
            
            # Get case mappings
            base_cases, contingency_cases = self.get_case_mapping()
            
            if not base_cases:
                logging.error("No base cases found in database!")
                return False
            
            folder_path = Path(folder_path)
            total_slr = 0
            total_dlr = 0
            
            # Process all Excel files in the folder
            for file_path in folder_path.rglob("*.xlsx"):
                try:
                    filename = file_path.name
                    logging.info(f"\n--- Processing {filename} ---")
                    
                    # Try to determine which case this file belongs to
                    base_case_id = None
                    contingency_case_id = None
                    
                    # Look for case identifier in filename or folder structure
                    if 'SLR' in filename.upper() or 'LOAD' in filename.upper():
                        # Try to match to a base case or contingency case
                        for case_name, case_info in base_cases.items():
                            if any(part in filename for part in case_name.split('_')):
                                base_case_id = case_info['id']
                                break
                        
                        if base_case_id:
                            slr_count = self.import_slr_data(file_path, base_case_id, contingency_case_id)
                            total_slr += slr_count
                    
                    if 'DLR' in filename.upper() or 'DYNAMIC' in filename.upper() or 'RATING' in filename.upper():
                        # Try to match to a base case or contingency case
                        for case_name, case_info in base_cases.items():
                            if any(part in filename for part in case_name.split('_')):
                                base_case_id = case_info['id']
                                break
                        
                        if base_case_id:
                            dlr_count = self.import_dlr_data(file_path, base_case_id, contingency_case_id)
                            total_dlr += dlr_count
                    
                    # If no specific type detected, try both
                    if 'SLR' not in filename.upper() and 'DLR' not in filename.upper():
                        for case_name, case_info in base_cases.items():
                            if any(part in filename for part in case_name.split('_')):
                                base_case_id = case_info['id']
                                break
                        
                        if base_case_id:
                            slr_count = self.import_slr_data(file_path, base_case_id, contingency_case_id)
                            dlr_count = self.import_dlr_data(file_path, base_case_id, contingency_case_id)
                            total_slr += slr_count
                            total_dlr += dlr_count
                    
                except Exception as e:
                    logging.error(f"Error processing {file_path}: {e}")
                    continue
            
            self.conn.commit()
            
            logging.info(f"\n🎉 Import Complete!")
            logging.info(f"   Total SLR actions imported: {total_slr}")
            logging.info(f"   Total DLR actions imported: {total_dlr}")
            
            # Show summary
            self.show_import_summary()
            
            return True
            
        except Exception as e:
            logging.error(f"Error during SLR/DLR folder import: {e}")
            return False
        finally:
            self.disconnect_database()
    
    def show_import_summary(self):
        """Show summary of imported SLR/DLR data"""
        try:
            # SLR Summary
            self.cursor.execute("SELECT COUNT(*) FROM SLR_Actions")
            slr_count = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT SUM(load_shed_mw) FROM SLR_Actions")
            total_load_shed = self.cursor.fetchone()[0] or 0
            
            # DLR Summary
            self.cursor.execute("SELECT COUNT(*) FROM DLR_Actions")
            dlr_count = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT AVG(rating_increase_percent) FROM DLR_Actions WHERE rating_increase_percent IS NOT NULL")
            avg_rating_increase = self.cursor.fetchone()[0] or 0
            
            logging.info(f"\n📊 Database Summary:")
            logging.info(f"   SLR Actions: {slr_count}")
            logging.info(f"   Total Load Shed: {total_load_shed:.2f} MW")
            logging.info(f"   DLR Actions: {dlr_count}")
            logging.info(f"   Avg Rating Increase: {avg_rating_increase:.2f}%")
            
        except Exception as e:
            logging.error(f"Error showing summary: {e}")

def main():
    """Main function to run SLR/DLR import"""
    
    # Database configuration
    DB_CONFIG = {
        'host': 'localhost',
        'port': '5432',
        'database': '118',  # Your 118.db database
        'user': 'postgres',
        'password': 'pnnl'
    }
    
    # Path to your SLR/DLR data folder
    SLR_DLR_FOLDER = r"C:\Users\nira771\slr_dlr_cor_action"
    
    # Verify folder exists
    if not os.path.exists(SLR_DLR_FOLDER):
        print(f"❌ Error: Folder '{SLR_DLR_FOLDER}' does not exist!")
        print("Please update the SLR_DLR_FOLDER path in the script.")
        return
    
    print("⚡ SLR/DLR Data Loader for 118.db")
    print("=" * 40)
    print(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    print(f"Data folder: {SLR_DLR_FOLDER}")
    print(f"Log file: slr_dlr_import.log")
    
    # Create loader and run
    loader = SLRDLRDataLoader(DB_CONFIG)
    
    print(f"\n🚀 Starting SLR/DLR import at {datetime.now()}")
    success = loader.import_slr_dlr_folder(SLR_DLR_FOLDER)
    
    if success:
        print("\n✅ SLR/DLR import completed successfully!")
    else:
        print("\n⚠️ Import completed with errors. Check the log file.")
    
    print(f"Finished at {datetime.now()}")

if __name__ == "__main__":
    main()