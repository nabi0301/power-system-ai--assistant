"""
Integration script for adding power_viz_component.py to data_viz_fall.py
-------------------------------------------------------------------
This script modifies data_viz_fall.py to replace the Statistical Analysis tab
with the Power Visualization tab from power_viz_component.py.
"""

import os
import re

# Define paths
current_dir = os.path.dirname(os.path.abspath(__file__))
data_viz_file = os.path.join(current_dir, "data_viz_fall.py")
backup_file = os.path.join(current_dir, "data_viz_fall.py.bak")

def create_backup():
    """Create a backup of the original data_viz_fall.py file"""
    try:
        with open(data_viz_file, 'r') as f:
            content = f.read()
        
        with open(backup_file, 'w') as f:
            f.write(content)
        
        print(f"✅ Created backup at {backup_file}")
        return True
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return False

def integrate_power_visualization():
    """
    Integrate power visualization component into data_viz_fall.py by:
    1. Adding necessary imports
    2. Replacing the Statistical Analysis tab with Power Visualization tab
    """
    try:
        # Read the original file
        with open(data_viz_file, 'r') as f:
            content = f.read()
        
        # 1. Add imports for power_viz_integration at the top after existing imports
        import_pattern = r"(import dash.*?(?:^$|\n\n))"
        import_section = re.search(import_pattern, content, re.DOTALL | re.MULTILINE)
        
        if not import_section:
            print("❌ Could not find import section")
            return False
        
        new_imports = (
            import_section.group(1) + 
            "\n# Import power visualization integration\n" +
            "from power_viz_integration import get_power_viz_tab, integrate_power_viz_into_dataviz_fall\n\n"
        )
        
        content = content.replace(import_section.group(1), new_imports)
        
        # 2. Replace the Statistical Analysis tab with Power Visualization tab
        # Find the statistical analysis tab definition
        stats_tab_pattern = r"(\s+# Statistical Analysis Tab \(New Functionality\)[\s\S]*?tab_id=\"stats-tab\"[\s\S]*?)(\s+children=\[[\s\S]*?)(\s+\],?\s+\),)"
        
        stats_tab_match = re.search(stats_tab_pattern, content)
        if not stats_tab_match:
            print("❌ Could not find Statistical Analysis tab definition")
            return False
        
        # Replace the entire tab with the Power Visualization tab
        power_viz_tab_code = (
            stats_tab_match.group(1) + 
            "\n                children=[\n" + 
            "                    # Power Visualization tab content from power_viz_component.py\n" + 
            "                    get_power_viz_tab().children\n" +
            "                ]," + 
            stats_tab_match.group(3)
        )
        
        content = content.replace(
            stats_tab_match.group(1) + stats_tab_match.group(2) + stats_tab_match.group(3),
            power_viz_tab_code
        )
        
        # 3. Update tab label from "Statistical Analysis" to "Power Visualization"
        content = content.replace(
            'label="Statistical Analysis"',
            'label="Power Visualization"'
        )
        
        # 4. Add code to initialize the power visualization integration at the end of the file
        if_server_pattern = r"(if __name__ == ['\"]__main__['\"]:[\s\S]*)(app\.run_server\(.*\))"
        
        if_server_match = re.search(if_server_pattern, content)
        if not if_server_match:
            print("❌ Could not find server initialization section")
            return False
        
        integration_code = (
            if_server_match.group(1) + 
            "    # Integrate power visualization component\n" + 
            "    integrate_power_viz_into_dataviz_fall(app)\n\n    " + 
            if_server_match.group(2)
        )
        
        content = content.replace(
            if_server_match.group(1) + if_server_match.group(2),
            integration_code
        )
        
        # Write the modified content back to the file
        with open(data_viz_file, 'w') as f:
            f.write(content)
        
        print("✅ Successfully integrated Power Visualization into data_viz_fall.py")
        return True
    except Exception as e:
        print(f"❌ Error during integration: {e}")
        return False

def main():
    """Main function to run the integration"""
    print("Starting integration of Power Visualization into data_viz_fall.py...")
    
    # Step 1: Create backup
    if not create_backup():
        print("Integration aborted due to backup failure.")
        return
    
    # Step 2: Integrate power visualization
    if not integrate_power_visualization():
        print("Integration failed. You can restore from the backup file.")
        return
    
    print("\n" + "="*60)
    print("Integration completed successfully!")
    print("The Statistical Analysis tab has been replaced with Power Visualization.")
    print("You can now run data_viz_fall.py to see the changes.")
    print("="*60 + "\n")
    print("If you need to revert changes, copy the backup file data_viz_fall.py.bak")
    print("back to data_viz_fall.py")

if __name__ == "__main__":
    main()