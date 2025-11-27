#!/usr/bin/env python3
"""
Load PF/QF data from contingency text files into existing contingency tables
"""

import psycopg2
import logging
import os
from pathlib import Path
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ContingencyPowerFlowLoader:
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
    
    def get_contingency_case_mapping(self):
        """Create mapping from file names to contingency_case_id"""
        try:
            # Get all contingency cases from the database
            self.cursor.execute("""
                SELECT contingency_case_id, from_bus, to_bus, circuit_id 
                FROM contingencybranchdata 
                WHERE contingency_case_id IS NOT NULL
                GROUP BY contingency_case_id, from_bus, to_bus, circuit_id
                ORDER BY contingency_case_id
                LIMIT 1000
            """)
            
            case_data = self.cursor.fetchall()
            
            # Create simple mapping: file number -> first available case ID
            case_mapping = {}
            used_case_ids = set()
            
            for case_id, from_bus, to_bus, circuit_id in case_data:
                if case_id not in used_case_ids:
                    file_num = len(case_mapping)
                    case_mapping[file_num] = case_id
                    used_case_ids.add(case_id)
                    
                    if len(case_mapping) >= 577:  # We have 577 files
                        break
            
            logging.info(f"Created mapping for {len(case_mapping)} contingency cases")
            return case_mapping
            
        except Exception as e:
            logging.error(f"Error creating case mapping: {e}")
            return {}
    
    def parse_text_file(self, file_path):
        """Parse contingency text file to extract branch power flow data"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            branch_data = []
            lines = content.strip().split('\n')
            
            # Look for branch data (usually after bus data)
            # Format is typically: branch_num from_bus to_bus circuit_id pf qf pt qt ...
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Try to parse as branch data line
                parts = line.split()
                if len(parts) >= 6:  # Need at least: from_bus to_bus circuit_id pf qf ...
                    try:
                        # Different possible formats, try to identify which one
                        if len(parts) >= 9 and all(self.is_number(parts[i]) for i in range(6)):
                            # Format: branch_num from_bus to_bus circuit_id pf qf ...
                            branch_num = int(parts[0])
                            from_bus = int(parts[1])
                            to_bus = int(parts[2])
                            circuit_id = int(parts[3])
                            pf = float(parts[4])
                            qf = float(parts[5])
                        elif len(parts) >= 8 and all(self.is_number(parts[i]) for i in range(5)):
                            # Format: from_bus to_bus circuit_id pf qf ...
                            from_bus = int(parts[0])
                            to_bus = int(parts[1])
                            circuit_id = int(parts[2])
                            pf = float(parts[3])
                            qf = float(parts[4])
                        else:
                            continue
                        
                        # Validate reasonable bus numbers (1-118 for IEEE 118 system)
                        if 1 <= from_bus <= 118 and 1 <= to_bus <= 118:
                            branch_data.append({
                                'from_bus': from_bus,
                                'to_bus': to_bus,
                                'circuit_id': circuit_id,
                                'pf': pf,
                                'qf': qf
                            })
                            
                    except (ValueError, IndexError):
                        continue
            
            return branch_data
            
        except Exception as e:
            logging.error(f"Error parsing {file_path}: {e}")
            return []
    
    def is_number(self, s):
        """Check if string can be converted to a number"""
        try:
            float(s)
            return True
        except ValueError:
            return False
    
    def load_file_data(self, file_path, contingency_case_id):
        """Load power flow data from one text file into database"""
        try:
            branch_data = self.parse_text_file(file_path)
            
            if not branch_data:
                logging.warning(f"No branch data found in {Path(file_path).name}")
                return 0
            
            updated_count = 0
            for branch in branch_data:
                try:
                    self.cursor.execute("""
                        UPDATE contingencybranchdata 
                        SET 
                            pf = %s, 
                            qf = %s,
                            mva = SQRT(%s * %s + %s * %s),
                            vio = CASE 
                                WHEN rate > 0 THEN 
                                    GREATEST(0, SQRT(%s * %s + %s * %s) - rate)
                                ELSE 0 
                            END
                        WHERE contingency_case_id = %s 
                            AND from_bus = %s 
                            AND to_bus = %s 
                            AND circuit_id = %s
                    """, (
                        branch['pf'], branch['qf'],
                        branch['pf'], branch['pf'], branch['qf'], branch['qf'],  # for mva 
                        branch['pf'], branch['pf'], branch['qf'], branch['qf'],  # for vio
                        contingency_case_id,
                        branch['from_bus'],
                        branch['to_bus'], 
                        branch['circuit_id']
                    ))
                    
                    if self.cursor.rowcount > 0:
                        updated_count += 1
                        
                except Exception as e:
                    logging.warning(f"Failed to update branch {branch['from_bus']}-{branch['to_bus']}-{branch['circuit_id']}: {e}")
            
            self.conn.commit()
            return updated_count
            
        except Exception as e:
            logging.error(f"Error loading data from {file_path}: {e}")
            return 0
    
    def load_all_files(self, text_folder):
        """Load power flow data from all contingency text files"""
        if not self.connect_database():
            return False
        
        try:
            # Get case mapping
            case_mapping = self.get_contingency_case_mapping()
            if not case_mapping:
                logging.error("No case mapping available!")
                return False
            
            # Get all text files
            text_files = list(Path(text_folder).glob('*.txt'))
            total_files = len(text_files)
            
            logging.info(f"Found {total_files} text files to process")
            
            successful = 0
            failed = 0
            
            for i, file_path in enumerate(text_files):
                # Extract file number from filename (e.g., CA_0_bus118_42.txt -> 42)
                file_name = file_path.stem
                match = re.search(r'(\d+)$', file_name)
                if match:
                    file_num = int(match.group(1))
                else:
                    file_num = i  # fallback to index
                
                # Get corresponding case ID
                case_id = case_mapping.get(file_num % len(case_mapping))
                if not case_id:
                    case_id = list(case_mapping.values())[i % len(case_mapping.values())]
                
                logging.info(f"Processing {i+1}/{total_files}: {file_path.name} -> Case {case_id}")
                
                updated_count = self.load_file_data(file_path, case_id)
                
                if updated_count > 0:
                    successful += 1
                    logging.info(f"  Updated {updated_count} branch records")
                else:
                    failed += 1
                    logging.warning(f"  Failed to update any records")
                
                # Progress update
                if (i + 1) % 50 == 0:
                    logging.info(f"Progress: {i+1}/{total_files} ({(i+1)/total_files*100:.1f}%)")
            
            # Final summary
            logging.info(f"\n=== LOADING COMPLETE ===")
            logging.info(f"Total files: {total_files}")
            logging.info(f"Successful: {successful}")
            logging.info(f"Failed: {failed}")
            
            # Check final status
            self.cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN pf != 0 OR qf != 0 THEN 1 END) as with_power_flow,
                    COUNT(CASE WHEN vio > 0 THEN 1 END) as with_violations,
                    MAX(vio) as max_violation
                FROM contingencybranchdata
            """)
            
            stats = self.cursor.fetchone()
            logging.info(f"\nFinal Database Status:")
            logging.info(f"  Total records: {stats[0]}")
            logging.info(f"  With power flow: {stats[1]}")
            logging.info(f"  With violations: {stats[2]}")
            logging.info(f"  Max violation: {stats[3]:.2f} MVA")
            
            return successful > 0
            
        except Exception as e:
            logging.error(f"Error during bulk loading: {e}")
            return False
        finally:
            self.disconnect_database()

def main():
    """Main function"""
    
    DB_CONFIG = {
        'host': 'localhost',
        'port': '5432',
        'database': '118',
        'user': 'postgres',
        'password': 'pnnl'
    }
    
    TEXT_FOLDER = r"C:\Projects\dlr-database-project\contingency_118"
    
    if not os.path.exists(TEXT_FOLDER):
        print(f"❌ Error: Folder '{TEXT_FOLDER}' does not exist!")
        return
    
    print("🔄 Loading PF/QF data from contingency text files...")
    print(f"Text folder: {TEXT_FOLDER}")
    print(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    
    loader = ContingencyPowerFlowLoader(DB_CONFIG)
    
    success = loader.load_all_files(TEXT_FOLDER)
    
    if success:
        print("\n✅ Power flow data loaded successfully!")
    else:
        print("\n❌ Power flow data loading failed!")

if __name__ == "__main__":
    main()