import sqlite3
import pandas as pd
from data_availability import check_data_availability, get_available_cases

def suggest_available_cases_for_network_comparison(message=""):
    """
    Generate suggestions for cases with complete data for network comparison.
    Can be used when the user explicitly asks for suggestions or when 
    their requested case doesn't have complete data.
    
    Parameters:
    -----------
    message : str
        User message to check for specific requests
        
    Returns:
    --------
    str
        Formatted message with case suggestions
    """
    try:
        # Get all cases with complete data
        complete_cases = get_available_cases()
        
        # If no complete cases were found
        if not complete_cases:
            return """⚠️ **No Complete Network Comparison Data Found**

I couldn't find any cases with complete data for all four visualizations (Base, Contingency, SLR, DLR).

You can still try to visualize specific cases, but some quadrants may show "Data Not Available".

**Suggested Actions:**
• Check if the database contains the required data
• Try importing example data if needed
• Consider visualizing individual network types instead"""
            
        # Format response based on available cases
        message = """📊 **Available Cases for Network Comparison**

The following cases have complete data for all four visualizations (Base, Contingency, SLR, DLR):

"""
        # Show the first 5 cases with complete data
        for i, case in enumerate(complete_cases[:5]):
            base_id = case['base_case_id']
            cont_id = case['contingency_case_id']
            
            if cont_id is not None:
                message += f"• Case {base_id}, Contingency {cont_id}\n"
            else:
                message += f"• Case {base_id} (no contingency)\n"
                
        # Add total count if more than 5 cases
        if len(complete_cases) > 5:
            message += f"\n...and {len(complete_cases) - 5} more cases with complete data.\n"
            
        message += """
To view any of these comparisons, you can:
• Type: "Show network comparison for case X, contingency Y"
• Or use the UI: Select "Network Comparison" visualization and enter the case/contingency IDs

These cases are guaranteed to have data for all four quadrants."""

        return message
        
    except Exception as e:
        print(f"Error suggesting available cases: {e}")
        return "I'm having trouble finding cases with complete data right now. Please try again later."