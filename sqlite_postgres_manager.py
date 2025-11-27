# sqlite_postgres_manager.py
import sqlite3
import pandas as pd
from typing import Dict, List, Optional, Any, Union
from sqlite_postgres_config import SQLitePostgreSQLConfig, DatabasePurpose
import logging
import json
import hashlib
from datetime import datetime

# Optional PostgreSQL support
try:
    import psycopg2
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print("⚠️ psycopg2 not available - PostgreSQL support disabled")

class SQLitePostgreSQLManager:
    def __init__(self, config: SQLitePostgreSQLConfig):
        self.config = config
        self.connections = {}
        self.purpose_mapping = {}
        self.logger = logging.getLogger(__name__)
        self._initialize_connections()
        self._map_purposes()

    def _initialize_connections(self):
        """Initialize connections to all configured databases"""
        for db_name, db_config in self.config.databases.items():
            try:
                if db_config.db_type == 'postgresql' and POSTGRES_AVAILABLE:
                    conn = psycopg2.connect(
                        host=db_config.host,
                        port=db_config.port,
                        database=db_config.database,
                        user=db_config.username,
                        password=db_config.password
                    )
                    # Test connection
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                    
                elif db_config.db_type == 'sqlite':
                    conn = sqlite3.connect(db_config.database, check_same_thread=False)
                    # Test connection
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                    
                elif db_config.db_type == 'postgresql' and not POSTGRES_AVAILABLE:
                    raise ImportError("PostgreSQL support not available (psycopg2 not installed)")
                    
                else:
                    raise ValueError(f"Unsupported database type: {db_config.db_type}")
                
                self.connections[db_name] = {
                    'connection': conn,
                    'config': db_config,
                    'status': 'connected'
                }
                print(f"✅ Connected to {db_name} ({db_config.db_type}) for {db_config.purpose.value}")
                
            except Exception as e:
                self.connections[db_name] = {
                    'connection': None,
                    'config': db_config,
                    'status': f'failed: {e}'
                }
                print(f"❌ Failed to connect to {db_name}: {e}")

    def _map_purposes(self):
        """Create purpose-based database mapping"""
        for db_name, db_info in self.connections.items():
            if db_info['status'] == 'connected':
                purpose = db_info['config'].purpose
                if purpose not in self.purpose_mapping:
                    self.purpose_mapping[purpose] = []
                self.purpose_mapping[purpose].append(db_name)

    def get_visualization_data(self, query: str, params: dict = None, case_id: int = None) -> pd.DataFrame:
        """Get data for visualizations from PostgreSQL (preferred) or SQLite fallback"""
        viz_databases = self.purpose_mapping.get(DatabasePurpose.VISUALIZATION, [])
        
        # Try PostgreSQL first, then SQLite
        preferred_order = ['power_viz_pg', 'fallback_sqlite']
        
        for db_name in preferred_order:
            if db_name in viz_databases:
                db_info = self.connections[db_name]
                if db_info['status'] == 'connected':
                    try:
                        return self._execute_sql_query(db_name, query, params)
                    except Exception as e:
                        print(f"⚠️ Visualization query failed on {db_name}: {e}")
                        continue
        
        raise Exception("No available visualization databases")

    def get_knowledge_data(self, search_term: str, category: str = None) -> List[Dict]:
        """Get data from SQLite knowledge base for Q&A"""
        knowledge_databases = self.purpose_mapping.get(DatabasePurpose.KNOWLEDGE, [])
        
        for db_name in knowledge_databases:
            db_info = self.connections[db_name]
            if db_info['status'] == 'connected':
                try:
                    return self._search_knowledge_base(db_name, search_term, category)
                except Exception as e:
                    print(f"⚠️ Knowledge query failed on {db_name}: {e}")
                    continue
        
        return []

    def store_analytics_result(self, result_type: str, data: Dict, case_id: int = None) -> bool:
        """Store analytics results in PostgreSQL analytics database"""
        analytics_databases = self.purpose_mapping.get(DatabasePurpose.ANALYTICS, [])
        
        for db_name in analytics_databases:
            db_info = self.connections[db_name]
            if db_info['status'] == 'connected':
                try:
                    return self._store_analytics_data(db_name, result_type, data, case_id)
                except Exception as e:
                    print(f"⚠️ Analytics storage failed on {db_name}: {e}")
                    continue
        
        return False

    def cache_query_result(self, query_hash: str, result_data: Any) -> bool:
        """Cache query results in SQLite for faster subsequent access"""
        cache_databases = self.purpose_mapping.get(DatabasePurpose.CACHE, [])
        
        for db_name in cache_databases:
            db_info = self.connections[db_name]
            if db_info['status'] == 'connected':
                try:
                    return self._cache_data(db_name, query_hash, result_data)
                except Exception as e:
                    print(f"⚠️ Cache storage failed on {db_name}: {e}")
                    continue
        
        return False

    def get_cached_result(self, query_hash: str) -> Optional[Any]:
        """Get cached query results from SQLite"""
        cache_databases = self.purpose_mapping.get(DatabasePurpose.CACHE, [])
        
        for db_name in cache_databases:
            db_info = self.connections[db_name]
            if db_info['status'] == 'connected':
                try:
                    return self._get_cached_data(db_name, query_hash)
                except Exception as e:
                    print(f"⚠️ Cache retrieval failed on {db_name}: {e}")
                    continue
        
        return None

    def generate_query_hash(self, query: str, params: dict = None) -> str:
        """Generate a hash for caching query results"""
        query_string = query + str(params or {})
        return hashlib.md5(query_string.encode()).hexdigest()

    def _execute_sql_query(self, db_name: str, query: str, params: dict = None) -> pd.DataFrame:
        """Execute SQL query on PostgreSQL or SQLite"""
        db_info = self.connections[db_name]
        config = db_info['config']
        conn = db_info['connection']
        
        # Apply schema mapping if available
        if config.schema_mapping:
            for logical_name, physical_name in config.schema_mapping.items():
                query = query.replace(logical_name, physical_name)
        
        return pd.read_sql_query(query, conn, params=params)

    def _search_knowledge_base(self, db_name: str, search_term: str, category: str = None) -> List[Dict]:
        """Search SQLite knowledge base using FTS or LIKE queries"""
        db_info = self.connections[db_name]
        conn = db_info['connection']
        cursor = conn.cursor()
        
        # Build search query
        if category:
            query = """
                SELECT * FROM power_system_concepts 
                WHERE (title LIKE ? OR content LIKE ?) AND category = ?
                ORDER BY 
                    CASE 
                        WHEN title LIKE ? THEN 1 
                        WHEN content LIKE ? THEN 2 
                        ELSE 3 
                    END
                LIMIT 10
            """
            search_pattern = f"%{search_term}%"
            params = (search_pattern, search_pattern, category, search_pattern, search_pattern)
        else:
            query = """
                SELECT * FROM power_system_concepts 
                WHERE title LIKE ? OR content LIKE ? OR keywords LIKE ?
                ORDER BY 
                    CASE 
                        WHEN title LIKE ? THEN 1 
                        WHEN content LIKE ? THEN 2 
                        ELSE 3 
                    END
                LIMIT 10
            """
            search_pattern = f"%{search_term}%"
            params = (search_pattern, search_pattern, search_pattern, search_pattern, search_pattern)
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        return results

    def _store_analytics_data(self, db_name: str, result_type: str, data: Dict, case_id: int = None) -> bool:
        """Store analytics results in PostgreSQL"""
        db_info = self.connections[db_name]
        conn = db_info['connection']
        cursor = conn.cursor()
        
        try:
            # Create table if it doesn't exist
            if db_info['config'].db_type == 'postgresql':
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS analytics_results (
                        id SERIAL PRIMARY KEY,
                        result_type VARCHAR(100),
                        case_id INTEGER,
                        data_json TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                # Insert the analytics result
                cursor.execute("""
                    INSERT INTO analytics_results (result_type, case_id, data_json)
                    VALUES (%s, %s, %s)
                """, (result_type, case_id, json.dumps(data)))
            else:
                # SQLite fallback
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS analytics_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        result_type TEXT,
                        case_id INTEGER,
                        data_json TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("""
                    INSERT INTO analytics_results (result_type, case_id, data_json)
                    VALUES (?, ?, ?)
                """, (result_type, case_id, json.dumps(data)))
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            raise e

    def _cache_data(self, db_name: str, query_hash: str, result_data: Any) -> bool:
        """Cache data in SQLite"""
        db_info = self.connections[db_name]
        conn = db_info['connection']
        cursor = conn.cursor()
        
        try:
            # Create cache table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS query_cache (
                    query_hash TEXT PRIMARY KEY,
                    result_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 1
                )
            """)
            
            # Insert or update cache entry
            cursor.execute("""
                INSERT OR REPLACE INTO query_cache (query_hash, result_data, created_at)
                VALUES (?, ?, ?)
            """, (query_hash, json.dumps(result_data, default=str), datetime.now()))
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            raise e

    def _get_cached_data(self, db_name: str, query_hash: str) -> Optional[Any]:
        """Get cached data from SQLite"""
        db_info = self.connections[db_name]
        conn = db_info['connection']
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT result_data FROM query_cache 
            WHERE query_hash = ? AND 
                  datetime(created_at) > datetime('now', '-1 hour')
        """, (query_hash,))
        
        result = cursor.fetchone()
        if result:
            # Update access count
            cursor.execute("""
                UPDATE query_cache 
                SET access_count = access_count + 1 
                WHERE query_hash = ?
            """, (query_hash,))
            conn.commit()
            
            return json.loads(result[0])
        
        return None

    def get_database_status(self) -> Dict[str, Any]:
        """Get status of all configured databases"""
        status = {
            'total_databases': len(self.connections),
            'connected_count': sum(1 for db in self.connections.values() if db['status'] == 'connected'),
            'databases': {},
            'purposes': {}
        }
        
        for db_name, db_info in self.connections.items():
            config = db_info['config']
            status['databases'][db_name] = {
                'type': config.db_type,
                'purpose': config.purpose.value,
                'status': db_info['status'],
                'database': config.database
            }
        
        for purpose, db_list in self.purpose_mapping.items():
            status['purposes'][purpose.value] = db_list
        
        return status

    def close_all_connections(self):
        """Close all database connections"""
        for db_name, db_info in self.connections.items():
            if db_info['connection'] and db_info['status'] == 'connected':
                try:
                    db_info['connection'].close()
                    print(f"✅ Closed connection to {db_name}")
                except Exception as e:
                    print(f"⚠️ Error closing {db_name}: {e}")