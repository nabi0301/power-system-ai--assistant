#!/usr/bin/env python3
"""
Load contingency power flow data from text files into PostgreSQL contingency tables.
This script populates PF/QF data from text files and calculates MVA/VIO.
"""

import psycopg2
import os
import re
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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

def extract_case_id_from_filename(filename):
    """Extract file number from filename like CA_0_bus118_123.txt -> 123, then map to database case ID"""
    match = re.search(r'CA_0_bus118_(\d+)\.txt', filename)
    if match:
        file_number = int(match.group(1))
        # Map file number to case number (file 0 -> case 1, file 1 -> case 2, etc.)
        case_number = file_number + 1
        return case_number
    return None

def get_database_case_id(cursor, case_number):
    """Get the database case ID for the given case number"""
    try:
        cursor.execute("""
            SELECT contingency_case_id 
            FROM ContingencyCases 
            WHERE case_number = %s
        """, (case_number,))
        
        result = cursor.fetchone()
        return result[0] if result else None
        
    except Exception as e:
        logging.error(f"Error getting case ID for case number {case_number}: {e}")
        return None

def parse_branch_flows_from_text(file_path):
    """Parse branch flow data from text file (lines 120-305)"""
    branch_flows = []
    
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Extract branch flow data from lines 120-305 (0-indexed: 119-304)
        for line_num in range(119, min(305, len(lines))):
            line = lines[line_num].strip()
            if line:
                parts = line.split()
                if len(parts) >= 6:
                    try:
                        from_bus = int(parts[0])
                        to_bus = int(parts[1])
                        pf = float(parts[4])
                        qf = float(parts[5])
                        branch_flows.append((from_bus, to_bus, pf, qf))
                    except (ValueError, IndexError):
                        continue
        
        logging.info(f"Extracted {len(branch_flows)} branch flows from {os.path.basename(file_path)}")
        return branch_flows
        
    except Exception as e:
        logging.error(f"Error parsing {file_path}: {e}")
        return []

def update_branch_flows(cursor, case_id, branch_flows):
    """Update branch flow data in the database"""
    updated_count = 0
    
    for from_bus, to_bus, pf, qf in branch_flows:
        try:
            cursor.execute("""
                UPDATE contingencybranchdata 
                SET 
                    pf = %s,
                    qf = %s,
                    mva = SQRT(%s * %s + %s * %s),
                    vio = CASE 
                        WHEN rate > 0 THEN GREATEST(0, SQRT(%s * %s + %s * %s) - rate)
                        ELSE 0 
                    END
                WHERE contingency_case_id = %s 
                    AND from_bus = %s 
                    AND to_bus = %s
            """, (
                pf, qf,
                pf, pf, qf, qf,  # for MVA calculation
                pf, pf, qf, qf,  # for VIO calculation
                case_id,
                from_bus,
                to_bus
            ))
            
            if cursor.rowcount > 0:
                updated_count += 1
                
        except Exception as e:
            logging.warning(f"Failed to update branch {from_bus}-{to_bus}: {e}")
    
    return updated_count

def main():
    """Main function to load power flow data"""
    
    # Verify folder exists
    if not os.path.exists(CONTINGENCY_FOLDER):
        logging.error(f"Contingency folder not found: {CONTINGENCY_FOLDER}")
        return False
    
    # Get all text files
    text_files = list(Path(CONTINGENCY_FOLDER).glob("CA_0_bus118_*.txt"))
    total_files = len(text_files)
    
    if total_files == 0:
        logging.error(f"No text files found in {CONTINGENCY_FOLDER}")
        return False
    
    logging.info(f"Found {total_files} contingency text files")
    
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        successful_files = 0
        failed_files = 0
        total_branches_updated = 0
        
        for i, file_path in enumerate(sorted(text_files), 1):
            filename = file_path.name
            
            # Extract case number from filename
            case_number = extract_case_id_from_filename(filename)
            if not case_number:
                logging.warning(f"Could not extract case number from {filename}")
                failed_files += 1
                continue
            
            # Get database case ID
            case_id = get_database_case_id(cursor, case_number)
            if not case_id:
                logging.warning(f"No database case found for case number {case_number}")
                failed_files += 1
                continue
            
            if i <= 10 or i % 50 == 0:
                logging.info(f"Processing {i}/{total_files}: {filename} -> Case ID {case_id}")
            
            # Parse branch flows
            branch_flows = parse_branch_flows_from_text(file_path)
            if not branch_flows:
                logging.warning(f"No branch flows extracted from {filename}")
                failed_files += 1
                continue
            
            # Update database
            updated_count = update_branch_flows(cursor, case_id, branch_flows)
            
            if updated_count > 0:
                successful_files += 1
                total_branches_updated += updated_count
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
        logging.info(f"Total branches updated: {total_branches_updated:,}")
        
        # Check final database status
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN pf IS NOT NULL AND pf != 0 THEN 1 END) as with_power_flow,
                COUNT(CASE WHEN vio > 0 THEN 1 END) as with_violations,
                MAX(vio) as max_violation
            FROM contingencybranchdata
        """)
        
        result = cursor.fetchone()
        total_records, with_power_flow, with_violations, max_violation = result
        
        logging.info("\nFinal Database Status:")
        logging.info(f"  Total records: {total_records:,}")
        logging.info(f"  With power flow: {with_power_flow:,}")
        logging.info(f"  With violations: {with_violations:,}")
        logging.info(f"  Max violation: {max_violation:.2f} MVA")
        
        cursor.close()
        conn.close()
        
        return successful_files > 0
        
    except Exception as e:
        logging.error(f"Database error: {e}")
        return False

if __name__ == "__main__":
    logging.info("🔌 Starting contingency power flow data loading...")
    success = main()
    if success:
        print("✅ Power flow data loading completed successfully!")
    else:
        print("❌ Power flow data loading failed!")