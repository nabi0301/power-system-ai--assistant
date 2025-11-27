#!/usr/bin/env python3
"""
PostgreSQL Setup and Configuration Tool for Power System Visualization
Helps users install dependencies and configure PostgreSQL connection
"""

import subprocess
import sys
import json
import os
from typing import Dict, Any

def install_postgresql_dependencies():
    """Install required Python packages for PostgreSQL support"""
    print("📦 Installing PostgreSQL dependencies...")
    
    packages = [
        "psycopg2-binary",  # PostgreSQL adapter
        "sqlalchemy",       # ORM support (optional but useful)
    ]
    
    for package in packages:
        try:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
            return False
    
    return True

def create_postgresql_config():
    """Interactive configuration setup for PostgreSQL"""
    print("\n🔧 PostgreSQL Configuration Setup")
    print("=" * 50)
    
    config = {
        "database_type": "postgresql",
        "sqlite": {
            "database": "data.db"
        },
        "postgresql": {
            "host": "localhost",
            "port": 5432,
            "database": "power_system_db",
            "user": "postgres",
            "password": "",
            "options": {
                "sslmode": "prefer",
                "connect_timeout": 10
            }
        }
    }
    
    try:
        # Get PostgreSQL connection details
        print("Enter PostgreSQL connection details:")
        
        host = input(f"Host [{config['postgresql']['host']}]: ").strip()
        if host:
            config['postgresql']['host'] = host
            
        port = input(f"Port [{config['postgresql']['port']}]: ").strip()
        if port:
            config['postgresql']['port'] = int(port)
            
        database = input(f"Database [{config['postgresql']['database']}]: ").strip()
        if database:
            config['postgresql']['database'] = database
            
        user = input(f"Username [{config['postgresql']['user']}]: ").strip()
        if user:
            config['postgresql']['user'] = user
            
        password = input("Password: ").strip()
        if password:
            config['postgresql']['password'] = password
        
        # Ask about SSL mode
        print("\nSSL Mode options: disable, allow, prefer, require")
        sslmode = input(f"SSL Mode [{config['postgresql']['options']['sslmode']}]: ").strip()
        if sslmode and sslmode in ['disable', 'allow', 'prefer', 'require']:
            config['postgresql']['options']['sslmode'] = sslmode
        
        # Save configuration
        with open("database_config.json", "w") as f:
            json.dump(config, f, indent=4)
        
        print("✅ Configuration saved to database_config.json")
        return config
        
    except KeyboardInterrupt:
        print("\n⏹️ Configuration cancelled")
        return None
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return None

def test_postgresql_connection(config: Dict[str, Any]):
    """Test PostgreSQL connection with provided configuration"""
    print("\n🔍 Testing PostgreSQL connection...")
    
    try:
        import psycopg2
        
        pg_config = config['postgresql']
        
        # Build connection parameters
        conn_params = {
            "host": pg_config["host"],
            "port": pg_config["port"],
            "database": pg_config["database"],
            "user": pg_config["user"],
            "password": pg_config["password"]
        }
        
        # Add SSL mode
        if "options" in pg_config and "sslmode" in pg_config["options"]:
            conn_params["sslmode"] = pg_config["options"]["sslmode"]
        
        # Test connection
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print(f"✅ Connection successful!")
        print(f"📊 PostgreSQL version: {version}")
        return True
        
    except ImportError:
        print("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Common solutions:")
        print("   • Check if PostgreSQL server is running")
        print("   • Verify host, port, database name, and credentials")
        print("   • Check firewall and network connectivity")
        print("   • Ensure database exists and user has access")
        return False

def create_sample_database():
    """Create sample power system database in PostgreSQL"""
    print("\n🏗️ Would you like to create a sample power system database?")
    response = input("This will create tables and insert sample data (y/n): ").lower().strip()
    
    if response not in ['y', 'yes']:
        print("⏹️ Skipping database creation")
        return
    
    try:
        from database_manager import DatabaseManager
        
        db = DatabaseManager()
        if not db.connect():
            print("❌ Could not connect to database")
            return
        
        # Create sample tables
        sample_tables = [
            """
            CREATE TABLE IF NOT EXISTS BaseBusData (
                base_case_id INTEGER,
                BUS_NUMBER INTEGER,
                VM REAL,
                VA REAL,
                BASE_KV REAL,
                PG REAL,
                QG REAL,
                PD REAL,
                QD REAL,
                PRIMARY KEY (base_case_id, BUS_NUMBER)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS BaseBranchData (
                base_case_id INTEGER,
                branch_number INTEGER,
                From_Bus INTEGER,
                To_Bus INTEGER,
                PF REAL,
                QF REAL,
                MVA REAL,
                RATE REAL,
                VIO REAL,
                PRIMARY KEY (base_case_id, branch_number)
            )
            """
        ]
        
        cursor = db.connection.cursor()
        
        for table_sql in sample_tables:
            cursor.execute(table_sql)
            print("✅ Created table")
        
        db.connection.commit()
        cursor.close()
        db.close()
        
        print("🎉 Sample database structure created!")
        print("💡 Use the migration tool to transfer data from SQLite")
        
    except Exception as e:
        print(f"❌ Database creation failed: {e}")

def main():
    """Main setup workflow"""
    print("🔧 PostgreSQL Setup Tool for Power System Visualization")
    print("=" * 60)
    
    print("\n1️⃣ Installing PostgreSQL dependencies...")
    if not install_postgresql_dependencies():
        print("❌ Dependency installation failed")
        return
    
    print("\n2️⃣ Setting up PostgreSQL configuration...")
    config = create_postgresql_config()
    if not config:
        print("❌ Configuration failed")
        return
    
    print("\n3️⃣ Testing connection...")
    if test_postgresql_connection(config):
        print("\n4️⃣ Database setup...")
        create_sample_database()
        
        print("\n🎉 Setup completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Use postgresql_migrator.py to transfer data from SQLite")
        print("   2. Run your power system visualization app")
        print("   3. The app will automatically use PostgreSQL when configured")
        
    else:
        print("\n❌ Setup incomplete - fix connection issues and try again")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")