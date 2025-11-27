#!/usr/bin/env python3
"""
PostgreSQL Migration Script for Power System Database
Transfers data from SQLite to PostgreSQL with schema conversion
"""

import json
import sqlite3
import pandas as pd
from typing import Dict, List, Tuple
from database_manager import DatabaseManager, POSTGRESQL_AVAILABLE

class PostgreSQLMigrator:
    """
    Migrate power system data from SQLite to PostgreSQL
    """
    
    def __init__(self, sqlite_db: str = "data.db", config_file: str = "database_config.json"):
        self.sqlite_db = sqlite_db
        self.config_file = config_file
        
    def create_postgresql_schema(self) -> str:
        """
        Generate PostgreSQL schema based on SQLite structure
        Returns SQL commands to create tables
        """
        
        # Connect to SQLite to analyze structure
        sqlite_conn = sqlite3.connect(self.sqlite_db)
        
        # Get all tables
        tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
        tables_df = pd.read_sql_query(tables_query, sqlite_conn)
        
        schema_sql = []
        schema_sql.append("-- PostgreSQL Schema for Power System Database")
        schema_sql.append("-- Generated from SQLite migration")
        schema_sql.append("")
        
        for table_name in tables_df['name']:
            print(f"📊 Analyzing table: {table_name}")
            
            # Get table structure
            pragma_query = f"PRAGMA table_info({table_name})"
            structure_df = pd.read_sql_query(pragma_query, sqlite_conn)
            
            # Generate CREATE TABLE statement
            create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ("
            columns = []
            
            for _, col in structure_df.iterrows():
                col_name = col['name']
                col_type = self._convert_sqlite_to_postgresql_type(col['type'])
                nullable = "NOT NULL" if col['notnull'] else "NULL"
                
                # Handle primary key
                if col['pk']:
                    if col_type == "INTEGER":
                        col_def = f"{col_name} SERIAL PRIMARY KEY"
                    else:
                        col_def = f"{col_name} {col_type} PRIMARY KEY"
                else:
                    col_def = f"{col_name} {col_type} {nullable}"
                
                columns.append(f"    {col_def}")
            
            create_sql += "\n" + ",\n".join(columns) + "\n);"
            schema_sql.append(create_sql)
            schema_sql.append("")
        
        sqlite_conn.close()
        
        return "\n".join(schema_sql)
    
    def _convert_sqlite_to_postgresql_type(self, sqlite_type: str) -> str:
        """Convert SQLite data types to PostgreSQL equivalents"""
        sqlite_type = sqlite_type.upper()
        
        type_mapping = {
            'INTEGER': 'INTEGER',
            'REAL': 'REAL',
            'TEXT': 'TEXT',
            'BLOB': 'BYTEA',
            'NUMERIC': 'NUMERIC',
            'VARCHAR': 'VARCHAR',
            'CHAR': 'CHAR',
            'BOOLEAN': 'BOOLEAN',
            'DATE': 'DATE',
            'DATETIME': 'TIMESTAMP',
            'TIME': 'TIME'
        }
        
        # Handle size specifications like VARCHAR(255)
        for sqlite_key, pg_type in type_mapping.items():
            if sqlite_type.startswith(sqlite_key):
                if '(' in sqlite_type:
                    # Preserve size specification
                    return sqlite_type.replace(sqlite_key, pg_type)
                else:
                    return pg_type
        
        # Default fallback
        return 'TEXT'
    
    def migrate_data(self, create_schema: bool = True) -> bool:
        """
        Migrate all data from SQLite to PostgreSQL
        """
        if not POSTGRESQL_AVAILABLE:
            print("❌ PostgreSQL support not available. Install psycopg2-binary first.")
            return False
        
        try:
            # Create PostgreSQL schema if requested
            if create_schema:
                schema_sql = self.create_postgresql_schema()
                print("📝 Generated PostgreSQL schema:")
                print(schema_sql)
                
                # Save schema to file
                with open("postgresql_schema.sql", "w") as f:
                    f.write(schema_sql)
                print("💾 Schema saved to postgresql_schema.sql")
            
            # Connect to both databases
            sqlite_conn = sqlite3.connect(self.sqlite_db)
            
            # Update config to use PostgreSQL
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            config['database_type'] = 'postgresql'
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            
            # Connect to PostgreSQL
            pg_db = DatabaseManager()
            if not pg_db.connect():
                print("❌ Could not connect to PostgreSQL")
                return False
            
            # Get list of tables
            tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
            tables_df = pd.read_sql_query(tables_query, sqlite_conn)
            
            total_rows = 0
            
            for table_name in tables_df['name']:
                print(f"📊 Migrating table: {table_name}")
                
                # Read data from SQLite
                data_df = pd.read_sql_query(f"SELECT * FROM {table_name}", sqlite_conn)
                
                if len(data_df) > 0:
                    # Write data to PostgreSQL
                    # Note: This will append to existing tables
                    data_df.to_sql(table_name, pg_db.connection, if_exists='append', index=False, method='multi')
                    print(f"✅ Migrated {len(data_df)} rows from {table_name}")
                    total_rows += len(data_df)
                else:
                    print(f"⚠️ Table {table_name} is empty")
            
            sqlite_conn.close()
            pg_db.close()
            
            print(f"🎉 Migration completed! Transferred {total_rows} total rows")
            print("🔄 Database configuration updated to use PostgreSQL")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return False
    
    def verify_migration(self) -> bool:
        """
        Verify that migration was successful by comparing row counts
        """
        try:
            # Connect to SQLite
            sqlite_conn = sqlite3.connect(self.sqlite_db)
            
            # Connect to PostgreSQL
            pg_db = DatabaseManager()
            if not pg_db.connect():
                print("❌ Could not connect to PostgreSQL for verification")
                return False
            
            # Compare table counts
            sqlite_tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", sqlite_conn)
            
            verification_passed = True
            
            for table_name in sqlite_tables['name']:
                # Count rows in SQLite
                sqlite_count = pd.read_sql_query(f"SELECT COUNT(*) as count FROM {table_name}", sqlite_conn).iloc[0]['count']
                
                # Count rows in PostgreSQL
                pg_count = pg_db.execute_query(f"SELECT COUNT(*) as count FROM {table_name}").iloc[0]['count']
                
                if sqlite_count == pg_count:
                    print(f"✅ {table_name}: {sqlite_count} rows (match)")
                else:
                    print(f"❌ {table_name}: SQLite={sqlite_count}, PostgreSQL={pg_count} (mismatch)")
                    verification_passed = False
            
            sqlite_conn.close()
            pg_db.close()
            
            if verification_passed:
                print("🎉 Verification passed! All tables match between databases.")
            else:
                print("⚠️ Verification failed! Some tables have mismatched row counts.")
            
            return verification_passed
            
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False

def main():
    """Main migration workflow"""
    print("🔄 PostgreSQL Migration Tool for Power System Database")
    print("=" * 60)
    
    migrator = PostgreSQLMigrator()
    
    print("1️⃣ Creating PostgreSQL schema...")
    schema = migrator.create_postgresql_schema()
    
    print("\n2️⃣ Would you like to proceed with migration? (y/n): ", end="")
    try:
        response = input().lower().strip()
        if response in ['y', 'yes']:
            print("\n3️⃣ Migrating data...")
            if migrator.migrate_data():
                print("\n4️⃣ Verifying migration...")
                migrator.verify_migration()
            else:
                print("❌ Migration failed")
        else:
            print("⏹️ Migration cancelled")
    except KeyboardInterrupt:
        print("\n⏹️ Migration cancelled by user")

if __name__ == "__main__":
    main()