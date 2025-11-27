import sqlite3
import pandas as pd

def check_data_availability(case_id, contingency_id=None):
    """
    Check data availability for base case, contingency, SLR, and DLR.
    
    Parameters:
    -----------
    case_id : int
        The base case ID to check
    contingency_id : int or None
        The contingency case ID to check
        
    Returns:
    --------
    dict
        Dictionary with availability status for each case type
    """
    try:
        # Connect to database
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        # Dictionary to store results
        availability = {
            'base_case': False,
            'contingency_case': False,
            'slr_case': False,
            'dlr_case': False
        }
        
        # Check base case data
        cursor.execute(f"SELECT COUNT(*) FROM BaseBusData WHERE base_case_id = {case_id}")
        base_bus_count = cursor.fetchone()[0]
        
        cursor.execute(f"SELECT COUNT(*) FROM BaseBranchData WHERE base_case_id = {case_id}")
        base_branch_count = cursor.fetchone()[0]
        
        availability['base_case'] = base_bus_count > 0 and base_branch_count > 0
        
        # Check contingency case data
        if contingency_id is not None:
            cursor.execute(f"""
                SELECT COUNT(*) FROM ContingencyBusData 
                WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}
            """)
            contingency_bus_count = cursor.fetchone()[0]
            
            cursor.execute(f"""
                SELECT COUNT(*) FROM ContingencyBranchData 
                WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}
            """)
            contingency_branch_count = cursor.fetchone()[0]
            
            availability['contingency_case'] = contingency_bus_count > 0 and contingency_branch_count > 0
        else:
            # If no contingency ID is specified, use base case data
            availability['contingency_case'] = availability['base_case']
        
        # Check SLR data
        slr_query = f"""
            SELECT COUNT(*) FROM SLR_Branches 
            WHERE base_case_id = {case_id}
            {f"AND contingency_case_id = {contingency_id}" if contingency_id is not None else ""}
        """
        cursor.execute(slr_query)
        slr_count = cursor.fetchone()[0]
        availability['slr_case'] = slr_count > 0 and availability['base_case']
        
        # Check DLR data
        dlr_query = f"""
            SELECT COUNT(*) FROM DLR_Branches 
            WHERE base_case_id = {case_id}
            {f"AND contingency_case_id = {contingency_id}" if contingency_id is not None else ""}
        """
        cursor.execute(dlr_query)
        dlr_count = cursor.fetchone()[0]
        availability['dlr_case'] = dlr_count > 0 and availability['base_case']
        
        # Close connection
        conn.close()
        
        return availability
        
    except Exception as e:
        print(f"Error checking data availability: {e}")
        # Return all False if there was an error
        return {
            'base_case': False,
            'contingency_case': False,
            'slr_case': False,
            'dlr_case': False
        }

def get_available_cases():
    """
    Get a list of cases with complete data for all four visualizations
    
    Returns:
    --------
    list
        List of dictionaries with base_case_id and contingency_case_id for cases with complete data
    """
    try:
        # Connect to database
        conn = sqlite3.connect('data.db')
        
        # Get distinct base case IDs
        base_cases_query = "SELECT DISTINCT base_case_id FROM BaseBusData ORDER BY base_case_id"
        base_cases = pd.read_sql_query(base_cases_query, conn)
        
        # Get distinct contingency combinations
        contingency_query = """
            SELECT DISTINCT b.base_case_id, c.contingency_case_id 
            FROM BaseBusData b 
            JOIN ContingencyBusData c ON b.base_case_id = c.base_case_id
            ORDER BY b.base_case_id, c.contingency_case_id
        """
        contingencies = pd.read_sql_query(contingency_query, conn)
        
        # Close connection
        conn.close()
        
        # Check which cases have complete data
        complete_cases = []
        
        # First check base cases without contingencies
        for _, row in base_cases.iterrows():
            base_id = row['base_case_id']
            availability = check_data_availability(base_id)
            
            # If all data is available, add to complete cases
            if all(availability.values()):
                complete_cases.append({
                    'base_case_id': base_id,
                    'contingency_case_id': None,
                    'description': f"Base case {base_id} (no contingency)"
                })
                
        # Check contingency cases
        for _, row in contingencies.iterrows():
            base_id = row['base_case_id']
            cont_id = row['contingency_case_id']
            
            availability = check_data_availability(base_id, cont_id)
            
            # If all data is available, add to complete cases
            if all(availability.values()):
                complete_cases.append({
                    'base_case_id': base_id,
                    'contingency_case_id': cont_id,
                    'description': f"Base case {base_id}, Contingency {cont_id}"
                })
                
        return complete_cases
        
    except Exception as e:
        print(f"Error getting available cases: {e}")
        return []