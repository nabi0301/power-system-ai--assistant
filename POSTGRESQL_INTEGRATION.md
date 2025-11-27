# PostgreSQL Integration for Power System Visualization

This guide explains how to integrate PostgreSQL database with your power system visualization application.

## 🎯 Overview

The application now supports both SQLite and PostgreSQL databases with automatic fallback. You can:
- Continue using SQLite (default, no changes needed)
- Migrate to PostgreSQL for better performance and scalability
- Switch between databases easily using configuration

## 🔧 Setup Process

### 1. Install PostgreSQL Dependencies

```bash
# Install PostgreSQL Python adapter
pip install psycopg2-binary

# Optional: Install SQLAlchemy for advanced ORM features
pip install sqlalchemy
```

### 2. Automated Setup (Recommended)

Run the automated setup script:

```bash
python postgresql_setup.py
```

This will:
- Install required Python packages
- Guide you through PostgreSQL configuration
- Test the connection
- Create sample database structure

### 3. Manual Configuration

Create or edit `database_config.json`:

```json
{
    "database_type": "postgresql",
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
```

## 📊 Database Migration

### Migrate from SQLite to PostgreSQL

```bash
# Run the migration script
python postgresql_migrator.py
```

The migration process:
1. Analyzes your SQLite database structure
2. Generates PostgreSQL schema
3. Transfers all data
4. Verifies migration integrity
5. Updates configuration to use PostgreSQL

### Manual Migration Steps

1. **Create PostgreSQL Database:**
```sql
CREATE DATABASE power_system_db;
CREATE USER power_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE power_system_db TO power_user;
```

2. **Generate Schema:**
```bash
python postgresql_migrator.py
# Review generated postgresql_schema.sql
```

3. **Apply Schema:**
```bash
psql -U postgres -d power_system_db -f postgresql_schema.sql
```

4. **Transfer Data:**
```bash
python postgresql_migrator.py
```

## 🚀 Application Usage

### Automatic Database Detection

The application automatically detects your database configuration:

```python
# No code changes needed - the app handles both databases
from power_viz_with_database import app

# The app will use PostgreSQL if configured, otherwise SQLite
```

### Database Status

Check current database status:

```python
from database_manager import get_database_info

status = get_database_info()
print(f"Database type: {status['type']}")
print(f"Connected: {status['connected']}")
```

## 🔄 Switching Between Databases

### Switch to PostgreSQL
```json
{
    "database_type": "postgresql"
}
```

### Switch to SQLite
```json
{
    "database_type": "sqlite"
}
```

### Automatic Fallback
If PostgreSQL connection fails, the app automatically falls back to SQLite.

## 📈 Performance Benefits

### PostgreSQL Advantages:
- **Better Performance:** Optimized for larger datasets
- **Concurrent Access:** Multiple users can access simultaneously
- **Advanced Features:** Window functions, CTEs, advanced indexing
- **Scalability:** Handles growing datasets efficiently
- **Data Integrity:** ACID compliance and robust transaction support

### When to Use PostgreSQL:
- Large power system datasets (>1M records)
- Multiple concurrent users
- Production environments
- Advanced analytics requirements
- Integration with other PostgreSQL systems

## 🔍 Troubleshooting

### Common Issues and Solutions

#### 1. Connection Refused
```
Error: connection to server at "localhost", port 5432 failed
```
**Solution:** Ensure PostgreSQL server is running
```bash
# Windows
net start postgresql

# Linux/Mac
sudo systemctl start postgresql
```

#### 2. Authentication Failed
```
Error: FATAL: password authentication failed
```
**Solutions:**
- Verify username and password in config
- Check PostgreSQL pg_hba.conf settings
- Ensure user has database access privileges

#### 3. Database Does Not Exist
```
Error: FATAL: database "power_system_db" does not exist
```
**Solution:** Create the database
```sql
CREATE DATABASE power_system_db;
```

#### 4. SSL/TLS Issues
```
Error: SSL connection has been closed unexpectedly
```
**Solution:** Adjust SSL mode in config
```json
{
    "postgresql": {
        "options": {
            "sslmode": "disable"
        }
    }
}
```

### Performance Tuning

#### PostgreSQL Configuration
```sql
-- Increase shared buffers for better performance
ALTER SYSTEM SET shared_buffers = '256MB';

-- Optimize for power system queries
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';

-- Restart PostgreSQL to apply changes
```

#### Indexing for Power System Data
```sql
-- Index on bus numbers for faster lookups
CREATE INDEX idx_bus_number ON BaseBusData(BUS_NUMBER);

-- Index on branch connections
CREATE INDEX idx_branch_from_to ON BaseBranchData(From_Bus, To_Bus);

-- Index on case IDs for fast filtering
CREATE INDEX idx_base_case ON BaseBusData(base_case_id);
CREATE INDEX idx_contingency_case ON BaseBranchData(base_case_id, contingency_case_id);
```

## 🔧 Database Schema

### Core Tables

#### BaseBusData
```sql
CREATE TABLE BaseBusData (
    base_case_id INTEGER,
    BUS_NUMBER INTEGER,
    VM REAL,                -- Voltage magnitude (p.u.)
    VA REAL,                -- Voltage angle (degrees)
    BASE_KV REAL,           -- Base voltage (kV)
    PG REAL,                -- Generated power (MW)
    QG REAL,                -- Generated reactive power (MVAR)
    PD REAL,                -- Load demand (MW)
    QD REAL,                -- Reactive load demand (MVAR)
    PRIMARY KEY (base_case_id, BUS_NUMBER)
);
```

#### BaseBranchData
```sql
CREATE TABLE BaseBranchData (
    base_case_id INTEGER,
    branch_number INTEGER,
    From_Bus INTEGER,       -- From bus number
    To_Bus INTEGER,         -- To bus number
    PF REAL,                -- Power flow (MW)
    QF REAL,                -- Reactive power flow (MVAR)
    MVA REAL,               -- Apparent power (MVA)
    RATE REAL,              -- Thermal rating (MVA)
    VIO REAL,               -- Violation indicator
    PRIMARY KEY (base_case_id, branch_number)
);
```

## 🎯 Best Practices

### 1. Development vs Production
- **Development:** Use SQLite for simplicity
- **Production:** Use PostgreSQL for performance

### 2. Data Backup
```bash
# PostgreSQL backup
pg_dump -U postgres power_system_db > backup.sql

# SQLite backup
cp data.db backup_data.db
```

### 3. Connection Pooling
For high-load applications, consider connection pooling:
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    'postgresql://user:password@localhost/power_system_db',
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20
)
```

### 4. Monitoring
Monitor database performance:
```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';

-- Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables WHERE schemaname = 'public';
```

## 📚 Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)
- [Power System Database Design](https://ieee-dataport.org/)

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify PostgreSQL server status
3. Test connection with psql command-line tool
4. Check application logs for detailed error messages
5. Use SQLite fallback for immediate operation