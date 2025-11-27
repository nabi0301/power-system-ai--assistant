"""
Create a sharing package for the Power System Visualization Application
This script copies all essential files into a distributable folder
"""

import os
import shutil
import zipfile
from datetime import datetime

def create_sharing_package():
    """Create a complete package for sharing the application"""
    
    # Create package directory
    package_name = f"PowerSystemViz_Package_{datetime.now().strftime('%Y%m%d')}"
    package_dir = f"./{package_name}"
    
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
    os.makedirs(package_dir)
    
    print(f"📦 Creating sharing package: {package_name}")
    print("=" * 60)
    
    # Essential files to include
    essential_files = [
        # Core application
        'power_viz_with_database.py',
        'data.db',
        
        # Visualization components
        'data_viz_fall.py',
        'branch_analysis.py',
        'bus_analysis.py',
        'generator_analysis_functions.py',
        'enhanced_network_graphs.py',
        
        # Data management
        'database_manager.py',
        'multi_database_manager.py',
        'dynamic_case_management.py',
        'data_availability.py',
        
        # AI features (if available)
        'simple_rag.py',
        'intelligent_data_completion.py',
        'entity_extraction.py',
        
        # Analysis features
        'case_comparison.py',
        'network_comparison.py',
        'network_comparison_helper.py',
        'comprehensive_trend_analyzer.py',
        'individual_analysis.py',
        'direct_network_integration.py',
        
        # Configuration and setup
        'config.json',
        'requirements.txt',
        'APPLICATION_SETUP_GUIDE.md',
        'verify_setup.py',
        'start_app.bat',
    ]
    
    # Copy files
    copied_files = []
    missing_files = []
    
    for file in essential_files:
        if os.path.exists(file):
            try:
                shutil.copy2(file, package_dir)
                copied_files.append(file)
                print(f"✅ Copied: {file}")
            except Exception as e:
                print(f"❌ Error copying {file}: {e}")
                missing_files.append(file)
        else:
            print(f"⚠️  Missing: {file}")
            missing_files.append(file)
    
    # Create additional helpful files in the package
    
    # Quick start instructions
    with open(f"{package_dir}/QUICK_START.txt", "w") as f:
        f.write("""🚀 QUICK START GUIDE

1. VERIFY SETUP:
   python verify_setup.py

2. INSTALL DEPENDENCIES:
   pip install -r requirements.txt

3. RUN APPLICATION:
   python power_viz_with_database.py
   OR
   Double-click: start_app.bat (Windows)

4. OPEN BROWSER:
   http://127.0.0.1:8054

5. TRY FEATURES:
   - Select Base Case 42
   - Choose "SLR vs DLR (5 Scenarios)"
   - Test AI chat assistant (🤖 icon)

For detailed instructions, see: APPLICATION_SETUP_GUIDE.md
""")
    
    # Create a simple README
    with open(f"{package_dir}/README.txt", "w") as f:
        f.write(f"""Power System Visualization Application
Package created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This package contains a complete power system analysis application with:
✅ IEEE 118-bus system visualization
✅ SLR vs DLR comparison analysis  
✅ AI-powered data completion
✅ Interactive network graphs
✅ Multi-scenario contingency analysis

REQUIREMENTS:
- Python 3.8+
- Dependencies in requirements.txt

FILES INCLUDED: {len(copied_files)}
FILES MISSING: {len(missing_files)}

See APPLICATION_SETUP_GUIDE.md for complete setup instructions.
""")
    
    # Summary
    print(f"\n📊 PACKAGE SUMMARY")
    print("=" * 60)
    print(f"📁 Package directory: {package_dir}")
    print(f"✅ Files included: {len(copied_files)}")
    print(f"⚠️  Files missing: {len(missing_files)}")
    
    if missing_files:
        print(f"\nMissing files:")
        for file in missing_files:
            print(f"  • {file}")
    
    # Create ZIP file
    zip_filename = f"{package_name}.zip"
    print(f"\n📦 Creating ZIP file: {zip_filename}")
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, package_dir)
                zipf.write(file_path, arcname)
    
    print(f"✅ ZIP file created: {zip_filename}")
    
    # Final instructions
    print(f"\n🎯 SHARING INSTRUCTIONS")
    print("=" * 60)
    print(f"1. Share the ZIP file: {zip_filename}")
    print(f"2. Recipient should:")
    print(f"   • Extract the ZIP file")
    print(f"   • Run: python verify_setup.py")
    print(f"   • Install: pip install -r requirements.txt")
    print(f"   • Start: python power_viz_with_database.py")
    print(f"3. Application opens at: http://127.0.0.1:8054")
    
    return package_dir, zip_filename

if __name__ == "__main__":
    package_dir, zip_file = create_sharing_package()
    print(f"\n🎉 Package ready for sharing!")
    input("Press Enter to exit...")