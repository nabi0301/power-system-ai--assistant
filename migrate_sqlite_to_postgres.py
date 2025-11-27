"""
SQLite to PostgreSQL Migration Script
Migrates data from SQLite database to PostgreSQL database '118'
"""

import sqlite3
import psycopg2
from psycopg2 import extras
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sqlite_to_postgres_migration.log'),
        logging.StreamHandler()
    ]
)

# Database configurations
SQLITE_DB_PATH = r"C:\Users\nira771\data - Copy.db"

POSTGRES_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'dbname': '118',
    'user': 'postgres',
    'password': 'pnnl'
}

def get_sqlite_tables(sqlite_conn):
    """Get all table names from SQLite database"""
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    return tables

def get_table_info(sqlite_conn, table_name):
    """Get column information for a table"""
    cursor = sqlite_conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    return columns

def map_sqlite_type_to_postgres(sqlite_type):
    """Map SQLite data types to PostgreSQL data types"""
    sqlite_type = sqlite_type.upper()
    
    type_mapping = {
        'INTEGER': 'INTEGER',
        'INT': 'INTEGER',
        'REAL': 'DOUBLE PRECISION',
        'FLOAT': 'DOUBLE PRECISION',
        'DOUBLE': 'DOUBLE PRECISION',
        'TEXT': 'TEXT',
        'VARCHAR': 'VARCHAR',
        'CHAR': 'CHAR',
        'BLOB': 'BYTEA',
        'NUMERIC': 'NUMERIC',
        'BOOLEAN': 'BOOLEAN',
        'DATE': 'DATE',
        'DATETIME': 'TIMESTAMP',
        'TIMESTAMP': 'TIMESTAMP'
    }
    
    # Check for VARCHAR with length
    if 'VARCHAR' in sqlite_type:
        return sqlite_type
    
    for sqlite_key, postgres_type in type_mapping.items():
        if sqlite_key in sqlite_type:
            return postgres_type
    
    # Default to TEXT if type not recognized
    return 'TEXT'

def check_postgres_table_exists(pg_conn, table_name):
    """Check if table exists in PostgreSQL"""
    cursor = pg_conn.cursor()
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %s
        );
    """, (table_name.lower(),))
    exists = cursor.fetchone()[0]
    cursor.close()
    return exists

def create_postgres_table(pg_conn, table_name, columns):
    """Create table in PostgreSQL based on SQLite schema"""
    cursor = pg_conn.cursor()
    
    column_defs = []
    primary_keys = []
    
    for col in columns:
        col_id, col_name, col_type, not_null, default_val, is_pk = col
        
        pg_type = map_sqlite_type_to_postgres(col_type)
        
        col_def = f"{col_name} {pg_type}"
        
        if is_pk:
            primary_keys.append(col_name)
            # Don't add NOT NULL here, will be handled by PRIMARY KEY
        elif not_null:
            col_def += " NOT NULL"
        
        if default_val is not None:
            col_def += f" DEFAULT {default_val}"
        
        column_defs.append(col_def)
    
    # Add primary key constraint if exists
    if primary_keys:
        pk_constraint = f"PRIMARY KEY ({', '.join(primary_keys)})"
        column_defs.append(pk_constraint)
    
    create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {', '.join(column_defs)}
        );
    """
    
    logging.info(f"Creating table: {table_name}")
    logging.debug(f"SQL: {create_table_sql}")
    
    try:
        cursor.execute(create_table_sql)
        pg_conn.commit()
        logging.info(f"✅ Table {table_name} created successfully")
    except Exception as e:
        logging.error(f"❌ Error creating table {table_name}: {e}")
        pg_conn.rollback()
        raise
    finally:
        cursor.close()

def migrate_table_data(sqlite_conn, pg_conn, table_name, batch_size=1000):
    """Migrate data from SQLite table to PostgreSQL table"""
    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()
    
    # Get row count
    sqlite_cur.execute(f"SELECT COUNT(*) FROM {table_name};")
    total_rows = sqlite_cur.fetchone()[0]
    
    if total_rows == 0:
        logging.info(f"Table {table_name} is empty, skipping data migration")
        return
    
    logging.info(f"Migrating {total_rows:,} rows from {table_name}...")
    
    # Get column names
    sqlite_cur.execute(f"PRAGMA table_info({table_name});")
    columns = [col[1] for col in sqlite_cur.fetchall()]
    
    # Fetch all data from SQLite
    sqlite_cur.execute(f"SELECT * FROM {table_name};")
    
    inserted_count = 0
    batch = []
    
    # Prepare INSERT statement
    placeholders = ', '.join(['%s'] * len(columns))
    insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
    
    try:
        while True:
            rows = sqlite_cur.fetchmany(batch_size)
            if not rows:
                break
            
            batch.extend(rows)
            
            if len(batch) >= batch_size:
                extras.execute_batch(pg_cur, insert_sql, batch, page_size=batch_size)
                inserted_count += len(batch)
                logging.info(f"  Inserted {inserted_count:,}/{total_rows:,} rows ({inserted_count/total_rows*100:.1f}%)")
                batch = []
        
        # Insert remaining rows
        if batch:
            extras.execute_batch(pg_cur, insert_sql, batch, page_size=len(batch))
            inserted_count += len(batch)
        
        pg_conn.commit()
        logging.info(f"✅ Migrated {inserted_count:,} rows to {table_name}")
        
    except Exception as e:
        logging.error(f"❌ Error migrating data to {table_name}: {e}")
        pg_conn.rollback()
        raise
    finally:
        sqlite_cur.close()
        pg_cur.close()

def reset_postgres_sequences(pg_conn, table_name, columns):
    """Reset PostgreSQL sequences for auto-increment columns"""
    cursor = pg_conn.cursor()
    
    for col in columns:
        col_id, col_name, col_type, not_null, default_val, is_pk = col
        
        if is_pk and 'INTEGER' in col_type.upper():
            try:
                # Get the maximum value from the column
                cursor.execute(f"SELECT MAX({col_name}) FROM {table_name};")
                max_val = cursor.fetchone()[0]
                
                if max_val is not None:
                    # Try to reset the sequence
                    sequence_name = f"{table_name}_{col_name}_seq"
                    cursor.execute(f"SELECT setval('{sequence_name}', {max_val}, true);")
                    logging.info(f"  Reset sequence {sequence_name} to {max_val}")
            except Exception as e:
                # Sequence might not exist or different naming
                logging.debug(f"  Could not reset sequence for {table_name}.{col_name}: {e}")
    
    pg_conn.commit()
    cursor.close()

def main():
    start_time = datetime.now()
    
    logging.info("=" * 70)
    logging.info("SQLite to PostgreSQL Migration")
    logging.info("=" * 70)
    logging.info(f"Source: {SQLITE_DB_PATH}")
    logging.info(f"Destination: PostgreSQL database '{POSTGRES_CONFIG['dbname']}'")
    logging.info(f"Started: {start_time}")
    logging.info("=" * 70)
    
    # Connect to SQLite
    try:
        sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
        logging.info(f"✅ Connected to SQLite database")
    except Exception as e:
        logging.error(f"❌ Failed to connect to SQLite: {e}")
        return
    
    # Connect to PostgreSQL
    try:
        pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
        logging.info(f"✅ Connected to PostgreSQL database")
    except Exception as e:
        logging.error(f"❌ Failed to connect to PostgreSQL: {e}")
        sqlite_conn.close()
        return
    
    try:
        # Get all tables from SQLite
        tables = get_sqlite_tables(sqlite_conn)
        logging.info(f"\nFound {len(tables)} tables to migrate: {', '.join(tables)}")
        
        migrated_tables = []
        failed_tables = []
        
        for table_name in tables:
            logging.info(f"\n{'='*70}")
            logging.info(f"Processing table: {table_name}")
            logging.info(f"{'='*70}")
            
            try:
                # Get table schema
                columns = get_table_info(sqlite_conn, table_name)
                
                # Check if table already exists in PostgreSQL
                if check_postgres_table_exists(pg_conn, table_name):
                    logging.warning(f"⚠️  Table {table_name} already exists in PostgreSQL")
                    user_input = input(f"Do you want to DROP and recreate {table_name}? (yes/no): ").strip().lower()
                    
                    if user_input == 'yes':
                        cursor = pg_conn.cursor()
                        cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
                        pg_conn.commit()
                        cursor.close()
                        logging.info(f"Dropped existing table {table_name}")
                    else:
                        logging.info(f"Skipping table {table_name}")
                        continue
                
                # Create table in PostgreSQL
                create_postgres_table(pg_conn, table_name, columns)
                
                # Migrate data
                migrate_table_data(sqlite_conn, pg_conn, table_name)
                
                # Reset sequences
                reset_postgres_sequences(pg_conn, table_name, columns)
                
                migrated_tables.append(table_name)
                
            except Exception as e:
                logging.error(f"❌ Failed to migrate table {table_name}: {e}")
                failed_tables.append(table_name)
                continue
        
        # Summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        logging.info("\n" + "=" * 70)
        logging.info("Migration Summary")
        logging.info("=" * 70)
        logging.info(f"Total tables: {len(tables)}")
        logging.info(f"✅ Successfully migrated: {len(migrated_tables)}")
        if migrated_tables:
            for table in migrated_tables:
                logging.info(f"   - {table}")
        
        if failed_tables:
            logging.info(f"❌ Failed: {len(failed_tables)}")
            for table in failed_tables:
                logging.info(f"   - {table}")
        
        logging.info(f"\nDuration: {duration}")
        logging.info(f"Completed: {end_time}")
        logging.info("=" * 70)
        
    finally:
        sqlite_conn.close()
        pg_conn.close()
        logging.info("Connections closed")

if __name__ == "__main__":
    main()
