import pandas as pd
import psycopg2
from pathlib import Path
import re

# Test importing one base case
def test_import_one_base_case():
    # Database connection
    conn = psycopg2.connect(
        host='localhost', 
        database='118', 
        user='postgres', 
        password='pnnl'
    )
    cursor = conn.cursor()
    
    # Find first base case file
    base_folder = Path(r"C:\Projects\dlr-database-project\Base_118")
    base_files = list(base_folder.glob("*.txt"))
    
    if not base_files:
        print("No base case files found!")
        return False
    
    file_path = base_files[0]
    print(f"Testing with file: {file_path.name}")
    
    # Extract case number
    match = re.search(r'BASE_(\d+)_', file_path.name, re.IGNORECASE)
    if not match:
        # Try alternative pattern
        match = re.search(r'BASE.*?(\d+)', file_path.name, re.IGNORECASE)
    if not match:
        print(f"Could not extract case number from {file_path.name}")
        return False
    
    case_number = int(match.group(1))
    print(f"Case number: {case_number}")
    
    # Read file
    try:
        # Read the file skipping the header and using fixed-width columns
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Skip first two lines (they seem to be headers)
        data_lines = [line.strip() for line in lines[2:] if line.strip()]
        
        if not data_lines:
            print("No data lines found in file")
            return False
        
        # Parse each line as space-separated values and handle duplicates
        data_dict = {}  # Use dict to handle duplicates by keeping last occurrence
        for line in data_lines:
            # Split by whitespace and convert to numbers
            parts = line.split()
            if len(parts) >= 8:  # Expecting at least 8 columns
                try:
                    bus_number = int(float(parts[0]))
                    row = [float(p) for p in parts[:8]]  # Take first 8 columns
                    data_dict[bus_number] = row  # This will overwrite duplicates with last occurrence
                except ValueError:
                    continue  # Skip lines that can't be parsed
        
        if not data_dict:
            print("No valid data rows found")
            return False
            
        # Convert to list format
        data_rows = list(data_dict.values())
        print(f"Original lines: {len(data_lines)}, Unique buses: {len(data_rows)}")
            
        # Create DataFrame
        df = pd.DataFrame(data_rows, columns=['BUS_NUMBER', 'VM', 'VA', 'BASE_KV', 'PG', 'QG', 'PD', 'QD'])
        
        print(f"File columns: {list(df.columns)}")
        print(f"File shape: {df.shape}")
        print(f"First few rows:")
        print(df.head(3))
        
        # Create base case record
        cursor.execute("""
            INSERT INTO BaseCases (case_number, filename, case_name, folder_name, processing_status)
            VALUES (%s, %s, %s, %s, 'processing')
            ON CONFLICT (case_number) DO UPDATE SET
                filename = EXCLUDED.filename,
                processing_status = EXCLUDED.processing_status
            RETURNING base_case_id
        """, (case_number, file_path.name, f"Base Case {case_number}", "Base_118"))
        
        base_case_id = cursor.fetchone()[0]
        print(f"Base case ID: {base_case_id}")
        
        # Import bus data
        bus_records = []
        for _, row in df.iterrows():
            bus_number = int(row['BUS_NUMBER'])
            vm = float(row.get('VM', 1.0))
            va = float(row.get('VA', 0.0))
            base_kv = float(row.get('BASE_KV', 138.0))
            pg = float(row.get('PG', 0.0))
            qg = float(row.get('QG', 0.0))
            pd_val = float(row.get('PD', 0.0))
            qd = float(row.get('QD', 0.0))
            
            bus_records.append((base_case_id, bus_number, vm, va, base_kv, pg, qg, pd_val, qd))
        
        print(f"Importing {len(bus_records)} bus records...")
        
        # Clear and insert
        cursor.execute("DELETE FROM BaseBusData WHERE base_case_id = %s", (base_case_id,))
        cursor.executemany("""
            INSERT INTO BaseBusData 
            (base_case_id, bus_number, vm, va, base_kv, pg, qg, pd, qd)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, bus_records)
        
        # Update status
        cursor.execute("""
            UPDATE BaseCases 
            SET buses_count = %s, processing_status = 'completed'
            WHERE base_case_id = %s
        """, (len(bus_records), base_case_id))
        
        conn.commit()
        print(f"✅ Successfully imported base case {case_number} with {len(bus_records)} buses")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        return False

# Test importing one contingency case
def test_import_one_contingency_case():
    # Database connection
    conn = psycopg2.connect(
        host='localhost', 
        database='118', 
        user='postgres', 
        password='pnnl'
    )
    cursor = conn.cursor()
    
    # Get base case ID
    cursor.execute("SELECT base_case_id FROM BaseCases ORDER BY case_number LIMIT 1")
    base_case_result = cursor.fetchone()
    if not base_case_result:
        print("No base case found - run base case import first")
        return False
    
    base_case_id = base_case_result[0]
    print(f"Using base case ID: {base_case_id}")
    
    # Find first contingency case file
    contingency_folder = Path(r"C:\Projects\dlr-database-project\contingency_118")
    contingency_files = list(contingency_folder.glob("*.txt"))
    
    if not contingency_files:
        print("No contingency case files found!")
        return False
    
    file_path = contingency_files[0]
    print(f"Testing with file: {file_path.name}")
    
    # Extract case number
    match = re.search(r'CA_(\d+)_', file_path.name, re.IGNORECASE)
    if not match:
        # Try alternative pattern
        match = re.search(r'CA.*?(\d+)', file_path.name, re.IGNORECASE)
    if not match:
        print(f"Could not extract case number from {file_path.name}")
        return False
    
    case_number = int(match.group(1))
    print(f"Case number: {case_number}")
    
    # Read file
    try:
        # Read the file - contingency files have different format
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Contingency files start with a number, skip only first line
        data_lines = [line.strip() for line in lines[1:] if line.strip()]
        
        if not data_lines:
            print("No data lines found in file")
            return False
        
        # Parse each line as space-separated values and handle duplicates
        data_dict = {}  # Use dict to handle duplicates by keeping last occurrence
        for line in data_lines:
            # Split by whitespace and convert to numbers
            parts = line.split()
            if len(parts) >= 7:  # Contingency files might have 7 columns (no BASE_KV)
                try:
                    bus_number = int(float(parts[0]))
                    if len(parts) >= 8:
                        # Full 8 columns
                        row = [float(p) for p in parts[:8]]
                    else:
                        # 7 columns, insert default BASE_KV
                        row = [float(parts[0]), float(parts[1]), float(parts[2]), 138.0,
                               float(parts[3]), float(parts[4]), float(parts[5]), float(parts[6])]
                    data_dict[bus_number] = row
                except ValueError:
                    continue  # Skip lines that can't be parsed
        
        if not data_dict:
            print("No valid data rows found")
            return False
            
        # Convert to list format
        data_rows = list(data_dict.values())
        print(f"Original lines: {len(data_lines)}, Unique buses: {len(data_rows)}")
            
        # Create DataFrame
        df = pd.DataFrame(data_rows, columns=['BUS_NUMBER', 'VM', 'VA', 'BASE_KV', 'PG', 'QG', 'PD', 'QD'])
        
        print(f"File columns: {list(df.columns)}")
        print(f"File shape: {df.shape}")
        print(f"First few rows:")
        print(df.head(3))
        
        # Create contingency case record
        cursor.execute("""
            INSERT INTO ContingencyCases 
            (base_case_id, case_number, filename, case_name, contingency_element, folder_name, processing_status)
            VALUES (%s, %s, %s, %s, %s, %s, 'processing')
            ON CONFLICT (base_case_id, case_number) DO UPDATE SET
                filename = EXCLUDED.filename,
                processing_status = EXCLUDED.processing_status
            RETURNING contingency_case_id
        """, (base_case_id, case_number, file_path.name, f"Contingency Case {case_number}", f"Contingency {case_number}", "contingency_118"))
        
        contingency_case_id = cursor.fetchone()[0]
        print(f"Contingency case ID: {contingency_case_id}")
        
        # Import bus data
        bus_records = []
        for _, row in df.iterrows():
            bus_number = int(row['BUS_NUMBER'])
            vm = float(row.get('VM', 1.0))
            va = float(row.get('VA', 0.0))
            base_kv = float(row.get('BASE_KV', 138.0))
            pg = float(row.get('PG', 0.0))
            qg = float(row.get('QG', 0.0))
            pd_val = float(row.get('PD', 0.0))
            qd = float(row.get('QD', 0.0))
            
            bus_records.append((contingency_case_id, bus_number, vm, va, base_kv, pg, qg, pd_val, qd))
        
        print(f"Importing {len(bus_records)} bus records...")
        
        # Clear and insert
        cursor.execute("DELETE FROM ContingencyBusData WHERE contingency_case_id = %s", (contingency_case_id,))
        cursor.executemany("""
            INSERT INTO ContingencyBusData 
            (contingency_case_id, bus_number, vm, va, base_kv, pg, qg, pd, qd)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, bus_records)
        
        # Update status
        cursor.execute("""
            UPDATE ContingencyCases 
            SET buses_count = %s, processing_status = 'completed'
            WHERE contingency_case_id = %s
        """, (len(bus_records), contingency_case_id))
        
        conn.commit()
        print(f"✅ Successfully imported contingency case {case_number} with {len(bus_records)} buses")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        return False

if __name__ == "__main__":
    print("🧪 Testing Contingency Case Loader")
    print("=" * 40)
    
    print("\n1. Testing base case import...")
    if test_import_one_base_case():
        print("✅ Base case import successful")
        
        print("\n2. Testing contingency case import...")
        if test_import_one_contingency_case():
            print("✅ Contingency case import successful")
            print("\n🎉 All tests passed!")
        else:
            print("❌ Contingency case import failed")
    else:
        print("❌ Base case import failed")