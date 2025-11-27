def perform_individual_bus_analysis(case_id, bus_numbers=None, contingency_id=None):
    """
    Perform detailed analysis on individual buses for a specific case and contingency.
    If bus_numbers is None, analyzes all buses in the case.
    If contingency_id is None, analyzes the base case data.
    """
    import pandas as pd
    import sqlite3
    
    try:
        conn = sqlite3.connect('data.db')
        
        # Determine which table to query based on contingency_id
        if contingency_id is None:
            table_name = "BaseBusData"
            where_clause = f"base_case_id = {case_id}"
            bus_column = "BUS_NUMBER"  # BaseBusData uses uppercase column name
        else:
            table_name = "ContingencyBusData"
            where_clause = f"base_case_id = {case_id} AND contingency_case_id = {contingency_id}"
            bus_column = "bus_number"  # ContingencyBusData uses lowercase column name
            
        # Query to get all bus data for the specified case
        query = f"""
        SELECT {bus_column} as BUS_NUMBER, VM, VA, BASE_KV, PG, QG, PD, QD,
               CASE WHEN VM < 0.90 THEN 'Critical Low Voltage'
                    WHEN VM < 0.95 THEN 'Low Voltage'
                    WHEN VM > 1.10 THEN 'Critical High Voltage'
                    WHEN VM > 1.05 THEN 'High Voltage'
                    WHEN VM BETWEEN 0.98 AND 1.02 THEN 'Optimal'
                    ELSE 'Normal' END as voltage_status
        FROM {table_name} WHERE {where_clause}
        """
        
        # If specific buses are requested, filter by those
        if bus_numbers and isinstance(bus_numbers, list) and len(bus_numbers) > 0:
            bus_list = ', '.join(str(bus) for bus in bus_numbers)
            query += f" AND BUS_NUMBER IN ({bus_list})"
        
        query += " ORDER BY BUS_NUMBER"
        bus_data = pd.read_sql_query(query, conn)
        
        if bus_data.empty:
            return {'error': f"No bus data found for case {case_id}"}
        
        # Calculate statistics
        voltage_stats = {
            'min_voltage': bus_data['VM'].min(),
            'max_voltage': bus_data['VM'].max(),
            'avg_voltage': bus_data['VM'].mean(),
            'std_voltage': bus_data['VM'].std(),
            'low_voltage_count': len(bus_data[bus_data['VM'] < 0.95]),
            'high_voltage_count': len(bus_data[bus_data['VM'] > 1.05]),
            'normal_voltage_count': len(bus_data[(bus_data['VM'] >= 0.95) & (bus_data['VM'] <= 1.05)]),
            'total_generation': bus_data['PG'].sum(),
            'total_load': bus_data['PD'].sum()
        }
        
        # Get connected branches for each bus
        all_branches = []
        branch_table = "ContingencyBranchData" if contingency_id is not None else "BaseBranchData"
        branch_where = f"base_case_id = {case_id}" + (f" AND contingency_case_id = {contingency_id}" if contingency_id is not None else "")
        branch_column = "branch_number"  # Both tables use lowercase for this column
        
        for bus in bus_data['BUS_NUMBER']:
            branch_query = f"""
            SELECT {branch_column} as branch_number, From_Bus, To_Bus, PF, QF, MVA, RATE, 
                   (MVA/RATE * 100) as loading_percent
            FROM {branch_table} 
            WHERE {branch_where} AND (From_Bus = {bus} OR To_Bus = {bus})
            ORDER BY loading_percent DESC
            """
            branch_data = pd.read_sql_query(branch_query, conn)
            if not branch_data.empty:
                all_branches.append({
                    'bus_number': bus,
                    'connected_branches': branch_data.to_dict('records')
                })
        
        conn.close()
        
        return {
            'case_id': case_id,
            'contingency_id': contingency_id,
            'bus_data': bus_data.to_dict('records'),
            'voltage_stats': voltage_stats,
            'connected_branches': all_branches,
            'total_buses': len(bus_data),
            'is_contingency_case': contingency_id is not None
        }
    
    except Exception as e:
        print(f"Error in individual bus analysis: {e}")
        return {'error': str(e)}

def perform_individual_branch_analysis(case_id, branch_specs=None, contingency_id=None):
    """
    Perform detailed analysis on individual branches for a specific case and contingency.
    branch_specs can be a list of dictionaries with from_bus and to_bus keys,
    or None to analyze all branches.
    If contingency_id is None, analyzes the base case data.
    """
    import pandas as pd
    import sqlite3
    
    try:
        conn = sqlite3.connect('data.db')
        
        # Determine which table to query based on contingency_id
        if contingency_id is None:
            table_name = "BaseBranchData"
            where_clause = f"base_case_id = {case_id}"
            branch_column = "branch_number"  # BaseBranchData uses lowercase column name
        else:
            table_name = "ContingencyBranchData"
            where_clause = f"base_case_id = {case_id} AND contingency_case_id = {contingency_id}"
            branch_column = "branch_number"  # ContingencyBranchData also uses lowercase column name
        
        # Query to get all branch data for the specified case
        query = f"""
        SELECT {branch_column} as branch_number, From_Bus, To_Bus, PF, QF, MVA, RATE, VIO,
               (MVA/RATE * 100) as loading_percent,
               CASE WHEN MVA/RATE > 1.1 THEN 'Critically Overloaded'
                    WHEN MVA/RATE > 1.0 THEN 'Overloaded'
                    WHEN MVA/RATE > 0.9 THEN 'Highly Loaded'
                    WHEN MVA/RATE > 0.8 THEN 'Moderately Loaded'
                    WHEN MVA/RATE < 0.2 THEN 'Underutilized'
                    ELSE 'Normal' END as loading_status
        FROM {table_name} WHERE {where_clause} AND RATE > 0
        """
        
        # If specific branches are requested, filter by those
        if branch_specs and isinstance(branch_specs, list) and len(branch_specs) > 0:
            branch_conditions = []
            for branch in branch_specs:
                if 'from_bus' in branch and 'to_bus' in branch:
                    from_bus = branch['from_bus']
                    to_bus = branch['to_bus']
                    branch_conditions.append(f"(From_Bus = {from_bus} AND To_Bus = {to_bus})")
            
            if branch_conditions:
                query += " AND (" + " OR ".join(branch_conditions) + ")"
        
        query += " ORDER BY loading_percent DESC"
        branch_data = pd.read_sql_query(query, conn)
        
        if branch_data.empty:
            return {'error': f"No branch data found for case {case_id}"}
        
        # Calculate statistics
        loading_stats = {
            'min_loading': branch_data['loading_percent'].min(),
            'max_loading': branch_data['loading_percent'].max(),
            'avg_loading': branch_data['loading_percent'].mean(),
            'std_loading': branch_data['loading_percent'].std(),
            'overloaded_count': len(branch_data[branch_data['loading_percent'] > 100]),
            'highly_loaded_count': len(branch_data[(branch_data['loading_percent'] > 80) & 
                                                (branch_data['loading_percent'] <= 100)]),
            'normal_count': len(branch_data[(branch_data['loading_percent'] <= 80) & 
                                         (branch_data['loading_percent'] >= 20)]),
            'underutilized_count': len(branch_data[branch_data['loading_percent'] < 20]),
            'total_mw_flow': branch_data['PF'].abs().sum(),
            'total_mvar_flow': branch_data['QF'].abs().sum()
        }
        
        # Get bus details for connected buses
        bus_details = {}
        all_buses = set()
        for _, row in branch_data.iterrows():
            all_buses.add(int(row['From_Bus']))
            all_buses.add(int(row['To_Bus']))
        
        if all_buses:
            bus_table = "ContingencyBusData" if contingency_id is not None else "BaseBusData"
            bus_where = f"base_case_id = {case_id}" + (f" AND contingency_case_id = {contingency_id}" if contingency_id is not None else "")
            
            # Use the correct column name based on the table
            bus_column = "bus_number" if contingency_id is not None else "BUS_NUMBER"
            
            bus_list = ', '.join(str(bus) for bus in all_buses)
            bus_query = f"""
            SELECT {bus_column} as BUS_NUMBER, VM, VA, BASE_KV, PG, QG, PD, QD
            FROM {bus_table}
            WHERE {bus_where} AND {bus_column} IN ({bus_list})
            """
            bus_data = pd.read_sql_query(bus_query, conn)
            for _, row in bus_data.iterrows():
                bus_details[row['BUS_NUMBER']] = row.to_dict()
        
        conn.close()
        
        return {
            'case_id': case_id,
            'contingency_id': contingency_id,
            'branch_data': branch_data.to_dict('records'),
            'loading_stats': loading_stats,
            'connected_buses': bus_details,
            'total_branches': len(branch_data),
            'is_contingency_case': contingency_id is not None
        }
    
    except Exception as e:
        print(f"Error in individual branch analysis: {e}")
        return {'error': str(e)}

def generate_bus_analysis_response(analysis_result):
    """Generate a detailed response for bus analysis"""
    if 'error' in analysis_result:
        return f"❌ **Bus Analysis Error:** {analysis_result['error']}"
    
    # Format the response header with contingency info if present
    case_header = f"Case {analysis_result['case_id']}"
    if analysis_result.get('contingency_id') is not None:
        case_header += f", Contingency {analysis_result['contingency_id']}"
    
    # Build HTML table for summary statistics
    summary_table = f"""
<div style="margin: 15px 0;">
    <h3 style="color: #2196F3; margin-bottom: 10px;">⚡ Bus Analysis for {case_header}</h3>
    
    <h4 style="color: #FF9800; margin: 15px 0 10px 0;">📊 Summary Statistics</h4>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px;">
        <tr style="background-color: #f5f5f5;">
            <th style="padding: 10px; text-align: left; border: 1px solid #ddd; font-weight: 600;">Metric</th>
            <th style="padding: 10px; text-align: right; border: 1px solid #ddd; font-weight: 600;">Value</th>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">Total Buses Analyzed</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{analysis_result['total_buses']}</td>
        </tr>
        <tr style="background-color: #fafafa;">
            <td style="padding: 8px; border: 1px solid #ddd;">Voltage Range</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{analysis_result['voltage_stats']['min_voltage']:.4f} - {analysis_result['voltage_stats']['max_voltage']:.4f} p.u.</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">Average Voltage</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{analysis_result['voltage_stats']['avg_voltage']:.4f} p.u.</td>
        </tr>
        <tr style="background-color: #fafafa;">
            <td style="padding: 8px; border: 1px solid #ddd;">Low Voltage Buses (&lt;0.95 p.u.)</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: right; color: {'red' if analysis_result['voltage_stats']['low_voltage_count'] > 0 else 'green'}; font-weight: bold;">{analysis_result['voltage_stats']['low_voltage_count']}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">High Voltage Buses (&gt;1.05 p.u.)</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: right; color: {'red' if analysis_result['voltage_stats']['high_voltage_count'] > 0 else 'green'}; font-weight: bold;">{analysis_result['voltage_stats']['high_voltage_count']}</td>
        </tr>
        <tr style="background-color: #fafafa;">
            <td style="padding: 8px; border: 1px solid #ddd;">Total Generation</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{analysis_result['voltage_stats']['total_generation']:.2f} MW</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">Total Load</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{analysis_result['voltage_stats']['total_load']:.2f} MW</td>
        </tr>
    </table>
</div>
"""
    
    # Add details for up to 10 buses, prioritizing problematic ones
    bus_data = analysis_result['bus_data']
    problematic_buses = [b for b in bus_data if b['voltage_status'] != 'Normal' and b['voltage_status'] != 'Optimal']
    normal_buses = [b for b in bus_data if b['voltage_status'] == 'Normal' or b['voltage_status'] == 'Optimal']
    
    selected_buses = problematic_buses[:7]  # Show up to 7 problematic buses
    if len(selected_buses) < 10:
        selected_buses.extend(normal_buses[:10-len(selected_buses)])  # Fill with normal buses
    
    # Build HTML table for voltage profile
    voltage_profile_table = """
<div style="margin: 15px 0;">
    <h4 style="color: #4CAF50; margin: 15px 0 10px 0;">🔌 Voltage Profile Analysis</h4>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px;">
        <tr style="background-color: #f5f5f5;">
            <th style="padding: 10px; text-align: center; border: 1px solid #ddd; font-weight: 600;">Status</th>
            <th style="padding: 10px; text-align: center; border: 1px solid #ddd; font-weight: 600;">Bus #</th>
            <th style="padding: 10px; text-align: center; border: 1px solid #ddd; font-weight: 600;">Voltage (p.u.)</th>
            <th style="padding: 10px; text-align: center; border: 1px solid #ddd; font-weight: 600;">Status</th>
            <th style="padding: 10px; text-align: right; border: 1px solid #ddd; font-weight: 600;">Generation/Load</th>
        </tr>
"""
    
    for idx, bus in enumerate(selected_buses[:10]):  # Limit to 10 buses total
        status_icon = "🔴" if "Critical" in bus['voltage_status'] else "🟠" if "Low" in bus['voltage_status'] or "High" in bus['voltage_status'] else "🟢"
        gen_load = f"{bus['PG']:.1f} MW" if bus['PG'] > 0 else f"{bus['PD']:.1f} MW" if bus['PD'] > 0 else "—"
        gen_load_type = "Gen:" if bus['PG'] > 0 else "Load:" if bus['PD'] > 0 else ""
        bg_color = "#fafafa" if idx % 2 == 1 else "white"
        
        voltage_profile_table += f"""
        <tr style="background-color: {bg_color};">
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-size: 16px;">{status_icon}</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-weight: bold;">{int(bus['BUS_NUMBER'])}</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-family: monospace;">{bus['VM']:.4f}</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{bus['voltage_status']}</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: right;"><span style="color: #666; font-size: 12px;">{gen_load_type}</span> {gen_load}</td>
        </tr>
"""
    
    voltage_profile_table += """
    </table>
</div>
"""
    
    # Build recommendations section
    recommendations = []
    if analysis_result['voltage_stats']['low_voltage_count'] > 0:
        recommendations.append("Consider reactive power support for low voltage areas")
    if analysis_result['voltage_stats']['high_voltage_count'] > 0:
        recommendations.append("Evaluate reactive power absorption for high voltage areas")
    if analysis_result['voltage_stats']['std_voltage'] > 0.03:
        recommendations.append("Voltage profile has high variability; consider voltage regulation strategies")
    
    recommendations_html = ""
    if recommendations:
        recommendations_html = """
<div style="margin: 15px 0;">
    <h4 style="color: #9C27B0; margin: 15px 0 10px 0;">💡 Recommendations</h4>
    <ul style="margin: 0; padding-left: 20px;">
"""
        for rec in recommendations:
            recommendations_html += f"        <li style=\"margin: 5px 0;\">{rec}</li>\n"
        recommendations_html += """    </ul>
</div>
"""
    
    response = summary_table + voltage_profile_table + recommendations_html
    
    return response

def generate_branch_analysis_response(analysis_result):
    """Generate a detailed response for branch analysis"""
    if 'error' in analysis_result:
        return f'<div style="color: red; padding: 10px; margin: 10px 0;">❌ <strong>Branch Analysis Error:</strong> {analysis_result["error"]}</div>'
    
    # Format the response header with contingency info if present
    case_header = f"Case {analysis_result['case_id']}"
    if analysis_result.get('contingency_id') is not None:
        case_header += f", Contingency {analysis_result['contingency_id']}"
    
    # Build HTML table for summary statistics
    summary_table = f"""
<div style="margin: 15px 0;">
    <h3 style="color: #2196F3; margin-bottom: 10px;">⚡ Branch Analysis for {case_header}</h3>
    
    <h4 style="color: #FF9800; margin: 15px 0 10px 0;">📊 Summary Statistics</h4>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px;">
        <tr style="background-color: #f5f5f5;">
            <th style="padding: 10px; text-align: left; border: 1px solid #ddd; font-weight: 600;">Metric</th>
            <th style="padding: 10px; text-align: right; border: 1px solid #ddd; font-weight: 600;">Value</th>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">Total Branches Analyzed</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{analysis_result['total_branches']}</td>
        </tr>
        <tr style="background-color: #fafafa;">
            <td style="padding: 8px; border: 1px solid #ddd;">Loading Range</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{analysis_result['loading_stats']['min_loading']:.1f}% - {analysis_result['loading_stats']['max_loading']:.1f}%</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">Average Loading</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{analysis_result['loading_stats']['avg_loading']:.1f}%</td>
        </tr>
        <tr style="background-color: #fafafa;">
            <td style="padding: 8px; border: 1px solid #ddd;">Overloaded Branches (&gt;100%)</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: right; color: {'red' if analysis_result['loading_stats']['overloaded_count'] > 0 else 'green'}; font-weight: bold;">{analysis_result['loading_stats']['overloaded_count']}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">Highly Loaded Branches (80-100%)</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: right; color: {'orange' if analysis_result['loading_stats']['highly_loaded_count'] > 0 else 'green'}; font-weight: bold;">{analysis_result['loading_stats']['highly_loaded_count']}</td>
        </tr>
        <tr style="background-color: #fafafa;">
            <td style="padding: 8px; border: 1px solid #ddd;">Total Active Power Flow</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{analysis_result['loading_stats']['total_mw_flow']:.2f} MW</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">Total Reactive Power Flow</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{analysis_result['loading_stats']['total_mvar_flow']:.2f} MVAR</td>
        </tr>
    </table>
</div>
"""
    
    # Add details for up to 10 branches, prioritizing overloaded ones
    branch_data = analysis_result['branch_data']
    overloaded = [b for b in branch_data if b['loading_percent'] > 100]
    highly_loaded = [b for b in branch_data if 80 < b['loading_percent'] <= 100]
    normal = [b for b in branch_data if b['loading_percent'] <= 80]
    
    selected_branches = overloaded[:5]  # Show up to 5 overloaded branches
    if len(selected_branches) < 10:
        selected_branches.extend(highly_loaded[:min(5, 10-len(selected_branches))])  # Add highly loaded
    if len(selected_branches) < 10:
        selected_branches.extend(normal[:10-len(selected_branches)])  # Fill with normal branches
    
    # Build HTML table for critical branches
    branches_table = """
<div style="margin: 15px 0;">
    <h4 style="color: #F44336; margin: 15px 0 10px 0;">⚡ Critical Branches</h4>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px;">
        <tr style="background-color: #f5f5f5;">
            <th style="padding: 10px; text-align: center; border: 1px solid #ddd; font-weight: 600;">Status</th>
            <th style="padding: 10px; text-align: center; border: 1px solid #ddd; font-weight: 600;">From Bus</th>
            <th style="padding: 10px; text-align: center; border: 1px solid #ddd; font-weight: 600;">To Bus</th>
            <th style="padding: 10px; text-align: center; border: 1px solid #ddd; font-weight: 600;">Loading (%)</th>
            <th style="padding: 10px; text-align: right; border: 1px solid #ddd; font-weight: 600;">Active Power (MW)</th>
            <th style="padding: 10px; text-align: right; border: 1px solid #ddd; font-weight: 600;">Reactive Power (MVAR)</th>
        </tr>
"""
    
    for idx, branch in enumerate(selected_branches[:10]):  # Limit to 10 branches total
        status_icon = "🔴" if branch['loading_percent'] > 100 else "🟠" if branch['loading_percent'] > 80 else "🟢"
        bg_color = "#fafafa" if idx % 2 == 1 else "white"
        loading_color = "red" if branch['loading_percent'] > 100 else "orange" if branch['loading_percent'] > 80 else "green"
        
        branches_table += f"""
        <tr style="background-color: {bg_color};">
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-size: 16px;">{status_icon}</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-weight: bold;">{int(branch['From_Bus'])}</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-weight: bold;">{int(branch['To_Bus'])}</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-family: monospace; color: {loading_color}; font-weight: bold;">{branch['loading_percent']:.1f}%</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{branch['PF']:.2f}</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{branch['QF']:.2f}</td>
        </tr>
"""
    
    branches_table += """
    </table>
</div>
"""
    
    # Build recommendations section
    recommendations = []
    if analysis_result['loading_stats']['overloaded_count'] > 0:
        recommendations.append("Urgent: Address overloaded lines to prevent thermal violations")
        recommendations.append("Consider generation redispatch or load management to relieve overloads")
    if analysis_result['loading_stats']['highly_loaded_count'] > 3:
        recommendations.append("Monitor highly loaded branches for potential issues during contingencies")
    if analysis_result['loading_stats']['underutilized_count'] > analysis_result['total_branches'] / 3:
        recommendations.append("System may have underutilized capacity; evaluate network optimization")
    
    recommendations_html = ""
    if recommendations:
        recommendations_html = """
<div style="margin: 15px 0;">
    <h4 style="color: #9C27B0; margin: 15px 0 10px 0;">💡 Recommendations</h4>
    <ul style="margin: 0; padding-left: 20px;">
"""
        for rec in recommendations:
            recommendations_html += f"        <li style=\"margin: 5px 0;\">{rec}</li>\n"
        recommendations_html += """    </ul>
</div>
"""
    
    response = summary_table + branches_table + recommendations_html
    
    return response

def extract_case_and_entity_info(message):
    """
    Extract case ID and entity information (bus or branch) from user message.
    Returns a dictionary with case_id, contingency_id, entity information, and query type.
    """
    import re
    
    result = {
        'case_id': 0,  # Default case ID
        'contingency_id': None,  # Default to None (means base case)
        'entity_type': None,  # 'bus' or 'branch'
        'entity_ids': [],  # List of bus numbers or branch specs
        'query_type': None  # 'voltage', 'loading', 'status', etc.
    }

    # Extract case ID - pattern like "case 5" or "case-5"
    case_matches = re.findall(r'case[\s-]*(\d+)', message.lower())
    if case_matches:
        result['case_id'] = int(case_matches[0])
        
    # Check for contingency references
    contingency_keywords = ['contingency', 'outage', 'failure', 'contingent']
    if any(keyword in message.lower() for keyword in contingency_keywords):
        # Look for explicit contingency ID like "contingency 3" or "outage 5"
        contingency_matches = re.findall(r'(?:contingency|outage|failure)[\s-]*(\d+)', message.lower())
        if contingency_matches:
            result['contingency_id'] = int(contingency_matches[0])
        else:
            # If no specific contingency ID, look for second number which might be contingency ID
            all_numbers = re.findall(r'\b(\d+)\b', message)
            if len(all_numbers) >= 2 and int(all_numbers[0]) == result['case_id']:
                result['contingency_id'] = int(all_numbers[1])    # Determine query type based on keywords
    message_lower = message.lower()
    if any(word in message_lower for word in ['voltage', 'volt', 'pu', 'p.u.', 'kv']):
        result['query_type'] = 'voltage'
    elif any(word in message_lower for word in ['load', 'loading', 'mva', 'mw', 'overload']):
        result['query_type'] = 'loading'
    elif any(word in message_lower for word in ['status', 'condition', 'state', 'health']):
        result['query_type'] = 'status'
    elif any(word in message_lower for word in ['generation', 'generator', 'generators', 'gen', 'redispatch', 'dispatch']):
        result['query_type'] = 'generation'
        # Check for SLR vs DLR comparison
        if ('slr' in message_lower and 'dlr' in message_lower) or ('compare' in message_lower and ('slr' in message_lower or 'dlr' in message_lower)):
            result['comparison_type'] = 'slr_vs_dlr'

    # Check if the message is about bus analysis
    bus_keywords = ['bus', 'buses', 'node']
    voltage_status_keywords = ['voltage status', 'voltage level', 'bus voltage']
    if (any(keyword in message_lower for keyword in bus_keywords) or 
        any(keyword in message_lower for keyword in voltage_status_keywords) or
        result['query_type'] == 'voltage'):
        result['entity_type'] = 'bus'
        # Extract bus numbers - patterns like "bus 5", "buses 1, 2, 3" or just numbers
        bus_matches = re.findall(r'bus(?:es)?[\s]*(\d+)', message_lower)
        if bus_matches:
            result['entity_ids'] = [int(bus) for bus in bus_matches]
        else:
            # Try to find just numbers after detecting it's a bus analysis
            all_numbers = re.findall(r'\b(\d+)\b', message)
            if all_numbers:
                # Filter out the case ID if it was found
                if case_matches:
                    # Make sure we don't treat case IDs as bus numbers
                    result['entity_ids'] = [int(n) for n in all_numbers if int(n) != result['case_id']]
    
    # Check if the message is about branch analysis
    branch_keywords = ['branch', 'line', 'branches', 'lines', 'transmission', 'flow']
    if any(keyword in message.lower() for keyword in branch_keywords) and not result['entity_type']:
        result['entity_type'] = 'branch'
        # Extract branch specifications like "line 5-10" or "branch from 5 to 10"
        branch_matches = re.findall(r'(?:branch|line)[\s]*(\d+)[\s-]+(?:to)?[\s]*(\d+)', message.lower())
        if branch_matches:
            result['entity_ids'] = [{'from_bus': int(from_bus), 'to_bus': int(to_bus)} 
                                   for from_bus, to_bus in branch_matches]
    
    # Check if the message is about generator analysis
    generator_keywords = ['generator', 'generators', 'gen', 'generation', 'redispatch', 'dispatch']
    if (any(keyword in message.lower() for keyword in generator_keywords) and not result['entity_type']) or result['query_type'] == 'generation':
        result['entity_type'] = 'generator'
        # Extract generator bus numbers - patterns like "generator at bus 5", "generators 1, 2, 3"
        gen_bus_matches = re.findall(r'generator(?:s)?[\s]*(?:at)?[\s]*(?:bus)?[\s]*(\d+)', message.lower())
        if gen_bus_matches:
            result['entity_ids'] = [int(bus) for bus in gen_bus_matches]
        else:
            # If no specific generators mentioned, we'll analyze all generators for that case
            pass
    
    return result
    
def perform_generator_analysis(case_id, contingency_id=None, generator_ids=None, comparison_type=None):
    """
    Perform detailed analysis on generators for a specific case and contingency.
    
    Args:
        case_id: The ID of the base case
        contingency_id: The ID of the contingency (None for base case only)
        generator_ids: List of generator bus numbers to filter by (optional)
        comparison_type: Optional comparison type ('slr_vs_dlr' for comparing SLR and DLR)
    
    Returns:
        Dictionary with analysis results
    """
    from generator_analysis import analyze_generators
    
    # Delegate the analysis to our specialized module
    return analyze_generators(case_id, contingency_id, comparison_type, generator_ids)

def generate_generator_analysis_response(analysis_result):
    """Generate a detailed response for generator analysis results"""
    if analysis_result.get('error'):
        return f"Error in generator analysis: {analysis_result['error']}"
    
    slr_data = analysis_result.get('slr_data')
    dlr_data = analysis_result.get('dlr_data')
    stats = analysis_result.get('stats', {})
    comparison = analysis_result.get('comparison')
    
    # Basic analysis response for SLR data
    slr_stats = stats.get('slr', {})
    total_gens = slr_stats.get('total_generators', 0)
    redispatched = slr_stats.get('num_redispatched', 0)
    total_initial = slr_stats.get('total_initial_generation', 0)
    total_new = slr_stats.get('total_new_generation', 0)
    
    response = f"Generator Analysis: {total_gens} generators found, with {redispatched} redispatched.\n\n"
    response += f"Total initial generation: {total_initial:.2f} MW\n"
    response += f"Total new generation: {total_new:.2f} MW\n"
    response += f"Net generation change: {total_new - total_initial:.2f} MW\n"
    
    if redispatched > 0:
        max_increase = slr_stats.get('max_increase', 0)
        max_decrease = slr_stats.get('max_decrease', 0)
        
        response += "\nRedispatch Summary:\n"
        response += f"- Largest increase: {max_increase:.2f} MW\n"
        response += f"- Largest decrease: {max_decrease:.2f} MW\n"
        
        # Find the top redispatched generators
        if slr_data is not None and not slr_data.empty:
            # Sort by absolute change
            top_changes = slr_data.loc[slr_data['IS_REDISPATCHED'] == 1].sort_values(by='GEN_DELTA', key=abs, ascending=False)
            if len(top_changes) > 0:
                response += "\nMost significant generator changes:\n"
                for idx, row in top_changes.head(3).iterrows():
                    bus = row['BUS_NUMBER']
                    delta = row['GEN_DELTA']
                    pct = row['GEN_PERCENT_CHANGE']
                    direction = "increased" if delta > 0 else "decreased"
                    response += f"- Generator at bus {bus}: {direction} by {abs(delta):.2f} MW ({abs(pct):.1f}%)\n"
    
    # Add SLR vs DLR comparison if available
    if comparison and dlr_data is not None:
        dlr_stats = stats.get('dlr', {})
        dlr_redispatched = dlr_stats.get('num_redispatched', 0)
        dlr_total_new = dlr_stats.get('total_new_generation', 0)
        
        diff_stats = comparison.get('diff_stats', {})
        diff_count = diff_stats.get('different_dispatch_count', 0)
        
        response += "\n\nSLR vs DLR Comparison:\n"
        response += f"- SLR redispatched {redispatched} generators\n"
        response += f"- DLR redispatched {dlr_redispatched} generators\n"
        response += f"- {diff_count} generators have different dispatch between SLR and DLR\n"
        
        gen_diff = diff_stats.get('total_generation_diff', 0)
        if abs(gen_diff) > 0.1:  # Only show if there's a meaningful difference
            response += f"- DLR total generation is {abs(gen_diff):.2f} MW {'higher' if gen_diff > 0 else 'lower'} than SLR\n"
        
        # Show which method required more redispatch
        redispatch_diff = diff_stats.get('dlr_redispatch_difference', 0)
        if redispatch_diff > 0:
            more_method = "DLR" if diff_stats.get('dlr_more_redispatch', False) else "SLR"
            response += f"- {more_method} required {redispatch_diff} more generator redispatches\n"
        
        # Show which method had more total generation change
        gen_change_diff = diff_stats.get('dlr_gen_change_vs_slr', 0)
        if abs(gen_change_diff) > 0.1:
            more_change = "DLR" if gen_change_diff > 0 else "SLR"
            response += f"- {more_change} had {abs(gen_change_diff):.2f} MW more total generation adjustment\n"
    
    return response
