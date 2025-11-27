def compare_cases(case_id1, case_id2):
    """Compare two power system cases and identify differences"""
    try:
        print(f"Comparing cases {case_id1} and {case_id2}")
        
        # Get detailed analysis for both cases
        analysis1 = perform_detailed_case_analysis(case_id1)
        analysis2 = perform_detailed_case_analysis(case_id2)
        
        if 'error' in analysis1 or 'error' in analysis2:
            return {'error': f"Error in case analysis: {analysis1.get('error', '')} {analysis2.get('error', '')}"}
        
        # Compare voltage metrics
        voltage_diff = {
            'avg_voltage_diff': analysis2['voltage_analysis']['avg_voltage'] - analysis1['voltage_analysis']['avg_voltage'],
            'max_voltage_diff': analysis2['voltage_analysis']['max_voltage'] - analysis1['voltage_analysis']['max_voltage'],
            'min_voltage_diff': analysis2['voltage_analysis']['min_voltage'] - analysis1['voltage_analysis']['min_voltage'],
            'voltage_std_diff': analysis2['voltage_analysis']['voltage_std'] - analysis1['voltage_analysis']['voltage_std'],
            'violations_diff': analysis2['voltage_analysis']['violations_total'] - analysis1['voltage_analysis']['violations_total'],
            'critical_violations_diff': (
                analysis2['voltage_analysis']['critical_high_count'] + analysis2['voltage_analysis']['critical_low_count'] -
                analysis1['voltage_analysis']['critical_high_count'] - analysis1['voltage_analysis']['critical_low_count']
            ),
            'vdi_diff': analysis2['voltage_analysis']['voltage_deviation_index'] - analysis1['voltage_analysis']['voltage_deviation_index']
        }
        
        # Compare loading metrics
        loading_diff = {
            'avg_loading_diff': analysis2['loading_analysis']['avg_loading'] - analysis1['loading_analysis']['avg_loading'],
            'max_loading_diff': analysis2['loading_analysis']['max_loading'] - analysis1['loading_analysis']['max_loading'],
            'overloaded_diff': analysis2['loading_analysis']['overloaded_count'] - analysis1['loading_analysis']['overloaded_count'],
            'critical_overloaded_diff': analysis2['loading_analysis']['critically_overloaded_count'] - analysis1['loading_analysis']['critically_overloaded_count'],
            'lui_diff': analysis2['loading_analysis']['line_utilization_index'] - analysis1['loading_analysis']['line_utilization_index'],
            'loi_diff': analysis2['loading_analysis']['line_overload_index'] - analysis1['loading_analysis']['line_overload_index']
        }
        
        # Find shared critical buses and branches
        # Find buses that are critical in both cases
        critical_buses_case1 = [bus['BUS_NUMBER'] for bus in analysis1['voltage_analysis']['critical_violation_buses']]
        critical_buses_case2 = [bus['BUS_NUMBER'] for bus in analysis2['voltage_analysis']['critical_violation_buses']]
        shared_critical_buses = list(set(critical_buses_case1) & set(critical_buses_case2))
        
        # Find branches that are critical in both cases
        critical_branches_case1 = [(branch['From_Bus'], branch['To_Bus']) for branch in analysis1['loading_analysis']['critical_branches']]
        critical_branches_case2 = [(branch['From_Bus'], branch['To_Bus']) for branch in analysis2['loading_analysis']['critical_branches']]
        shared_critical_branches = list(set(critical_branches_case1) & set(critical_branches_case2))
        
        # Analyze differences and create insights
        insights = []
        
        # Voltage insights
        if abs(voltage_diff['avg_voltage_diff']) > 0.01:
            direction = "increased" if voltage_diff['avg_voltage_diff'] > 0 else "decreased"
            insights.append(f"System voltage profile has {direction} by {abs(voltage_diff['avg_voltage_diff']):.3f} p.u. from Case {case_id1} to Case {case_id2}")
        
        if voltage_diff['violations_diff'] != 0:
            direction = "increased" if voltage_diff['violations_diff'] > 0 else "decreased"
            insights.append(f"Voltage violations have {direction} by {abs(voltage_diff['violations_diff'])} buses from Case {case_id1} to Case {case_id2}")
        
        if voltage_diff['vdi_diff'] > 1:
            insights.append(f"Voltage quality has degraded in Case {case_id2} compared to Case {case_id1}")
        elif voltage_diff['vdi_diff'] < -1:
            insights.append(f"Voltage quality has improved in Case {case_id2} compared to Case {case_id1}")
            
        # Loading insights
        if abs(loading_diff['avg_loading_diff']) > 5:
            direction = "increased" if loading_diff['avg_loading_diff'] > 0 else "decreased"
            insights.append(f"System loading has {direction} by {abs(loading_diff['avg_loading_diff']):.1f}% from Case {case_id1} to Case {case_id2}")
        
        if loading_diff['overloaded_diff'] != 0:
            direction = "increased" if loading_diff['overloaded_diff'] > 0 else "decreased"
            insights.append(f"Overloaded lines have {direction} by {abs(loading_diff['overloaded_diff'])} from Case {case_id1} to Case {case_id2}")
        
        if loading_diff['critical_overloaded_diff'] > 0:
            insights.append(f"WARNING: Critical overloads have increased by {loading_diff['critical_overloaded_diff']} lines in Case {case_id2}")
        elif loading_diff['critical_overloaded_diff'] < 0:
            insights.append(f"IMPROVEMENT: Critical overloads have decreased by {abs(loading_diff['critical_overloaded_diff'])} lines in Case {case_id2}")
        
        # Overall system status insights
        if voltage_diff['violations_diff'] < 0 and loading_diff['overloaded_diff'] < 0:
            insights.append(f"Case {case_id2} shows overall system improvement with fewer voltage and loading issues")
        elif voltage_diff['violations_diff'] > 0 and loading_diff['overloaded_diff'] > 0:
            insights.append(f"Case {case_id2} shows system degradation with more voltage and loading issues")
        
        # Persistent issues insights
        if shared_critical_buses:
            insights.append(f"Persistent voltage issues at buses {', '.join(map(str, shared_critical_buses[:5]))}{' and others' if len(shared_critical_buses) > 5 else ''}")
        
        if shared_critical_branches:
            branch_str = ', '.join([f"{from_bus}-{to_bus}" for from_bus, to_bus in shared_critical_branches[:5]])
            insights.append(f"Persistent overloading issues on lines {branch_str}{' and others' if len(shared_critical_branches) > 5 else ''}")
        
        # Return comparison results
        return {
            'case_id1': case_id1,
            'case_id2': case_id2,
            'voltage_comparison': voltage_diff,
            'loading_comparison': loading_diff,
            'shared_critical_buses': shared_critical_buses,
            'shared_critical_branches': shared_critical_branches,
            'insights': insights
        }
        
    except Exception as e:
        print(f"Case comparison error: {e}")
        return {'error': str(e)}

def generate_case_comparison_response(case_id1, case_id2):
    """Generate a comprehensive comparison between two cases"""
    comparison = compare_cases(case_id1, case_id2)
    
    if 'error' in comparison:
        return f"❌ **Case Comparison Error:** {comparison['error']}"
    
    response = f"""📊 **Case Comparison Analysis**

📋 **Comparison Information:**
• Base Case: {comparison['case_id1']}
• Comparison Case: {comparison['case_id2']}

⚡ **Voltage Comparison:**
• Average Voltage Change: {comparison['voltage_comparison']['avg_voltage_diff']:.3f} p.u.
• Voltage Range Change: Min {comparison['voltage_comparison']['min_voltage_diff']:.3f} p.u., Max {comparison['voltage_comparison']['max_voltage_diff']:.3f} p.u.
• Violation Change: {comparison['voltage_comparison']['violations_diff']} buses
• Critical Violation Change: {comparison['voltage_comparison']['critical_violations_diff']} buses
• Voltage Quality Index Change: {comparison['voltage_comparison']['vdi_diff']:.2f}%

📈 **Loading Comparison:**
• Average Loading Change: {comparison['loading_comparison']['avg_loading_diff']:.1f}%
• Maximum Loading Change: {comparison['loading_comparison']['max_loading_diff']:.1f}%
• Overloaded Lines Change: {comparison['loading_comparison']['overloaded_diff']}
• Critical Overloads Change: {comparison['loading_comparison']['critical_overloaded_diff']}
• Line Utilization Index Change: {comparison['loading_comparison']['lui_diff']:.1f}%
• Line Overload Index Change: {comparison['loading_comparison']['loi_diff']:.1f}%

🔄 **Shared Critical Elements:**
• Common Critical Buses: {len(comparison['shared_critical_buses'])}
• Common Critical Lines: {len(comparison['shared_critical_branches'])}
"""

    # Add key insights
    if comparison['insights']:
        response += "\n🧠 **Key Insights:**"
        for insight in comparison['insights']:
            response += f"\n• {insight}"
    
    # Add recommendations
    response += "\n\n💡 **Recommendations:**"
    
    # Generate case-specific recommendations
    if comparison['voltage_comparison']['vdi_diff'] > 0:
        response += "\n• Consider voltage regulation improvements in the comparison case"
    
    if comparison['loading_comparison']['overloaded_diff'] > 0:
        response += "\n• Investigate load redistribution options for the comparison case"
    
    if len(comparison['shared_critical_buses']) > 0:
        response += f"\n• Address persistent voltage issues at buses {', '.join(map(str, comparison['shared_critical_buses'][:3]))}"
    
    if len(comparison['shared_critical_branches']) > 0:
        branch_str = ', '.join([f"{from_bus}-{to_bus}" for from_bus, to_bus in comparison['shared_critical_branches'][:3]])
        response += f"\n• Consider line upgrades for persistently overloaded lines {branch_str}"
    
    if comparison['voltage_comparison']['violations_diff'] < 0 and comparison['loading_comparison']['overloaded_diff'] < 0:
        response += f"\n• Use Case {comparison['case_id2']} configuration as a model for system improvements"
    
    response += "\n\n🎯 **Available Actions:**"
    response += "\n• Request 'case analysis X' for detailed individual case assessment"
    response += "\n• Try 'smart analysis' for AI-powered insights on current visualization"
    response += "\n• Ask for 'pattern analysis' to detect anomalies across cases"
    
    return response