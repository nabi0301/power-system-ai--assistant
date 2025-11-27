"""
Migrate only the two large tables that failed:
- ContingencyBusData -> ContingencyBusData_sqlite (12.5M rows)
- ContingencyBranchData -> ContingencyBranchData_sqlite (19.7M rows)
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
        logging.FileHandler('C:\\Users\\nira771\\large_tables_migration.log', encoding='utf-8'),
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

BATCH_SIZE = 1000
TABLES_TO_MIGRATE = ['ContingencyBusData', 'ContingencyBranchData']

def get_table_info(sqlite_conn, table_name):
    """Get column information for a table"""
    cursor = sqlite_conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    return columns

def get_row_count(sqlite_conn, table_name):
    """Get row count from SQLite table"""
    cursor = sqlite_conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    count = cursor.fetchone()[0]
    cursor.close()
    return count

def map_sqlite_type_to_postgres(sqlite_type):
    """Map SQLite data types to PostgreSQL data types"""
    if not sqlite_type:
        return 'TEXT'
    
    sqlite_type_upper = sqlite_type.upper()
    
    if 'INT' in sqlite_type_upper:
        return 'INTEGER'
    elif any(t in sqlite_type_upper for t in ['REAL', 'FLOAT', 'DOUBLE']):
        return 'DOUBLE PRECISION'
    elif 'NUMERIC' in sqlite_type_upper or 'DECIMAL' in sqlite_type_upper:
        return 'NUMERIC'
    elif any(t in sqlite_type_upper for t in ['CHAR', 'CLOB', 'TEXT', 'VARCHAR']):
        return 'TEXT'
    elif 'BLOB' in sqlite_type_upper:
        return 'BYTEA'
    elif 'BOOL' in sqlite_type_upper:
        return 'BOOLEAN'
    elif 'DATE' in sqlite_type_upper:
        return 'DATE'
    elif 'TIME' in sqlite_type_upper:
        return 'TIMESTAMP'
    else:
        return 'TEXT'

def create_postgres_table(pg_conn, table_name, columns):
    """Create table in PostgreSQL based on SQLite schema"""
    cursor = pg_conn.cursor()
    
    column_defs = []
    primary_keys = []
    
    for col in columns:
        col_id, col_name, col_type, not_null, default_val, is_pk = col
        
        pg_type = map_sqlite_type_to_postgres(col_type)
        
        col_def = f'"{col_name}" {pg_type}'
        
        if is_pk:
            primary_keys.append(col_name)
        elif not_null:
            col_def += " NOT NULL"
        
        column_defs.append(col_def)
    
    # Add primary key constraint if exists
    if primary_keys:
        pk_cols = ', '.join([f'"{pk}"' for pk in primary_keys])
        pk_constraint = f"PRIMARY KEY ({pk_cols})"
        column_defs.append(pk_constraint)
    
    create_table_sql = f"""
        CREATE TABLE "{table_name}" (
            {',\n            '.join(column_defs)}
        );
    """
    
    logging.info(f"Creating table: {table_name}")
    
    try:
        cursor.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE;')
        cursor.execute(create_table_sql)
        pg_conn.commit()
        logging.info(f"[OK] Table '{table_name}' created successfully")
        return True
    except Exception as e:
        logging.error(f"[ERROR] Error creating table '{table_name}': {e}")
        pg_conn.rollback()
        return False
    finally:
        cursor.close()

def migrate_table_data(sqlite_conn, pg_conn, source_table, dest_table, batch_size=1000):
    """Migrate data from SQLite table to PostgreSQL table"""
    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()
    
    # Get row count
    total_rows = get_row_count(sqlite_conn, source_table)
    
    if total_rows == 0:
        logging.info(f"  Table '{source_table}' is empty")
        return 0
    
    logging.info(f"  Migrating {total_rows:,} rows from '{source_table}' to '{dest_table}'...")
    
    # Get column names
    sqlite_cur.execute(f"PRAGMA table_info({source_table});")
    columns = [col[1] for col in sqlite_cur.fetchall()]
    
    # Fetch data from SQLite in batches
    sqlite_cur.execute(f'SELECT * FROM "{source_table}";')
    
    inserted_count = 0
    batch = []
    
    # Prepare INSERT statement with quoted column names
    column_list = ', '.join([f'"{col}"' for col in columns])
    placeholders = ', '.join(['%s'] * len(columns))
    insert_sql = f'INSERT INTO "{dest_table}" ({column_list}) VALUES ({placeholders})'
    
    try:
        start_time = datetime.now()
        last_log_time = start_time
        
        while True:
            rows = sqlite_cur.fetchmany(batch_size)
            if not rows:
                break
            
            batch.extend(rows)
            
            if len(batch) >= batch_size:
                extras.execute_batch(pg_cur, insert_sql, batch, page_size=batch_size)
                inserted_count += len(batch)
                
                # Log progress every 10 seconds or 10,000 rows
                current_time = datetime.now()
                if inserted_count % 10000 == 0 or (current_time - last_log_time).seconds >= 10:
                    elapsed = (current_time - start_time).seconds
                    rate = inserted_count / elapsed if elapsed > 0 else 0
                    remaining = (total_rows - inserted_count) / rate if rate > 0 else 0
                    logging.info(f"    Progress: {inserted_count:,}/{total_rows:,} rows ({inserted_count/total_rows*100:.1f}%) - {rate:.0f} rows/sec - Est. remaining: {remaining/60:.1f} min")
                    last_log_time = current_time
                
                batch = []
        
        # Insert remaining rows
        if batch:
            extras.execute_batch(pg_cur, insert_sql, batch, page_size=len(batch))
            inserted_count += len(batch)
        
        pg_conn.commit()
        duration = (datetime.now() - start_time).seconds
        logging.info(f"  [OK] Successfully migrated {inserted_count:,} rows in {duration} seconds ({inserted_count/duration if duration > 0 else 0:.0f} rows/sec)")
        return inserted_count
        
    except Exception as e:
        logging.error(f"  [ERROR] Error migrating data: {e}")
        pg_conn.rollback()
        return 0
    finally:
        sqlite_cur.close()
        pg_cur.close()

def main():
    start_time = datetime.now()
    
    logging.info("=" * 80)
    logging.info("Large Tables Migration (ContingencyBusData & ContingencyBranchData)")
    logging.info("=" * 80)
    logging.info(f"Source SQLite: {SQLITE_DB_PATH}")
    logging.info(f"Destination PostgreSQL: {POSTGRES_CONFIG['dbname']} at {POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}")
    logging.info(f"Started: {start_time}")
    logging.info("=" * 80)
    
    # Connect to SQLite
    try:
        sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
        logging.info(f"[OK] Connected to SQLite database")
    except Exception as e:
        logging.error(f"[ERROR] Failed to connect to SQLite: {e}")
        return
    
    # Connect to PostgreSQL
    try:
        pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
        logging.info(f"[OK] Connected to PostgreSQL database '{POSTGRES_CONFIG['dbname']}'")
    except Exception as e:
        logging.error(f"[ERROR] Failed to connect to PostgreSQL: {e}")
        sqlite_conn.close()
        return
    
    try:
        total_rows_migrated = 0
        
        for idx, table_name in enumerate(TABLES_TO_MIGRATE, 1):
            dest_table_name = f"{table_name}_sqlite"
            row_count = get_row_count(sqlite_conn, table_name)
            
            logging.info(f"\n[{idx}/{len(TABLES_TO_MIGRATE)}] Processing: '{table_name}' ({row_count:,} rows)")
            logging.info("-" * 80)
            
            try:
                # Get table schema
                columns = get_table_info(sqlite_conn, table_name)
                
                # Create table
                if create_postgres_table(pg_conn, dest_table_name, columns):
                    # Migrate data
                    rows_migrated = migrate_table_data(sqlite_conn, pg_conn, table_name, dest_table_name, BATCH_SIZE)
                    total_rows_migrated += rows_migrated
                else:
                    logging.error(f"Failed to create table {dest_table_name}")
                
            except Exception as e:
                logging.error(f"[ERROR] Failed to migrate table '{table_name}': {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        logging.info("\n" + "=" * 80)
        logging.info("Migration Summary")
        logging.info("=" * 80)
        logging.info(f"Total rows migrated: {total_rows_migrated:,}")
        logging.info(f"Duration: {duration}")
        logging.info(f"Completed: {end_time}")
        logging.info("=" * 80)
        
    finally:
        sqlite_conn.close()
        pg_conn.close()
        logging.info("\n[OK] Database connections closed")

if __name__ == "__main__":
    main()
