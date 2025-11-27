"""
DLR Data Import Tools
Handles CSV, Excel, JSON data import into flexible schema
"""

import pandas as pd
import json
import uuid
from datetime import datetime
from sqlalchemy import create_engine, text
from config import DATABASE_URL

class DLRDataImporter:
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        
    def import_csv_file(self, file_path, data_source="csv_import"):
        """Import CSV file with DLR data"""
        print(f"📁 Importing CSV file: {file_path}")
        
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            print(f"📊 Found {len(df)} rows and {len(df.columns)} columns")
            
            # Generate batch ID for tracking
            batch_id = f"csv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
            
            # Import data
            imported_count = 0
            failed_count = 0
            
            with self.engine.connect() as conn:
                # Log import start
                self._log_import_start(conn, batch_id, file_path, len(df))
                
                for index, row in df.iterrows():
                    try:
                        # Convert row to dictionary and handle NaN values
                        row_data = row.to_dict()
                        row_data = {k: (v if pd.notna(v) else None) for k, v in row_data.items()}
                        
                        # Try to extract timestamp if exists
                        timestamp = self._extract_timestamp(row_data)
                        
                        # Store in database
                        conn.execute(text("""
                            INSERT INTO dlr_raw_data 
                            (data_source, data_type, raw_data, measurement_timestamp, 
                             file_name, import_batch_id)
                            VALUES (:source, :type, :data, :timestamp, :filename, :batch)
                        """), {
                            'source': data_source,
                            'type': 'csv_record',
                            'data': json.dumps(row_data),
                            'timestamp': timestamp,
                            'filename': file_path,
                            'batch': batch_id
                        })
                        imported_count += 1
                        
                    except Exception as e:
                        print(f"⚠️ Failed to import row {index}: {e}")
                        failed_count += 1
                
                # Log import completion
                self._log_import_complete(conn, batch_id, imported_count, failed_count)
                conn.commit()
            
            print(f"✅ Import complete: {imported_count} successful, {failed_count} failed")
            return batch_id
            
        except Exception as e:
            print(f"❌ Error importing CSV: {e}")
            return None
    
    def import_excel_file(self, file_path, data_source="excel_import"):
        """Import Excel file with multiple sheets"""
        print(f"📁 Importing Excel file: {file_path}")
        
        try:
            # Read all sheets
            xl_file = pd.ExcelFile(file_path)
            print(f"📊 Found {len(xl_file.sheet_names)} sheets: {xl_file.sheet_names}")
            
            batch_ids = []
            
            for sheet_name in xl_file.sheet_names:
                print(f"📄 Processing sheet: {sheet_name}")
                
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                batch_id = f"excel_{sheet_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
                
                # Import each sheet as separate data source
                sheet_source = f"{data_source}_{sheet_name}"
                imported_count = 0
                
                with self.engine.connect() as conn:
                    self._log_import_start(conn, batch_id, f"{file_path}#{sheet_name}", len(df))
                    
                    for index, row in df.iterrows():
                        try:
                            row_data = row.to_dict()
                            row_data = {k: (v if pd.notna(v) else None) for k, v in row_data.items()}
                            
                            timestamp = self._extract_timestamp(row_data)
                            
                            conn.execute(text("""
                                INSERT INTO dlr_raw_data 
                                (data_source, data_type, raw_data, measurement_timestamp, 
                                 file_name, import_batch_id)
                                VALUES (:source, :type, :data, :timestamp, :filename, :batch)
                            """), {
                                'source': sheet_source,
                                'type': 'excel_record',
                                'data': json.dumps(row_data),
                                'timestamp': timestamp,
                                'filename': f"{file_path}#{sheet_name}",
                                'batch': batch_id
                            })
                            imported_count += 1
                            
                        except Exception as e:
                            print(f"⚠️ Failed to import row {index} from {sheet_name}: {e}")
                    
                    self._log_import_complete(conn, batch_id, imported_count, 0)
                    conn.commit()
                
                batch_ids.append(batch_id)
                print(f"✅ Sheet '{sheet_name}' imported: {imported_count} records")
            
            return batch_ids
            
        except Exception as e:
            print(f"❌ Error importing Excel: {e}")
            return None
    
    def import_json_data(self, json_data, data_source="json_import"):
        """Import JSON data directly"""
        print(f"📄 Importing JSON data from: {data_source}")
        
        batch_id = f"json_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        try:
            with self.engine.connect() as conn:
                if isinstance(json_data, list):
                    # Array of records
                    self._log_import_start(conn, batch_id, "json_array", len(json_data))
                    
                    for i, record in enumerate(json_data):
                        timestamp = self._extract_timestamp(record)
                        
                        conn.execute(text("""
                            INSERT INTO dlr_raw_data 
                            (data_source, data_type, raw_data, measurement_timestamp, import_batch_id)
                            VALUES (:source, :type, :data, :timestamp, :batch)
                        """), {
                            'source': data_source,
                            'type': 'json_record',
                            'data': json.dumps(record),
                            'timestamp': timestamp,
                            'batch': batch_id
                        })
                else:
                    # Single record
                    self._log_import_start(conn, batch_id, "json_object", 1)
                    
                    timestamp = self._extract_timestamp(json_data)
                    conn.execute(text("""
                        INSERT INTO dlr_raw_data 
                        (data_source, data_type, raw_data, measurement_timestamp, import_batch_id)
                        VALUES (:source, :type, :data, :timestamp, :batch)
                    """), {
                        'source': data_source,
                        'type': 'json_record',
                        'data': json.dumps(json_data),
                        'timestamp': timestamp,
                        'batch': batch_id
                    })
                
                self._log_import_complete(conn, batch_id, 1, 0)
                conn.commit()
            
            print(f"✅ JSON data imported successfully")
            return batch_id
            
        except Exception as e:
            print(f"❌ Error importing JSON: {e}")
            return None
    
    def analyze_imported_data(self, batch_id=None):
        """Analyze structure of imported data"""
        print("🔍 Analyzing imported data structure...")
        
        with self.engine.connect() as conn:
            if batch_id:
                # Analyze specific batch
                result = conn.execute(text("""
                    SELECT data_source, data_type, COUNT(*) as record_count,
                           raw_data
                    FROM dlr_raw_data 
                    WHERE import_batch_id = :batch_id
                    GROUP BY data_source, data_type, raw_data
                    LIMIT 10
                """), {'batch_id': batch_id})
            else:
                # Analyze all data
                result = conn.execute(text("""
                    SELECT data_source, data_type, COUNT(*) as record_count
                    FROM dlr_raw_data 
                    GROUP BY data_source, data_type
                    ORDER BY record_count DESC
                """))
            
            analysis = result.fetchall()
            
            print("\n📊 Data Analysis Results:")
            for row in analysis:
                print(f"   {row[0]} | {row[1]} | {row[2]} records")
        
        return analysis
    
    def get_import_history(self):
        """Show import history"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT batch_id, file_name, records_imported, 
                       import_status, started_at, completed_at
                FROM dlr_import_log 
                ORDER BY started_at DESC
                LIMIT 10
            """))
            
            history = result.fetchall()
            
            print("\n📚 Recent Import History:")
            for row in history:
                print(f"   {row[0][:20]} | {row[1]} | {row[2]} records | {row[3]}")
        
        return history
    
    def _extract_timestamp(self, data_dict):
        """Try to extract timestamp from data"""
        timestamp_fields = ['timestamp', 'time', 'datetime', 'date', 'measurement_time']
        
        for field in timestamp_fields:
            if field in data_dict and data_dict[field]:
                try:
                    # Try to parse timestamp
                    return pd.to_datetime(data_dict[field])
                except:
                    continue
        
        return None
    
    def _log_import_start(self, conn, batch_id, file_name, record_count):
        """Log import start"""
        conn.execute(text("""
            INSERT INTO dlr_import_log 
            (batch_id, file_name, import_status, started_at)
            VALUES (:batch, :filename, 'in_progress', NOW())
        """), {
            'batch': batch_id,
            'filename': file_name
        })
    
    def _log_import_complete(self, conn, batch_id, imported, failed):
        """Log import completion"""
        status = 'completed' if failed == 0 else 'completed_with_errors'
        
        conn.execute(text("""
            UPDATE dlr_import_log 
            SET records_imported = :imported,
                records_failed = :failed,
                import_status = :status,
                completed_at = NOW()
            WHERE batch_id = :batch
        """), {
            'imported': imported,
            'failed': failed,
            'status': status,
            'batch': batch_id
        })

# Test and demonstration functions
def test_importer():
    """Test the importer with sample data"""
    print("🧪 Testing DLR Data Importer...")
    
    importer = DLRDataImporter()
    
    # Test with sample DLR data
    sample_dlr_data = [
        {
            "timestamp": "2024-01-15 10:00:00",
            "line_id": "LINE_001",
            "current_amps": 450.2,
            "temperature_celsius": 25.5,
            "wind_speed_mps": 3.2,
            "dynamic_rating_amps": 520
        },
        {
            "timestamp": "2024-01-15 10:15:00",
            "line_id": "LINE_001", 
            "current_amps": 465.8,
            "temperature_celsius": 26.1,
            "wind_speed_mps": 2.8,
            "dynamic_rating_amps": 510
        }
    ]
    
    # Test JSON import
    batch_id = importer.import_json_data(sample_dlr_data, "test_dlr_data")
    
    if batch_id:
        print(f"✅ Test import successful: {batch_id}")
        importer.analyze_imported_data(batch_id)
        importer.get_import_history()
    
if __name__ == "__main__":
    test_importer()