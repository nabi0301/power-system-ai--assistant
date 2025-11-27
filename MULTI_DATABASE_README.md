# Multi-Database System for Power System Visualization

## 🎯 Overview

Your power system visualization app now supports **multiple databases simultaneously**! This enables powerful scenarios like:

- **🔄 Real-time vs Historical**: Live data + historical analysis
- **🏗️ Development vs Production**: Separate environments  
- **⚖️ Multi-source Comparison**: Compare different power systems
- **🛡️ Backup & Redundancy**: Primary + backup databases
- **🔍 A/B Testing**: Test different data scenarios

## 🚀 Quick Start

### 1. Interactive Setup
```bash
python multi_database_setup.py
```
- Configure multiple databases through guided interface
- Test connections automatically
- Set primary database for default operations

### 2. View Current Configuration
```bash
python multi_database_demo.py
```
- See connected databases
- Test multi-database queries
- Compare data across databases

### 3. Run Application
```bash
python power_viz_with_database.py
```
- Multi-database status panel shows all connections
- Switch between databases for queries
- Compare data across multiple databases

## ⚙️ Configuration

### Database Types Supported
- **SQLite**: Local file databases (`data.db`, `backup.db`, etc.)
- **PostgreSQL**: Remote/local PostgreSQL servers

### Sample Configuration (`multi_database_config.json`)
```json
{
  "primary_database": "main",
  "databases": {
    "main": {
      "type": "sqlite",
      "enabled": true,
      "description": "Primary SQLite database",
      "config": { "database": "data.db" }
    },
    "historical": {
      "type": "postgresql", 
      "enabled": true,
      "description": "Historical power system data",
      "config": {
        "host": "localhost",
        "port": 5432,
        "database": "power_system_historical",
        "user": "postgres",
        "password": "your_password"
      }
    },
    "realtime": {
      "type": "postgresql",
      "enabled": true, 
      "description": "Real-time monitoring data",
      "config": {
        "host": "realtime-server.com",
        "port": 5432,
        "database": "power_system_live",
        "user": "realtime_user",
        "password": "your_password"
      }
    }
  }
}
```

## 💻 Programming Interface

### Basic Usage
```python
from multi_database_manager import MultiDatabaseManager

# Initialize multi-database manager
with MultiDatabaseManager() as multi_db:
    # Query primary database
    result = multi_db.execute_query("SELECT * FROM bus_data LIMIT 5")
    
    # Query specific database
    historical = multi_db.execute_query(
        "SELECT * FROM bus_data WHERE timestamp < '2024-01-01'", 
        database="historical"
    )
```

### Multi-Database Comparison
```python
# Compare same query across databases
results = multi_db.compare_data(
    "SELECT AVG(voltage_pu) as avg_voltage FROM bus_data",
    databases=["main", "historical", "realtime"]
)

for db_name, df in results.items():
    print(f"{db_name}: {df['avg_voltage'].iloc[0]:.3f}")
```

### Different Queries on Different Databases
```python
# Execute different queries simultaneously
queries = {
    "main": "SELECT COUNT(*) as current_buses FROM bus_data",
    "historical": "SELECT COUNT(*) as historical_records FROM archived_data", 
    "realtime": "SELECT MAX(timestamp) as latest_update FROM live_data"
}

results = multi_db.execute_multi_query(queries)
```

### Convenience Functions
```python
from multi_database_manager import (
    execute_on_primary,      # Query primary database
    execute_on_database,     # Query specific database
    compare_across_databases, # Compare across multiple DBs
    get_multi_db_info        # Get status information
)

# Simple primary database query
data = execute_on_primary("SELECT * FROM bus_data LIMIT 10")

# Compare voltage data across all databases
voltage_comparison = compare_across_databases(
    "SELECT bus_id, voltage_pu FROM bus_data ORDER BY bus_id",
    ["main", "historical", "backup"]
)
```

## 🎛️ Web Interface Features

### Database Status Panel
- **🗃️ Database Status**: Shows all connected databases
- **🎯 Primary Database**: Highlighted with special indicator
- **🔄 Refresh**: Update connection status
- **⚖️ Database Comparison**: Select multiple databases to compare

### Active Database Selection
- **📊 Switch Database**: Choose which database to query
- **🔍 Per-Query Selection**: Different visualizations can use different databases

### Comparison Mode
- **Multi-Select**: Choose databases to compare
- **📊 Compare Button**: Trigger side-by-side comparison visualizations

## 🛠️ Advanced Scenarios

### 1. Development Workflow
```json
{
  "primary_database": "development",
  "databases": {
    "development": {
      "type": "sqlite",
      "enabled": true,
      "config": { "database": "dev_data.db" }
    },
    "production": {
      "type": "postgresql",
      "enabled": false,
      "config": { ... }
    }
  }
}
```

### 2. Real-time + Historical Analysis
```python
# Get current status from real-time DB
current_status = execute_on_database(
    "SELECT * FROM bus_data WHERE timestamp > NOW() - INTERVAL '5 minutes'",
    database="realtime"
)

# Get historical trends from archive DB  
historical_trends = execute_on_database(
    "SELECT DATE(timestamp), AVG(voltage_pu) FROM bus_data GROUP BY DATE(timestamp)",
    database="historical"
)
```

### 3. Multi-System Comparison
```python
# Compare voltage stability across different power systems
systems = ["ieee_118", "ieee_300", "custom_grid"]

stability_comparison = compare_across_databases(
    "SELECT AVG(voltage_pu), STDDEV(voltage_pu) FROM bus_data",
    systems
)
```

## 🔧 Troubleshooting

### Connection Issues
1. **Check Configuration**: Verify `multi_database_config.json`
2. **Test Individually**: Use `multi_database_setup.py` to test each database
3. **Check Dependencies**: Ensure `psycopg2` installed for PostgreSQL

### Performance Optimization
- **Connection Pooling**: Automatically handled by the manager
- **Query Caching**: Enable in configuration for frequently-used queries
- **Limit Result Sets**: Use `LIMIT` clauses for large datasets

### Fallback Behavior
- **Automatic Fallback**: If multi-DB fails, falls back to single database manager
- **Single Database Mode**: If only one database configured, operates normally
- **SQLite Fallback**: Final fallback to local SQLite if all else fails

## 📈 Benefits

### Operational
- **🔄 Zero Downtime**: Switch databases without stopping application
- **🛡️ Redundancy**: Automatic failover to backup databases
- **📊 Real-time Monitoring**: Live data + historical context

### Development
- **🏗️ Environment Separation**: Dev/test/prod database isolation
- **🔍 A/B Testing**: Compare different data scenarios easily
- **🎯 Targeted Analysis**: Route specific queries to optimized databases

### Analysis
- **⚖️ Comparative Studies**: Multi-system analysis
- **📈 Trend Analysis**: Current vs historical performance
- **🔬 Research**: Multiple datasets in single interface

## 🎉 Ready to Use!

Your multi-database system is ready! Start with:

1. **Configure**: `python multi_database_setup.py`
2. **Test**: `python multi_database_demo.py`  
3. **Visualize**: `python power_viz_with_database.py`

The web interface will show your multi-database status and provide controls for switching between databases and running comparisons! 🚀