#!/usr/bin/env python3
"""
Complete Power Flow Data Loader for Contingency Analysis
Ensures all 577 contingency cases get proper power flow data
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import math
from typing import Dict, List, Optional, Tuple
import glob

# Configure logging with UTF-8 encoding for Windows
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('power_flow_loader.log', encoding='utf-8')
    ]
)

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'database': '118',
    'user': 'postgres',
    'password': 'pnnl',
    'port': 5432
}

# File path configuration
CONTINGENCY_FOLDER = r"C:\Projects\dlr-database-project\contingency_118"

def get_database_connection():
    """Establish database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return None

def get_contingency_cases() -> Dict[int, int]:
    """Get mapping of case_number to contingency_case_id from database"""
    conn = get_database_connection()
    if not conn:
        return {}
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get all contingency cases with their case numbers
        cursor.execute("""
            SELECT contingency_case_id, case_number 
            FROM contingencycases 
            ORDER BY case_number
        """)
        
        results = cursor.fetchall()
        logging.info(f"Found {len(results)} contingency cases in database")
        
        # Create mapping: case_number -> contingency_case_id
        case_mapping = {}
        for row in results:
            case_mapping[row['case_number']] = row['contingency_case_id']
        
        return case_mapping
        
    except Exception as e:
        logging.error(f"Error getting contingency cases: {e}")
        return {}
    finally:
        conn.close()

def get_available_text_files() -> List[str]:
    """Get list of all available text files"""
    pattern = os.path.join(CONTINGENCY_FOLDER, "CA_0_bus118_*.txt")
    files = glob.glob(pattern)
    
    # Extract case numbers from filenames
    file_mapping = {}
    for file_path in files:
        filename = os.path.basename(file_path)
        # Extract number from CA_0_bus118_N.txt
        if filename.startswith("CA_0_bus118_") and filename.endswith(".txt"):
            try:
                case_num = int(filename.replace("CA_0_bus118_", "").replace(".txt", ""))
                file_mapping[case_num] = file_path
            except ValueError:
                continue
    
    logging.info(f"Found {len(file_mapping)} text files with case numbers: {sorted(file_mapping.keys())[:10]}...")
    return file_mapping

def parse_power_flow_file(file_path: str) -> Dict[int, List[Dict]]:
    """Parse power flow data from text file - returns scenarios mapped to branch data"""
    scenarios = {}
    
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        current_scenario = None
        line_idx = 0
        
        while line_idx < len(lines):
            line = lines[line_idx].strip()
            
            # Look for scenario headers
            if line.startswith("scenario"):
                try:
                    current_scenario = int(line.split()[1])
                    scenarios[current_scenario] = []
                    # Skip the next 118 lines (bus voltage data)
                    line_idx += 119  # Skip scenario line + 118 bus lines
                    continue
                except (IndexError, ValueError):
                    pass
            
            # Parse branch flow data
            if current_scenario is not None and line_idx < len(lines):
                parts = lines[line_idx].strip().split()
                if len(parts) >= 3:
                    try:
                        from_bus = int(parts[0])
                        pf = float(parts[1])
                        qf = float(parts[2])
                        
                        # Calculate MVA
                        mva = math.sqrt(pf*pf + qf*qf)
                        
                        scenarios[current_scenario].append({
                            'from_bus': from_bus,
                            'pf': pf,
                            'qf': qf,
                            'mva': mva
                        })
                    except (ValueError, IndexError):
                        pass
            
            line_idx += 1
    
    except Exception as e:
        logging.error(f"Error parsing file {file_path}: {e}")
        return {}
    
    return scenarios

def update_power_flow_data(conn, contingency_case_id: int, branch_data: List[Dict]) -> int:
    """Update power flow data for a specific contingency case"""
    try:
        cursor = conn.cursor()
        updates = 0
        
        for branch in branch_data:
            # Update branch data
            cursor.execute("""
                UPDATE contingencybranchdata 
                SET pf = %s, qf = %s, mva = %s
                WHERE contingency_case_id = %s 
                AND from_bus = %s
            """, (
                branch['pf'], 
                branch['qf'], 
                branch['mva'],
                contingency_case_id,
                branch['from_bus']
            ))
            
            if cursor.rowcount > 0:
                updates += cursor.rowcount
        
        conn.commit()
        return updates
        
    except Exception as e:
        logging.error(f"Error updating case {contingency_case_id}: {e}")
        conn.rollback()
        return 0

def load_all_power_flow_data():
    """Main function to load all power flow data"""
    logging.info("Starting comprehensive power flow data loading...")
    
    # Get database case mapping
    case_mapping = get_contingency_cases()
    if not case_mapping:
        logging.error("Failed to get contingency case mapping")
        return
    
    logging.info(f"Database has {len(case_mapping)} cases: {min(case_mapping.keys())} to {max(case_mapping.keys())}")
    
    # Get available text files
    text_files = get_available_text_files()
    if not text_files:
        logging.error("No text files found")
        return
    
    logging.info(f"Found {len(text_files)} text files")
    
    # Connect to database
    conn = get_database_connection()
    if not conn:
        return
    
    total_updates = 0
    processed_cases = 0
    failed_cases = []
    
    # Process each case number in the database
    for case_number in sorted(case_mapping.keys()):
        contingency_case_id = case_mapping[case_number]
        
        # Find corresponding text file
        # Try multiple mapping strategies
        text_file_path = None
        
        # Strategy 1: Direct mapping (case_number matches file number)
        if case_number in text_files:
            text_file_path = text_files[case_number]
        # Strategy 2: Offset mapping (case_number + 1)
        elif (case_number + 1) in text_files:
            text_file_path = text_files[case_number + 1]
        # Strategy 3: Zero-based mapping (case_number corresponds to scenario 1 in file case_number)
        elif case_number == 0 and 1 in text_files:
            text_file_path = text_files[1]
        
        if not text_file_path:
            logging.warning(f"No text file found for case_number {case_number} (ID {contingency_case_id})")
            failed_cases.append(case_number)
            continue
        
        # Parse the text file
        scenarios = parse_power_flow_file(text_file_path)
        if not scenarios:
            logging.warning(f"No scenarios found in file {text_file_path}")
            failed_cases.append(case_number)
            continue
        
        # Use the first available scenario for this case
        scenario_number = min(scenarios.keys())
        branch_data = scenarios[scenario_number]
        
        if not branch_data:
            logging.warning(f"No branch data in scenario {scenario_number} for case {case_number}")
            failed_cases.append(case_number)
            continue
        
        # Update database
        updates = update_power_flow_data(conn, contingency_case_id, branch_data)
        total_updates += updates
        processed_cases += 1
        
        if processed_cases % 50 == 0:
            logging.info(f"Processed {processed_cases} cases, {total_updates} total updates")
    
    conn.close()
    
    # Final summary
    logging.info(f"""
=== LOADING COMPLETE ===
Cases in database: {len(case_mapping)}
Cases processed: {processed_cases}
Cases failed: {len(failed_cases)}
Total branch updates: {total_updates}
""")
    
    if failed_cases:
        logging.warning(f"Failed cases: {failed_cases[:20]}{'...' if len(failed_cases) > 20 else ''}")
    
    # Check final status
    check_final_status()

def check_final_status():
    """Check final database status"""
    conn = get_database_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Total records
        cursor.execute("SELECT COUNT(*) FROM contingencybranchdata")
        total = cursor.fetchone()[0]
        
        # Records with power flow data
        cursor.execute("SELECT COUNT(*) FROM contingencybranchdata WHERE pf != 0 OR qf != 0")
        with_data = cursor.fetchone()[0]
        
        # Cases with any power flow data
        cursor.execute("""
            SELECT COUNT(DISTINCT contingency_case_id) 
            FROM contingencybranchdata 
            WHERE pf != 0 OR qf != 0
        """)
        cases_with_data = cursor.fetchone()[0]
        
        logging.info(f"""
Final Database Status:
  Total records: {total:,}
  With power flow: {with_data:,} ({100*with_data/total:.1f}%)
  Cases with data: {cases_with_data}/577 ({100*cases_with_data/577:.1f}%)
""")
        
        if with_data < total * 0.8:
            logging.warning("Power flow data loading incomplete!")
        else:
            logging.info("Power flow data loading successful!")
            
    except Exception as e:
        logging.error(f"Error checking final status: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    load_all_power_flow_data()