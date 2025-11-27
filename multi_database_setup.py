#!/usr/bin/env python3
"""
Multi-Database Setup Utility for Power System Visualization
Interactive configuration for multiple database connections
"""

import json
import os
import sys
from typing import Dict, Any, List, Optional

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def get_user_input(prompt: str, default: Optional[str] = None, required: bool = True) -> str:
    """Get user input with optional default value"""
    if default:
        prompt += f" [{default}]"
    prompt += ": "
    
    while True:
        value = input(prompt).strip()
        if value:
            return value
        elif default:
            return default
        elif not required:
            return ""
        else:
            print("❌ This field is required. Please enter a value.")

def get_yes_no(prompt: str, default: bool = False) -> bool:
    """Get yes/no input from user"""
    default_str = "Y/n" if default else "y/N"
    response = input(f"{prompt} [{default_str}]: ").strip().lower()
    
    if not response:
        return default
    return response in ['y', 'yes', 'true', '1']

def configure_sqlite_database() -> Dict[str, Any]:
    """Configure SQLite database settings"""
    print("\n📁 SQLite Database Configuration")
    
    database_file = get_user_input("Database file path", "data.db")
    
    config = {
        "type": "sqlite",
        "enabled": True,
        "config": {
            "database": database_file
        }
    }
    
    return config

def configure_postgresql_database() -> Dict[str, Any]:
    """Configure PostgreSQL database settings"""
    print("\n🐘 PostgreSQL Database Configuration")
    
    host = get_user_input("Host", "localhost")
    port = int(get_user_input("Port", "5432"))
    database = get_user_input("Database name")
    user = get_user_input("Username", "postgres")
    password = get_user_input("Password (will be stored in config file)")
    
    # Optional advanced settings
    print("\n🔧 Advanced PostgreSQL Settings (optional)")
    use_ssl = get_yes_no("Use SSL connection?", False)
    
    config = {
        "type": "postgresql",
        "enabled": True,
        "config": {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password
        }
    }
    
    if use_ssl:
        config["config"]["sslmode"] = "require"
    
    return config

def test_database_connection(db_name: str, db_config: Dict[str, Any]) -> bool:
    """Test database connection"""
    print(f"\n🔍 Testing connection to {db_name}...")
    
    try:
        from multi_database_manager import MultiDatabaseManager
        
        # Create temporary config for testing
        test_config = {
            "primary_database": db_name,
            "databases": {
                db_name: db_config
            }
        }
        
        # Save temporary config
        with open("temp_test_config.json", "w") as f:
            json.dump(test_config, f, indent=2)
        
        # Test connection
        manager = MultiDatabaseManager("temp_test_config.json")
        success = manager.connect_database(db_name)
        
        if success:
            print(f"✅ Successfully connected to {db_name}")
            # Test a simple query
            try:
                if db_config["type"] == "sqlite":
                    result = manager.execute_query("SELECT 1 as test", db_name)
                else:
                    result = manager.execute_query("SELECT 1 as test", db_name)
                print(f"✅ Query test successful")
            except Exception as e:
                print(f"⚠️ Connection successful but query failed: {e}")
        else:
            print(f"❌ Failed to connect to {db_name}")
        
        manager.close_all()
        
        # Clean up temp file
        if os.path.exists("temp_test_config.json"):
            os.remove("temp_test_config.json")
        
        return success
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def main():
    """Main setup interface"""
    print("🚀 Multi-Database Setup for Power System Visualization")
    print("=" * 60)
    
    # Load existing config if it exists
    config_file = "multi_database_config.json"
    if os.path.exists(config_file):
        print(f"📋 Found existing configuration: {config_file}")
        if get_yes_no("Load existing configuration?", True):
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            config = {"primary_database": "main", "databases": {}}
    else:
        config = {"primary_database": "main", "databases": {}}
    
    while True:
        print("\n" + "=" * 60)
        print("📊 Current Database Configuration:")
        
        if not config["databases"]:
            print("   No databases configured")
        else:
            for db_name, db_config in config["databases"].items():
                status = "✅ Enabled" if db_config.get("enabled", False) else "❌ Disabled"
                primary = "🎯 PRIMARY" if db_name == config.get("primary_database") else ""
                description = db_config.get("description", "No description")
                print(f"   {db_name}: {db_config['type']} {status} {primary}")
                print(f"      {description}")
        
        print("\n🛠️ Available Actions:")
        print("1. Add SQLite Database")
        print("2. Add PostgreSQL Database") 
        print("3. Edit Existing Database")
        print("4. Remove Database")
        print("5. Set Primary Database")
        print("6. Test Database Connections")
        print("7. Save Configuration")
        print("8. Exit")
        
        choice = get_user_input("\nSelect action (1-8)", required=False)
        
        if choice == "1":
            print("\n➕ Adding SQLite Database")
            db_name = get_user_input("Database name")
            description = get_user_input("Description (optional)", f"SQLite database: {db_name}", False)
            
            db_config = configure_sqlite_database()
            if description:
                db_config["description"] = description
            
            config["databases"][db_name] = db_config
            
            if get_yes_no("Test connection now?", True):
                test_database_connection(db_name, db_config)
        
        elif choice == "2":
            print("\n➕ Adding PostgreSQL Database")
            db_name = get_user_input("Database name")
            description = get_user_input("Description (optional)", f"PostgreSQL database: {db_name}", False)
            
            db_config = configure_postgresql_database()
            if description:
                db_config["description"] = description
            
            config["databases"][db_name] = db_config
            
            if get_yes_no("Test connection now?", True):
                test_database_connection(db_name, db_config)
        
        elif choice == "3":
            if not config["databases"]:
                print("❌ No databases to edit")
                continue
            
            print("\n✏️ Edit Database")
            print("Available databases:")
            for i, db_name in enumerate(config["databases"].keys(), 1):
                print(f"  {i}. {db_name}")
            
            try:
                db_index = int(get_user_input("Select database number")) - 1
                db_names = list(config["databases"].keys())
                if 0 <= db_index < len(db_names):
                    db_name = db_names[db_index]
                    db_config = config["databases"][db_name]
                    
                    print(f"\nEditing: {db_name}")
                    enabled = get_yes_no("Enabled?", db_config.get("enabled", True))
                    db_config["enabled"] = enabled
                    
                    # Allow editing description
                    current_desc = db_config.get("description", "")
                    new_desc = get_user_input("Description", current_desc, False)
                    if new_desc:
                        db_config["description"] = new_desc
                    
                    print(f"✅ Updated {db_name}")
                else:
                    print("❌ Invalid selection")
            except ValueError:
                print("❌ Invalid number")
        
        elif choice == "4":
            if not config["databases"]:
                print("❌ No databases to remove")
                continue
            
            print("\n🗑️ Remove Database")
            print("Available databases:")
            for i, db_name in enumerate(config["databases"].keys(), 1):
                print(f"  {i}. {db_name}")
            
            try:
                db_index = int(get_user_input("Select database number to remove")) - 1
                db_names = list(config["databases"].keys())
                if 0 <= db_index < len(db_names):
                    db_name = db_names[db_index]
                    if get_yes_no(f"Really remove {db_name}?", False):
                        del config["databases"][db_name]
                        
                        # Update primary if needed
                        if config.get("primary_database") == db_name:
                            if config["databases"]:
                                config["primary_database"] = next(iter(config["databases"]))
                                print(f"🎯 Primary database changed to: {config['primary_database']}")
                            else:
                                config["primary_database"] = None
                        
                        print(f"🗑️ Removed {db_name}")
                else:
                    print("❌ Invalid selection")
            except ValueError:
                print("❌ Invalid number")
        
        elif choice == "5":
            if not config["databases"]:
                print("❌ No databases available")
                continue
            
            print("\n🎯 Set Primary Database")
            print("Available databases:")
            for i, db_name in enumerate(config["databases"].keys(), 1):
                current = "🎯 CURRENT" if db_name == config.get("primary_database") else ""
                print(f"  {i}. {db_name} {current}")
            
            try:
                db_index = int(get_user_input("Select primary database number")) - 1
                db_names = list(config["databases"].keys())
                if 0 <= db_index < len(db_names):
                    config["primary_database"] = db_names[db_index]
                    print(f"🎯 Primary database set to: {config['primary_database']}")
                else:
                    print("❌ Invalid selection")
            except ValueError:
                print("❌ Invalid number")
        
        elif choice == "6":
            if not config["databases"]:
                print("❌ No databases to test")
                continue
            
            print("\n🔍 Testing Database Connections")
            for db_name, db_config in config["databases"].items():
                if db_config.get("enabled", False):
                    test_database_connection(db_name, db_config)
                else:
                    print(f"⏸️ Skipping disabled database: {db_name}")
        
        elif choice == "7":
            print(f"\n💾 Saving configuration to {config_file}")
            
            # Add metadata
            config.setdefault("connection_settings", {
                "auto_connect_on_startup": True,
                "failover_enabled": True,
                "connection_timeout": 30,
                "retry_attempts": 3
            })
            
            config.setdefault("query_settings", {
                "default_limit": 1000,
                "enable_query_logging": False,
                "cache_results": True
            })
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"✅ Configuration saved successfully!")
            print(f"\n📝 Next steps:")
            print(f"   1. Run your application with multi-database support")
            print(f"   2. Use the multi_database_manager module in your code")
            print(f"   3. Edit {config_file} manually if needed")
        
        elif choice == "8":
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please select 1-8.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Setup error: {e}")
        sys.exit(1)