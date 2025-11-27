#!/usr/bin/env python3
"""
Database Configuration Module for Power System Visualization
Supports both SQLite and PostgreSQL databases with automatic fallback
"""

import os
import sqlite3
from typing import Optional, Dict, Any, Tuple
import pandas as pd

# PostgreSQL support (optional)
try:
    import psycopg2
    import psycopg2.extras
    POSTGRESQL_AVAILABLE = True
    print("✅ PostgreSQL support available")
except ImportError:
    POSTGRESQL_AVAILABLE = False
    print("⚠️ PostgreSQL not available - install psycopg2-binary for PostgreSQL support")

class DatabaseManager:
    """
    Unified database manager supporting both SQLite and PostgreSQL
    """
    
    def __init__(self, config_file: str = "database_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self.connection = None
        self.db_type = None
        
    def _load_config(self) -> Dict[str, Any]:
        """Load database configuration with fallback to defaults"""
        default_config = {
            "database_type": "sqlite",  # "sqlite" or "postgresql"
            "sqlite": {
                "database": "data.db"
            },
            "postgresql": {
                "host": "localhost",
                "port": 5432,
                "database": "power_system_db",
                "user": "postgres",
                "password": "your_password",
                "options": {
                    "sslmode": "prefer",
                    "connect_timeout": 10
                }
            }
        }
        
        # Try to load from file, otherwise use defaults
        try:
            import json
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    for key, value in loaded_config.items():
                        if key in default_config and isinstance(value, dict):
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
        except Exception as e:
            print(f"⚠️ Could not load config file, using defaults: {e}")
        
        return default_config
    
    def connect(self) -> bool:
        """
        Establish database connection based on configuration
        Returns True if successful, False otherwise
        """
        db_type = self.config.get("database_type", "sqlite").lower()
        
        try:
            if db_type == "postgresql" and POSTGRESQL_AVAILABLE:
                return self._connect_postgresql()
            else:
                return self._connect_sqlite()
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            if db_type == "postgresql":
                print("🔄 Falling back to SQLite...")
                return self._connect_sqlite()
            return False
    
    def _connect_postgresql(self) -> bool:
        """Connect to PostgreSQL database"""
        try:
            pg_config = self.config["postgresql"]
            
            # Build connection string
            conn_params = {
                "host": pg_config["host"],
                "port": pg_config["port"],
                "database": pg_config["database"],
                "user": pg_config["user"],
                "password": pg_config["password"]
            }
            
            # Add optional parameters
            if "options" in pg_config:
                conn_params.update(pg_config["options"])
            
            self.connection = psycopg2.connect(**conn_params)
            self.db_type = "postgresql"
            print(f"✅ Connected to PostgreSQL: {pg_config['host']}:{pg_config['port']}/{pg_config['database']}")
            return True
            
        except Exception as e:
            print(f"❌ PostgreSQL connection failed: {e}")
            raise
    
    def _connect_sqlite(self) -> bool:
        """Connect to SQLite database"""
        try:
            sqlite_config = self.config["sqlite"]
            db_path = sqlite_config["database"]
            
            self.connection = sqlite3.connect(db_path)
            self.db_type = "sqlite"
            print(f"✅ Connected to SQLite: {db_path}")
            return True
            
        except Exception as e:
            print(f"❌ SQLite connection failed: {e}")
            raise
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> pd.DataFrame:
        """
        Execute SQL query and return results as pandas DataFrame
        Handles differences between SQLite and PostgreSQL
        """
        if not self.connection:
            if not self.connect():
                raise Exception("Could not establish database connection")
        
        try:
            # Adapt query for different database types if needed
            adapted_query = self._adapt_query(query)
            
            # Execute query
            if params:
                df = pd.read_sql_query(adapted_query, self.connection, params=params)
            else:
                df = pd.read_sql_query(adapted_query, self.connection)
            
            return df
            
        except Exception as e:
            print(f"❌ Query execution failed: {e}")
            print(f"📝 Query: {query}")
            raise
    
    def _adapt_query(self, query: str) -> str:
        """
        Adapt SQL query for different database types
        Handle syntax differences between SQLite and PostgreSQL
        """
        if self.db_type == "postgresql":
            # PostgreSQL adaptations
            adapted_query = query
            
            # Replace SQLite-specific syntax
            if "LIMIT" in query.upper() and "OFFSET" in query.upper():
                # PostgreSQL uses same LIMIT/OFFSET syntax as SQLite, no change needed
                pass
            
            # Handle date/time functions
            adapted_query = adapted_query.replace("datetime('now')", "NOW()")
            
            # Handle auto-increment differences (if creating tables)
            adapted_query = adapted_query.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
            
            return adapted_query
        
        return query  # No adaptation needed for SQLite
    
    def get_table_info(self, table_name: str) -> pd.DataFrame:
        """Get information about table structure"""
        if self.db_type == "postgresql":
            query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = %s
            ORDER BY ordinal_position
            """
            return self.execute_query(query, (table_name,))
        else:
            query = f"PRAGMA table_info({table_name})"
            return self.execute_query(query)
    
    def list_tables(self) -> pd.DataFrame:
        """List all tables in the database"""
        if self.db_type == "postgresql":
            query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
            """
        else:
            query = "SELECT name as table_name FROM sqlite_master WHERE type='table' ORDER BY name"
        
        return self.execute_query(query)
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            print(f"🔒 Closed {self.db_type} connection")
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

# Global database manager instance
db_manager = DatabaseManager()

def get_database_connection():
    """
    Get database connection - unified interface for the app
    This replaces all sqlite3.connect('data.db') calls
    """
    if not db_manager.connection:
        db_manager.connect()
    return db_manager.connection

def execute_power_system_query(query: str, params: Optional[Tuple] = None) -> pd.DataFrame:
    """
    Execute power system database query
    This replaces pd.read_sql_query(query, sqlite3.connect('data.db'))
    """
    return db_manager.execute_query(query, params)

def get_database_info() -> Dict[str, Any]:
    """Get current database configuration and status"""
    return {
        "type": db_manager.db_type,
        "connected": db_manager.connection is not None,
        "config": db_manager.config,
        "postgresql_available": POSTGRESQL_AVAILABLE
    }

# Example usage and testing
if __name__ == "__main__":
    print("🔧 Testing Database Manager...")
    
    # Test connection
    with DatabaseManager() as db:
        print(f"📊 Connected to {db.db_type} database")
        
        # List tables
        try:
            tables = db.list_tables()
            print(f"📋 Found {len(tables)} tables:")
            for table in tables['table_name']:
                print(f"   • {table}")
        except Exception as e:
            print(f"⚠️ Could not list tables: {e}")
    
    print("✅ Database manager test complete")