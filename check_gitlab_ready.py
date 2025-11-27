"""
GitLab Upload Preparation Script
Verifies that your project is ready to be shared on GitLab
"""

import os
import subprocess
import sys

def check_git_installation():
    """Check if Git is installed"""
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Git installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ Git not found")
            return False
    except FileNotFoundError:
        print("❌ Git not installed or not in PATH")
        print("   Download from: https://git-scm.com/download/")
        return False

def check_essential_files():
    """Check if essential files are present"""
    essential_files = [
        'power_viz_with_database.py',
        'data.db',
        'requirements.txt',
        'APPLICATION_SETUP_GUIDE.md',
        'SHARING_GUIDE.md',
        'GITLAB_SHARING_GUIDE.md'
    ]
    
    print("\n📋 Essential Files Check:")
    print("-" * 40)
    
    all_present = True
    for file in essential_files:
        if os.path.exists(file):
            size = os.path.getsize(file) / (1024 * 1024)  # Size in MB
            print(f"✅ {file} ({size:.1f} MB)")
        else:
            print(f"❌ {file} - MISSING")
            all_present = False
    
    return all_present

def check_optional_files():
    """Check optional but recommended files"""
    optional_files = [
        'data_viz_fall.py',
        'branch_analysis.py',
        'bus_analysis.py',
        'generator_analysis_functions.py',
        'database_manager.py',
        'multi_database_manager.py',
        'dynamic_case_management.py',
        'data_availability.py',
        'simple_rag.py',
        'intelligent_data_completion.py',
        'entity_extraction.py',
        'enhanced_network_graphs.py',
        'case_comparison.py',
        'network_comparison.py',
        'comprehensive_trend_analyzer.py',
        'individual_analysis.py',
        'verify_setup.py',
        'start_app.bat',
        'setup_gitlab.bat'
    ]
    
    print("\n📦 Optional Files Check:")
    print("-" * 40)
    
    present_count = 0
    for file in optional_files:
        if os.path.exists(file):
            print(f"✅ {file}")
            present_count += 1
        else:
            print(f"⚠️  {file} - missing")
    
    print(f"\nOptional files present: {present_count}/{len(optional_files)}")
    return present_count

def check_git_status():
    """Check git repository status"""
    print("\n🔧 Git Repository Status:")
    print("-" * 40)
    
    if not os.path.exists('.git'):
        print("❌ Not a git repository")
        print("   Run: git init")
        return False
    
    try:
        # Check if there are any commits
        result = subprocess.run(['git', 'log', '--oneline', '-n', '1'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Git repository initialized with commits")
        else:
            print("⚠️  Git repository initialized but no commits yet")
        
        # Check remote
        result = subprocess.run(['git', 'remote', '-v'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            print(f"✅ Git remote configured:")
            for line in result.stdout.strip().split('\n'):
                print(f"   {line}")
        else:
            print("⚠️  No git remote configured")
            print("   Run: git remote add origin https://gitlab.com/username/repo.git")
        
        # Check status
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            print("⚠️  Uncommitted changes:")
            print(f"   {len(result.stdout.strip().split())} files modified")
        else:
            print("✅ Working directory clean")
        
        return True
        
    except Exception as e:
        print(f"❌ Git error: {e}")
        return False

def estimate_repo_size():
    """Estimate repository size"""
    print("\n📊 Repository Size Estimation:")
    print("-" * 40)
    
    total_size = 0
    file_count = 0
    
    for root, dirs, files in os.walk('.'):
        # Skip .git directory and other hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if not file.startswith('.'):
                filepath = os.path.join(root, file)
                try:
                    size = os.path.getsize(filepath)
                    total_size += size
                    file_count += 1
                except OSError:
                    pass
    
    total_mb = total_size / (1024 * 1024)
    
    print(f"Total files: {file_count}")
    print(f"Total size: {total_mb:.1f} MB")
    
    if total_mb > 100:
        print("⚠️  Large repository size - consider using Git LFS for large files")
    elif total_mb > 50:
        print("📝 Medium repository size - upload may take a few minutes")
    else:
        print("✅ Reasonable repository size - quick upload expected")
    
    return total_mb

def generate_gitlab_instructions():
    """Generate step-by-step GitLab instructions"""
    print("\n🚀 GitLab Upload Instructions:")
    print("=" * 50)
    
    print("\n1. CREATE GITLAB REPOSITORY:")
    print("   • Go to https://gitlab.com")
    print("   • Click '+' → 'New project/repository'")
    print("   • Project name: power-system-visualization")
    print("   • Visibility: Public (or Private)")
    print("   • DO NOT initialize with README")
    print("   • Click 'Create project'")
    
    print("\n2. PREPARE LOCAL REPOSITORY:")
    if not os.path.exists('.git'):
        print("   git init")
    print("   git add .")
    print("   git commit -m 'Initial commit: Power System Visualization App'")
    
    print("\n3. CONNECT TO GITLAB:")
    print("   git remote add origin https://gitlab.com/USERNAME/power-system-visualization.git")
    print("   (Replace USERNAME with your GitLab username)")
    
    print("\n4. PUSH TO GITLAB:")
    print("   git branch -M main")
    print("   git push -u origin main")
    
    print("\n5. SHARE YOUR REPOSITORY:")
    print("   Repository URL: https://gitlab.com/USERNAME/power-system-visualization")
    print("   Clone command: git clone https://gitlab.com/USERNAME/power-system-visualization.git")

def main():
    """Main verification function"""
    print("🦊 GitLab Upload Preparation Check")
    print("=" * 50)
    
    # Check Git installation
    git_ok = check_git_installation()
    
    # Check essential files
    files_ok = check_essential_files()
    
    # Check optional files
    optional_count = check_optional_files()
    
    # Check git status
    git_status_ok = check_git_status()
    
    # Estimate repository size
    repo_size = estimate_repo_size()
    
    # Final assessment
    print("\n🎯 READINESS ASSESSMENT:")
    print("=" * 50)
    
    if git_ok and files_ok:
        print("✅ READY FOR GITLAB!")
        print("   All essential components are present")
        print(f"   Optional features: {optional_count}/19 available")
        
        if repo_size > 100:
            print("⚠️  Consider optimizing large files before upload")
        
        print("\n🚀 Next steps:")
        print("   1. Run: setup_gitlab.bat (automated setup)")
        print("   2. OR follow manual instructions below")
        
        generate_gitlab_instructions()
        
    else:
        print("❌ NOT READY YET")
        
        if not git_ok:
            print("   • Install Git first")
        
        if not files_ok:
            print("   • Ensure all essential files are present")
        
        print("\n   Run this script again after addressing issues")
    
    print(f"\n📄 For detailed GitLab guide, see: GITLAB_SHARING_GUIDE.md")

if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")