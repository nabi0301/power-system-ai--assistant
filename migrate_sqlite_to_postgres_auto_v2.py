"""
SQLite to PostgreSQL Migration Script (Auto mode)
Automatically appends "_sqlite" to table names that conflict with existing PostgreSQL tables.
Skips tables that have already been successfully migrated.
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
        logging.FileHandler('C:\\Users\\nira771\\sqlite_to_postgres_migration_auto.log', encoding='utf-8'),
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

# Migration settings
DROP_EXISTING_TABLES = True  # Set to True to drop existing tables, False to append "_sqlite"
BATCH_SIZE = 1000

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

def get_row_count(sqlite_conn, table_name):
    """Get row count from SQLite table"""
    cursor = sqlite_conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    count = cursor.fetchone()[0]
    cursor.close()
    return count

def get_postgres_row_count(pg_conn, table_name):
    """Get row count from a PostgreSQL table"""
    try:
        cursor = pg_conn.cursor()
        cursor.execute(f'SELECT COUNT(*) FROM "{table_name}";')
        count = cursor.fetchone()[0]
        cursor.close()
        return count
    except Exception as e:
        logging.error(f"Error getting row count for {table_name}: {e}")
        pg_conn.rollback()  # Rollback the failed transaction
        return 0

def map_sqlite_type_to_postgres(sqlite_type):
    """Map SQLite data types to PostgreSQL data types"""
    if not sqlite_type:
        return 'TEXT'
    
    sqlite_type_upper = sqlite_type.upper()
    
    # Handle specific type mappings
    if 'INT' in sqlite_type_upper:
        return 'INTEGER'
    elif any(t in sqlite_type_upper for t in ['REAL', 'FLOAT', 'DOUBLE']):
        return 'DOUBLE PRECISION'
    elif 'NUMERIC' in sqlite_type_upper or 'DECIMAL' in sqlite_type_upper:
        return 'NUMERIC'
    elif any(t in sqlite_type_upper for t in ['CHAR', 'CLOB', 'TEXT', 'VARCHAR']):
        if 'VARCHAR' in sqlite_type and '(' in sqlite_type:
            return sqlite_type  # Preserve VARCHAR(n)
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

def check_postgres_table_exists(pg_conn, table_name):
    """Check if table exists in PostgreSQL"""
    try:
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
    except Exception as e:
        logging.error(f"Error checking if table {table_name} exists: {e}")
        pg_conn.rollback()
        return False

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
        
        if default_val is not None and not is_pk:
            # Skip CURRENT_TIMESTAMP string defaults - let PostgreSQL handle it natively
            if default_val == 'CURRENT_TIMESTAMP':
                col_def += " DEFAULT CURRENT_TIMESTAMP"
            elif isinstance(default_val, str) and not default_val.startswith("'"):
                col_def += f" DEFAULT '{default_val}'"
            else:
                col_def += f" DEFAULT {default_val}"
        
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
        logging.info(f"  Table '{source_table}' is empty, skipping data migration")
        return 0
    
    logging.info(f"  Migrating {total_rows:,} rows from '{source_table}' to '{dest_table}'...")
    
    # Get column names
    sqlite_cur.execute(f"PRAGMA table_info({source_table});")
    columns = [col[1] for col in sqlite_cur.fetchall()]
    
    # Fetch all data from SQLite
    sqlite_cur.execute(f'SELECT * FROM "{source_table}";')
    
    inserted_count = 0
    batch = []
    
    # Prepare INSERT statement with quoted column names
    column_list = ', '.join([f'"{col}"' for col in columns])
    placeholders = ', '.join(['%s'] * len(columns))
    insert_sql = f'INSERT INTO "{dest_table}" ({column_list}) VALUES ({placeholders})'
    
    try:
        while True:
            rows = sqlite_cur.fetchmany(batch_size)
            if not rows:
                break
            
            batch.extend(rows)
            
            if len(batch) >= batch_size:
                extras.execute_batch(pg_cur, insert_sql, batch, page_size=batch_size)
                inserted_count += len(batch)
                logging.info(f"    Progress: {inserted_count:,}/{total_rows:,} rows ({inserted_count/total_rows*100:.1f}%)")
                batch = []
        
        # Insert remaining rows
        if batch:
            extras.execute_batch(pg_cur, insert_sql, batch, page_size=len(batch))
            inserted_count += len(batch)
        
        pg_conn.commit()
        logging.info(f"  [OK] Successfully migrated {inserted_count:,} rows")
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
    logging.info("SQLite to PostgreSQL Migration (Auto Mode)")
    logging.info("=" * 80)
    logging.info(f"Source SQLite: {SQLITE_DB_PATH}")
    logging.info(f"Destination PostgreSQL: {POSTGRES_CONFIG['dbname']} at {POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}")
    logging.info(f"Drop existing tables: {DROP_EXISTING_TABLES}")
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
        # Get all tables from SQLite
        tables = get_sqlite_tables(sqlite_conn)
        logging.info(f"\nFound {len(tables)} tables to migrate:")
        for table in tables:
            row_count = get_row_count(sqlite_conn, table)
            logging.info(f"  - {table}: {row_count:,} rows")
        
        logging.info("\n" + "=" * 80)
        
        migrated_tables = []
        skipped_tables = []
        failed_tables = []
        total_rows_migrated = 0
        
        for idx, table_name in enumerate(tables, 1):
            logging.info(f"\n[{idx}/{len(tables)}] Processing table: '{table_name}'")
            logging.info("-" * 80)
            
            try:
                # Get table schema
                columns = get_table_info(sqlite_conn, table_name)
                
                # Determine destination table name
                dest_table_name = table_name
                
                # Check if table already exists in PostgreSQL
                if check_postgres_table_exists(pg_conn, table_name):
                    if DROP_EXISTING_TABLES:
                        logging.warning(f"  Table '{table_name}' exists. Dropping...")
                        cursor = pg_conn.cursor()
                        cursor.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE;')
                        pg_conn.commit()
                        cursor.close()
                        logging.info(f"  [OK] Dropped existing table '{table_name}'")
                    else:
                        # Check if original table has the right data
                        existing_rows = get_postgres_row_count(pg_conn, table_name)
                        sqlite_rows = get_row_count(sqlite_conn, table_name)
                        
                        if existing_rows > 0 and existing_rows == sqlite_rows:
                            logging.info(f"  [SKIP] Table '{table_name}' already migrated with {existing_rows:,} rows. Skipping.")
                            skipped_tables.append((table_name, table_name, existing_rows))
                            total_rows_migrated += existing_rows
                            continue
                        
                        dest_table_name = f"{table_name}_sqlite"
                        logging.warning(f"  Table '{table_name}' exists. Creating as '{dest_table_name}'")
                        
                        # Check if renamed table also exists
                        if check_postgres_table_exists(pg_conn, dest_table_name):
                            # Check if it has data already
                            existing_rows = get_postgres_row_count(pg_conn, dest_table_name)
                            
                            if existing_rows > 0 and existing_rows == sqlite_rows:
                                logging.info(f"  [SKIP] Table '{dest_table_name}' already migrated with {existing_rows:,} rows. Skipping.")
                                skipped_tables.append((table_name, dest_table_name, existing_rows))
                                total_rows_migrated += existing_rows
                                continue
                            elif existing_rows > 0:
                                logging.warning(f"  Table '{dest_table_name}' has {existing_rows:,} rows (expected {sqlite_rows:,}). Re-migrating...")
                            
                            cursor = pg_conn.cursor()
                            cursor.execute(f'DROP TABLE IF EXISTS "{dest_table_name}" CASCADE;')
                            pg_conn.commit()
                            cursor.close()
                            logging.info(f"  Dropped existing table '{dest_table_name}'")
                
                # Create table in PostgreSQL
                if create_postgres_table(pg_conn, dest_table_name, columns):
                    # Migrate data
                    rows_migrated = migrate_table_data(sqlite_conn, pg_conn, table_name, dest_table_name, BATCH_SIZE)
                    total_rows_migrated += rows_migrated
                    migrated_tables.append((table_name, dest_table_name, rows_migrated))
                else:
                    failed_tables.append(table_name)
                
            except Exception as e:
                logging.error(f"[ERROR] Failed to migrate table '{table_name}': {e}")
                import traceback
                traceback.print_exc()
                failed_tables.append(table_name)
                continue
        
        # Summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        logging.info("\n" + "=" * 80)
        logging.info("Migration Summary")
        logging.info("=" * 80)
        logging.info(f"Total tables in SQLite: {len(tables)}")
        logging.info(f"[OK] Successfully migrated: {len(migrated_tables)}")
        logging.info(f"[SKIP] Skipped (already migrated): {len(skipped_tables)}")
        
        if skipped_tables:
            logging.info("\nSkipped tables (already complete):")
            for source, dest, rows in skipped_tables:
                if source != dest:
                    logging.info(f"  [SKIP] {source} -> {dest} ({rows:,} rows)")
                else:
                    logging.info(f"  [SKIP] {source} ({rows:,} rows)")
        
        if migrated_tables:
            logging.info("\nNewly migrated tables:")
            for source, dest, rows in migrated_tables:
                if source != dest:
                    logging.info(f"  [OK] {source} -> {dest} ({rows:,} rows)")
                else:
                    logging.info(f"  [OK] {source} ({rows:,} rows)")
        
        if failed_tables:
            logging.info(f"\n[ERROR] Failed: {len(failed_tables)}")
            for table in failed_tables:
                logging.info(f"  [ERROR] {table}")
        
        logging.info(f"\nTotal rows migrated: {total_rows_migrated:,}")
        logging.info(f"Duration: {duration}")
        logging.info(f"Completed: {end_time}")
        logging.info("=" * 80)
        
    finally:
        sqlite_conn.close()
        pg_conn.close()
        logging.info("\n[OK] Database connections closed")

if __name__ == "__main__":
    main()
