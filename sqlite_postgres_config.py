# sqlite_postgres_config.py
from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum

class DatabasePurpose(Enum):
    VISUALIZATION = "visualization"  # PostgreSQL - Power system data
    KNOWLEDGE = "knowledge"          # SQLite - Q&A knowledge base
    ANALYTICS = "analytics"          # PostgreSQL - Analysis results
    CACHE = "cache"                 # SQLite - Temporary/cache data

@dataclass
class DatabaseConfig:
    database: str
    db_type: str  # 'postgresql' or 'sqlite'
    purpose: DatabasePurpose
    host: str = 'localhost'
    port: int = 5432
    username: str = 'postgres'
    password: str = 'postgres'
    schema_mapping: Dict[str, str] = None
    connection_params: Dict[str, Any] = None

class SQLitePostgreSQLConfig:
    def __init__(self):
        self.databases = {
            # PostgreSQL - Main power system visualization data
            'power_viz_pg': DatabaseConfig(
                database='ieee118_db',
                db_type='postgresql',
                purpose=DatabasePurpose.VISUALIZATION,
                host='localhost',
                port=5432,
                username='postgres',
                password='postgres',
                schema_mapping={
                    'base_buses': 'BaseBusData',
                    'base_branches': 'BaseBranchData',
                    'contingency_buses': 'ContingencyBusData',
                    'contingency_branches': 'ContingencyBranchData',
                    'slr_branches': 'SLR_Branches',
                    'dlr_branches': 'DLR_Branches'
                }
            ),
            
            # PostgreSQL - Analytics and results
            'analytics_pg': DatabaseConfig(
                database='power_analytics',
                db_type='postgresql',
                purpose=DatabasePurpose.ANALYTICS,
                host='localhost',
                port=5432,
                username='postgres',
                password='postgres',
                schema_mapping={
                    'trend_analysis': 'TrendAnalysis',
                    'optimization_results': 'OptimizationResults',
                    'case_comparisons': 'CaseComparisons'
                }
            ),
            
            # SQLite - Knowledge base for Q&A
            'knowledge_sqlite': DatabaseConfig(
                database='knowledge_base.db',
                db_type='sqlite',
                purpose=DatabasePurpose.KNOWLEDGE,
                schema_mapping={
                    'power_concepts': 'power_system_concepts',
                    'faqs': 'frequently_asked_questions',
                    'definitions': 'technical_definitions',
                    'procedures': 'operational_procedures'
                }
            ),
            
            # SQLite - Local cache and temporary data
            'cache_sqlite': DatabaseConfig(
                database='cache_data.db',
                db_type='sqlite',
                purpose=DatabasePurpose.CACHE,
                schema_mapping={
                    'user_sessions': 'user_sessions',
                    'query_cache': 'cached_queries',
                    'temp_results': 'temporary_results'
                }
            ),
            
            # SQLite - Fallback (your existing data.db)
            'fallback_sqlite': DatabaseConfig(
                database='data.db',
                db_type='sqlite',
                purpose=DatabasePurpose.VISUALIZATION,
                schema_mapping={}
            )
        }

    def get_databases_by_purpose(self, purpose: DatabasePurpose) -> Dict[str, DatabaseConfig]:
        """Get all databases for a specific purpose"""
        return {name: config for name, config in self.databases.items() 
                if config.purpose == purpose}

    def get_primary_database(self, purpose: DatabasePurpose) -> Optional[DatabaseConfig]:
        """Get primary database for a purpose (first available)"""
        purpose_dbs = self.get_databases_by_purpose(purpose)
        return list(purpose_dbs.values())[0] if purpose_dbs else None