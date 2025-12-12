"""
Add new SLR data from additional_slr_data folder to data - Copy.db
This will keep the existing old data and append the new 184 cases.
"""

import os
import sqlite3
import pandas as pd

# Configuration
DATABASE_PATH = "C:\\Projects\\dlr-database-project\\data - Copy.db"
DATA_FOLDER = "C:\\Projects\\dlr-database-project\\additional_slr_data"

def get_base_case_id_from_idx(idx):
    """Map idx to base_case_id based on the pattern."""
    if 1 <= idx <= 43:
        return 43
    elif 44 <= idx <= 86:
        return 44
    elif 87 <= idx <= 129:
        return 45
    elif 130 <= idx <= 172:
        return 46
    elif 173 <= idx <= 186:
        return 47
    else:
        return 43

def get_existing_case_ids(conn):
    """Get all existing contingency_case_ids to avoid duplicates."""
    cursor = conn.cursor()
    cursor.execute("SELECT contingency_case_id FROM SLR_Cases")
    return set(row[0] for row in cursor.fetchall())

def load_new_slr_data(conn):
    """Load new SLR data from CSV files."""
    print("\n" + "="*80)
    print("LOADING NEW SLR DATA FROM CSV FILES")
    print("="*80)
    print(f"Data folder: {DATA_FOLDER}\n")
    
    cursor = conn.cursor()
    
    # Get existing case IDs
    existing_case_ids = get_existing_case_ids(conn)
    print(f"[INFO] Existing SLR cases in database: {len(existing_case_ids)}")
    if existing_case_ids:
        print(f"       Existing case IDs: {sorted(existing_case_ids)}")
    
    # Find all contingency folders
    contingency_folders = []
    for item in os.listdir(DATA_FOLDER):
        item_path = os.path.join(DATA_FOLDER, item)
        if os.path.isdir(item_path) and item.startswith('contingency_'):
            contingency_folders.append(item_path)
    
    contingency_folders.sort()
    print(f"\n[INFO] Found {len(contingency_folders)} contingency folders")
    
    total_cases_added = 0
    total_cases_skipped = 0
    total_buses = 0
    total_branches = 0
    total_loads = 0
    total_generators = 0
    
    for folder_path in contingency_folders:
        folder_name = os.path.basename(folder_path)
        
        # Extract contingency case ID from folder name
        try:
            case_id = int(folder_name.split('_')[1])
        except (IndexError, ValueError):
            print(f"[WARNING] Skipping folder with invalid name: {folder_name}")
            continue
        
        # Skip if case already exists
        if case_id in existing_case_ids:
            total_cases_skipped += 1
            continue
        
        # Get base_case_id
        base_case_id = get_base_case_id_from_idx(case_id)
        
        # Find CSV files
        bus_file = os.path.join(folder_path, f'bus_data_cont_{case_id}.csv')
        branch_file = os.path.join(folder_path, f'branch_data_cont_{case_id}.csv')
        load_file = os.path.join(folder_path, f'load_data_cont_{case_id}.csv')
        gen_file = os.path.join(folder_path, f'generator_data_cont_{case_id}.csv')
        
        # Check if all files exist
        if not all(os.path.exists(f) for f in [bus_file, branch_file, load_file, gen_file]):
            print(f"[WARNING] Missing files in {folder_name}, skipping...")
            continue
        
        # Extract case information from CSV data
        try:
            df_bus_sample = pd.read_csv(bus_file, nrows=1)
            from_bus = int(df_bus_sample['tripped_from_bus'].iloc[0])
            to_bus = int(df_bus_sample['tripped_to_bus'].iloc[0])
            line_id = str(df_bus_sample['tripped_line_id'].iloc[0])
            slr_case_name = f"SLR_idx{case_id}_Line_{from_bus}_{to_bus}_{line_id}"
        except Exception as e:
            from_bus = 0
            to_bus = 0
            line_id = "1.0"
            slr_case_name = f"SLR_idx{case_id}"
        
        # Insert into SLR_Cases
        cursor.execute("""
            INSERT INTO SLR_Cases (base_case_id, contingency_case_id, tripped_from_bus, 
                                   tripped_to_bus, tripped_line_id, SLR_Case)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (base_case_id, case_id, from_bus, to_bus, line_id, slr_case_name))
        total_cases_added += 1
        
        # Load bus data
        df_bus = pd.read_csv(bus_file)
        for _, row in df_bus.iterrows():
            cursor.execute("""
                INSERT INTO SLR_PostAction_BusData 
                (base_case_id, contingency_case_id, tripped_from_bus, tripped_to_bus, 
                 tripped_line_id, Bus_Number, VM, VA, BASE_KV, PG, QG, PD, QD)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (base_case_id, case_id, from_bus, to_bus, line_id,
                  int(row['bus_number']), float(row['vm']), 
                  float(row['va']), float(row['Base_kV']), float(row['pg']),
                  float(row['qg']), float(row['pd']), float(row['qd'])))
        total_buses += len(df_bus)
        
        # Load branch data (with updated RATE and VIO)
        df_branch = pd.read_csv(branch_file)
        for _, row in df_branch.iterrows():
            # Check if this branch record already exists (to handle duplicates)
            cursor.execute("""
                SELECT COUNT(*) FROM SLRBranchData 
                WHERE base_case_id=? AND contingency_case_id=? 
                AND tripped_from_bus=? AND tripped_to_bus=? 
                AND tripped_line_id=? AND From_Bus=? AND To_Bus=?
            """, (base_case_id, case_id, from_bus, to_bus, line_id,
                  int(row['FROM_BUS']), int(row['TO_BUS'])))
            
            if cursor.fetchone()[0] == 0:  # Only insert if doesn't exist
                cursor.execute("""
                    INSERT INTO SLRBranchData 
                    (base_case_id, contingency_case_id, tripped_from_bus, tripped_to_bus, 
                     tripped_line_id, From_Bus, To_Bus, PF, QF, MVA, RATE, VIO)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (base_case_id, case_id, from_bus, to_bus, line_id,
                      int(row['FROM_BUS']), int(row['TO_BUS']),
                      float(row['PF']), float(row['QF']), 
                      float(row['MVA']), float(row['RATE']), float(row['VIO'])))
        total_branches += len(df_branch)
        
        # Load load data
        df_load = pd.read_csv(load_file)
        for _, row in df_load.iterrows():
            cursor.execute("""
                INSERT INTO SLR_Load 
                (base_case_id, contingency_case_id, tripped_from_bus, tripped_to_bus, 
                 tripped_line_id, Bus_Number, KV_LEVEL, LOAD_INI, LOAD_NEW, LOAD_ADJ)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (base_case_id, case_id, from_bus, to_bus, line_id,
                  int(row['load_bus']), float(row['Base_kV']),
                  0.0, float(row['Load_New']), 0.0))
        total_loads += len(df_load)
        
        # Load generator data
        df_gen = pd.read_csv(gen_file)
        for _, row in df_gen.iterrows():
            cursor.execute("""
                INSERT INTO SLR_Generator 
                (base_case_id, contingency_case_id, tripped_from_bus, tripped_to_bus, 
                 tripped_line_id, Bus_Number, KV_LEVEL, GEN_INI, GEN_NEW, GEN_ADJ)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (base_case_id, case_id, from_bus, to_bus, line_id,
                  int(row['gen_bus']), float(row['Base_kV']),
                  0.0, float(row['Gen_New']), 0.0))
        total_generators += len(df_gen)
        
        # Progress update
        if total_cases_added % 20 == 0:
            print(f"  Progress: {total_cases_added} new cases added...")
    
    conn.commit()
    
    print("\n" + "="*80)
    print("LOADING SUMMARY")
    print("="*80)
    print(f"  New SLR Cases Added: {total_cases_added}")
    print(f"  Cases Skipped (already exist): {total_cases_skipped}")
    print(f"  New Bus Records: {total_buses}")
    print(f"  New Branch Records: {total_branches}")
    print(f"  New Load Records: {total_loads}")
    print(f"  New Generator Records: {total_generators}")
    print("="*80)

def verify_data(conn):
    """Verify the loaded data."""
    print("\n" + "="*80)
    print("VERIFICATION")
    print("="*80)
    
    cursor = conn.cursor()
    
    # Check total counts
    cursor.execute("SELECT COUNT(*) FROM SLR_Cases")
    total_cases = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM SLR_PostAction_BusData")
    total_buses = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM SLRBranchData")
    total_branches = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM SLR_Load")
    total_loads = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM SLR_Generator")
    total_generators = cursor.fetchone()[0]
    
    print(f"\nTotal SLR Cases: {total_cases}")
    print(f"Total Bus Records: {total_buses}")
    print(f"Total Branch Records: {total_branches}")
    print(f"Total Load Records: {total_loads}")
    print(f"Total Generator Records: {total_generators}")
    
    # List all case IDs
    cursor.execute("SELECT DISTINCT contingency_case_id FROM SLR_Cases ORDER BY contingency_case_id")
    case_ids = [row[0] for row in cursor.fetchall()]
    print(f"\nCase ID range: {min(case_ids)} to {max(case_ids)}")
    print(f"Case IDs: {case_ids}")
    
    # Check branch RATE statistics
    cursor.execute("SELECT COUNT(*) FROM SLRBranchData WHERE Rate > 0")
    non_zero_rate = cursor.fetchone()[0]
    if total_branches > 0:
        print(f"\nBranches with RATE > 0: {non_zero_rate} / {total_branches} ({100*non_zero_rate/total_branches:.1f}%)")
    
    # Sample new data
    print("\nSample branch data from new cases (Case 1, first 3 branches):")
    cursor.execute("""
        SELECT contingency_case_id, from_bus, to_bus, Rate, MVA, VIO 
        FROM SLRBranchData 
        WHERE contingency_case_id = 1 
        LIMIT 3
    """)
    for row in cursor.fetchall():
        print(f"  Case {row[0]}, Line {row[1]}-{row[2]}: Rate={row[3]:.2f}, MVA={row[4]:.2f}, VIO={row[5]:.2f}%")
    
    print("\n" + "="*80)
    print("✓ NEW DATA ADDED SUCCESSFULLY!")
    print("="*80)

def main():
    """Main execution function."""
    print("\n" + "="*80)
    print("ADD NEW SLR DATA TO data - Copy.db")
    print("="*80)
    print(f"Database: {DATABASE_PATH}")
    print(f"Data Folder: {DATA_FOLDER}")
    
    if not os.path.exists(DATA_FOLDER):
        print(f"\n[ERROR] Data folder not found: {DATA_FOLDER}")
        return
    
    if not os.path.exists(DATABASE_PATH):
        print(f"\n[ERROR] Database not found: {DATABASE_PATH}")
        return
    
    # Connect to database
    conn = sqlite3.connect(DATABASE_PATH)
    
    try:
        # Load new data
        load_new_slr_data(conn)
        
        # Verify
        verify_data(conn)
        
    except Exception as e:
        print(f"\n[ERROR] Failed to load data: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
