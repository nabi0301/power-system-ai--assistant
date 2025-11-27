"""
Test script to run power_viz_with_database.py with data_viz_fall.py integration
"""

import os
import sys
import subprocess
import time

def check_requirements():
    """Check if all required files exist and validate their content"""
    required_files = ['power_viz_with_database.py', 'data_viz_fall.py']
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Error: The following required files are missing:")
        for file in missing_files:
            print(f" - {file}")
        return False
    
    # Verify data_viz_fall.py has create_network_graph function
    try:
        with open('data_viz_fall.py', 'r') as f:
            data_viz_content = f.read()
            if 'def create_network_graph(' not in data_viz_content:
                print("❌ Error: data_viz_fall.py does not contain create_network_graph function")
                return False
    except Exception as e:
        print(f"❌ Error reading data_viz_fall.py: {e}")
        return False
    
    # Make sure numpy is installed
    try:
        import numpy
        print("✅ numpy is installed")
    except ImportError:
        print("❌ Error: numpy is not installed, which is required for the integration")
        print("   Please run: pip install numpy")
        return False
    
    return True

def activate_virtual_environment():
    """Activate the virtual environment"""
    try:
        venv_path = os.path.join(os.getcwd(), "dlr-env")
        if os.name == 'nt':  # Windows
            activate_script = os.path.join(venv_path, "Scripts", "Activate.ps1")
            if os.path.exists(activate_script):
                print(f"🔄 Activating virtual environment: {activate_script}")
                subprocess.run(["powershell", "-Command", f"& '{activate_script}'"], check=True)
            else:
                print(f"⚠️ Activation script not found: {activate_script}")
                print("⚠️ Proceeding without virtual environment activation")
        else:  # Linux/Mac
            activate_script = os.path.join(venv_path, "bin", "activate")
            if os.path.exists(activate_script):
                print(f"🔄 Activating virtual environment: {activate_script}")
                subprocess.run(f"source {activate_script}", shell=True, check=True)
            else:
                print(f"⚠️ Activation script not found: {activate_script}")
                print("⚠️ Proceeding without virtual environment activation")
    except Exception as e:
        print(f"⚠️ Failed to activate virtual environment: {e}")
        print("⚠️ Proceeding without virtual environment activation")

def fix_power_viz_integration():
    """Fix the data_viz_fall.py network visualization in power_viz_with_database.py"""
    try:
        # Read content of power_viz_with_database.py
        with open('power_viz_with_database.py', 'r') as f:
            content = f.read()
        
        # Check if we need to fix the create_power_system_plot function
        if "return data_viz_fall.create_network_graph" not in content:
            print("🔄 Modifying power_viz_with_database.py to directly use data_viz_fall.py's create_network_graph function")
            
            # Create a backup file just in case
            with open('power_viz_with_database.py.bak', 'w') as f:
                f.write(content)
            print("✅ Created backup at power_viz_with_database.py.bak")
            
            # Look for the create_power_system_plot function
            import re
            create_function_match = re.search(r'def\s+create_power_system_plot\s*\([^)]*\):[^}]*?\s+return\s+fig', content, re.DOTALL)
            
            if create_function_match:
                # Get the original function code
                original_function = create_function_match.group(0)
                
                # Define the replacement function that uses data_viz_fall directly
                replacement_function = """def create_power_system_plot(buses_df, branches_df, case_id=None, contingency_id=None):
    \"\"\"
    Create power system visualization using data_viz_fall.py's visualization directly
    \"\"\"
    import os
    import importlib.util
    import numpy as np
    
    try:
        # Import data_viz_fall.py dynamically
        module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data_viz_fall.py')
        spec = importlib.util.spec_from_file_location("data_viz_fall", module_path)
        data_viz_fall = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(data_viz_fall)
        
        # Prepare data for data_viz_fall.py's create_network_graph function
        buses_renamed = buses_df.copy()
        branches_renamed = branches_df.copy()
        
        # Rename columns to match data_viz_fall.py's expected format
        column_mapping = {
            'From_Bus': 'FROM_BUS',
            'To_Bus': 'TO_BUS',
            'branch_number': 'BRANCH_NUMBER',
        }
        for old_col, new_col in column_mapping.items():
            if old_col in branches_renamed.columns:
                branches_renamed.rename(columns={old_col: new_col}, inplace=True)
        
        # Fill in missing columns if needed
        required_columns = {
            'buses': ['BUS_NUMBER', 'VM', 'VA', 'BASE_KV', 'PG', 'QG', 'PD', 'QD'],
            'branches': ['FROM_BUS', 'TO_BUS', 'PF', 'QF', 'LOAD_LEVEL', 'VIO', 'MVA', 'RATE']
        }
        
        for col in required_columns['buses']:
            if col not in buses_renamed.columns:
                if col in buses_df.columns:
                    buses_renamed[col] = buses_df[col]
                else:
                    buses_renamed[col] = np.nan
                    
        for col in required_columns['branches']:
            if col not in branches_renamed.columns:
                if col == 'LOAD_LEVEL' and 'MVA' in branches_renamed.columns and 'RATE' in branches_renamed.columns:
                    # Calculate load level from MVA and RATE
                    branches_renamed['LOAD_LEVEL'] = branches_renamed['MVA'] / branches_renamed['RATE'] * 100
                else:
                    branches_renamed[col] = np.nan
        
        # Get min_load and max_load for visualization
        min_load = buses_renamed['PD'].min() if 'PD' in buses_renamed.columns else 0
        max_load = buses_renamed['PD'].max() if 'PD' in buses_renamed.columns else 100
        
        # Get the title based on case_id
        title = "Power System Network"
        if case_id is not None:
            title = f"Case {case_id}"
            if contingency_id is not None:
                title += f" - Contingency {contingency_id}"
        
        # Print information about the data being passed to create_network_graph
        print(f"Creating network graph with {len(buses_renamed)} buses and {len(branches_renamed)} branches")
        print(f"Bus columns: {buses_renamed.columns.tolist()}")
        print(f"Branch columns: {branches_renamed.columns.tolist()}")
        
        # Call data_viz_fall.py's create_network_graph function directly
        return data_viz_fall.create_network_graph(
            buses_renamed, branches_renamed, title, min_load, max_load, case_id
        )
    except Exception as e:
        print(f"❌ Error using data_viz_fall visualization: {e}")
        # Fall back to original visualization
        print("⚠️ Falling back to original visualization")
        fig = go.Figure()
        
        # Create a basic visualization
        fig.add_trace(go.Scatter(
            x=buses_df['x_coord'] if 'x_coord' in buses_df.columns else buses_df['BUS_NUMBER'],
            y=buses_df['y_coord'] if 'y_coord' in buses_df.columns else buses_df['VM'],
            mode='markers',
            marker=dict(
                size=10,
                color=buses_df['VM'] if 'VM' in buses_df.columns else 'blue',
                colorscale='RdYlGn',
                showscale=True
            ),
            text=buses_df.apply(lambda row: f"Bus {int(row['BUS_NUMBER'])}" if 'BUS_NUMBER' in buses_df.columns else "", axis=1),
            name='Buses'
        ))
        
        # Add a message about the error
        fig.add_annotation(
            text=f"Error loading data_viz_fall visualization: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.9,
            showarrow=False,
            font=dict(color="red", size=12)
        )
        
        fig.update_layout(
            title=f"Network Visualization (Fallback) - Case {case_id if case_id is not None else 'Default'}",
            height=600
        )
        return fig"""
                
                # Replace the function in the content
                modified_content = content.replace(original_function, replacement_function)
                
                # Write the modified content back to the file
                with open('power_viz_with_database.py', 'w') as f:
                    f.write(modified_content)
                print("✅ Successfully modified power_viz_with_database.py")
                return True
            else:
                print("❌ Could not find the create_power_system_plot function in power_viz_with_database.py")
                return False
        else:
            print("✅ power_viz_with_database.py already uses data_viz_fall.py's create_network_graph function")
            return True
    except Exception as e:
        print(f"❌ Error modifying power_viz_with_database.py: {e}")
        return False

def run_visualization():
    """Run the power_viz_with_database.py script with data_viz_fall.py integration"""
    try:
        print("\n" + "="*70)
        print("🚀 Starting Power Visualization with data_viz_fall.py Integration")
        print("="*70)
        
        # Fix the integration first
        if not fix_power_viz_integration():
            print("⚠️ Could not fix integration, but will try to run anyway")
        
        print("\n📝 Instructions:")
        print(" 1. The application will launch in your web browser")
        print(" 2. Select '🌐 data_viz_fall Network View' from the dropdown")
        print(" 3. You should see the network visualization using data_viz_fall.py's interface")
        print("="*70 + "\n")
        
        # Run the visualization script
        print("🔄 Starting power_viz_with_database.py...")
        
        # Use python executable to run the script
        python_cmd = sys.executable if sys.executable else "python"
        subprocess.run([python_cmd, "power_viz_with_database.py"], check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running visualization: {e}")

def main():
    """Main function"""
    # Check if required files exist
    if not check_requirements():
        print("❌ Cannot proceed due to missing files")
        return
    
    # Activate virtual environment
    activate_virtual_environment()
    
    # Run the visualization
    run_visualization()

if __name__ == "__main__":
    main()