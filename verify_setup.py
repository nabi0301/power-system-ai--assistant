"""
File Verification Script for Power System Visualization App
Run this to check if you have all required files
"""

import os
import sys

def check_files():
    """Check for required files and provide setup guidance"""
    
    print("🔍 Power System Visualization App - File Verification")
    print("=" * 60)
    
    # Essential files for basic functionality
    essential_files = {
        'Core Application': [
            'power_viz_with_database.py',
            'data.db',
        ],
        'Visualization Components': [
            'data_viz_fall.py',
            'branch_analysis.py',
            'bus_analysis.py',
            'generator_analysis_functions.py',
        ],
        'Data Management': [
            'database_manager.py',
            'multi_database_manager.py',
            'dynamic_case_management.py',
            'data_availability.py',
        ]
    }
    
    # Optional but recommended files
    optional_files = {
        'AI Features': [
            'simple_rag.py',
            'intelligent_data_completion.py',
            'entity_extraction.py',
        ],
        'Enhanced Analysis': [
            'enhanced_network_graphs.py',
            'case_comparison.py',
            'network_comparison.py',
            'comprehensive_trend_analyzer.py',
            'individual_analysis.py',
            'network_comparison_helper.py',
        ],
        'Configuration': [
            'config.json',
            'requirements.txt',
        ]
    }
    
    all_good = True
    missing_essential = []
    missing_optional = []
    
    # Check essential files
    print("📋 ESSENTIAL FILES (Required for basic functionality)")
    print("-" * 60)
    
    for category, files in essential_files.items():
        print(f"\n{category}:")
        for file in files:
            if os.path.exists(file):
                print(f"  ✅ {file}")
            else:
                print(f"  ❌ {file} - MISSING")
                missing_essential.append(file)
                all_good = False
    
    # Check optional files
    print(f"\n📦 OPTIONAL FILES (Enhanced functionality)")
    print("-" * 60)
    
    for category, files in optional_files.items():
        print(f"\n{category}:")
        for file in files:
            if os.path.exists(file):
                print(f"  ✅ {file}")
            else:
                print(f"  ⚠️  {file} - missing (optional)")
                missing_optional.append(file)
    
    # Summary
    print(f"\n📊 SUMMARY")
    print("=" * 60)
    
    if all_good:
        print("🎉 SUCCESS: All essential files present!")
        print("✅ Your application should run correctly")
        
        if missing_optional:
            print(f"📝 NOTE: {len(missing_optional)} optional files missing")
            print("   App will run with reduced functionality")
    else:
        print(f"❌ ERROR: {len(missing_essential)} essential files missing!")
        print("🔧 REQUIRED ACTIONS:")
        
        for file in missing_essential:
            print(f"   • Download: {file}")
        
        print("\n📁 Essential files needed:")
        print("   • power_viz_with_database.py (main application)")
        print("   • data.db (database file)")
        print("   • All visualization and data management files")
    
    # Check Python dependencies
    print(f"\n🐍 PYTHON DEPENDENCIES")
    print("-" * 60)
    
    required_packages = [
        'dash', 'plotly', 'pandas', 'numpy', 'networkx'
    ]
    
    optional_packages = [
        'scikit-learn', 'chromadb', 'langchain'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - MISSING (required)")
            all_good = False
    
    print(f"\nOptional packages:")
    for package in optional_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ⚠️  {package} - missing (optional)")
    
    # Final instructions
    print(f"\n🚀 NEXT STEPS")
    print("=" * 60)
    
    if all_good:
        print("1. Run: python power_viz_with_database.py")
        print("2. Open: http://127.0.0.1:8054")
        print("3. Select Base Case 42 for SLR vs DLR comparison")
        print("4. Try the AI chat assistant (🤖 icon)")
    else:
        print("1. Install missing Python packages:")
        print("   pip install -r requirements.txt")
        print("2. Download missing essential files")
        print("3. Re-run this verification script")
        print("4. When all files present, run the application")
    
    return all_good

if __name__ == "__main__":
    success = check_files()
    
    if success:
        print(f"\n🎯 Ready to run! Use: python power_viz_with_database.py")
    else:
        print(f"\n⚠️  Setup incomplete. Please address missing files/packages.")
        
    input(f"\nPress Enter to exit...")
    sys.exit(0 if success else 1)