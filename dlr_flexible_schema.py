"""
DLR (Dynamic Line Rating) Database - Flexible Schema Setup
Created for Power Systems DLR Analytics Project

This script creates a flexible database structure that can adapt
to any DLR data format until we receive actual data files.
"""

import sys
from sqlalchemy import create_engine, text
from config import DATABASE_URL

def create_flexible_dlr_schema():
    """Create adaptable database structure for DLR data"""
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("🔄 Creating DLR flexible database schema...")
        
        # Main flexible data table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dlr_raw_data (
                id BIGSERIAL PRIMARY KEY,
                
                -- Data identification
                data_source VARCHAR(100),           -- 'scada', 'weather_station', 'manual_entry'
                data_type VARCHAR(100),             -- 'temperature', 'current', 'wind_speed'
                measurement_timestamp TIMESTAMP WITH TIME ZONE,
                
                -- Flexible storage
                raw_data JSONB,                     -- Original data as received
                processed_data JSONB,               -- Cleaned/processed version
                metadata JSONB,                     -- Additional information
                
                -- Import tracking
                file_name VARCHAR(255),
                import_batch_id VARCHAR(100),
                import_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                
                -- Data quality
                data_quality_score DECIMAL(3,2),   -- 0.0 to 1.0
                validation_status VARCHAR(50),      -- 'pending', 'validated', 'rejected'
                quality_notes TEXT,
                
                -- Timestamps
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """))
        
        # Create performance indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_dlr_raw_source_type 
            ON dlr_raw_data (data_source, data_type);
            
            CREATE INDEX IF NOT EXISTS idx_dlr_raw_timestamp 
            ON dlr_raw_data (measurement_timestamp DESC);
            
            CREATE INDEX IF NOT EXISTS idx_dlr_raw_data_gin 
            ON dlr_raw_data USING GIN (raw_data);
            
            CREATE INDEX IF NOT EXISTS idx_dlr_raw_processed_gin 
            ON dlr_raw_data USING GIN (processed_data);
        """))
        
        # Data import log table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dlr_import_log (
                id BIGSERIAL PRIMARY KEY,
                batch_id VARCHAR(100) UNIQUE,
                file_name VARCHAR(255),
                file_size_bytes BIGINT,
                records_imported INTEGER,
                records_failed INTEGER,
                import_status VARCHAR(50),
                error_summary TEXT,
                started_at TIMESTAMP WITH TIME ZONE,
                completed_at TIMESTAMP WITH TIME ZONE,
                imported_by VARCHAR(100)
            );
        """))
        
        conn.commit()
        print("✅ DLR flexible schema created successfully!")
        
        # Test the schema
        test_flexible_schema(conn)

def test_flexible_schema(conn):
    """Test the flexible schema with sample DLR data"""
    print("🧪 Testing flexible schema...")
    
    # Insert sample DLR data
    sample_data = {
        "temperature": 25.5,
        "current": 450.2,
        "wind_speed": 3.2,
        "line_id": "LINE_001"
    }
    
    conn.execute(text("""
        INSERT INTO dlr_raw_data 
        (data_source, data_type, raw_data, import_batch_id)
        VALUES 
        (:source, :type, :data, :batch)
    """), {
        'source': 'test_data',
        'type': 'dlr_measurement',
        'data': str(sample_data).replace("'", '"'),  # Convert to JSON format
        'batch': 'test_batch_001'
    })
    
    # Query back the data
    result = conn.execute(text("""
        SELECT data_source, data_type, raw_data 
        FROM dlr_raw_data 
        WHERE import_batch_id = 'test_batch_001'
    """))
    
    row = result.fetchone()
    if row:
        print(f"✅ Test data stored: {row[0]} - {row[1]}")
        print(f"✅ Sample data: {row[2]}")
    
    conn.commit()

if __name__ == "__main__":
    try:
        create_flexible_dlr_schema()
        print("\n🎉 Task 1.2 Complete: Flexible DLR Database Created!")
        print("➡️ Ready for Task 1.3: Data Import Tools")
    except Exception as e:
        print(f"❌ Error creating schema: {e}")
        sys.exit(1)