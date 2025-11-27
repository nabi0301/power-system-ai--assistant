#!/usr/bin/env python3
"""
Debug PostgreSQL detection in the application
"""

import sys
import traceback

try:
    import psycopg2
    print("✅ psycopg2 imported successfully")
    
    # Simulate the exact logic from the application
    auth_configs = [
        {"user": "postgres", "password": "pnnl"},  # IEEE 118 Bus System Database
        {"user": "postgres", "password": "postgres"},
        {"user": "postgres", "password": "admin"},
        {"user": "postgres", "password": ""},
        {"user": "postgres"},  # No password
        {"user": "postgres", "password": "password"},
        {"user": "postgres", "password": "123456"},
    ]
    
    status = {
        "databases": {},
        "postgresql_available": False,
        "active_database": "main"
    }
    
    print(f"🔄 Testing {len(auth_configs)} authentication configurations...")
    
    for i, auth_config in enumerate(auth_configs, 1):
        print(f"\n--- Config {i}: {auth_config} ---")
        try:
            # Try to connect to default postgres database first
            conn_params = {
                "host": "localhost",
                "port": "5432",
                "database": "postgres",
                **auth_config
            }
            
            print(f"🔗 Attempting connection with: {conn_params}")
            conn = psycopg2.connect(**conn_params)
            cursor = conn.cursor()
            
            # Get list of all databases
            cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
            databases = cursor.fetchall()
            
            print(f"📋 Found {len(databases)} databases")
            
            # Look for databases with "118" or "ieee" in the name
            ieee_databases = []
            for db_tuple in databases:
                db_name = db_tuple[0]
                print(f"   • {db_name}")
                if ('118' in db_name.lower() or 'ieee' in db_name.lower() or 
                    db_name.lower() in ['ieee118_db', 'ieee118', '118', 'powerdb']):
                    ieee_databases.append(db_name)
                    print(f"     ✅ MATCHED as IEEE database!")
            
            cursor.close()
            conn.close()
            
            print(f"🎯 IEEE databases found: {ieee_databases}")
            
            # If we found IEEE databases, test connections
            if ieee_databases:
                for db_name in ieee_databases:
                    print(f"\n🔍 Testing connection to '{db_name}'...")
                    try:
                        test_conn_params = conn_params.copy()
                        test_conn_params["database"] = db_name
                        test_conn = psycopg2.connect(**test_conn_params)
                        test_conn.close()
                        
                        # Set appropriate description
                        if db_name == "118":
                            description = "IEEE 118 Bus System Database"
                        else:
                            description = f"IEEE 118-bus PostgreSQL Database ({db_name})"
                        
                        status["databases"][db_name] = {
                            "type": "postgresql",
                            "connected": True,
                            "config": {
                                "host": "localhost",
                                "port": "5432",
                                "database": db_name,
                                "user": auth_config.get("user", "postgres"),
                                "password": auth_config.get("password", "")
                            },
                            "description": description
                        }
                        status["postgresql_available"] = True
                        print(f"✅ Successfully connected to '{db_name}'")
                        
                    except Exception as e:
                        print(f"❌ Failed to connect to '{db_name}': {e}")
                        
                        if db_name == "118":
                            description = "IEEE 118 Bus System Database - Connection Failed"
                        else:
                            description = f"IEEE 118-bus PostgreSQL Database ({db_name}) - Connection Failed"
                        
                        status["databases"][db_name] = {
                            "type": "postgresql", 
                            "connected": False,
                            "config": {
                                "host": "localhost",
                                "port": "5432", 
                                "database": db_name,
                                "user": auth_config.get("user", "postgres")
                            },
                            "description": description
                        }
            
            # Successfully connected with this auth config, break out of loop
            if ieee_databases:
                print(f"🎯 Breaking loop - found working configuration")
                break
                
        except Exception as e:
            print(f"❌ Auth config {i} failed: {e}")
            continue
    
    print(f"\n🏁 FINAL STATUS:")
    print(f"   PostgreSQL Available: {status['postgresql_available']}")
    print(f"   Databases Found: {len(status['databases'])}")
    
    for db_name, db_info in status["databases"].items():
        connected = "✅" if db_info.get("connected") else "❌"
        print(f"   {connected} {db_name}: {db_info.get('description', 'No description')}")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    traceback.print_exc()