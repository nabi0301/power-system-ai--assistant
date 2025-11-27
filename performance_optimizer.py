#!/usr/bin/env python3
"""
Performance Optimization Module for Power System Visualization
Implements database connection pooling, caching, and query optimization
"""

import sqlite3
import pandas as pd
from functools import lru_cache
from contextlib import contextmanager
import threading

# ============================================================================
# 1. DATABASE CONNECTION POOL
# ============================================================================

class DatabasePool:
    """Thread-safe database connection pool to avoid reopening database"""
    
    def __init__(self, db_path='data.db', pool_size=5):
        self.db_path = db_path
        self.pool_size = pool_size
        self.connections = []
        self.lock = threading.Lock()
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Create initial pool of connections"""
        for _ in range(self.pool_size):
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            self.connections.append(conn)
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool (context manager)"""
        with self.lock:
            if self.connections:
                conn = self.connections.pop()
            else:
                # Pool exhausted, create temporary connection
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row
        
        try:
            yield conn
        finally:
            with self.lock:
                if len(self.connections) < self.pool_size:
                    self.connections.append(conn)
                else:
                    conn.close()
    
    def close_all(self):
        """Close all connections in the pool"""
        with self.lock:
            for conn in self.connections:
                conn.close()
            self.connections.clear()

# Global connection pool
db_pool = DatabasePool(pool_size=5)

# ============================================================================
# 2. STATIC DATA CACHE (Load once at startup)
# ============================================================================

class StaticDataCache:
    """Cache for rarely-changing data (base cases, metadata)"""
    
    def __init__(self):
        self._base_buses = None
        self._base_branches = None
        self._case_metadata = None
        self._initialized = False
    
    def initialize(self):
        """Load all base case data into memory once"""
        if self._initialized:
            return
        
        print("🔄 Initializing static data cache...")
        
        with db_pool.get_connection() as conn:
            # Load ALL base case data at once
            # Only select columns we actually need
            self._base_buses = pd.read_sql_query("""
                SELECT base_case_id, BUS_NUMBER, VM, VA, BASE_KV, 
                       PG, QG, PD, QD
                FROM BaseBusData
            """, conn)
            
            self._base_branches = pd.read_sql_query("""
                SELECT base_case_id, From_Bus, To_Bus, 
                       PF, QF, MVA, RATE, VIO
                FROM BaseBranchData
            """, conn)
            
            # Get case metadata
            self._case_metadata = pd.read_sql_query("""
                SELECT DISTINCT base_case_id 
                FROM BaseBusData 
                ORDER BY base_case_id
            """, conn)
        
        self._initialized = True
        print(f"✅ Cached {len(self._base_buses)} base bus records")
        print(f"✅ Cached {len(self._base_branches)} base branch records")
    
    def get_base_buses(self, case_id):
        """Get base bus data for a specific case (from cache)"""
        if not self._initialized:
            self.initialize()
        return self._base_buses[self._base_buses['base_case_id'] == case_id].copy()
    
    def get_base_branches(self, case_id):
        """Get base branch data for a specific case (from cache)"""
        if not self._initialized:
            self.initialize()
        return self._base_branches[self._base_branches['base_case_id'] == case_id].copy()
    
    def get_all_case_ids(self):
        """Get list of all available case IDs (from cache)"""
        if not self._initialized:
            self.initialize()
        return self._case_metadata['base_case_id'].tolist()

# Global static cache
static_cache = StaticDataCache()

# ============================================================================
# 3. OPTIMIZED QUERY FUNCTIONS (Only needed columns)
# ============================================================================

@lru_cache(maxsize=256)
def get_contingency_buses_optimized(case_id, contingency_id):
    """
    Get contingency bus data with only needed columns
    Cached for performance
    """
    with db_pool.get_connection() as conn:
        query = """
            SELECT bus_number as BUS_NUMBER, VM, VA, BASE_KV, 
                   PG, QG, PD, QD
            FROM ContingencyBusData
            WHERE base_case_id = ? AND contingency_case_id = ?
        """
        df = pd.read_sql_query(query, conn, params=(case_id, contingency_id))
    
    return df

@lru_cache(maxsize=256)
def get_contingency_branches_optimized(case_id, contingency_id):
    """
    Get contingency branch data with only needed columns
    Cached for performance
    """
    with db_pool.get_connection() as conn:
        query = """
            SELECT From_Bus, To_Bus, PF, QF, 
                   MVA, RATE, VIO
            FROM ContingencyBranchData
            WHERE base_case_id = ? AND contingency_case_id = ?
        """
        df = pd.read_sql_query(query, conn, params=(case_id, contingency_id))
    
    return df

# ============================================================================
# 4. DATABASE INDEXING HELPER
# ============================================================================

def create_performance_indexes():
    """
    Create indexes on frequently queried columns
    Run this once to improve query performance
    """
    indexes = [
        # Base case indexes
        "CREATE INDEX IF NOT EXISTS idx_base_bus_case ON BaseBusData(base_case_id)",
        "CREATE INDEX IF NOT EXISTS idx_base_branch_case ON BaseBranchData(base_case_id)",
        
        # Contingency case indexes (compound for WHERE with multiple columns)
        "CREATE INDEX IF NOT EXISTS idx_cont_bus_case_cont ON ContingencyBusData(base_case_id, contingency_case_id)",
        "CREATE INDEX IF NOT EXISTS idx_cont_branch_case_cont ON ContingencyBranchData(base_case_id, contingency_case_id)",
        
        # Additional useful indexes
        "CREATE INDEX IF NOT EXISTS idx_base_bus_number ON BaseBusData(BUS_NUMBER)",
        "CREATE INDEX IF NOT EXISTS idx_cont_bus_number ON ContingencyBusData(bus_number)",
    ]
    
    print("🔧 Creating database indexes for performance...")
    
    with db_pool.get_connection() as conn:
        cursor = conn.cursor()
        for idx_sql in indexes:
            try:
                cursor.execute(idx_sql)
                idx_name = idx_sql.split("idx_")[1].split(" ")[0] if "idx_" in idx_sql else "unknown"
                print(f"  ✅ Created index: idx_{idx_name}")
            except sqlite3.Error as e:
                print(f"  ⚠️ Index creation skipped: {e}")
        
        conn.commit()
    
    print("✅ Database indexing complete")

# ============================================================================
# 5. UNIFIED DATA FETCHER (Replaces multiple db opens)
# ============================================================================

def fetch_case_data_unified(case_id, contingency_id=None):
    """
    Unified function to fetch case data efficiently
    
    - Uses static cache for base cases
    - Uses optimized queries with connection pool for contingencies
    - Returns normalized column names
    """
    
    if contingency_id is None:
        # Base case - use static cache
        buses_df = static_cache.get_base_buses(case_id)
        branches_df = static_cache.get_base_branches(case_id)
        title = f"Base Case {case_id}"
    else:
        # Contingency case - use optimized cached query
        buses_df = get_contingency_buses_optimized(case_id, contingency_id)
        branches_df = get_contingency_branches_optimized(case_id, contingency_id)
        title = f"Contingency {contingency_id} (Case {case_id})"
    
    # Handle empty data
    if buses_df.empty or branches_df.empty:
        return None, None, title, 0, 100
    
    # Calculate loading statistics
    min_load = 0
    max_load = 100
    
    if 'MVA' in branches_df.columns and 'RATE' in branches_df.columns:
        # Vectorized calculation (faster than apply)
        mask = branches_df['RATE'] > 0
        branches_df.loc[mask, 'loading_percent'] = (
            branches_df.loc[mask, 'MVA'] / branches_df.loc[mask, 'RATE'] * 100
        )
        branches_df.loc[~mask, 'loading_percent'] = 0
        
        min_load = branches_df['loading_percent'].min()
        max_load = branches_df['loading_percent'].max()
    
    # Ensure reasonable values
    min_load = max(0, min_load if not pd.isna(min_load) else 0)
    max_load = min(150, max_load if not pd.isna(max_load) and max_load > 0 else 100)
    
    return buses_df, branches_df, title, min_load, max_load

# ============================================================================
# 6. CACHE STATISTICS (For monitoring)
# ============================================================================

def get_cache_stats():
    """Get statistics about cache usage"""
    stats = {
        'static_initialized': static_cache._initialized,
        'contingency_bus_cache_size': get_contingency_buses_optimized.cache_info().currsize,
        'contingency_bus_cache_hits': get_contingency_buses_optimized.cache_info().hits,
        'contingency_bus_cache_misses': get_contingency_buses_optimized.cache_info().misses,
        'contingency_branch_cache_size': get_contingency_branches_optimized.cache_info().currsize,
        'contingency_branch_cache_hits': get_contingency_branches_optimized.cache_info().hits,
        'contingency_branch_cache_misses': get_contingency_branches_optimized.cache_info().misses,
    }
    
    # Calculate hit rate
    bus_total = stats['contingency_bus_cache_hits'] + stats['contingency_bus_cache_misses']
    branch_total = stats['contingency_branch_cache_hits'] + stats['contingency_branch_cache_misses']
    
    if bus_total > 0:
        stats['bus_hit_rate'] = f"{stats['contingency_bus_cache_hits'] / bus_total * 100:.1f}%"
    else:
        stats['bus_hit_rate'] = "N/A"
    
    if branch_total > 0:
        stats['branch_hit_rate'] = f"{stats['contingency_branch_cache_hits'] / branch_total * 100:.1f}%"
    else:
        stats['branch_hit_rate'] = "N/A"
    
    return stats

def print_cache_stats():
    """Print cache statistics in a readable format"""
    stats = get_cache_stats()
    
    print("\n" + "="*60)
    print("📊 CACHE PERFORMANCE STATISTICS")
    print("="*60)
    print(f"Static Cache Initialized: {stats['static_initialized']}")
    print(f"\nContingency Bus Cache:")
    print(f"  Size: {stats['contingency_bus_cache_size']}/256")
    print(f"  Hits: {stats['contingency_bus_cache_hits']}")
    print(f"  Misses: {stats['contingency_bus_cache_misses']}")
    print(f"  Hit Rate: {stats['bus_hit_rate']}")
    print(f"\nContingency Branch Cache:")
    print(f"  Size: {stats['contingency_branch_cache_size']}/256")
    print(f"  Hits: {stats['contingency_branch_cache_hits']}")
    print(f"  Misses: {stats['contingency_branch_cache_misses']}")
    print(f"  Hit Rate: {stats['branch_hit_rate']}")
    print("="*60 + "\n")

# ============================================================================
# 7. INITIALIZATION FUNCTION
# ============================================================================

def initialize_performance_optimizations():
    """
    Initialize all performance optimizations
    Call this once at application startup
    """
    print("\n🚀 Initializing Performance Optimizations...")
    print("="*60)
    
    # Create database indexes
    create_performance_indexes()
    
    # Initialize static cache
    static_cache.initialize()
    
    print("="*60)
    print("✅ Performance optimizations initialized successfully!")
    print("💡 Use fetch_case_data_unified() instead of individual db queries")
    print("💡 Call print_cache_stats() to monitor cache performance\n")

# ============================================================================
# 8. CLEANUP FUNCTION
# ============================================================================

def cleanup_resources():
    """Cleanup resources on application shutdown"""
    print("\n🧹 Cleaning up resources...")
    db_pool.close_all()
    print("✅ Database connections closed")

# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Initialize optimizations
    initialize_performance_optimizations()
    
    # Example usage
    print("\n📝 Example: Fetching case data...")
    
    # Fetch base case (uses static cache)
    buses, branches, title, min_load, max_load = fetch_case_data_unified(0, None)
    print(f"✅ {title}: {len(buses)} buses, {len(branches)} branches")
    
    # Fetch contingency (first time - queries database)
    buses, branches, title, min_load, max_load = fetch_case_data_unified(0, 1)
    print(f"✅ {title}: {len(buses)} buses, {len(branches)} branches")
    
    # Fetch same contingency again (uses cache)
    buses, branches, title, min_load, max_load = fetch_case_data_unified(0, 1)
    print(f"✅ {title}: {len(buses)} buses, {len(branches)} branches (cached)")
    
    # Show cache statistics
    print_cache_stats()
    
    # Cleanup
    cleanup_resources()
