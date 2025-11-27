"""
PostgreSQL Base and Contingency Data Reloader for 118.db
Replaces existing data with corrected MVA and VIO calculations
"""

import os
import psycopg2
from psycopg2 import extras
import pandas as pd
import numpy as np
import time
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reload_base_contingency.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Paths to folders containing datasets
BASE_FOLDER = r"C:\Projects\dlr-database-project\Base_118"
CONTINGENCY_FOLDER = r"C:\Projects\dlr-database-project\contingency_118"

# PostgreSQL database connection parameters
DB_CONFIG = {
    'dbname': '118',
    'user': 'postgres',
    'password': 'pnnl',
    'host': 'localhost',
    'port': 5432
}

# Batch processing configuration
COMMIT_BATCH_SIZE = 10  # Commit every N base files

def calculate_mva(pf, qf):
    """Calculate MVA from PF and QF"""
    if pd.isna(pf) or pd.isna(qf):
        return np.nan
    return np.sqrt(pf**2 + qf**2)

def calculate_vio_percentage(pf, qf, rate):
    """Calculate violation percentage: (MVA / Rate) * 100"""
    if pd.isna(rate) or rate <= 0:
        return np.nan
    mva = calculate_mva(pf, qf)
    if pd.isna(mva):
        return np.nan
    return (mva / rate) * 100

def standardize_columns(df):
    """Standardize column names to match database schema"""
    if df.empty:
        return df
    
    df.columns = (
        df.columns.str.strip()
        .str.replace('-', '_')
        .str.replace(' ', '_')
        .str.lower()
    )
    rename_map = {
        'busnumber': 'bus_number',
        'bus': 'bus_number',
        'from': 'from_bus',
        'to': 'to_bus',
        'f_bus': 'from_bus',
        't_bus': 'to_bus',
        'frm_bus': 'from_bus',
        't_bus': 'to_bus'
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    
    # Ensure critical columns exist
    if 'bus_number' not in df.columns and len(df.columns) > 0:
        # First column might be bus number
        first_col = df.columns[0]
        if first_col not in ['from_bus', 'to_bus', 'pf', 'qf']:
            df = df.rename(columns={first_col: 'bus_number'})
    
    return df

def read_txt_file(file_path):
    """
    Read .txt files and return bus and branch data as DataFrames
    Handles both base case and contingency case formats
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            return pd.DataFrame(), pd.DataFrame()
        
        # Find section markers
        bus_header_idx = None
        branch_header_idx = None
        
        for i, line in enumerate(lines):
            line_upper = line.upper()
            if 'BUS' in line_upper and ('VM' in line_upper or 'VA' in line_upper):
                bus_header_idx = i
            elif 'FROM' in line_upper and 'TO' in line_upper and ('PF' in line_upper or 'QF' in line_upper):
                branch_header_idx = i
        
        buses_df = pd.DataFrame()
        branches_df = pd.DataFrame()
        
        # Process bus data
        if bus_header_idx is not None:
            bus_header = lines[bus_header_idx].strip()
            bus_columns = [col.strip().rstrip(',') for col in bus_header.split()]
            
            bus_end_idx = branch_header_idx if branch_header_idx else len(lines)
            
            bus_data_rows = []
            for i in range(bus_header_idx + 1, bus_end_idx):
                line = lines[i].strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = [p for p in line.split() if p]
                if len(parts) >= len(bus_columns):
                    bus_data_rows.append(parts[:len(bus_columns)])
            
            if bus_data_rows:
                buses_df = pd.DataFrame(bus_data_rows, columns=bus_columns)
                for col in buses_df.columns:
                    try:
                        buses_df[col] = pd.to_numeric(buses_df[col])
                    except (ValueError, TypeError):
                        pass
        
        # Process branch data
        if branch_header_idx is not None:
            branch_header = lines[branch_header_idx].strip()
            branch_columns = [col.strip().rstrip(',') for col in branch_header.split()]
            
            branch_data_rows = []
            for i in range(branch_header_idx + 1, len(lines)):
                line = lines[i].strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = [p for p in line.split() if p]
                if len(parts) >= len(branch_columns):
                    branch_data_rows.append(parts[:len(branch_columns)])
            
            if branch_data_rows:
                branches_df = pd.DataFrame(branch_data_rows, columns=branch_columns)
                for col in branches_df.columns:
                    try:
                        branches_df[col] = pd.to_numeric(branches_df[col])
                    except (ValueError, TypeError):
                        pass
        
        return buses_df, branches_df
        
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
        return pd.DataFrame(), pd.DataFrame()

def clear_existing_data(conn):
    """Clear existing base and contingency data (preserving DLR/SLR tables)"""
    cur = conn.cursor()
    
    logging.info("Clearing existing base and contingency data...")
    
    try:
        # Delete in correct order (respecting foreign keys)
        cur.execute("DELETE FROM ContingencyBranchData")
        cur.execute("DELETE FROM ContingencyBusData")
        cur.execute("DELETE FROM ContingencyCases")
        cur.execute("DELETE FROM BaseBranchData")
        cur.execute("DELETE FROM BaseBusData")
        cur.execute("DELETE FROM BaseCases")
        
        conn.commit()
        logging.info("✅ Existing data cleared successfully")
        
    except Exception as e:
        logging.error(f"Error clearing existing data: {e}")
        conn.rollback()
        raise

def process_contingency_file_with_multiple_cases(contingency_file_path, base_case_id, cur, base_buses, base_branches, conn):
    """
    Process a single contingency file containing multiple cases
    Each case is separated by a line with just the case number
    """
    try:
        with open(contingency_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by case numbers (lines with just 1-3 digit numbers)
        import re
        
        # Find all case number markers
        case_markers = list(re.finditer(r'^\s*(\d{1,3})\s*$', content, re.MULTILINE))
        
        if not case_markers:
            logging.warning(f"No case markers found in {contingency_file_path}")
            return 0
        
        cases_processed = 0
        
        for i, marker in enumerate(case_markers):
            case_number = int(marker.group(1))
            
            # Get content between this marker and next marker (or end of file)
            start_pos = marker.end()
            end_pos = case_markers[i + 1].start() if i + 1 < len(case_markers) else len(content)
            
            case_content = content[start_pos:end_pos].strip()
            
            if not case_content:
                continue
            
            # Process this case
            success = process_single_contingency_case(
                case_content, case_number, base_case_id, cur, base_buses, base_branches, conn
            )
            
            if success:
                cases_processed += 1
        
        return cases_processed
        
    except Exception as e:
        logging.error(f"Error processing contingency file {contingency_file_path}: {e}")
        return 0

def process_single_contingency_case(case_content, case_number, base_case_id, cur, base_buses, base_branches, conn):
    """Process a single contingency case from text content"""
    try:
        lines = case_content.strip().split('\n')
        
        if len(lines) < 118:
            logging.warning(f"Insufficient lines for case {case_number}")
            return False
        
        # Split into bus and branch sections
        # First 118 lines: bus data (BUS VM VA PG QG PD QD)
        # Remaining lines: branch data (TO PF QF)
        bus_lines = lines[:118]
        branch_lines = lines[118:]
        
        # Create contingency case record
        case_name = f"Contingency_{case_number}"
        filename = f"CA_0_bus118_case_{case_number}"
        
        cur.execute("""
            INSERT INTO ContingencyCases 
            (base_case_id, case_number, filename, case_name, processing_status, buses_count, branches_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING contingency_case_id
        """, (base_case_id, case_number, filename, case_name, 'completed', 118, len(branch_lines)))
        
        contingency_case_id = cur.fetchone()[0]
        
        # Process bus data
        bus_data = []
        for line in bus_lines:
            parts = line.split()
            if len(parts) >= 7:
                try:
                    bus_num = int(parts[0])
                    vm = float(parts[1])
                    va = float(parts[2])
                    pg = float(parts[3])
                    qg = float(parts[4])
                    pd = float(parts[5])
                    qd = float(parts[6])
                    
                    # Get BASE_KV from base case
                    base_kv = 138.0  # Default
                    if not base_buses.empty:
                        base_bus = base_buses[base_buses['bus_number'] == bus_num]
                        if not base_bus.empty:
                            base_kv = base_bus.iloc[0]['base_kv']
                    
                    bus_data.append((
                        contingency_case_id, bus_num, vm, va, base_kv, pg, qg, pd, qd
                    ))
                except (ValueError, IndexError) as e:
                    logging.warning(f"Error parsing bus line: {line} - {e}")
        
        if bus_data:
            extras.execute_batch(cur, """
                INSERT INTO ContingencyBusData 
                (contingency_case_id, bus_number, vm, va, base_kv, pg, qg, pd, qd)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, bus_data, page_size=100)
        
        # Process branch data
        # Contingency format: TO PF QF (one line per branch)
        # Need to match with base case branches to get FROM, LINE_ID, RATE
        branch_data = []
        
        if not base_branches.empty and len(branch_lines) <= len(base_branches):
            for idx, line in enumerate(branch_lines):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        to_bus = int(parts[0])
                        pf = float(parts[1])
                        qf = float(parts[2]) if len(parts) >= 3 else 0.0
                        
                        # Get corresponding base branch info
                        base_branch = base_branches.iloc[idx]
                        from_bus = int(base_branch['from_bus'])
                        line_id = str(base_branch.get('line_id', '1'))
                        rate = float(base_branch.get('rate', 100.0))
                        
                        # Calculate MVA and VIO
                        mva = calculate_mva(pf, qf)
                        vio = calculate_vio_percentage(pf, qf, rate)
                        
                        branch_data.append((
                            contingency_case_id, base_case_id, from_bus, to_bus, 
                            line_id, pf, qf, mva, rate, vio
                        ))
                    except (ValueError, IndexError) as e:
                        logging.warning(f"Error parsing branch line: {line} - {e}")
        
        if branch_data:
            extras.execute_batch(cur, """
                INSERT INTO ContingencyBranchData 
                (contingency_case_id, base_case_id, from_bus, to_bus, circuit_id, pf, qf, mva, rate, vio)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, branch_data, page_size=100)
        
        logging.info(f"✅ Processed case {case_number}: {len(bus_data)} buses, {len(branch_data)} branches")
        return True
        
    except Exception as e:
        logging.error(f"Error processing contingency case {case_number}: {e}")
        return False

def load_base_and_contingency_data(conn):
    """Load all base cases and their contingency cases"""
    cur = conn.cursor()
    
    if not os.path.exists(BASE_FOLDER):
        logging.error(f"Base folder not found: {BASE_FOLDER}")
        return
    
    # Get all base case files
    base_files = [f for f in os.listdir(BASE_FOLDER) 
                  if f.startswith('BASE_0_bus118_') and f.endswith('.txt')]
    base_files.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
    
    logging.info(f"Found {len(base_files)} base case files")
    
    start_time = time.time()
    total_contingency_cases = 0
    
    for i, base_filename in enumerate(base_files):
        base_path = os.path.join(BASE_FOLDER, base_filename)
        logging.info(f"\n{'='*70}")
        logging.info(f"[{i+1}/{len(base_files)}] Processing: {base_filename}")
        logging.info(f"{'='*70}")
        
        try:
            # Extract case number from filename
            case_num = int(base_filename.split('_')[-1].split('.')[0])
            
            # Read base case data
            base_buses, base_branches = read_txt_file(base_path)
            
            if base_buses.empty or base_branches.empty:
                logging.warning(f"Empty data in {base_filename}, skipping")
                continue
            
            # Standardize column names
            base_buses = standardize_columns(base_buses)
            base_branches = standardize_columns(base_branches)
            
            # Verify required columns exist
            if 'bus_number' not in base_buses.columns:
                logging.warning(f"Missing 'bus_number' column in {base_filename}. Columns: {list(base_buses.columns)}")
                continue
            
            if 'from_bus' not in base_branches.columns or 'to_bus' not in base_branches.columns:
                logging.warning(f"Missing bus columns in branches for {base_filename}. Columns: {list(base_branches.columns)}")
                continue
            
            # Insert base case record
            case_name = f"Base_Case_{case_num}"
            folder_name = "Base_118"
            
            cur.execute("""
                INSERT INTO BaseCases 
                (case_number, filename, case_name, folder_name, buses_count, branches_count, processing_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING base_case_id
            """, (case_num, base_filename, case_name, folder_name, len(base_buses), len(base_branches), 'completed'))
            
            base_case_id = cur.fetchone()[0]
            
            # Process and insert bus data
            bus_data = []
            for _, row in base_buses.iterrows():
                bus_data.append((
                    base_case_id,
                    int(row['bus_number']),
                    float(row.get('vm', 1.0)),
                    float(row.get('va', 0.0)),
                    float(row.get('base_kv', 138.0)),
                    float(row.get('pg', 0.0)),
                    float(row.get('qg', 0.0)),
                    float(row.get('pd', 0.0)),
                    float(row.get('qd', 0.0))
                ))
            
            extras.execute_batch(cur, """
                INSERT INTO BaseBusData 
                (base_case_id, bus_number, vm, va, base_kv, pg, qg, pd, qd)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, bus_data, page_size=100)
            
            # Process and insert branch data with MVA and VIO calculations
            branch_data = []
            
            # Create line_id for parallel lines
            if 'line_id' not in base_branches.columns:
                base_branches['line_id'] = base_branches.groupby(['from_bus', 'to_bus']).cumcount() + 1
                base_branches['line_id'] = base_branches['line_id'].astype(str)
            
            for branch_num, (_, row) in enumerate(base_branches.iterrows(), start=1):
                pf = float(row.get('pf', 0.0))
                qf = float(row.get('qf', 0.0))
                rate = float(row.get('rate', 100.0))
                
                # Calculate MVA and VIO
                mva = calculate_mva(pf, qf)
                vio = calculate_vio_percentage(pf, qf, rate)
                
                branch_data.append((
                    base_case_id,
                    branch_num,
                    int(row['from_bus']),
                    int(row['to_bus']),
                    str(row.get('line_id', '1')),
                    pf, qf, mva, rate, vio
                ))
            
            extras.execute_batch(cur, """
                INSERT INTO BaseBranchData 
                (base_case_id, branch_number, from_bus, to_bus, line_id, pf, qf, mva, rate, vio)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, branch_data, page_size=100)
            
            logging.info(f"✅ Base case: {len(bus_data)} buses, {len(branch_data)} branches")
            
            # Process contingency cases
            contingency_filename = f"CA_0_bus118_{case_num}.txt"
            contingency_path = os.path.join(CONTINGENCY_FOLDER, contingency_filename)
            
            if os.path.exists(contingency_path):
                logging.info(f"Processing contingency file: {contingency_filename}")
                
                cases_count = process_contingency_file_with_multiple_cases(
                    contingency_path, base_case_id, cur, base_buses, base_branches, conn
                )
                
                total_contingency_cases += cases_count
                logging.info(f"✅ Processed {cases_count} contingency cases")
            else:
                logging.warning(f"Contingency file not found: {contingency_path}")
            
            # Periodic commit
            if (i + 1) % COMMIT_BATCH_SIZE == 0:
                conn.commit()
                elapsed = time.time() - start_time
                avg_time = elapsed / (i + 1)
                remaining = avg_time * (len(base_files) - (i + 1))
                
                logging.info(f"\n📊 Progress: {i+1}/{len(base_files)} files")
                logging.info(f"⏱️  Elapsed: {elapsed/60:.1f} min | Remaining: {remaining/60:.1f} min")
                logging.info(f"📦 Total contingency cases: {total_contingency_cases}")
        
        except Exception as e:
            logging.error(f"Error processing {base_filename}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Final commit
    conn.commit()
    
    total_time = time.time() - start_time
    logging.info(f"\n{'='*70}")
    logging.info(f"🎉 IMPORT COMPLETE!")
    logging.info(f"{'='*70}")
    logging.info(f"✅ Base cases: {len(base_files)}")
    logging.info(f"✅ Contingency cases: {total_contingency_cases}")
    logging.info(f"⏱️  Total time: {total_time/60:.1f} minutes")
    logging.info(f"{'='*70}")

def show_database_summary(conn):
    """Display summary statistics"""
    cur = conn.cursor()
    
    logging.info("\n" + "="*70)
    logging.info("DATABASE SUMMARY")
    logging.info("="*70)
    
    queries = {
        'Base Cases': "SELECT COUNT(*) FROM BaseCases",
        'Base Bus Data': "SELECT COUNT(*) FROM BaseBusData",
        'Base Branch Data': "SELECT COUNT(*) FROM BaseBranchData",
        'Contingency Cases': "SELECT COUNT(*) FROM ContingencyCases",
        'Contingency Bus Data': "SELECT COUNT(*) FROM ContingencyBusData",
        'Contingency Branch Data': "SELECT COUNT(*) FROM ContingencyBranchData"
    }
    
    for label, query in queries.items():
        cur.execute(query)
        count = cur.fetchone()[0]
        logging.info(f"  {label}: {count:,}")
    
    logging.info("="*70)

def main():
    """Main execution function"""
    logging.info("="*70)
    logging.info("PostgreSQL Base & Contingency Data Reloader")
    logging.info("="*70)
    logging.info(f"Database: {DB_CONFIG['dbname']}")
    logging.info(f"Base folder: {BASE_FOLDER}")
    logging.info(f"Contingency folder: {CONTINGENCY_FOLDER}")
    logging.info(f"Started: {datetime.now()}")
    logging.info("="*70)
    
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        logging.info("✅ Connected to PostgreSQL")
        
        # Clear existing data
        clear_existing_data(conn)
        
        # Load new data
        load_base_and_contingency_data(conn)
        
        # Show summary
        show_database_summary(conn)
        
        conn.close()
        logging.info("\n✅ Data reload completed successfully!")
        
    except Exception as e:
        logging.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    logging.info(f"\nFinished: {datetime.now()}")

if __name__ == "__main__":
    main()
