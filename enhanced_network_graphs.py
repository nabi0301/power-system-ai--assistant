#!/usr/bin/env python3
"""
Enhanced Network Graph Visualization Module

This module enhances the AI assistant's ability to show comprehensive network graph comparisons
by detecting user requests and automatically showing the relevant visualizations.
"""

import re
import sqlite3
import pandas as pd
import plotly.graph_objects as go

def get_available_network_graphs():
    """
    Get a list of available case IDs and contingency IDs with complete data for network visualization.
    This helps the AI to suggest valid options to users.
    """
    try:
        conn = sqlite3.connect('data.db')
        
        # Get base cases with available data
        base_query = """
        SELECT DISTINCT b.base_case_id
        FROM BaseBusData b
        JOIN BaseBranchData br ON b.base_case_id = br.base_case_id
        ORDER BY b.base_case_id
        """
        base_cases = pd.read_sql_query(base_query, conn)
        
        # Get contingency cases with available data
        contingency_query = """
        SELECT DISTINCT cb.base_case_id, cb.contingency_case_id
        FROM ContingencyBusData cb
        JOIN ContingencyBranchData cbr ON 
            cb.base_case_id = cbr.base_case_id AND 
            cb.contingency_case_id = cbr.contingency_case_id
        ORDER BY cb.base_case_id, cb.contingency_case_id
        """
        contingency_cases = pd.read_sql_query(contingency_query, conn)
        
        # Get SLR cases with available data
        slr_query = """
        SELECT DISTINCT base_case_id, contingency_case_id
        FROM SLR_Branches
        ORDER BY base_case_id, contingency_case_id
        """
        slr_cases = pd.read_sql_query(slr_query, conn)
        
        # Get DLR cases with available data
        dlr_query = """
        SELECT DISTINCT base_case_id, contingency_case_id
        FROM DLR_Branches
        ORDER BY base_case_id, contingency_case_id
        """
        dlr_cases = pd.read_sql_query(dlr_query, conn)
        
        conn.close()
        
        # Combine the results to find cases with all four data types
        complete_cases = []
        
        for _, base_row in base_cases.iterrows():
            base_id = base_row['base_case_id']
            
            # Check for cases with no contingency (base case only)
            if ((slr_cases['base_case_id'] == base_id) & 
                (slr_cases['contingency_case_id'].isnull())).any() and \
               ((dlr_cases['base_case_id'] == base_id) & 
                (dlr_cases['contingency_case_id'].isnull())).any():
                complete_cases.append({
                    'base_case_id': base_id,
                    'contingency_case_id': None,
                    'data_types': ['base']
                })
            
            # Check for cases with contingencies
            for _, cont_row in contingency_cases[contingency_cases['base_case_id'] == base_id].iterrows():
                cont_id = cont_row['contingency_case_id']
                
                data_types = ['base', 'contingency']
                
                # Check if SLR data is available for this case/contingency
                if ((slr_cases['base_case_id'] == base_id) & 
                    (slr_cases['contingency_case_id'] == cont_id)).any():
                    data_types.append('slr')
                
                # Check if DLR data is available for this case/contingency
                if ((dlr_cases['base_case_id'] == base_id) & 
                    (dlr_cases['contingency_case_id'] == cont_id)).any():
                    data_types.append('dlr')
                
                # Only add if we have at least base and contingency data
                if len(data_types) >= 2:
                    complete_cases.append({
                        'base_case_id': base_id,
                        'contingency_case_id': cont_id,
                        'data_types': data_types
                    })
        
        return complete_cases
    
    except Exception as e:
        print(f"Error getting available network graphs: {e}")
        return []

def extract_network_graph_request(message):
    """
    Extract case and contingency IDs from a user message requesting network visualization.
    
    Returns:
    --------
    dict
        A dictionary with case_id, contingency_id, and visualization_type
    """
    result = {
        'case_id': None,
        'contingency_id': None,
        'visualization_type': None
    }
    
    message = message.lower()
    
    # First, determine the visualization type
    if any(term in message for term in ['compare', 'comparison', 'four panel', '4-panel', 'all networks', 'all graphs']):
        result['visualization_type'] = 'network_comparison'
    elif any(term in message for term in ['network graph', 'network diagram', 'fall network']):
        result['visualization_type'] = 'fall_network'
    
    # Look for case IDs
    case_patterns = [
        r'case\s+(\d+)',
        r'case id\s+(\d+)',
        r'base\s+case\s+(\d+)',
        r'base\s+(\d+)'
    ]
    
    for pattern in case_patterns:
        match = re.search(pattern, message)
        if match:
            result['case_id'] = int(match.group(1))
            break
    
    # Look for contingency IDs
    cont_patterns = [
        r'contingency\s+(\d+)',
        r'cont\s+(\d+)',
        r'contingency id\s+(\d+)',
        r'contingency case\s+(\d+)'
    ]
    
    for pattern in cont_patterns:
        match = re.search(pattern, message)
        if match:
            result['contingency_id'] = int(match.group(1))
            break
    
    # Look for SLR/DLR specific requests
    if 'slr' in message or 'static line rating' in message:
        result['visualization_type'] = 'slr_network'
    elif 'dlr' in message or 'dynamic line rating' in message:
        result['visualization_type'] = 'dlr_network'
    
    return result

def generate_network_graph_response(request_info, available_cases):
    """
    Generate a response with appropriate network visualization based on the request.
    
    Parameters:
    -----------
    request_info : dict
        Information about the request from extract_network_graph_request
    available_cases : list
        List of available cases from get_available_network_graphs
    
    Returns:
    --------
    tuple
        (response_text, visualization_type, case_id, contingency_id)
    """
    case_id = request_info.get('case_id')
    contingency_id = request_info.get('contingency_id')
    viz_type = request_info.get('visualization_type', 'fall_network')
    
    # If no specific case requested, use the first available case
    if case_id is None and available_cases:
        case_id = available_cases[0]['base_case_id']
        
        if viz_type in ['network_comparison', 'slr_network', 'dlr_network'] and contingency_id is None:
            # For these visualization types, we prefer cases with contingencies
            for case in available_cases:
                if case['contingency_case_id'] is not None:
                    case_id = case['base_case_id']
                    contingency_id = case['contingency_case_id']
                    break
    
    # Generate an appropriate response
    if viz_type == 'network_comparison':
        response = f"Showing network comparison for case {case_id}"
        if contingency_id is not None:
            response += f" with contingency {contingency_id}"
        response += ". The comparison displays base case, contingency, SLR, and DLR network graphs together."
        
    elif viz_type == 'slr_network':
        response = f"Showing SLR (Static Line Rating) network graph for case {case_id}"
        if contingency_id is not None:
            response += f" with contingency {contingency_id}"
        response += ". The network shows branches with static line ratings and highlights violations in red."
        
    elif viz_type == 'dlr_network':
        response = f"Showing DLR (Dynamic Line Rating) network graph for case {case_id}"
        if contingency_id is not None:
            response += f" with contingency {contingency_id}"
        response += ". The network shows branches with dynamic line ratings and highlights violations in red."
        
    else:  # fall_network (default)
        response = f"Showing network graph for case {case_id}"
        if contingency_id is not None:
            response += f" with contingency {contingency_id}"
        response += ". The network shows buses and branches with voltage and loading information."
    
    return response, viz_type, case_id, contingency_id

def has_network_graph_request(message):
    """
    Determine if a message contains a request for a network graph visualization.
    
    Parameters:
    -----------
    message : str
        User message
        
    Returns:
    --------
    bool
        True if the message contains a network graph request
    """
    message = message.lower()
    
    # List of network-related terms
    network_terms = [
        'network graph', 'network diagram', 'show network', 'display network',
        'network visualization', 'network view', 'network map', 'power system diagram',
        'compare networks', 'network comparison', 'four panel', '4-panel', 
        'fall network', 'data_viz_fall', 'slr network', 'dlr network',
        'show graph for case', 'graph of case', 'contingency graph',
        'network topology', 'system topology', 'topology diagram', 'see the network',
        'show the network', 'display the network', 'want to see network'
    ]
    
    # Check for exact term matches
    if any(term in message for term in network_terms):
        return True
    
    # Check for pattern-based matches (e.g., "show me the network")
    network_patterns = [
        r'\bnetwork\b',
        r'\btopology\b',
        r'\bshow.*\bgraph\b',
        r'\bdisplay.*\bgraph\b',
        r'\bgraph.*\bof\b',
    ]
    
    for pattern in network_patterns:
        if re.search(pattern, message):
            # Make sure it's not about other types of graphs (voltage, loading, etc.)
            exclusions = ['voltage graph', 'loading graph', 'bar graph', 'histogram']
            if not any(excl in message for excl in exclusions):
                return True
    
    return False