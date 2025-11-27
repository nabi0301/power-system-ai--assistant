import psycopg2
import sys
from pathlib import Path

def clear_database():
    """Clear all data from the database tables"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='118', 
            user='postgres',
            password='pnnl'
        )
        cursor = conn.cursor()
        
        print("🗑️  Clearing all database tables...")
        
        # Clear in order to respect foreign key constraints
        cursor.execute("DELETE FROM ContingencyBranchData")
        cursor.execute("DELETE FROM ContingencyBusData") 
        cursor.execute("DELETE FROM BaseBranchData")
        cursor.execute("DELETE FROM BaseBusData")
        cursor.execute("DELETE FROM ContingencyCases")
        cursor.execute("DELETE FROM BaseCases")
        
        conn.commit()
        print("✅ Database cleared successfully")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error clearing database: {e}")
        return False

def count_files():
    """Count available files"""
    base_folder = Path(r"C:\Projects\dlr-database-project\Base_118")
    contingency_folder = Path(r"C:\Projects\dlr-database-project\contingency_118")
    
    base_files = list(base_folder.glob("*.txt")) if base_folder.exists() else []
    contingency_files = list(contingency_folder.glob("*.txt")) if contingency_folder.exists() else []
    
    print(f"📁 Found {len(base_files)} base case files")
    print(f"📁 Found {len(contingency_files)} contingency case files")
    print(f"📁 Expected: {len(base_files)} × 186 contingency branches per base case")
    print(f"📁 Total files to process: {len(base_files) + len(contingency_files)}")
    
    return len(base_files), len(contingency_files)

if __name__ == "__main__":
    print("🚀 FULL DATA LOADER - BUS + BRANCH DATA")
    print("This will import ALL bus and branch data with proper relationships")
    print("=" * 70)
    
    # Count files first
    base_count, contingency_count = count_files()
    
    if base_count == 0:
        print("❌ No base case files found! Check the Base_118 folder path.")
        sys.exit(1)
    
    print(f"\n⚠️  This will:")
    print(f"   • Clear all existing data from the database")
    print(f"   • Import {base_count} base case files (bus + branch data)") 
    print(f"   • Import {contingency_count} contingency case files (bus + branch data)")
    print(f"   • Create proper relationships between base and contingency branch data")
    print(f"   • Calculate violations for all branch data")
    print(f"   • Expected result: ~{base_count * 186} contingency branch records")
    
    response = input("\n🔥 Continue? This will delete existing data! (yes/no): ").lower().strip()
    
    if response != 'yes':
        print("❌ Operation cancelled")
        sys.exit(0)
    
    # Clear database
    if not clear_database():
        print("❌ Failed to clear database")
        sys.exit(1)
    
    # Import the full data loader and run it
    print("\n🏗️  Starting full data loader (bus + branch data)...")
    print("=" * 70)
    
    try:
        from full_data_loader import FullDataLoader
        
        # Database configuration
        DB_CONFIG = {
            'host': 'localhost',
            'database': '118',
            'user': 'postgres', 
            'password': 'pnnl'
        }
        
        # Data folder path
        DATA_FOLDER = r"C:\Projects\dlr-database-project"
        
        # Create and run the loader
        loader = FullDataLoader(DATA_FOLDER, DB_CONFIG)
        success = loader.run_full_import()
        
        if success:
            print("\n🎉 ALL DATA (BUS + BRANCH) LOADED SUCCESSFULLY!")
            print("Check full_loader.log for detailed progress information")
        else:
            print("\n❌ Import failed. Check full_loader.log for error details")
            
    except Exception as e:
        print(f"❌ Error running full data loader: {e}")
        sys.exit(1)