#!/usr/bin/env python3
"""
Multi-Database Manager for Power System Visualization
Supports multiple simultaneous database connections
"""

import os
import sqlite3
import json
from typing import Optional, Dict, Any, Tuple, List
import pandas as pd
from dataclasses import dataclass

# PostgreSQL support (optional)
try:
    import psycopg2
    import psycopg2.extras
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False

@dataclass
class DatabaseConnection:
    """Represents a single database connection"""
    name: str
    db_type: str
    connection: Any
    config: Dict[str, Any]
    is_primary: bool = False

class MultiDatabaseManager:
    """
    Multi-database manager supporting multiple simultaneous connections
    """
    
    def __init__(self, config_file: str = "multi_database_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self.connections: Dict[str, DatabaseConnection] = {}
        self.primary_db = None
        
    def _load_config(self) -> Dict[str, Any]:
        """Load multi-database configuration"""
        default_config = {
            "primary_database": "main",
            "databases": {
                "main": {
                    "type": "sqlite",
                    "enabled": True,
                    "config": {
                        "database": "data.db"
                    }
                },
                "historical": {
                    "type": "postgresql",
                    "enabled": False,
                    "config": {
                        "host": "localhost",
                        "port": 5432,
                        "database": "power_system_historical",
                        "user": "postgres",
                        "password": "password"
                    }
                },
                "realtime": {
                    "type": "postgresql", 
                    "enabled": False,
                    "config": {
                        "host": "realtime-server",
                        "port": 5432,
                        "database": "power_system_live",
                        "user": "postgres",
                        "password": "password"
                    }
                }
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    for key, value in loaded_config.items():
                        if key == "databases" and isinstance(value, dict):
                            for db_name, db_config in value.items():
                                if db_name in default_config["databases"]:
                                    default_config["databases"][db_name].update(db_config)
                                else:
                                    default_config["databases"][db_name] = db_config
                        else:
                            default_config[key] = value
        except Exception as e:
            print(f"⚠️ Could not load multi-db config, using defaults: {e}")
        
        return default_config
    
    def connect_all(self) -> Dict[str, bool]:
        """Connect to all enabled databases"""
        results = {}
        
        for db_name, db_config in self.config["databases"].items():
            if db_config.get("enabled", False):
                success = self.connect_database(db_name)
                results[db_name] = success
                
                # Set primary database
                if success and db_name == self.config.get("primary_database"):
                    self.set_primary_database(db_name)
        
        return results
    
    def connect_database(self, db_name: str) -> bool:
        """Connect to a specific database"""
        if db_name not in self.config["databases"]:
            print(f"❌ Database '{db_name}' not found in configuration")
            return False
        
        db_config = self.config["databases"][db_name]
        db_type = db_config["type"].lower()
        
        try:
            if db_type == "postgresql" and POSTGRESQL_AVAILABLE:
                connection = self._connect_postgresql(db_config["config"])
            elif db_type == "sqlite":
                connection = self._connect_sqlite(db_config["config"])
            else:
                print(f"❌ Unsupported database type '{db_type}' or dependencies not available")
                return False
            
            # Store connection
            is_primary = db_name == self.config.get("primary_database")
            self.connections[db_name] = DatabaseConnection(
                name=db_name,
                db_type=db_type,
                connection=connection,
                config=db_config,
                is_primary=is_primary
            )
            
            print(f"✅ Connected to {db_type} database: {db_name}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to {db_name}: {e}")
            return False
    
    def _connect_postgresql(self, config: Dict[str, Any]):
        """Connect to PostgreSQL database"""
        conn_params = {
            "host": config["host"],
            "port": config["port"],
            "database": config["database"],
            "user": config["user"],
            "password": config["password"]
        }
        
        if "options" in config:
            conn_params.update(config["options"])
        
        return psycopg2.connect(**conn_params)
    
    def _connect_sqlite(self, config: Dict[str, Any]):
        """Connect to SQLite database"""
        return sqlite3.connect(config["database"])
    
    def set_primary_database(self, db_name: str):
        """Set the primary database for default operations"""
        if db_name in self.connections:
            # Update primary flag
            for conn in self.connections.values():
                conn.is_primary = False
            
            self.connections[db_name].is_primary = True
            self.primary_db = db_name
            print(f"🎯 Set primary database: {db_name}")
        else:
            print(f"❌ Database '{db_name}' not connected")
    
    def execute_query(self, query: str, database: Optional[str] = None, params: Optional[Tuple] = None) -> pd.DataFrame:
        """
        Execute query on specified database or primary database
        """
        # Determine which database to use
        if database is None:
            database = self.primary_db
        
        if database is None or database not in self.connections:
            raise Exception(f"Database '{database}' not available")
        
        conn_info = self.connections[database]
        
        try:
            # Adapt query for database type
            adapted_query = self._adapt_query(query, conn_info.db_type)
            
            # Execute query
            if params:
                df = pd.read_sql_query(adapted_query, conn_info.connection, params=params)
            else:
                df = pd.read_sql_query(adapted_query, conn_info.connection)
            
            return df
            
        except Exception as e:
            print(f"❌ Query failed on database '{database}': {e}")
            raise
    
    def execute_multi_query(self, queries: Dict[str, str], params: Optional[Dict[str, Tuple]] = None) -> Dict[str, pd.DataFrame]:
        """
        Execute different queries on different databases simultaneously
        
        Args:
            queries: Dict of {database_name: query_string}
            params: Dict of {database_name: query_params}
        
        Returns:
            Dict of {database_name: result_dataframe}
        """
        results = {}
        
        for db_name, query in queries.items():
            if db_name in self.connections:
                try:
                    query_params = params.get(db_name) if params else None
                    results[db_name] = self.execute_query(query, db_name, query_params)
                except Exception as e:
                    print(f"❌ Multi-query failed for {db_name}: {e}")
                    results[db_name] = pd.DataFrame()  # Empty DataFrame on error
            else:
                print(f"⚠️ Database '{db_name}' not connected for multi-query")
                results[db_name] = pd.DataFrame()
        
        return results
    
    def compare_data(self, query: str, databases: List[str], params: Optional[Tuple] = None) -> Dict[str, pd.DataFrame]:
        """
        Execute same query on multiple databases for comparison
        
        Args:
            query: SQL query to execute
            databases: List of database names to query
            params: Query parameters
            
        Returns:
            Dict of {database_name: result_dataframe}
        """
        queries = {db_name: query for db_name in databases if db_name in self.connections}
        query_params = {db_name: params for db_name in queries.keys()} if params else None
        
        return self.execute_multi_query(queries, query_params)
    
    def _adapt_query(self, query: str, db_type: str) -> str:
        """Adapt query for different database types"""
        if db_type == "postgresql":
            # PostgreSQL adaptations
            adapted_query = query.replace("datetime('now')", "NOW()")
            adapted_query = adapted_query.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
            return adapted_query
        
        return query  # No adaptation needed for SQLite
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get information about all connected databases"""
        info = {
            "primary_database": self.primary_db,
            "connected_databases": len(self.connections),
            "databases": {}
        }
        
        for db_name, conn in self.connections.items():
            info["databases"][db_name] = {
                "type": conn.db_type,
                "is_primary": conn.is_primary,
                "config": {k: v for k, v in conn.config.items() if k != "password"}  # Hide password
            }
        
        return info
    
    def list_tables(self, database: Optional[str] = None) -> pd.DataFrame:
        """List tables in specified database"""
        db_name = database or self.primary_db
        if db_name not in self.connections:
            raise Exception(f"Database '{db_name}' not connected")
        
        conn_info = self.connections[db_name]
        
        if conn_info.db_type == "postgresql":
            query = """
            SELECT table_name, table_schema
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
            """
        else:
            query = "SELECT name as table_name, 'main' as table_schema FROM sqlite_master WHERE type='table' ORDER BY name"
        
        return self.execute_query(query, db_name)
    
    def close_all(self):
        """Close all database connections"""
        for db_name, conn in self.connections.items():
            try:
                conn.connection.close()
                print(f"🔒 Closed connection to {db_name}")
            except Exception as e:
                print(f"⚠️ Error closing {db_name}: {e}")
        
        self.connections.clear()
        self.primary_db = None
    
    def close_database(self, db_name: str):
        """Close specific database connection"""
        if db_name in self.connections:
            try:
                self.connections[db_name].connection.close()
                del self.connections[db_name]
                
                # Update primary if needed
                if self.primary_db == db_name:
                    self.primary_db = None
                    # Set new primary if other connections exist
                    if self.connections:
                        first_db = next(iter(self.connections))
                        self.set_primary_database(first_db)
                
                print(f"🔒 Closed connection to {db_name}")
            except Exception as e:
                print(f"⚠️ Error closing {db_name}: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        self.connect_all()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close_all()

# Global multi-database manager instance
multi_db_manager = MultiDatabaseManager()

# Convenience functions for common operations
def execute_on_primary(query: str, params: Optional[Tuple] = None) -> pd.DataFrame:
    """Execute query on primary database"""
    return multi_db_manager.execute_query(query, params=params)

def execute_on_database(query: str, database: str, params: Optional[Tuple] = None) -> pd.DataFrame:
    """Execute query on specific database"""
    return multi_db_manager.execute_query(query, database, params)

def compare_across_databases(query: str, databases: List[str], params: Optional[Tuple] = None) -> Dict[str, pd.DataFrame]:
    """Execute same query across multiple databases"""
    return multi_db_manager.compare_data(query, databases, params)

def get_multi_db_info() -> Dict[str, Any]:
    """Get multi-database status information"""
    return multi_db_manager.get_database_info()

# Example usage
if __name__ == "__main__":
    print("🔧 Testing Multi-Database Manager...")
    
    with MultiDatabaseManager() as multi_db:
        print(f"📊 Connected databases: {list(multi_db.connections.keys())}")
        print(f"🎯 Primary database: {multi_db.primary_db}")
        
        # Test listing tables from primary database
        if multi_db.primary_db:
            try:
                tables = multi_db.list_tables()
                print(f"📋 Tables in primary database: {len(tables)}")
            except Exception as e:
                print(f"⚠️ Could not list tables: {e}")
    
    print("✅ Multi-database manager test complete")