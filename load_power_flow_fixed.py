#!/usr/bin/env python3
"""
Fixed Power Flow Data Loader for PostgreSQL

This script loads power flow data from contingency text files into the PostgreSQL database.
The text files contain multiple contingency scenarios, each with bus voltage data followed by branch flow data.

File Format:
- Each scenario starts with a number (1, 2, 3, etc.)
- First 118 lines: Bus voltage data
- Following lines: Branch flow data (from_bus pf qf)
"""

import os
import psycopg2
import logging
import re
from typing import Dict, List, Tuple, Optional

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': '118',
    'user': 'postgres',
    'password': 'pnnl'
}

# File paths
TEXT_FILES_DIR = r"C:\Projects\dlr-database-project\contingency_118"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('power_flow_loader.log'),
        logging.StreamHandler()
    ]
)

def get_database_branch_mapping(conn) -> Dict[int, Dict[Tuple[int, int, str], int]]:
    """
    Get the mapping of case_id -> {(from_bus, to_bus, circuit_id): branch_data_id}
    """
    logging.info("Loading database branch mapping...")
    cur = conn.cursor()
    
    cur.execute("""
        SELECT contingency_case_id, from_bus, to_bus, circuit_id, branch_data_id
        FROM contingencybranchdata
        ORDER BY contingency_case_id, from_bus, to_bus, circuit_id
    """)
    
    mapping = {}
    for case_id, from_bus, to_bus, circuit_id, branch_data_id in cur.fetchall():
        if case_id not in mapping:
            mapping[case_id] = {}
        mapping[case_id][(from_bus, to_bus, circuit_id)] = branch_data_id
    
    logging.info(f"Loaded mapping for {len(mapping)} cases")
    return mapping

def get_case_number_to_id_mapping(conn) -> Dict[int, int]:
    """
    Get mapping from case numbers (1-577) to database case IDs
    """
    logging.info("Loading case number to ID mapping...")
    cur = conn.cursor()
    
    cur.execute("""
        SELECT contingency_case_id, case_number
        FROM contingencycases
        WHERE case_number IS NOT NULL
        ORDER BY case_number
    """)
    
    mapping = {}
    for case_id, case_number in cur.fetchall():
        mapping[case_number] = case_id
    
    logging.info(f"Loaded case mapping for {len(mapping)} cases")
    return mapping

def parse_text_file(filepath: str) -> Dict[int, Dict[int, Tuple[float, float]]]:
    """
    Parse a contingency text file and extract power flow data for all scenarios.
    
    Returns:
        Dict[scenario_num, Dict[from_bus, (pf, qf)]]
    """
    scenarios = {}
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for scenario number (single number on its own line)
        if re.match(r'^\s*\d+\s*$', line):
            scenario_num = int(line)
            logging.debug(f"Found scenario {scenario_num} at line {i+1}")
            
            # Skip 118 lines of bus data
            bus_start = i + 1
            bus_end = bus_start + 118
            
            # Start reading branch flow data
            branch_start = bus_end
            branch_flows = {}
            
            j = branch_start
            while j < len(lines):
                branch_line = lines[j].strip()
                
                # Check if this is the start of the next scenario
                if re.match(r'^\s*\d+\s*$', branch_line):
                    break
                
                # Parse branch flow data: from_bus pf qf
                parts = branch_line.split()
                if len(parts) >= 3:
                    try:
                        from_bus = int(parts[0])
                        pf = float(parts[1])
                        qf = float(parts[2])
                        branch_flows[from_bus] = (pf, qf)
                    except (ValueError, IndexError):
                        pass  # Skip malformed lines
                
                j += 1
            
            scenarios[scenario_num] = branch_flows
            i = j  # Continue from where we left off
        else:
            i += 1
    
    return scenarios

def update_database_with_flows(conn, case_mapping: Dict[int, int], 
                              branch_mapping: Dict[int, Dict[Tuple[int, int, str], int]],
                              scenario_num: int, flows: Dict[int, Tuple[float, float]]) -> int:
    """
    Update database with power flow data for a specific scenario.
    
    Returns number of records updated.
    """
    if scenario_num not in case_mapping:
        logging.warning(f"No database case found for scenario {scenario_num}")
        return 0
    
    case_id = case_mapping[scenario_num]
    if case_id not in branch_mapping:
        logging.warning(f"No branch mapping found for case ID {case_id}")
        return 0
    
    cur = conn.cursor()
    updates = 0
    
    # For each from_bus flow, try to match it to database branches
    for from_bus, (pf, qf) in flows.items():
        # Find all branches that start from this bus
        matching_branches = [
            (to_bus, circuit_id, branch_data_id)
            for (f_bus, to_bus, circuit_id), branch_data_id in branch_mapping[case_id].items()
            if f_bus == from_bus
        ]
        
        if not matching_branches:
            logging.debug(f"No branches found starting from bus {from_bus}")
            continue
        
        # For now, update the first matching branch
        # TODO: This logic might need refinement based on actual data structure
        to_bus, circuit_id, branch_data_id = matching_branches[0]
        
        # Calculate MVA
        mva = (pf**2 + qf**2)**0.5
        
        # Update the database
        cur.execute("""
            UPDATE contingencybranchdata 
            SET pf = %s, qf = %s, mva = %s
            WHERE branch_data_id = %s
        """, (pf, qf, mva, branch_data_id))
        
        updates += 1
    
    return updates

def main():
    logging.info("Starting Power Flow Data Loading...")
    
    # Connect to database
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    
    try:
        # Get mappings
        case_mapping = get_case_number_to_id_mapping(conn)
        branch_mapping = get_database_branch_mapping(conn)
        
        # Get list of text files
        text_files = [f for f in os.listdir(TEXT_FILES_DIR) if f.endswith('.txt')]
        text_files.sort()
        
        total_updates = 0
        processed_files = 0
        
        for filename in text_files:
            filepath = os.path.join(TEXT_FILES_DIR, filename)
            logging.info(f"Processing {filename}...")
            
            try:
                # Parse the file
                scenarios = parse_text_file(filepath)
                
                # Update database for each scenario
                for scenario_num, flows in scenarios.items():
                    updates = update_database_with_flows(
                        conn, case_mapping, branch_mapping, scenario_num, flows
                    )
                    total_updates += updates
                    
                    if updates > 0:
                        logging.info(f"  Scenario {scenario_num}: {updates} branches updated")
                
                processed_files += 1
                
                # Commit every 10 files
                if processed_files % 10 == 0:
                    conn.commit()
                    logging.info(f"Committed after {processed_files} files")
                
            except Exception as e:
                logging.error(f"Error processing {filename}: {e}")
                continue
        
        # Final commit
        conn.commit()
        
        logging.info(f"""
=== LOADING COMPLETE ===
Files processed: {processed_files}
Total branch updates: {total_updates}
        """)
        
        # Check final status
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM contingencybranchdata WHERE pf != 0 OR qf != 0")
        populated_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM contingencybranchdata")
        total_count = cur.fetchone()[0]
        
        percentage = (populated_count / total_count * 100) if total_count > 0 else 0
        
        logging.info(f"""
Final Database Status:
  Total records: {total_count:,}
  With power flow: {populated_count:,} ({percentage:.1f}%)
        """)
        
        if percentage > 50:
            logging.info("✅ Power flow data loading successful!")
        else:
            logging.warning("⚠️ Power flow data loading incomplete!")
            
    except Exception as e:
        logging.error(f"Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()