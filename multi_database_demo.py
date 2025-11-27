#!/usr/bin/env python3
"""
Multi-Database Demo for Power System Visualization
Demonstrates using multiple databases simultaneously
"""

import os
import sys
import pandas as pd
from datetime import datetime

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def demo_multi_database():
    """Demonstrate multi-database functionality"""
    print("🚀 Multi-Database Demo for Power System Visualization")
    print("=" * 60)
    
    try:
        from multi_database_manager import MultiDatabaseManager
        
        # Create demo with different database scenarios
        print("\n1️⃣ Loading Multi-Database Configuration...")
        
        with MultiDatabaseManager() as multi_db:
            print(f"   📊 Connected databases: {list(multi_db.connections.keys())}")
            print(f"   🎯 Primary database: {multi_db.primary_db}")
            
            # Demo 1: Query primary database
            print("\n2️⃣ Querying Primary Database...")
            try:
                if multi_db.primary_db:
                    # Get basic statistics
                    result = multi_db.execute_query("SELECT COUNT(*) as bus_count FROM bus_data LIMIT 5")
                    print(f"   📈 Primary database bus count: {result.iloc[0]['bus_count'] if not result.empty else 'No data'}")
                else:
                    print("   ⚠️ No primary database available")
            except Exception as e:
                print(f"   ⚠️ Primary database query failed: {e}")
            
            # Demo 2: Multi-database comparison (if multiple databases available)
            if len(multi_db.connections) > 1:
                print("\n3️⃣ Multi-Database Comparison...")
                
                # Compare bus data across databases
                comparison_query = "SELECT bus_id, voltage_pu FROM bus_data LIMIT 10"
                db_names = list(multi_db.connections.keys())[:2]  # Use first 2 databases
                
                try:
                    results = multi_db.compare_data(comparison_query, db_names)
                    
                    for db_name, df in results.items():
                        if not df.empty:
                            print(f"   📊 {db_name}: {len(df)} buses, avg voltage: {df['voltage_pu'].mean():.3f}")
                        else:
                            print(f"   📊 {db_name}: No data")
                            
                except Exception as e:
                    print(f"   ⚠️ Multi-database comparison failed: {e}")
            else:
                print("\n3️⃣ Multi-Database Comparison...")
                print("   📝 Only one database connected - comparison not possible")
            
            # Demo 3: Different queries on different databases
            if len(multi_db.connections) > 1:
                print("\n4️⃣ Different Queries on Different Databases...")
                
                try:
                    # Create different queries for different databases
                    queries = {}
                    db_names = list(multi_db.connections.keys())
                    
                    if len(db_names) >= 2:
                        queries[db_names[0]] = "SELECT COUNT(*) as total_buses FROM bus_data"
                        queries[db_names[1]] = "SELECT COUNT(*) as total_branches FROM branch_data"
                    
                    if queries:
                        results = multi_db.execute_multi_query(queries)
                        
                        for db_name, df in results.items():
                            if not df.empty:
                                col_name = df.columns[0]
                                value = df.iloc[0][col_name]
                                print(f"   📊 {db_name}: {col_name} = {value}")
                            else:
                                print(f"   📊 {db_name}: No results")
                                
                except Exception as e:
                    print(f"   ⚠️ Multi-query execution failed: {e}")
            
            # Demo 4: Database information
            print("\n5️⃣ Database Information...")
            try:
                db_info = multi_db.get_database_info()
                print(f"   🎯 Primary: {db_info.get('primary_database', 'None')}")
                print(f"   🔗 Connected: {db_info.get('connected_databases', 0)}")
                
                for db_name, info in db_info.get('databases', {}).items():
                    db_type = info.get('type', 'unknown')
                    is_primary = info.get('is_primary', False)
                    primary_tag = " (PRIMARY)" if is_primary else ""
                    print(f"   • {db_name}: {db_type}{primary_tag}")
                    
            except Exception as e:
                print(f"   ⚠️ Database info retrieval failed: {e}")
            
            # Demo 5: List tables from each database
            print("\n6️⃣ Tables in Each Database...")
            for db_name in multi_db.connections.keys():
                try:
                    tables = multi_db.list_tables(db_name)
                    if not tables.empty:
                        table_names = tables['table_name'].tolist()
                        print(f"   📋 {db_name}: {len(table_names)} tables - {', '.join(table_names[:3])}{'...' if len(table_names) > 3 else ''}")
                    else:
                        print(f"   📋 {db_name}: No tables found")
                except Exception as e:
                    print(f"   📋 {db_name}: Could not list tables - {e}")
    
    except ImportError:
        print("❌ Multi-database manager not available")
        print("   💡 Run 'python multi_database_setup.py' to configure databases")
    except Exception as e:
        print(f"❌ Demo failed: {e}")

def demo_convenience_functions():
    """Demonstrate convenience functions"""
    print("\n" + "=" * 60)
    print("🛠️ Convenience Functions Demo")
    print("=" * 60)
    
    try:
        from multi_database_manager import (
            execute_on_primary,
            execute_on_database, 
            compare_across_databases,
            get_multi_db_info
        )
        
        # Demo convenience function usage
        print("\n1️⃣ Execute on Primary Database...")
        try:
            result = execute_on_primary("SELECT COUNT(*) as count FROM bus_data LIMIT 1")
            if not result.empty:
                print(f"   ✅ Primary database query successful: {result.iloc[0]['count']} buses")
            else:
                print("   📝 Primary database query returned no results")
        except Exception as e:
            print(f"   ⚠️ Primary database query failed: {e}")
        
        print("\n2️⃣ Multi-Database Info...")
        try:
            info = get_multi_db_info()
            print(f"   📊 Status: {info.get('connected_databases', 0)} databases connected")
            primary = info.get('primary_database')
            if primary:
                print(f"   🎯 Primary: {primary}")
        except Exception as e:
            print(f"   ⚠️ Info retrieval failed: {e}")
        
    except ImportError:
        print("❌ Multi-database convenience functions not available")

def create_sample_databases():
    """Create sample databases for testing"""
    print("\n" + "=" * 60)
    print("🏗️ Creating Sample Databases for Testing")
    print("=" * 60)
    
    # Create sample development database
    import sqlite3
    
    dev_db_path = "dev_data.db"
    backup_db_path = "backup_data.db"
    
    try:
        # Create development database with sample data
        print("\n1️⃣ Creating development database...")
        conn = sqlite3.connect(dev_db_path)
        
        # Create sample bus data
        conn.execute("""
        CREATE TABLE IF NOT EXISTS bus_data (
            bus_id INTEGER PRIMARY KEY,
            voltage_pu REAL,
            angle_deg REAL,
            base_kv REAL
        )
        """)
        
        # Insert sample data
        sample_buses = [
            (1, 1.06, 0.0, 138.0),
            (2, 1.05, -1.2, 138.0),
            (3, 1.04, -2.1, 138.0),
            (4, 1.03, -3.5, 138.0),
            (5, 1.02, -4.2, 138.0)
        ]
        
        conn.executemany("INSERT OR REPLACE INTO bus_data VALUES (?, ?, ?, ?)", sample_buses)
        
        # Create sample branch data
        conn.execute("""
        CREATE TABLE IF NOT EXISTS branch_data (
            branch_id INTEGER PRIMARY KEY,
            from_bus INTEGER,
            to_bus INTEGER,
            resistance REAL,
            reactance REAL
        )
        """)
        
        sample_branches = [
            (1, 1, 2, 0.01, 0.05),
            (2, 2, 3, 0.02, 0.06),
            (3, 3, 4, 0.015, 0.055),
            (4, 4, 5, 0.018, 0.062)
        ]
        
        conn.executemany("INSERT OR REPLACE INTO branch_data VALUES (?, ?, ?, ?, ?)", sample_branches)
        conn.commit()
        conn.close()
        
        print(f"   ✅ Created development database: {dev_db_path}")
        
        # Create backup database (copy of dev)
        print("\n2️⃣ Creating backup database...")
        import shutil
        shutil.copy2(dev_db_path, backup_db_path)
        print(f"   ✅ Created backup database: {backup_db_path}")
        
        print("\n📝 Sample databases created. Update multi_database_config.json to enable them:")
        print(f'   • Set "development" database enabled: true')
        print(f'   • Set "backup" database enabled: true')
        
    except Exception as e:
        print(f"❌ Failed to create sample databases: {e}")

if __name__ == "__main__":
    try:
        demo_multi_database()
        demo_convenience_functions()
        
        print("\n" + "=" * 60)
        if input("\n🔧 Create sample databases for testing? (y/N): ").lower().startswith('y'):
            create_sample_databases()
        
        print("\n✅ Multi-Database Demo Complete!")
        print("\n📝 Next Steps:")
        print("   1. Run 'python multi_database_setup.py' to configure databases")
        print("   2. Run 'python power_viz_with_database.py' to see multi-DB interface")
        print("   3. Edit 'multi_database_config.json' to customize database settings")
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo cancelled by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()