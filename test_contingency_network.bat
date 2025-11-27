@echo off
echo Testing Contingency Network Graph Visualization...

:: Activate the Python environment if it exists
if exist "dlr-env\Scripts\activate.bat" (
    echo Activating Python environment...
    call dlr-env\Scripts\activate.bat
) else (
    echo Warning: Python environment not found at dlr-env\Scripts\activate.bat
)

:: Run the power visualization with a test contingency case
python -c "
import sys
import os
import importlib.util
import pandas as pd
import sqlite3

# Add current directory to path
sys.path.append(os.getcwd())

try:
    # Connect to database
    conn = sqlite3.connect('data.db')
    
    # Get available contingency cases
    query = \"\"\"
        SELECT DISTINCT base_case_id, contingency_case_id 
        FROM ContingencyBusData 
        ORDER BY base_case_id, contingency_case_id
        LIMIT 5
    \"\"\"
    
    contingency_df = pd.read_sql_query(query, conn)
    
    if contingency_df.empty:
        print('No contingency cases found in database')
        sys.exit(1)
    
    # Get first available contingency case
    test_base_case = contingency_df.iloc[0]['base_case_id']
    test_contingency = contingency_df.iloc[0]['contingency_case_id']
    
    print(f'Testing with base case {test_base_case}, contingency {test_contingency}')
    
    # Import the visualization function
    spec = importlib.util.spec_from_file_location('power_viz', 'power_viz_with_database.py')
    power_viz = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(power_viz)
    
    # Get case data
    case_buses_query = f\"\"\"
        SELECT * FROM ContingencyBusData 
        WHERE base_case_id = {test_base_case} AND contingency_case_id = {test_contingency}
    \"\"\"
    case_branches_query = f\"\"\"
        SELECT * FROM ContingencyBranchData 
        WHERE base_case_id = {test_base_case} AND contingency_case_id = {test_contingency}
    \"\"\"
    
    case_buses_df = pd.read_sql_query(case_buses_query, conn)
    case_branches_df = pd.read_sql_query(case_branches_query, conn)
    
    # Add coordinates for visualization
    case_buses_df['x_coord'] = (case_buses_df['BUS_NUMBER'] % 12) * 30
    case_buses_df['y_coord'] = (case_buses_df['BUS_NUMBER'] // 12) * 25
    
    # Close connection
    conn.close()
    
    # Create figure
    fig = power_viz.create_power_system_plot(
        case_buses_df, 
        case_branches_df, 
        case_id=test_base_case, 
        contingency_id=test_contingency
    )
    
    # Save figure
    fig.write_html('contingency_network_test.html')
    print('Successfully created contingency network visualization!')
    print('Saved as contingency_network_test.html')
    
    # Open the file in browser
    import webbrowser
    webbrowser.open('contingency_network_test.html')
    
except Exception as e:
    print(f'Error testing contingency network visualization: {e}')
"

:: Pause to show any errors before closing
pause