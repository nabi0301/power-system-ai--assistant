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