#!/usr/bin/env python3
"""
Load contingency power flow data from text files into existing contingency table structure.
Updated to handle the specific file format: Bus data + Branch flow data.
"""

import os
import sqlite3
import logging
import re
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Database configuration
DATABASE_PATH = "data.db"
CONTINGENCY_FOLDER = "contingency_118"

# SQL queries
GET_CASE_EXISTS_SQL = """
SELECT 1 FROM contingencycases 
WHERE contingency_case_id = ?
"""

UPDATE_BRANCH_POWER_FLOW_SQL = """
UPDATE contingencybranchdata 
SET 
    PF = ?,
    QF = ?,
    MVA = SQRT(PF * PF + QF * QF),
    VIO = CASE 
        WHEN SQRT(PF * PF + QF * QF) > RATE THEN SQRT(PF * PF + QF * QF) - RATE 
        ELSE 0 
    END
WHERE contingency_case_id = ? AND branch_number = ?
"""

COUNT_BRANCHES_SQL = """
SELECT COUNT(*) FROM contingencybranchdata 
WHERE contingency_case_id = ?
"""

def extract_case_id_from_filename(filename):
    """Extract file number from filename like CA_0_bus118_123.txt -> 123, then map to database case ID"""
    match = re.search(r'CA_0_bus118_(\d+)\.txt', filename)
    if match:
        file_number = int(match.group(1))
        # Map file number to case ID: skip missing IDs 13 and 146
        # Files 0-11 map to case IDs 1-12
        # Files 12+ map to case IDs 14+ (skip 13)
        # Files 145+ map to case IDs 147+ (skip 146)
        if file_number <= 11:
            case_id = file_number + 1
        elif file_number <= 144:
            case_id = file_number + 2  # Skip 13
        elif file_number <= 183:
            case_id = file_number + 3  # Skip 13 and 146
        else:
            # Files beyond 183 don't have corresponding database cases
            return None
        return case_id
    return None

def parse_power_flow_file(file_path):
    """
    Parse contingency text file to extract branch power flows.
    File format:
    - Line 1: Header "1"  
    - Lines 2-119: Bus data (118 buses)
    - Lines 120-305: Branch flow data (186 branches)
    """
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Check if file has enough lines
        if len(lines) < 305:
            logging.warning(f"File {file_path} has only {len(lines)} lines, expected at least 305")
            return []
        
        branch_flows = []
        
        # Extract branch flow data (lines 120-305, which is index 119-304)
        for i in range(119, 305):  # Lines 120-305 (0-indexed: 119-304)
            line = lines[i].strip()
            if not line:
                continue
                
            # Parse branch flow line: branch_number PF QF
            parts = line.split()
            if len(parts) >= 3:
                try:
                    branch_number = int(parts[0])
                    pf = float(parts[1])
                    qf = float(parts[2])
                    
                    branch_flows.append({
                        'branch_number': branch_number,
                        'pf': pf,
                        'qf': qf
                    })
                except (ValueError, IndexError) as e:
                    logging.warning(f"Could not parse line {i+1} in {file_path}: {line} - {e}")
                    continue
        
        logging.info(f"Extracted {len(branch_flows)} branch flows from {file_path}")
        return branch_flows
        
    except Exception as e:
        logging.error(f"Error parsing {file_path}: {e}")
        return []

def get_case_id(cursor, case_id):
    """Check if case ID exists in database"""
    cursor.execute(GET_CASE_EXISTS_SQL, (case_id,))
    result = cursor.fetchone()
    return case_id if result else None

def update_branch_flows(cursor, case_id, branch_flows):
    """Update branch power flows for a specific case"""
    updated_count = 0
    
    for flow in branch_flows:
        try:
            cursor.execute(UPDATE_BRANCH_POWER_FLOW_SQL, (
                flow['pf'],
                flow['qf'], 
                case_id,
                flow['branch_number']
            ))
            
            if cursor.rowcount > 0:
                updated_count += 1
                
        except Exception as e:
            logging.error(f"Error updating branch {flow['branch_number']} for case {case_id}: {e}")
    
    return updated_count

def main():
    """Main execution function"""
    logging.info("Starting contingency power flow data loading...")
    
    # Check if database exists
    if not os.path.exists(DATABASE_PATH):
        logging.error(f"Database {DATABASE_PATH} not found!")
        return False
    
    # Check if contingency folder exists
    if not os.path.exists(CONTINGENCY_FOLDER):
        logging.error(f"Contingency folder {CONTINGENCY_FOLDER} not found!")
        return False
    
    # Get list of text files
    txt_files = list(Path(CONTINGENCY_FOLDER).glob("*.txt"))
    if not txt_files:
        logging.error(f"No .txt files found in {CONTINGENCY_FOLDER}")
        return False
    
    logging.info(f"Found {len(txt_files)} text files to process")
    
    # Connect to database
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Statistics
        total_files = len(txt_files)
        successful_files = 0
        failed_files = 0
        
        # Process each file
        for i, file_path in enumerate(txt_files, 1):
            filename = file_path.name
            case_id = extract_case_id_from_filename(filename)
            
            if not case_id:
                logging.warning(f"Could not extract case ID from {filename} or case beyond available range")
                failed_files += 1
                continue
            
            # Progress indicator
            if i % 50 == 0 or i <= 10:
                logging.info(f"Processing {i}/{total_files}: {filename} -> Case ID {case_id}")
            
            # Check if case ID exists in database
            verified_case_id = get_case_id(cursor, case_id)
            if not verified_case_id:
                logging.warning(f"Case ID {case_id} not found in database")
                failed_files += 1
                continue
            
            # Parse power flow data
            branch_flows = parse_power_flow_file(file_path)
            if not branch_flows:
                logging.warning(f"No branch flows extracted from {filename}")
                failed_files += 1
                continue
            
            # Update database
            updated_count = update_branch_flows(cursor, case_id, branch_flows)
            
            if updated_count > 0:
                successful_files += 1
                if i % 50 == 0 or i <= 10:
                    logging.info(f"  Updated {updated_count} branches")
            else:
                logging.warning(f"  Failed to update any records")
                failed_files += 1
        
        # Commit all changes
        conn.commit()
        
        # Final statistics
        logging.info("\n=== LOADING COMPLETE ===")
        logging.info(f"Total files: {total_files}")
        logging.info(f"Successful: {successful_files}")
        logging.info(f"Failed: {failed_files}")
        
        # Check final database status
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                SUM(CASE WHEN PF != 0 OR QF != 0 THEN 1 ELSE 0 END) as with_power_flow,
                SUM(CASE WHEN VIO > 0 THEN 1 ELSE 0 END) as with_violations,
                MAX(VIO) as max_violation
            FROM contingencybranchdata
        """)
        
        total_records, with_power_flow, with_violations, max_violation = cursor.fetchone()
        
        logging.info("\nFinal Database Status:")
        logging.info(f"  Total records: {total_records}")
        logging.info(f"  With power flow: {with_power_flow}")
        logging.info(f"  With violations: {with_violations}")
        logging.info(f"  Max violation: {max_violation:.2f} MVA")
        
        return successful_files > 0
        
    except Exception as e:
        logging.error(f"Database error: {e}")
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()
            logging.info("Database connection closed")

if __name__ == "__main__":
    success = main()
    if success:
        print("✅ Power flow data loading completed successfully!")
    else:
        print("❌ Power flow data loading failed!")