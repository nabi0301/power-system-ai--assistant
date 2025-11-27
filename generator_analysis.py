import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sqlite3
import numpy as np
from typing import List, Dict, Optional, Union, Tuple

def get_generator_data(base_case_id: int, contingency_id: Optional[int] = None, 
                      table_prefix: str = "SLR", bus_numbers: Optional[List[int]] = None) -> pd.DataFrame:
    """
    Retrieve generator data from the database for a specific case and contingency.
    
    Args:
        base_case_id: The ID of the base case
        contingency_id: The ID of the contingency (None for base case only)
        table_prefix: 'SLR' or 'DLR' to specify which type of data to retrieve
        bus_numbers: List of specific bus numbers to filter by (optional)
    
    Returns:
        DataFrame with generator data
    """
    try:
        conn = sqlite3.connect('data.db')
        
        # Build the WHERE clause
        where_clause = f"base_case_id = {base_case_id}"
        if contingency_id is not None:
            where_clause += f" AND contingency_case_id = {contingency_id}"
            
        # Filter by bus numbers if provided
        bus_filter = ""
        if bus_numbers and len(bus_numbers) > 0:
            bus_list = ', '.join(str(bus) for bus in bus_numbers)
            bus_filter = f" AND BUS_NUMBER IN ({bus_list})"
            
        # Execute the query
        query = f"""
        SELECT base_case_id, contingency_case_id, BUS_NUMBER, KV_LEVEL, 
               GEN_INI, GEN_NEW, GEN_ADJ,
               (GEN_NEW - GEN_INI) as GEN_DELTA,
               ((GEN_NEW - GEN_INI) / CASE WHEN GEN_INI = 0 THEN 1 ELSE GEN_INI END * 100) as GEN_PERCENT_CHANGE,
               CASE WHEN ABS(GEN_NEW - GEN_INI) > 1 THEN 1 ELSE 0 END as IS_REDISPATCHED
        FROM {table_prefix}_Generator 
        WHERE {where_clause}{bus_filter}
        ORDER BY BUS_NUMBER
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    except Exception as e:
        print(f"Error retrieving generator data: {e}")
        return pd.DataFrame()

def analyze_generators(base_case_id: int, contingency_id: Optional[int] = None, 
                       comparison_type: Optional[str] = None, 
                       bus_numbers: Optional[List[int]] = None) -> Dict:
    """
    Perform comprehensive generator analysis with optional SLR vs DLR comparison.
    
    Args:
        base_case_id: The ID of the base case
        contingency_id: The ID of the contingency (None for base case only)
        comparison_type: Optional comparison type ('slr_vs_dlr' for comparing SLR and DLR)
        bus_numbers: List of specific bus numbers to filter by (optional)
    
    Returns:
        Dictionary with analysis results
    """
    result = {
        'slr_data': None,
        'dlr_data': None,
        'comparison': None,
        'stats': {},
        'error': None
    }
    
    try:
        # Get SLR generator data
        slr_data = get_generator_data(base_case_id, contingency_id, "SLR", bus_numbers)
        
        # If no data found, return error
        if slr_data.empty:
            result['error'] = f"No generator data found for base case {base_case_id}"
            if contingency_id is not None:
                result['error'] += f", contingency {contingency_id}"
            return result
        
        result['slr_data'] = slr_data
        
        # Calculate SLR statistics
        result['stats']['slr'] = {
            'total_generators': len(slr_data),
            'total_initial_generation': slr_data['GEN_INI'].sum(),
            'total_new_generation': slr_data['GEN_NEW'].sum(),
            'num_redispatched': slr_data['IS_REDISPATCHED'].sum(),
            'max_increase': slr_data['GEN_DELTA'].max(),
            'max_decrease': slr_data['GEN_DELTA'].min(),
            'total_abs_change': slr_data['GEN_DELTA'].abs().sum(),
        }
        
        # If comparison is requested, get DLR data
        if comparison_type == 'slr_vs_dlr':
            dlr_data = get_generator_data(base_case_id, contingency_id, "DLR", bus_numbers)
            
            if not dlr_data.empty:
                result['dlr_data'] = dlr_data
                
                # Calculate DLR statistics
                result['stats']['dlr'] = {
                    'total_generators': len(dlr_data),
                    'total_initial_generation': dlr_data['GEN_INI'].sum(),
                    'total_new_generation': dlr_data['GEN_NEW'].sum(),
                    'num_redispatched': dlr_data['IS_REDISPATCHED'].sum(),
                    'max_increase': dlr_data['GEN_DELTA'].max(),
                    'max_decrease': dlr_data['GEN_DELTA'].min(),
                    'total_abs_change': dlr_data['GEN_DELTA'].abs().sum(),
                }
                
                # Compare SLR and DLR
                # Merge data on BUS_NUMBER for comparison
                merged = pd.merge(
                    slr_data, 
                    dlr_data, 
                    on='BUS_NUMBER', 
                    suffixes=('_SLR', '_DLR')
                )
                
                if not merged.empty:
                    # Calculate differences between SLR and DLR
                    merged['GEN_NEW_DIFF'] = merged['GEN_NEW_DLR'] - merged['GEN_NEW_SLR']
                    merged['GEN_ADJ_DIFF'] = merged['GEN_ADJ_DLR'] - merged['GEN_ADJ_SLR']
                    merged['GEN_DELTA_DIFF'] = merged['GEN_DELTA_DLR'] - merged['GEN_DELTA_SLR']
                    
                    # Find generators redispatched differently
                    merged['DISPATCH_DIFFERENCE'] = (merged['IS_REDISPATCHED_DLR'] != merged['IS_REDISPATCHED_SLR']).astype(int)
                    
                    result['comparison'] = {
                        'merged_data': merged,
                        'diff_stats': {
                            'total_generation_diff': (dlr_data['GEN_NEW'].sum() - slr_data['GEN_NEW'].sum()),
                            'different_dispatch_count': merged['DISPATCH_DIFFERENCE'].sum(),
                            'max_generation_diff': merged['GEN_NEW_DIFF'].abs().max(),
                            'dlr_more_redispatch': (result['stats']['dlr']['num_redispatched'] > result['stats']['slr']['num_redispatched']),
                            'dlr_redispatch_difference': abs(result['stats']['dlr']['num_redispatched'] - result['stats']['slr']['num_redispatched']),
                            'dlr_gen_change_vs_slr': (result['stats']['dlr']['total_abs_change'] - result['stats']['slr']['total_abs_change'])
                        }
                    }
        
        return result
        
    except Exception as e:
        result['error'] = f"Error in generator analysis: {str(e)}"
        return result

def create_generator_plot(analysis_result: Dict, show_redispatched: bool = False) -> go.Figure:
    """
    Create a generator analysis plot from the analysis results.
    
    Args:
        analysis_result: Dictionary with analysis results from analyze_generators()
        show_redispatched: If True, highlight redispatched generators
    
    Returns:
        Plotly Figure object
    """
    # If there's an error, return a figure with the error message
    if analysis_result.get('error'):
        fig = go.Figure()
        fig.add_annotation(text=analysis_result['error'], xref="paper", yref="paper", x=0.5, y=0.5)
        return fig
    
    # Get the data
    slr_data = analysis_result.get('slr_data')
    dlr_data = analysis_result.get('dlr_data')
    comparison = analysis_result.get('comparison')
    
    # If no data, return empty figure
    if slr_data is None:
        fig = go.Figure()
        fig.add_annotation(text="No generator data available", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig
    
    fig = go.Figure()
    
    if comparison and dlr_data is not None:
        # SLR vs DLR comparison mode
        bus_numbers = slr_data['BUS_NUMBER'].tolist()
        
        # SLR Initial generation
        fig.add_trace(go.Bar(
            x=bus_numbers,
            y=slr_data['GEN_INI'],
            name='SLR Initial',
            marker_color='lightblue'
        ))
        
        # SLR New generation
        redispatched_mask = slr_data['IS_REDISPATCHED'] == 1
        
        if show_redispatched:
            # Split into redispatched and non-redispatched for SLR
            fig.add_trace(go.Bar(
                x=slr_data.loc[~redispatched_mask, 'BUS_NUMBER'].tolist(),
                y=slr_data.loc[~redispatched_mask, 'GEN_NEW'].tolist(),
                name='SLR New (No Change)',
                marker_color='blue'
            ))
            
            fig.add_trace(go.Bar(
                x=slr_data.loc[redispatched_mask, 'BUS_NUMBER'].tolist(),
                y=slr_data.loc[redispatched_mask, 'GEN_NEW'].tolist(),
                name='SLR New (Redispatched)',
                marker_color='darkblue'
            ))
        else:
            fig.add_trace(go.Bar(
                x=bus_numbers,
                y=slr_data['GEN_NEW'],
                name='SLR New',
                marker_color='darkblue'
            ))
        
        # DLR Initial generation
        fig.add_trace(go.Bar(
            x=dlr_data['BUS_NUMBER'].tolist(),
            y=dlr_data['GEN_INI'],
            name='DLR Initial',
            marker_color='lightgreen'
        ))
        
        # DLR New generation
        dlr_redispatched_mask = dlr_data['IS_REDISPATCHED'] == 1
        
        if show_redispatched:
            # Split into redispatched and non-redispatched for DLR
            fig.add_trace(go.Bar(
                x=dlr_data.loc[~dlr_redispatched_mask, 'BUS_NUMBER'].tolist(),
                y=dlr_data.loc[~dlr_redispatched_mask, 'GEN_NEW'].tolist(),
                name='DLR New (No Change)',
                marker_color='green'
            ))
            
            fig.add_trace(go.Bar(
                x=dlr_data.loc[dlr_redispatched_mask, 'BUS_NUMBER'].tolist(),
                y=dlr_data.loc[dlr_redispatched_mask, 'GEN_NEW'].tolist(),
                name='DLR New (Redispatched)',
                marker_color='darkgreen'
            ))
        else:
            fig.add_trace(go.Bar(
                x=dlr_data['BUS_NUMBER'].tolist(),
                y=dlr_data['GEN_NEW'],
                name='DLR New',
                marker_color='darkgreen'
            ))
        
        title = f"Generator Analysis - SLR vs DLR Comparison ({len(slr_data)} units)"
        
    else:
        # SLR mode only
        bus_numbers = slr_data['BUS_NUMBER'].tolist()
        
        # Initial generation
        fig.add_trace(go.Bar(
            x=bus_numbers,
            y=slr_data['GEN_INI'],
            name='Initial Generation',
            marker_color='lightblue'
        ))
        
        # New generation
        redispatched_mask = slr_data['IS_REDISPATCHED'] == 1
        
        if show_redispatched:
            # Split into redispatched and non-redispatched
            fig.add_trace(go.Bar(
                x=slr_data.loc[~redispatched_mask, 'BUS_NUMBER'].tolist(),
                y=slr_data.loc[~redispatched_mask, 'GEN_NEW'].tolist(),
                name='New Generation (No Change)',
                marker_color='blue'
            ))
            
            fig.add_trace(go.Bar(
                x=slr_data.loc[redispatched_mask, 'BUS_NUMBER'].tolist(),
                y=slr_data.loc[redispatched_mask, 'GEN_NEW'].tolist(),
                name='New Generation (Redispatched)',
                marker_color='darkblue'
            ))
        else:
            fig.add_trace(go.Bar(
                x=bus_numbers,
                y=slr_data['GEN_NEW'],
                name='New Generation',
                marker_color='darkblue'
            ))
        
        title = f"Generator Analysis - {len(slr_data)} Units"
        if redispatched_mask.sum() > 0:
            title += f" ({redispatched_mask.sum()} Redispatched)"
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title="Bus Number",
        yaxis_title="Generation (MW)",
        height=600,
        barmode='group',
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    
    return fig

def create_generator_delta_plot(analysis_result: Dict, 
                               comparison_type: Optional[str] = None) -> go.Figure:
    """
    Create a generator delta plot showing generation changes.
    
    Args:
        analysis_result: Dictionary with analysis results from analyze_generators()
        comparison_type: Optional comparison type ('slr_vs_dlr' for comparing SLR and DLR)
    
    Returns:
        Plotly Figure object
    """
    # If there's an error, return a figure with the error message
    if analysis_result.get('error'):
        fig = go.Figure()
        fig.add_annotation(text=analysis_result['error'], xref="paper", yref="paper", x=0.5, y=0.5)
        return fig
    
    # Get the data
    slr_data = analysis_result.get('slr_data')
    dlr_data = analysis_result.get('dlr_data')
    comparison = analysis_result.get('comparison')
    
    # If no data, return empty figure
    if slr_data is None:
        fig = go.Figure()
        fig.add_annotation(text="No generator data available", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig
    
    fig = go.Figure()
    
    if comparison and dlr_data is not None and comparison_type == 'slr_vs_dlr':
        # SLR vs DLR comparison mode - show delta plot
        merged = comparison['merged_data']
        bus_numbers = merged['BUS_NUMBER'].tolist()
        
        # Add SLR delta
        fig.add_trace(go.Bar(
            x=bus_numbers,
            y=merged['GEN_DELTA_SLR'],
            name='SLR Generation Change',
            marker_color='blue'
        ))
        
        # Add DLR delta
        fig.add_trace(go.Bar(
            x=bus_numbers,
            y=merged['GEN_DELTA_DLR'],
            name='DLR Generation Change',
            marker_color='green'
        ))
        
        # Add difference line
        fig.add_trace(go.Scatter(
            x=bus_numbers,
            y=merged['GEN_DELTA_DIFF'],
            name='DLR-SLR Difference',
            mode='lines+markers',
            marker=dict(color='red'),
            line=dict(width=2)
        ))
        
        title = f"Generator Change Analysis - SLR vs DLR ({len(merged)} units)"
        
    else:
        # SLR mode only - show delta
        bus_numbers = slr_data['BUS_NUMBER'].tolist()
        deltas = slr_data['GEN_DELTA'].tolist()
        
        # Color bars based on positive or negative change
        colors = ['green' if d >= 0 else 'red' for d in deltas]
        
        fig.add_trace(go.Bar(
            x=bus_numbers,
            y=deltas,
            name='Generation Change (MW)',
            marker_color=colors
        ))
        
        title = f"Generator Change Analysis - {len(slr_data)} Units"
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title="Bus Number",
        yaxis_title="Generation Change (MW)",
        height=600,
        barmode='group',
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    
    # Add a horizontal line at y=0
    fig.add_shape(
        type="line",
        x0=min(bus_numbers) - 1,
        y0=0,
        x1=max(bus_numbers) + 1,
        y1=0,
        line=dict(color="black", width=1, dash="dash")
    )
    
    return fig