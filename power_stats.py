"""
Advanced Statistical Analysis Module for Power System Data

This module provides comprehensive functions to perform statistical analysis on power system data
from both the network graph and the database directly, with advanced modeling and prediction capabilities.
"""

import pandas as pd
import numpy as np
import sqlite3
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from scipy import stats
import scipy.cluster.hierarchy as hcluster
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.metrics import silhouette_score, calinski_harabasz_score
import plotly.figure_factory as ff
from matplotlib import pyplot as plt
import seaborn as sns
from scipy.interpolate import interp1d
from scipy.optimize import curve_fit
from sklearn.ensemble import RandomForestRegressor
from sklearn.neighbors import LocalOutlierFactor
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import logging
from datetime import datetime, timedelta
from io import BytesIO
import base64

# Configure logging for advanced analysis
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_stats(db_path, base_case_id=42, contingency_case_id=1):
    """
    Get statistical data from the database for the given case IDs
    
    Args:
        db_path (str): Path to the SQLite database
        base_case_id (int): Base case ID to analyze
        contingency_case_id (int): Contingency case ID to analyze
        
    Returns:
        dict: Dictionary containing various statistical analyses
    """
    results = {}
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        
        # Get base case statistics
        base_buses = pd.read_sql_query(f"SELECT * FROM BaseBusData WHERE base_case_id = {base_case_id}", conn)
        base_branches = pd.read_sql_query(f"SELECT * FROM BaseBranchData WHERE base_case_id = {base_case_id}", conn)
        
        # Get contingency case statistics
        cont_buses = pd.read_sql_query(
            f"SELECT * FROM ContingencyBusData WHERE base_case_id = {base_case_id} AND contingency_case_id = {contingency_case_id}", 
            conn
        )
        cont_branches = pd.read_sql_query(
            f"SELECT * FROM ContingencyBranchData WHERE base_case_id = {base_case_id} AND contingency_case_id = {contingency_case_id}", 
            conn
        )
        
        # Get SLR data if available
        try:
            slr_buses = pd.read_sql_query(
                f"SELECT * FROM SLR_Buses WHERE base_case_id = {base_case_id} AND contingency_case_id = {contingency_case_id}", 
                conn
            )
            slr_branches = pd.read_sql_query(
                f"SELECT * FROM SLR_Branches WHERE base_case_id = {base_case_id} AND contingency_case_id = {contingency_case_id}", 
                conn
            )
            has_slr = True
        except:
            has_slr = False
        
        # Get DLR data if available
        try:
            dlr_buses = pd.read_sql_query(
                f"SELECT * FROM DLR_Buses WHERE base_case_id = {base_case_id} AND contingency_case_id = {contingency_case_id}", 
                conn
            )
            dlr_branches = pd.read_sql_query(
                f"SELECT * FROM DLR_Branches WHERE base_case_id = {base_case_id} AND contingency_case_id = {contingency_case_id}", 
                conn
            )
            has_dlr = True
        except:
            has_dlr = False
            
        # Basic statistics
        results['bus_count'] = len(base_buses)
        results['branch_count'] = len(base_branches)
        
        # Calculate voltage statistics
        voltage_stats = {
            'base': base_buses['Vm'].describe().to_dict(),
            'contingency': cont_buses['Vm'].describe().to_dict() if not cont_buses.empty else None
        }
        
        if has_slr:
            voltage_stats['slr'] = slr_buses['Vm'].describe().to_dict()
        
        if has_dlr:
            voltage_stats['dlr'] = dlr_buses['Vm'].describe().to_dict()
            
        results['voltage_stats'] = voltage_stats
        
        # Calculate loading statistics
        if not base_branches.empty and 'loading' in base_branches.columns:
            base_loading = base_branches['loading']
        else:
            # Calculate loading if not directly available
            base_loading = base_branches['MVA'] / base_branches['Limit'] * 100 if 'MVA' in base_branches.columns and 'Limit' in base_branches.columns else None
        
        if not cont_branches.empty and 'loading' in cont_branches.columns:
            cont_loading = cont_branches['loading']
        else:
            # Calculate loading if not directly available
            cont_loading = cont_branches['MVA'] / cont_branches['Limit'] * 100 if 'MVA' in cont_branches.columns and 'Limit' in cont_branches.columns else None
            
        loading_stats = {
            'base': base_loading.describe().to_dict() if base_loading is not None else None,
            'contingency': cont_loading.describe().to_dict() if cont_loading is not None else None
        }
        
        if has_slr:
            if 'loading' in slr_branches.columns:
                slr_loading = slr_branches['loading']
            else:
                slr_loading = slr_branches['MVA'] / slr_branches['Limit'] * 100 if 'MVA' in slr_branches.columns and 'Limit' in slr_branches.columns else None
            loading_stats['slr'] = slr_loading.describe().to_dict() if slr_loading is not None else None
            
        if has_dlr:
            if 'loading' in dlr_branches.columns:
                dlr_loading = dlr_branches['loading']
            else:
                dlr_loading = dlr_branches['MVA'] / dlr_branches['Limit'] * 100 if 'MVA' in dlr_branches.columns and 'Limit' in dlr_branches.columns else None
            loading_stats['dlr'] = dlr_loading.describe().to_dict() if dlr_loading is not None else None
            
        results['loading_stats'] = loading_stats
        
        # Generator and load statistics
        gen_stats = {
            'base': base_buses[base_buses['Type'] != 1]['Pg'].sum(),
            'contingency': cont_buses[cont_buses['Type'] != 1]['Pg'].sum() if not cont_buses.empty else None
        }
        
        load_stats = {
            'base': base_buses['Pd'].sum(),
            'contingency': cont_buses['Pd'].sum() if not cont_buses.empty else None
        }
        
        if has_slr:
            gen_stats['slr'] = slr_buses[slr_buses['Type'] != 1]['Pg'].sum() if not slr_buses.empty else None
            load_stats['slr'] = slr_buses['Pd'].sum() if not slr_buses.empty else None
            
        if has_dlr:
            gen_stats['dlr'] = dlr_buses[dlr_buses['Type'] != 1]['Pg'].sum() if not dlr_buses.empty else None
            load_stats['dlr'] = dlr_buses['Pd'].sum() if not dlr_buses.empty else None
            
        results['gen_stats'] = gen_stats
        results['load_stats'] = load_stats
        
        # If DLR and SLR data are available, compare the benefits
        if has_dlr and has_slr:
            try:
                # Compare loading relief
                slr_max_loading = slr_loading.max() if slr_loading is not None else None
                dlr_max_loading = dlr_loading.max() if dlr_loading is not None else None
                
                if slr_max_loading is not None and dlr_max_loading is not None:
                    results['dlr_benefit'] = {
                        'max_loading_reduction': slr_max_loading - dlr_max_loading,
                        'percent_improvement': (slr_max_loading - dlr_max_loading) / slr_max_loading * 100 if slr_max_loading > 0 else 0
                    }
                    
                # Compare overloaded branches
                if slr_loading is not None and dlr_loading is not None:
                    slr_overloads = (slr_loading > 100).sum()
                    dlr_overloads = (dlr_loading > 100).sum()
                    results['overload_comparison'] = {
                        'slr_overloaded_branches': int(slr_overloads),
                        'dlr_overloaded_branches': int(dlr_overloads),
                        'overloads_prevented': int(slr_overloads - dlr_overloads)
                    }
            except:
                pass
                
        conn.close()
        
        # Add timestamps for reference
        results['base_case_id'] = base_case_id
        results['contingency_case_id'] = contingency_case_id
        results['has_slr'] = has_slr
        results['has_dlr'] = has_dlr
        
    except Exception as e:
        results['error'] = str(e)
        
    return results

def get_graph_stats(graph):
    """
    Get statistical data from a NetworkX graph
    
    Args:
        graph (nx.Graph): NetworkX graph object
        
    Returns:
        dict: Dictionary containing graph statistics
    """
    if not graph or not isinstance(graph, nx.Graph):
        return {'error': 'Invalid graph object'}
        
    stats = {}
    
    # Basic graph topology statistics
    stats['node_count'] = graph.number_of_nodes()
    stats['edge_count'] = graph.number_of_edges()
    stats['density'] = nx.density(graph)
    
    # Component analysis
    components = list(nx.connected_components(graph))
    stats['connected_components'] = len(components)
    
    if len(components) > 0:
        largest_cc = max(components, key=len)
        stats['largest_component_size'] = len(largest_cc)
        stats['largest_component_percentage'] = len(largest_cc) / stats['node_count'] * 100
    
    # Centrality measures (computationally expensive, so limit to moderate sized graphs)
    if stats['node_count'] <= 500:  # Only calculate for smaller graphs
        try:
            # Degree statistics
            degrees = [d for _, d in graph.degree()]
            stats['degree_stats'] = {
                'min': min(degrees),
                'max': max(degrees),
                'mean': sum(degrees) / len(degrees),
                'median': sorted(degrees)[len(degrees) // 2]
            }
            
            # Top nodes by degree centrality
            degree_centrality = nx.degree_centrality(graph)
            top_nodes = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:5]
            stats['top_central_nodes'] = [{'node': node, 'centrality': value} for node, value in top_nodes]
            
            # Path statistics for connected graphs
            if stats['connected_components'] == 1:
                # Expensive calculation, only do on very small graphs
                if stats['node_count'] <= 100:  
                    try:
                        diameter = nx.diameter(graph)
                        avg_path = nx.average_shortest_path_length(graph)
                        stats['diameter'] = diameter
                        stats['average_path_length'] = avg_path
                    except:
                        # Graph might not be connected or other issues
                        pass
        except Exception as e:
            stats['centrality_error'] = str(e)
    
    # Node attribute statistics if available
    if graph.nodes and len(graph.nodes) > 0:
        node = list(graph.nodes)[0]
        node_data = graph.nodes[node]
        
        if node_data:
            # Check for voltage attributes
            if 'voltage' in node_data:
                voltages = [graph.nodes[n]['voltage'] for n in graph.nodes if 'voltage' in graph.nodes[n]]
                if voltages:
                    stats['voltage_mean'] = sum(voltages) / len(voltages)
                    stats['voltage_std'] = np.std(voltages) if len(voltages) > 1 else 0
                    stats['voltage_min'] = min(voltages)
                    stats['voltage_max'] = max(voltages)
            
    # Edge attribute statistics if available
    if graph.edges and len(graph.edges) > 0:
        edge = list(graph.edges)[0]
        edge_data = graph.edges[edge]
        
        if edge_data:
            # Check for loading attributes
            if 'loading' in edge_data:
                loadings = [graph.edges[e]['loading'] for e in graph.edges if 'loading' in graph.edges[e]]
                if loadings:
                    stats['loading_mean'] = sum(loadings) / len(loadings)
                    stats['loading_std'] = np.std(loadings) if len(loadings) > 1 else 0
                    stats['loading_min'] = min(loadings)
                    stats['loading_max'] = max(loadings)
                    stats['overloaded_branches'] = sum(1 for load in loadings if load > 100)
                    stats['overloaded_percentage'] = stats['overloaded_branches'] / len(loadings) * 100
            
    return stats

def generate_comparison_plot(db_stats):
    """
    Generate a comparison plot between different scenarios based on database statistics
    
    Args:
        db_stats (dict): Dictionary of database statistics from get_database_stats()
        
    Returns:
        go.Figure: Plotly figure object
    """
    # Create a figure with subplots
    fig = make_subplots(
        rows=2, 
        cols=2,
        subplot_titles=(
            "Voltage Distribution", 
            "Branch Loading Comparison", 
            "Generation and Load", 
            "Overloaded Branch Count"
        )
    )
    
    scenarios = ['base', 'contingency']
    if db_stats.get('has_slr', False):
        scenarios.append('slr')
    if db_stats.get('has_dlr', False):
        scenarios.append('dlr')
    
    colors = {
        'base': 'blue',
        'contingency': 'red',
        'slr': 'green',
        'dlr': 'purple'
    }
    
    # 1. Voltage Distribution Plot
    voltage_data = []
    for scenario in scenarios:
        if scenario in db_stats.get('voltage_stats', {}) and db_stats['voltage_stats'][scenario]:
            stats = db_stats['voltage_stats'][scenario]
            voltage_data.append({
                'scenario': scenario.upper(),
                'min': stats['min'],
                'mean': stats['mean'] if 'mean' in stats else stats['50%'],
                'max': stats['max']
            })
    
    if voltage_data:
        for item in voltage_data:
            fig.add_trace(
                go.Bar(
                    name=item['scenario'],
                    x=['Min', 'Mean', 'Max'],
                    y=[item['min'], item['mean'], item['max']],
                    marker_color=colors[item['scenario'].lower()]
                ),
                row=1, col=1
            )
    
    # 2. Branch Loading Comparison
    loading_data = []
    for scenario in scenarios:
        if scenario in db_stats.get('loading_stats', {}) and db_stats['loading_stats'][scenario]:
            stats = db_stats['loading_stats'][scenario]
            loading_data.append({
                'scenario': scenario.upper(),
                'min': stats['min'],
                'mean': stats['mean'] if 'mean' in stats else stats['50%'],
                'max': stats['max']
            })
    
    if loading_data:
        for item in loading_data:
            fig.add_trace(
                go.Bar(
                    name=item['scenario'],
                    x=['Min', 'Mean', 'Max'],
                    y=[item['min'], item['mean'], item['max']],
                    marker_color=colors[item['scenario'].lower()]
                ),
                row=1, col=2
            )
    
    # 3. Generation and Load
    if db_stats.get('gen_stats') and db_stats.get('load_stats'):
        gen_data = []
        load_data = []
        
        for scenario in scenarios:
            if scenario in db_stats['gen_stats'] and db_stats['gen_stats'][scenario] is not None:
                gen_data.append({
                    'scenario': scenario.upper(),
                    'value': db_stats['gen_stats'][scenario]
                })
            
            if scenario in db_stats['load_stats'] and db_stats['load_stats'][scenario] is not None:
                load_data.append({
                    'scenario': scenario.upper(),
                    'value': db_stats['load_stats'][scenario]
                })
        
        if gen_data:
            fig.add_trace(
                go.Bar(
                    name='Generation',
                    x=[item['scenario'] for item in gen_data],
                    y=[item['value'] for item in gen_data],
                    marker_color='darkblue'
                ),
                row=2, col=1
            )
        
        if load_data:
            fig.add_trace(
                go.Bar(
                    name='Load',
                    x=[item['scenario'] for item in load_data],
                    y=[item['value'] for item in load_data],
                    marker_color='darkred'
                ),
                row=2, col=1
            )
    
    # 4. Overloaded Branch Comparison
    if db_stats.get('overload_comparison'):
        overload_data = db_stats['overload_comparison']
        
        fig.add_trace(
            go.Bar(
                x=['SLR', 'DLR'],
                y=[overload_data['slr_overloaded_branches'], overload_data['dlr_overloaded_branches']],
                marker_color=['green', 'purple']
            ),
            row=2, col=2
        )
        
        # Add annotation for improvement
        if overload_data['slr_overloaded_branches'] > 0:
            improvement = (overload_data['slr_overloaded_branches'] - overload_data['dlr_overloaded_branches']) / overload_data['slr_overloaded_branches'] * 100
            fig.add_annotation(
                x=0.5,
                y=0.5,
                text=f"{improvement:.1f}% Reduction",
                showarrow=False,
                font=dict(size=14),
                xref="x3 domain",
                yref="y3 domain",
            )
    
    # Update layout
    fig.update_layout(
        title_text=f"Power System Statistical Analysis (Base Case {db_stats['base_case_id']}, Contingency {db_stats['contingency_case_id']})",
        height=600,
        width=900,
        showlegend=False
    )
    
    return fig

def generate_graph_plot(graph_stats, title="Network Graph Statistics"):
    """
    Generate a visualization of graph statistics
    
    Args:
        graph_stats (dict): Dictionary of graph statistics from get_graph_stats()
        title (str): Title for the plot
        
    Returns:
        go.Figure: Plotly figure object
    """
    # Create a figure with subplots
    fig = make_subplots(
        rows=2, 
        cols=2,
        subplot_titles=(
            "Graph Structure", 
            "Degree Distribution", 
            "Top Central Nodes", 
            "Loading Distribution"
        ),
        specs=[
            [{"type": "domain"}, {"type": "xy"}],
            [{"type": "xy"}, {"type": "xy"}]
        ]
    )
    
    # 1. Graph Structure (Pie Chart)
    structure_labels = ['Nodes', 'Edges']
    structure_values = [graph_stats.get('node_count', 0), graph_stats.get('edge_count', 0)]
    
    fig.add_trace(
        go.Pie(
            labels=structure_labels,
            values=structure_values,
            hole=0.4
        ),
        row=1, col=1
    )
    
    # 2. Degree Distribution
    if 'degree_stats' in graph_stats:
        degree_stats = graph_stats['degree_stats']
        
        fig.add_trace(
            go.Bar(
                x=['Min', 'Median', 'Mean', 'Max'],
                y=[
                    degree_stats['min'], 
                    degree_stats['median'], 
                    degree_stats['mean'], 
                    degree_stats['max']
                ]
            ),
            row=1, col=2
        )
    
    # 3. Top Central Nodes
    if 'top_central_nodes' in graph_stats:
        top_nodes = graph_stats['top_central_nodes']
        
        fig.add_trace(
            go.Bar(
                x=[str(item['node']) for item in top_nodes],
                y=[item['centrality'] for item in top_nodes],
                text=[f"Node {item['node']}" for item in top_nodes],
                textposition='auto'
            ),
            row=2, col=1
        )
    
    # 4. Loading Distribution if available
    if 'loading_mean' in graph_stats:
        fig.add_trace(
            go.Bar(
                x=['Min', 'Mean', 'Max'],
                y=[
                    graph_stats['loading_min'],
                    graph_stats['loading_mean'],
                    graph_stats['loading_max']
                ]
            ),
            row=2, col=2
        )
        
        # Add overloaded percentage as annotation
        if 'overloaded_percentage' in graph_stats:
            fig.add_annotation(
                x=2,
                y=graph_stats['loading_max'] * 0.9,
                text=f"{graph_stats['overloaded_percentage']:.1f}% Branches Overloaded",
                showarrow=False,
                font=dict(size=12, color='red'),
                row=2, col=2
            )
    
    # Update layout
    fig.update_layout(
        title_text=title,
        height=600,
        width=900,
        showlegend=False
    )
    
    return fig

def analyze_system_resilience(db_stats, graph_stats):
    """
    Analyze the power system's resilience based on statistics
    
    Args:
        db_stats (dict): Database statistics
        graph_stats (dict): Graph statistics
        
    Returns:
        html.Div: HTML components with resilience analysis
    """
    from dash import html, dcc
    
    # Initialize resilience analysis
    resilience = {
        'score': 0,
        'factors': [],
        'recommendations': []
    }
    
    # Check for connectivity
    if graph_stats.get('connected_components', 1) > 1:
        resilience['factors'].append({
            'name': 'System Fragmentation',
            'description': f"System has {graph_stats['connected_components']} isolated components",
            'impact': 'negative'
        })
        resilience['recommendations'].append("Improve connectivity between isolated system components")
    else:
        resilience['factors'].append({
            'name': 'System Connectivity',
            'description': "System is fully connected",
            'impact': 'positive'
        })
    
    # Check for overloaded branches
    if 'overloaded_percentage' in graph_stats:
        if graph_stats['overloaded_percentage'] > 0:
            resilience['factors'].append({
                'name': 'Branch Overloads',
                'description': f"{graph_stats['overloaded_percentage']:.1f}% of branches are overloaded",
                'impact': 'negative'
            })
            resilience['recommendations'].append("Address overloaded branches to improve system security")
    
    # Check for voltage issues in base case
    if db_stats.get('voltage_stats', {}).get('base'):
        v_stats = db_stats['voltage_stats']['base']
        if v_stats['min'] < 0.9 or v_stats['max'] > 1.1:
            resilience['factors'].append({
                'name': 'Voltage Violations',
                'description': f"Voltage range: {v_stats['min']:.3f} to {v_stats['max']:.3f} p.u.",
                'impact': 'negative'
            })
            resilience['recommendations'].append("Improve voltage profile through reactive power support")
    
    # Check for DLR benefits
    if db_stats.get('dlr_benefit'):
        benefit = db_stats['dlr_benefit']
        if benefit['percent_improvement'] > 10:
            resilience['factors'].append({
                'name': 'DLR Advantage',
                'description': f"DLR provides {benefit['percent_improvement']:.1f}% loading reduction",
                'impact': 'positive'
            })
            resilience['recommendations'].append("Implement DLR to increase system transfer capacity")
    
    # Check for network structure
    if 'degree_stats' in graph_stats:
        if graph_stats['degree_stats']['mean'] < 2.5:
            resilience['factors'].append({
                'name': 'Network Structure',
                'description': "Low average connectivity (radial-like structure)",
                'impact': 'negative'
            })
            resilience['recommendations'].append("Add strategic connections to improve network redundancy")
        else:
            resilience['factors'].append({
                'name': 'Network Structure',
                'description': "Good network mesh structure",
                'impact': 'positive'
            })
    
    # Calculate resilience score (0-100)
    positive_count = sum(1 for factor in resilience['factors'] if factor['impact'] == 'positive')
    negative_count = sum(1 for factor in resilience['factors'] if factor['impact'] == 'negative')
    total_factors = len(resilience['factors'])
    
    if total_factors > 0:
        resilience['score'] = int((positive_count / total_factors) * 100)
    
    # Add overall assessment
    if resilience['score'] >= 75:
        resilience['assessment'] = "High system resilience"
        assessment_color = "green"
    elif resilience['score'] >= 50:
        resilience['assessment'] = "Moderate system resilience"
        assessment_color = "orange"
    else:
        resilience['assessment'] = "Low system resilience - improvements needed"
        assessment_color = "red"
    
    # Create HTML components
    children = [
        html.H4("System Resilience Assessment"),
        html.Div([
            html.Div([
                html.H1(f"{resilience['score']}", style={"color": assessment_color}),
                html.P("Resilience Score", style={"fontSize": "14px"})
            ], className="text-center", style={"padding": "10px", "backgroundColor": "#f8f9fa", "borderRadius": "5px"}),
            html.H5(resilience['assessment'], style={"color": assessment_color, "marginTop": "20px"})
        ], className="text-center mb-4")
    ]
    
    # Add factors table
    factor_rows = []
    for factor in resilience['factors']:
        color = "green" if factor['impact'] == 'positive' else "red"
        icon = "✓" if factor['impact'] == 'positive' else "✗"
        
        factor_rows.append(html.Tr([
            html.Td([html.Span(icon, style={"color": color}), " ", factor['name']]),
            html.Td(factor['description']),
            html.Td(factor['impact'].capitalize(), style={"color": color})
        ]))
    
    if factor_rows:
        children.append(html.H5("Resilience Factors"))
        children.append(html.Table([
            html.Thead(
                html.Tr([
                    html.Th("Factor"),
                    html.Th("Description"),
                    html.Th("Impact")
                ])
            ),
            html.Tbody(factor_rows)
        ], className="table table-striped table-bordered"))
    
    # Add recommendations
    if resilience['recommendations']:
        children.append(html.H5("Recommendations", className="mt-4"))
        children.append(html.Ul([
            html.Li(rec) for rec in resilience['recommendations']
        ]))
    
    return html.Div(children)

# Add advanced analysis functions

def perform_advanced_clustering(data, n_clusters=3):
    """
    Perform advanced clustering on power system data
    
    Args:
        data (pd.DataFrame): DataFrame containing power system data
        n_clusters (int): Number of clusters to form
        
    Returns:
        dict: Clustering results and visualization
    """
    # Check if we have enough data
    if data is None or len(data) < n_clusters:
        return {"error": "Insufficient data for clustering"}
    
    try:
        # Select numerical columns and handle missing values
        numerical_data = data.select_dtypes(include=['number']).fillna(0)
        
        # Standardize data
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(numerical_data)
        
        # Perform PCA for dimensionality reduction
        pca = PCA(n_components=min(3, scaled_data.shape[1]))
        pca_data = pca.fit_transform(scaled_data)
        
        # Apply K-Means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(scaled_data)
        
        # Calculate silhouette score for clustering quality
        silhouette = silhouette_score(scaled_data, clusters) if len(set(clusters)) > 1 else 0
        
        # Create 3D visualization of clusters
        fig = px.scatter_3d(
            x=pca_data[:, 0],
            y=pca_data[:, 1] if pca_data.shape[1] > 1 else np.zeros(len(pca_data)),
            z=pca_data[:, 2] if pca_data.shape[1] > 2 else np.zeros(len(pca_data)),
            color=clusters,
            title=f"Power System Data Clustering (Silhouette Score: {silhouette:.3f})",
            labels={"x": "PC1", "y": "PC2", "z": "PC3"},
            color_continuous_scale=px.colors.qualitative.G10
        )
        
        # Analyze cluster characteristics
        cluster_stats = {}
        for i in range(n_clusters):
            cluster_data = numerical_data.iloc[clusters == i]
            cluster_stats[f"cluster_{i}"] = {
                "size": len(cluster_data),
                "percentage": len(cluster_data) / len(numerical_data) * 100,
                "mean": cluster_data.mean().to_dict(),
                "std": cluster_data.std().to_dict()
            }
        
        return {
            "clusters": clusters,
            "cluster_stats": cluster_stats,
            "silhouette_score": silhouette,
            "explained_variance": pca.explained_variance_ratio_.tolist(),
            "figure": fig
        }
        
    except Exception as e:
        return {"error": f"Clustering error: {str(e)}"}

def detect_anomalies(data, contamination=0.05):
    """
    Detect anomalies in power system data using Isolation Forest
    
    Args:
        data (pd.DataFrame): DataFrame containing power system data
        contamination (float): Expected proportion of anomalies
        
    Returns:
        dict: Anomaly detection results
    """
    if data is None or len(data) < 10:
        return {"error": "Insufficient data for anomaly detection"}
    
    try:
        # Select numerical columns and handle missing values
        numerical_data = data.select_dtypes(include=['number']).fillna(0)
        
        # Standardize data
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(numerical_data)
        
        # Apply Isolation Forest for anomaly detection
        iso_forest = IsolationForest(contamination=contamination, random_state=42)
        anomalies = iso_forest.fit_predict(scaled_data)
        
        # Convert predictions to binary anomaly indicators (1: normal, -1: anomaly)
        is_anomaly = anomalies == -1
        
        # Perform PCA for visualization
        pca = PCA(n_components=min(2, scaled_data.shape[1]))
        pca_data = pca.fit_transform(scaled_data)
        
        # Create visualization
        anomaly_fig = px.scatter(
            x=pca_data[:, 0],
            y=pca_data[:, 1] if pca_data.shape[1] > 1 else np.zeros(len(pca_data)),
            color=is_anomaly,
            title=f"Anomaly Detection in Power System Data ({sum(is_anomaly)} anomalies found)",
            labels={"x": "PC1", "y": "PC2", "color": "Is Anomaly"},
            color_discrete_sequence=["#00CC96", "#EF553B"]
        )
        
        # Extract anomaly statistics
        anomaly_indices = np.where(is_anomaly)[0]
        anomaly_data = numerical_data.iloc[anomaly_indices]
        
        # Calculate statistics for normal vs anomalous data
        normal_stats = numerical_data.iloc[~is_anomaly].describe().to_dict()
        anomaly_stats = anomaly_data.describe().to_dict() if not anomaly_data.empty else {}
        
        return {
            "anomaly_indices": anomaly_indices.tolist(),
            "anomaly_percentage": sum(is_anomaly) / len(is_anomaly) * 100,
            "normal_stats": normal_stats,
            "anomaly_stats": anomaly_stats,
            "figure": anomaly_fig
        }
        
    except Exception as e:
        return {"error": f"Anomaly detection error: {str(e)}"}

def perform_correlation_analysis(data):
    """
    Perform correlation analysis on power system data
    
    Args:
        data (pd.DataFrame): DataFrame containing power system data
        
    Returns:
        dict: Correlation analysis results
    """
    if data is None or data.empty:
        return {"error": "No data available for correlation analysis"}
    
    try:
        # Select numerical columns and handle missing values
        numerical_data = data.select_dtypes(include=['number']).fillna(0)
        
        # Calculate correlation matrix
        corr_matrix = numerical_data.corr()
        
        # Create heatmap
        corr_fig = px.imshow(
            corr_matrix,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="RdBu_r",
            title="Power System Parameter Correlation Matrix",
            zmin=-1, zmax=1
        )
        
        # Find strongest positive and negative correlations
        corr_pairs = []
        for i, col1 in enumerate(corr_matrix.columns):
            for j, col2 in enumerate(corr_matrix.columns):
                if i < j:  # Only look at upper triangle
                    corr_pairs.append((col1, col2, corr_matrix.loc[col1, col2]))
        
        # Sort by absolute correlation
        corr_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        
        # Get top correlations
        top_correlations = corr_pairs[:10]
        
        return {
            "correlation_matrix": corr_matrix.to_dict(),
            "top_correlations": top_correlations,
            "figure": corr_fig
        }
        
    except Exception as e:
        return {"error": f"Correlation analysis error: {str(e)}"}

def forecast_system_loading(data, forecast_hours=24):
    """
    Forecast system loading based on historical data
    
    Args:
        data (pd.DataFrame): DataFrame containing historical loading data
        forecast_hours (int): Number of hours to forecast
        
    Returns:
        dict: Forecasting results
    """
    if data is None or data.empty:
        return {"error": "No data available for forecasting"}
    
    try:
        # Assuming we have a time-series of loading values
        if 'loading' not in data.columns and 'LOAD_LEVEL' in data.columns:
            data['loading'] = data['LOAD_LEVEL']
        
        if 'loading' not in data.columns:
            return {"error": "No loading data found for forecasting"}
            
        # Use a simple moving average model for demonstration
        # In a real system, this would use more sophisticated time-series forecasting
        window_size = min(len(data) // 3, 5)
        
        if window_size < 2:
            # Not enough data for moving average
            # Use the mean with some random variation
            mean_loading = data['loading'].mean()
            forecast = [mean_loading + np.random.normal(0, mean_loading * 0.05) for _ in range(forecast_hours)]
        else:
            # Moving average with trend
            historical = data['loading'].values
            moving_avg = np.convolve(historical, np.ones(window_size)/window_size, mode='valid')
            
            # Calculate trend
            if len(moving_avg) >= 2:
                trend = (moving_avg[-1] - moving_avg[0]) / len(moving_avg)
            else:
                trend = 0
                
            # Generate forecast
            last_value = historical[-1]
            forecast = []
            for i in range(forecast_hours):
                next_val = last_value + trend + np.random.normal(0, historical.std() * 0.2)
                forecast.append(max(0, next_val))  # Ensure non-negative loading
                last_value = next_val
        
        # Create visualization
        time_points = list(range(len(data))) + list(range(len(data), len(data) + forecast_hours))
        values = list(data['loading']) + forecast
        
        forecast_fig = go.Figure()
        
        # Historical data
        forecast_fig.add_trace(
            go.Scatter(
                x=time_points[:len(data)],
                y=values[:len(data)],
                mode='lines+markers',
                name='Historical Data',
                line=dict(color='blue')
            )
        )
        
        # Forecast data
        forecast_fig.add_trace(
            go.Scatter(
                x=time_points[len(data):],
                y=values[len(data):],
                mode='lines+markers',
                name='Forecast',
                line=dict(color='red', dash='dash')
            )
        )
        
        forecast_fig.update_layout(
            title='System Loading Forecast',
            xaxis_title='Time Period',
            yaxis_title='Loading (%)',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        return {
            "forecast": forecast,
            "mean_forecast": np.mean(forecast),
            "max_forecast": np.max(forecast),
            "figure": forecast_fig
        }
        
    except Exception as e:
        return {"error": f"Forecasting error: {str(e)}"}

def advanced_system_assessment(db_stats, graph_stats):
    """
    Perform advanced system assessment using multiple metrics
    
    Args:
        db_stats (dict): Database statistics
        graph_stats (dict): Graph statistics
        
    Returns:
        dict: Advanced assessment results
    """
    results = {}
    
    try:
        # System stability assessment
        stability_score = 0
        stability_factors = []
        
        # Check voltage profile
        if db_stats.get('voltage_stats', {}).get('base'):
            v_stats = db_stats['voltage_stats']['base']
            v_range = v_stats['max'] - v_stats['min']
            
            if v_range < 0.1:
                stability_score += 30
                stability_factors.append({"factor": "Excellent voltage profile", "impact": "positive"})
            elif v_range < 0.2:
                stability_score += 20
                stability_factors.append({"factor": "Good voltage profile", "impact": "positive"})
            elif v_range > 0.3:
                stability_score -= 20
                stability_factors.append({"factor": "Poor voltage profile", "impact": "negative"})
        
        # Check network connectivity
        if graph_stats:
            # Assess graph connectivity
            if graph_stats.get('connected_components', 1) == 1:
                stability_score += 20
                stability_factors.append({"factor": "Fully connected network", "impact": "positive"})
            else:
                stability_score -= 20
                stability_factors.append({
                    "factor": f"Network has {graph_stats.get('connected_components')} isolated components",
                    "impact": "negative"
                })
                
            # Assess network redundancy using average node degree
            if 'degree_stats' in graph_stats:
                avg_degree = graph_stats['degree_stats'].get('mean', 0)
                if avg_degree >= 3:
                    stability_score += 25
                    stability_factors.append({"factor": f"High network redundancy (avg degree: {avg_degree:.2f})", "impact": "positive"})
                elif avg_degree >= 2:
                    stability_score += 10
                    stability_factors.append({"factor": f"Moderate network redundancy (avg degree: {avg_degree:.2f})", "impact": "positive"})
                else:
                    stability_score -= 15
                    stability_factors.append({"factor": f"Low network redundancy (avg degree: {avg_degree:.2f})", "impact": "negative"})
        
        # Check loading conditions
        if db_stats.get('loading_stats', {}).get('base'):
            l_stats = db_stats['loading_stats']['base']
            
            if l_stats['max'] > 95:
                stability_score -= 25
                stability_factors.append({"factor": f"Critical loading condition ({l_stats['max']:.1f}%)", "impact": "negative"})
            elif l_stats['max'] > 80:
                stability_score -= 10
                stability_factors.append({"factor": f"High loading condition ({l_stats['max']:.1f}%)", "impact": "negative"})
            else:
                stability_score += 15
                stability_factors.append({"factor": f"Safe loading condition ({l_stats['max']:.1f}%)", "impact": "positive"})
        
        # Check DLR benefit if available
        if db_stats.get('dlr_benefit'):
            benefit = db_stats['dlr_benefit']
            if benefit['percent_improvement'] > 15:
                stability_score += 15
                stability_factors.append({"factor": f"Significant DLR benefit ({benefit['percent_improvement']:.1f}%)", "impact": "positive"})
        
        # Calculate final stability score (0-100)
        stability_score = max(0, min(100, 50 + stability_score))
        
        # Reliability assessment
        reliability = calculate_reliability_indices(db_stats, graph_stats)
        
        # Congestion assessment
        congestion = calculate_congestion_indices(db_stats)
        
        # Generate gauge chart for visualization
        gauge_fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=stability_score,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "System Stability Score"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": get_color_by_score(stability_score)},
                "steps": [
                    {"range": [0, 40], "color": "red"},
                    {"range": [40, 75], "color": "orange"},
                    {"range": [75, 100], "color": "green"}
                ],
                "threshold": {
                    "line": {"color": "black", "width": 4},
                    "thickness": 0.75,
                    "value": 75
                }
            }
        ))
        
        # Compile results
        results = {
            "stability_score": stability_score,
            "stability_factors": stability_factors,
            "reliability": reliability,
            "congestion": congestion,
            "assessment_level": get_assessment_level(stability_score),
            "figure": gauge_fig
        }
        
    except Exception as e:
        results = {"error": f"Advanced assessment error: {str(e)}"}
    
    return results

def calculate_reliability_indices(db_stats, graph_stats):
    """Helper function to calculate reliability indices"""
    indices = {}
    
    # Simplified reliability calculations for demonstration
    # In a real system, this would use historical outage data and more complex calculations
    
    try:
        # Estimate SAIFI (System Average Interruption Frequency Index)
        # and SAIDI (System Average Interruption Duration Index)
        # based on network characteristics
        
        # Use graph statistics for estimation
        if graph_stats and 'degree_stats' in graph_stats:
            avg_degree = graph_stats['degree_stats'].get('mean', 0)
            
            # Higher connectivity generally means better reliability
            base_saifi = 2.0  # Average interruptions per customer per year
            base_saidi = 120  # Average minutes of interruption per customer per year
            
            # Adjust based on network characteristics
            connectivity_factor = min(1, max(0.5, avg_degree / 4))
            
            saifi = base_saifi * (1 - connectivity_factor * 0.5)
            saidi = base_saidi * (1 - connectivity_factor * 0.5)
            
            indices["saifi"] = saifi
            indices["saidi"] = saidi
            indices["caidi"] = saidi / saifi if saifi > 0 else 0  # Customer Average Interruption Duration Index
            
        # Energy Not Supplied (ENS) estimation
        if db_stats.get('load_stats', {}).get('base'):
            total_load = db_stats['load_stats']['base']
            
            # Estimate probability of interruption and typical duration
            interruption_prob = 0.01  # 1% chance per period
            avg_duration_hours = 2
            
            # Calculate expected energy not supplied
            ens = total_load * interruption_prob * avg_duration_hours
            indices["ens"] = ens
    except:
        # Fallback values if calculation fails
        indices = {
            "saifi": 1.5,
            "saidi": 100,
            "caidi": 66.7,
            "ens": 50
        }
        
    return indices

def calculate_congestion_indices(db_stats):
    """Helper function to calculate congestion indices"""
    indices = {}
    
    try:
        # Congestion calculation based on loading statistics
        if db_stats.get('loading_stats', {}).get('base'):
            l_stats = db_stats['loading_stats']['base']
            
            # Calculate congestion index based on loading distribution
            congestion_index = 0
            
            if l_stats.get('75%', 0) > 80:
                # Severe congestion - more than 25% of branches above 80% loading
                congestion_index = 3
            elif l_stats.get('max', 0) > 90:
                # High congestion - some branches near capacity
                congestion_index = 2
            elif l_stats.get('max', 0) > 75:
                # Moderate congestion
                congestion_index = 1
            
            indices["congestion_index"] = congestion_index
            indices["congestion_level"] = ["Low", "Moderate", "High", "Severe"][congestion_index]
            
            # Calculate LMP (Locational Marginal Price) variation estimation
            # In a real system, this would use actual LMP data
            # Here we estimate based on loading conditions
            lmp_variation = 0
            
            if l_stats.get('max', 0) > 95:
                lmp_variation = 30  # High price differences across the system
            elif l_stats.get('max', 0) > 85:
                lmp_variation = 20  # Moderate price differences
            elif l_stats.get('max', 0) > 75:
                lmp_variation = 10  # Small price differences
                
            indices["estimated_lmp_variation"] = lmp_variation
    except:
        # Fallback values
        indices = {
            "congestion_index": 1,
            "congestion_level": "Moderate",
            "estimated_lmp_variation": 15
        }
    
    return indices

def get_color_by_score(score):
    """Get color for gauge based on score"""
    if score >= 75:
        return "green"
    elif score >= 40:
        return "orange"
    else:
        return "red"

def get_assessment_level(score):
    """Get assessment level text based on score"""
    if score >= 85:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 50:
        return "Fair"
    elif score >= 30:
        return "Poor"
    else:
        return "Critical"

def format_statistical_summary(db_stats, graph_stats=None):
    """
    Format the statistical results into HTML components for display
    
    Args:
        db_stats (dict): Database statistics
        graph_stats (dict, optional): Graph statistics
        
    Returns:
        html.Div: Dash HTML component with formatted summary
    """
    from dash import html, dcc
    
    # Check for error in db_stats
    if db_stats.get('error'):
        return html.Div([
            html.H4("Error in Database Statistics"),
            html.P(f"An error occurred: {db_stats['error']}"),
            html.P("Please check your database connection and try again.")
        ])
    
    # System overview
    children = [
        html.H4("Power System Statistical Analysis"),
        html.Hr(),
        html.P([
            html.Strong("Base Case ID: "), f"{db_stats.get('base_case_id', 'N/A')}", html.Br(),
            html.Strong("Contingency Case ID: "), f"{db_stats.get('contingency_case_id', 'N/A')}", html.Br(),
            html.Strong("System Size: "), f"{db_stats.get('bus_count', 0)} buses, {db_stats.get('branch_count', 0)} branches"
        ])
    
    ]
    
    # Add voltage statistics
    if db_stats.get('voltage_stats'):
        voltage_table = html.Table([
            html.Thead(
                html.Tr([
                    html.Th("Scenario"), 
                    html.Th("Min"), 
                    html.Th("Mean"), 
                    html.Th("Max")
                ])
            ),
            html.Tbody([
                html.Tr([
                    html.Td(scenario.upper()),
                    html.Td(f"{stats['min']:.3f}"),
                    html.Td(f"{stats.get('mean', stats.get('50%', 0)):.3f}"),
                    html.Td(f"{stats['max']:.3f}")
                ]) for scenario, stats in db_stats['voltage_stats'].items() if stats
            ])
        ], className="table table-striped table-bordered")
        
        children.extend([
            html.H5("Voltage Statistics (p.u.)", className="mt-4"),
            voltage_table
        ])
    
    # Add loading statistics
    if db_stats.get('loading_stats'):
        loading_table = html.Table([
            html.Thead(
                html.Tr([
                    html.Th("Scenario"), 
                    html.Th("Min"), 
                    html.Th("Mean"), 
                    html.Th("Max")
                ])
            ),
            html.Tbody([
                html.Tr([
                    html.Td(scenario.upper()),
                    html.Td(f"{stats['min']:.1f}%"),
                    html.Td(f"{stats.get('mean', stats.get('50%', 0)):.1f}%"),
                    html.Td(f"{stats['max']:.1f}%")
                ]) for scenario, stats in db_stats['loading_stats'].items() if stats
            ])
        ], className="table table-striped table-bordered")
        
        children.extend([
            html.H5("Branch Loading Statistics (%)", className="mt-4"),
            loading_table
        ])
    
    # Add generation and load comparison
    if db_stats.get('gen_stats') and db_stats.get('load_stats'):
        gen_load_rows = []
        
        for scenario in ['base', 'contingency', 'slr', 'dlr']:
            if (scenario in db_stats['gen_stats'] and db_stats['gen_stats'][scenario] is not None and 
                scenario in db_stats['load_stats'] and db_stats['load_stats'][scenario] is not None):
                gen = db_stats['gen_stats'][scenario]
                load = db_stats['load_stats'][scenario]
                diff = gen - load
                
                gen_load_rows.append(html.Tr([
                    html.Td(scenario.upper()),
                    html.Td(f"{gen:.1f}"),
                    html.Td(f"{load:.1f}"),
                    html.Td(f"{diff:.1f}")
                ]))
        
        if gen_load_rows:
            gen_load_table = html.Table([
                html.Thead(
                    html.Tr([
                        html.Th("Scenario"), 
                        html.Th("Generation"), 
                        html.Th("Load"), 
                        html.Th("Difference")
                    ])
                ),
                html.Tbody(gen_load_rows)
            ], className="table table-striped table-bordered")
            
            children.extend([
                html.H5("Generation and Load (MW)", className="mt-4"),
                gen_load_table
            ])
    
    # Add DLR benefit analysis
    if db_stats.get('dlr_benefit'):
        benefit = db_stats['dlr_benefit']
        children.extend([
            html.H5("DLR Benefit Analysis", className="mt-4"),
            html.Ul([
                html.Li(f"Maximum loading reduction: {benefit['max_loading_reduction']:.1f}%"),
                html.Li(f"Percent improvement: {benefit['percent_improvement']:.1f}%")
            ])
        ])
    
    # Add overloaded branch comparison
    if db_stats.get('overload_comparison'):
        overload = db_stats['overload_comparison']
        overload_items = [
            html.Li(f"SLR overloaded branches: {overload['slr_overloaded_branches']}"),
            html.Li(f"DLR overloaded branches: {overload['dlr_overloaded_branches']}"),
            html.Li(f"Overloads prevented by DLR: {overload['overloads_prevented']}")
        ]
        
        if overload['slr_overloaded_branches'] > 0:
            percent_reduction = (overload['slr_overloaded_branches'] - overload['dlr_overloaded_branches']) / overload['slr_overloaded_branches'] * 100
            overload_items.append(html.Li(f"Percent reduction: {percent_reduction:.1f}%"))
        
        children.extend([
            html.H5("Overloaded Branch Analysis", className="mt-4"),
            html.Ul(overload_items)
        ])
    
    # Add graph statistics if available
    if graph_stats and not graph_stats.get('error'):
        children.extend([
            html.H4("Network Graph Statistics", className="mt-4"),
            html.Hr(),
            html.Ul([
                html.Li(f"Node count: {graph_stats.get('node_count')}"),
                html.Li(f"Edge count: {graph_stats.get('edge_count')}"),
                html.Li(f"Graph density: {graph_stats.get('density', 0):.4f}")
            ])
        ])
        
        if 'connected_components' in graph_stats:
            component_items = [
                html.Li(f"Connected components: {graph_stats['connected_components']}")
            ]
            
            if graph_stats['connected_components'] > 0:
                component_items.append(html.Li(
                    f"Largest component size: {graph_stats.get('largest_component_size')} nodes " +
                    f"({graph_stats.get('largest_component_percentage', 0):.1f}% of network)"
                ))
            
            children.append(html.Ul(component_items))
        
        if 'degree_stats' in graph_stats:
            children.extend([
                html.H5("Node Degree Statistics", className="mt-4"),
                html.Ul([
                    html.Li(f"Minimum degree: {graph_stats['degree_stats']['min']}"),
                    html.Li(f"Maximum degree: {graph_stats['degree_stats']['max']}"),
                    html.Li(f"Mean degree: {graph_stats['degree_stats']['mean']:.2f}"),
                    html.Li(f"Median degree: {graph_stats['degree_stats']['median']}")
                ])
            ])
        
        if 'diameter' in graph_stats:
            children.append(html.Ul([
                html.Li(f"Network diameter: {graph_stats['diameter']}"),
                html.Li(f"Average path length: {graph_stats['average_path_length']:.2f}")
            ]))
        
        if 'loading_mean' in graph_stats:
            children.extend([
                html.H5("Branch Loading from Graph", className="mt-4"),
                html.Ul([
                    html.Li(f"Mean loading: {graph_stats['loading_mean']:.1f}%"),
                    html.Li(f"Max loading: {graph_stats['loading_max']:.1f}%"),
                    html.Li(
                        f"Overloaded branches: {graph_stats.get('overloaded_branches', 0)} " +
                        f"({graph_stats.get('overloaded_percentage', 0):.1f}% of branches)"
                    )
                ])
            ])
    
    return html.Div(children, className="statistics-summary")

def perform_advanced_analysis(db_path, graph=None, analysis_type="all"):
    """
    Perform advanced statistical analysis on power system data.
    
    Args:
        db_path (str): Path to the SQLite database
        graph (networkx.Graph, optional): Network graph if available
        analysis_type (str): Type of analysis to perform - options are:
            'clustering', 'anomaly', 'correlation', 'forecast', 
            'reliability', 'congestion', or 'all'
    
    Returns:
        dict: Dictionary containing advanced analysis results
    """
    results = {}
    
    try:
        # Load data from database
        conn = sqlite3.connect(db_path)
        
        # Load buses, branches, loads, and generators
        buses = pd.read_sql_query("SELECT * FROM buses", conn)
        branches = pd.read_sql_query("SELECT * FROM branches", conn)
        
        # Try to load additional tables if they exist
        try:
            loads = pd.read_sql_query("SELECT * FROM loads", conn)
        except:
            loads = pd.DataFrame()
        
        try:
            generators = pd.read_sql_query("SELECT * FROM generators", conn)
        except:
            generators = pd.DataFrame()
        
        # Build graph if not provided
        if graph is None:
            graph = build_network_graph(buses, branches)
        
        # Perform requested analysis
        if analysis_type in ['clustering', 'all']:
            results['clustering_analysis'] = perform_clustering_analysis(buses, branches)
        
        if analysis_type in ['anomaly', 'all']:
            results['anomaly_detection'] = perform_anomaly_detection(buses, branches, graph)
        
        if analysis_type in ['correlation', 'all']:
            results['correlation_analysis'] = perform_correlation_analysis(buses, branches, loads, generators, graph)
        
        if analysis_type in ['forecast', 'all']:
            results['load_forecast'] = perform_load_forecasting(loads)
        
        if analysis_type in ['reliability', 'all']:
            results['reliability_analysis'] = perform_reliability_analysis(graph, branches)
        
        if analysis_type in ['congestion', 'all']:
            results['congestion_analysis'] = perform_congestion_analysis(branches)
            
        conn.close()
        
    except Exception as e:
        logger.error(f"Error in advanced analysis: {str(e)}")
        results['error'] = str(e)
        
    return results

def build_network_graph(buses, branches):
    """Build a NetworkX graph from bus and branch data."""
    try:
        G = nx.Graph()
        
        # Add nodes from bus data
        for _, bus in buses.iterrows():
            G.add_node(bus['bus_id'], 
                       voltage=bus.get('voltage', 1.0), 
                       type=bus.get('type', 'PQ'),
                       area=bus.get('area', 1))
        
        # Add edges from branch data
        for _, branch in branches.iterrows():
            from_bus = branch['from_bus']
            to_bus = branch['to_bus']
            G.add_edge(from_bus, to_bus, 
                      resistance=branch.get('r', 0), 
                      reactance=branch.get('x', 0),
                      capacity=branch.get('rate_a', 0))
        
        return G
            
    except Exception as e:
        logger.error(f"Error building network graph: {str(e)}")
        return nx.Graph()  # Return empty graph on error

def perform_clustering_analysis(buses, branches):
    """Perform clustering analysis on bus data."""
    results = {}
    
    try:
        # Prepare data for clustering
        features = ['voltage', 'angle']
        if all(feat in buses.columns for feat in features):
            X = buses[features].copy()
        else:
            # Use available numeric columns if standard features aren't available
            numeric_cols = buses.select_dtypes(include=['float64', 'int64']).columns.tolist()
            X = buses[numeric_cols].copy()
        
        # Drop rows with missing values
        X = X.dropna()
        
        if len(X) < 2:
            return {"error": "Not enough valid data points for clustering"}
        
        # Standardize the data
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Determine optimal number of clusters using the silhouette method
        max_clusters = min(10, len(X) - 1)
        silhouette_scores = []
        
        for k in range(2, max_clusters + 1):
            kmeans = KMeans(n_clusters=k, random_state=42)
            cluster_labels = kmeans.fit_predict(X_scaled)
            silhouette_avg = silhouette_score(X_scaled, cluster_labels)
            silhouette_scores.append((k, silhouette_avg))
        
        # Get the optimal number of clusters
        optimal_k = max(silhouette_scores, key=lambda x: x[1])[0]
        
        # Perform K-means clustering with optimal k
        kmeans = KMeans(n_clusters=optimal_k, random_state=42)
        cluster_labels = kmeans.fit_predict(X_scaled)
        
        # Add cluster labels to the original data
        cluster_data = X.copy()
        cluster_data['cluster'] = cluster_labels
        
        # Compute cluster statistics
        cluster_stats = cluster_data.groupby('cluster').agg(['mean', 'std', 'count'])
        
        # Create cluster visualization using Plotly
        if X.shape[1] >= 2:
            fig = go.Figure()
            
            for i in range(optimal_k):
                cluster_points = cluster_data[cluster_data['cluster'] == i]
                fig.add_trace(go.Scatter(
                    x=cluster_points[X.columns[0]], 
                    y=cluster_points[X.columns[1]],
                    mode='markers',
                    name=f'Cluster {i}',
                    marker=dict(size=8)
                ))
            
            # Add cluster centroids
            centroids = kmeans.cluster_centers_
            fig.add_trace(go.Scatter(
                x=centroids[:, 0],
                y=centroids[:, 1],
                mode='markers',
                marker=dict(
                    color='black',
                    size=12,
                    symbol='x',
                    line=dict(width=2)
                ),
                name='Centroids'
            ))
            
            fig.update_layout(
                title=f'K-means Clustering (k={optimal_k})',
                xaxis_title=X.columns[0],
                yaxis_title=X.columns[1],
                legend_title='Clusters'
            )
            
            cluster_visualization = fig
        else:
            cluster_visualization = None
        
        # Store results
        results = {
            'optimal_clusters': optimal_k,
            'silhouette_scores': silhouette_scores,
            'cluster_statistics': cluster_stats.to_dict(),
            'cluster_visualization': cluster_visualization,
            'cluster_data': cluster_data.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Error in clustering analysis: {str(e)}")
        results['error'] = str(e)
        
    return results

def perform_anomaly_detection(buses, branches, graph=None):
    """Perform anomaly detection on power system data."""
    results = {}
    
    try:
        # Detect voltage anomalies
        if 'voltage' in buses.columns:
            voltage_data = buses[['bus_id', 'voltage']].dropna()
            
            # Isolation Forest for voltage anomalies
            if len(voltage_data) > 10:
                X = voltage_data[['voltage']].values
                iso_forest = IsolationForest(contamination=0.1, random_state=42)
                voltage_data['anomaly_score'] = iso_forest.fit_predict(X)
                voltage_data['is_anomaly'] = voltage_data['anomaly_score'] == -1
                
                # Extract anomalies
                voltage_anomalies = voltage_data[voltage_data['is_anomaly']]
                
                # Create visualization with Plotly
                fig = go.Figure()
                
                # Normal points
                fig.add_trace(go.Scatter(
                    x=voltage_data[~voltage_data['is_anomaly']]['bus_id'],
                    y=voltage_data[~voltage_data['is_anomaly']]['voltage'],
                    mode='markers',
                    marker=dict(
                        color='blue',
                        size=8,
                        opacity=0.7
                    ),
                    name='Normal'
                ))
                
                # Anomalies
                if len(voltage_anomalies) > 0:
                    fig.add_trace(go.Scatter(
                        x=voltage_anomalies['bus_id'],
                        y=voltage_anomalies['voltage'],
                        mode='markers',
                        marker=dict(
                            color='red',
                            size=12,
                            symbol='circle-open',
                            line=dict(width=2)
                        ),
                        name='Anomaly'
                    ))
                
                fig.update_layout(
                    title='Voltage Anomaly Detection',
                    xaxis_title='Bus ID',
                    yaxis_title='Voltage (pu)',
                    showlegend=True
                )
                
                voltage_anomaly_viz = fig
                
                # Store results
                results['voltage_anomalies'] = {
                    'num_anomalies': len(voltage_anomalies),
                    'anomaly_buses': voltage_anomalies['bus_id'].tolist(),
                    'visualization': voltage_anomaly_viz
                }
        
        # Detect loading anomalies
        if 'rate_a' in branches.columns and 'mva' in branches.columns:
            branch_data = branches.copy()
            branch_data['loading_percent'] = branch_data.apply(
                lambda x: (x['mva'] / x['rate_a'] * 100) if x['rate_a'] > 0 else 0, axis=1
            )
            branch_data = branch_data.replace([np.inf, -np.inf], np.nan).dropna(subset=['loading_percent'])
            
            if len(branch_data) > 10:
                # Use Local Outlier Factor for loading anomalies
                X = branch_data[['loading_percent']].values
                lof = LocalOutlierFactor(n_neighbors=5, contamination=0.1)
                branch_data['anomaly_score'] = lof.fit_predict(X)
                branch_data['is_anomaly'] = branch_data['anomaly_score'] == -1
                
                # Extract anomalies
                loading_anomalies = branch_data[branch_data['is_anomaly']]
                
                # Create visualization
                fig = go.Figure()
                
                # Normal points
                fig.add_trace(go.Scatter(
                    x=list(range(len(branch_data[~branch_data['is_anomaly']]))),
                    y=branch_data[~branch_data['is_anomaly']]['loading_percent'],
                    mode='markers',
                    marker=dict(
                        color='blue',
                        size=8,
                        opacity=0.7
                    ),
                    name='Normal'
                ))
                
                # Anomalies
                if len(loading_anomalies) > 0:
                    fig.add_trace(go.Scatter(
                        x=[branch_data.index.get_loc(i) for i in loading_anomalies.index],
                        y=loading_anomalies['loading_percent'],
                        mode='markers',
                        marker=dict(
                            color='red',
                            size=12,
                            symbol='circle-open',
                            line=dict(width=2)
                        ),
                        name='Anomaly'
                    ))
                
                fig.update_layout(
                    title='Line Loading Anomaly Detection',
                    xaxis_title='Branch Index',
                    yaxis_title='Loading (%)',
                    showlegend=True
                )
                
                loading_anomaly_viz = fig
                
                # Store results
                results['loading_anomalies'] = {
                    'num_anomalies': len(loading_anomalies),
                    'anomaly_branches': loading_anomalies[['from_bus', 'to_bus']].values.tolist(),
                    'visualization': loading_anomaly_viz
                }
        
    except Exception as e:
        logger.error(f"Error in anomaly detection: {str(e)}")
        results['error'] = str(e)
        
    return results

def perform_correlation_analysis(buses, branches, loads, generators, graph=None):
    """Perform correlation analysis on power system data."""
    results = {}
    
    try:
        # Create a combined dataframe for correlation analysis
        # First, get bus-specific data
        if not buses.empty and 'bus_id' in buses.columns:
            bus_data = buses.set_index('bus_id')
            
            # Aggregate load data by bus
            if not loads.empty and 'bus_id' in loads.columns and 'pd' in loads.columns:
                load_by_bus = loads.groupby('bus_id')['pd'].sum().rename('load_mw')
            else:
                load_by_bus = pd.Series(dtype='float64')
            
            # Aggregate generation data by bus
            if not generators.empty and 'bus_id' in generators.columns and 'pg' in generators.columns:
                gen_by_bus = generators.groupby('bus_id')['pg'].sum().rename('gen_mw')
            else:
                gen_by_bus = pd.Series(dtype='float64')
            
            # Calculate degree and centrality metrics
            if graph:
                degree_dict = dict(graph.degree())
                degree_series = pd.Series(degree_dict, name='degree')
                betweenness_dict = nx.betweenness_centrality(graph)
                betweenness_series = pd.Series(betweenness_dict, name='betweenness')
            else:
                degree_series = pd.Series(dtype='float64')
                betweenness_series = pd.Series(dtype='float64')
            
            # Combine all data
            corr_data = pd.concat([
                bus_data,
                load_by_bus,
                gen_by_bus,
                degree_series,
                betweenness_series
            ], axis=1)
            
            # Drop non-numeric columns
            corr_data = corr_data.select_dtypes(include=['float64', 'int64'])
            
            # Compute correlation matrix
            correlation_matrix = corr_data.corr()
            
            # Create heatmap visualization with Plotly
            fig = go.Figure(data=go.Heatmap(
                z=correlation_matrix.values,
                x=correlation_matrix.columns,
                y=correlation_matrix.columns,
                colorscale='RdBu_r',
                zmid=0,
                text=np.around(correlation_matrix.values, decimals=2),
                texttemplate='%{text:.2f}',
                textfont={"size": 10},
            ))
            
            fig.update_layout(
                title='Correlation Matrix of Power System Variables',
                width=800,
                height=800
            )
            
            correlation_viz = fig
            
            # Identify strongest correlations (excluding self-correlations)
            corr_pairs = []
            for i in range(len(correlation_matrix.columns)):
                for j in range(i+1, len(correlation_matrix.columns)):
                    col1 = correlation_matrix.columns[i]
                    col2 = correlation_matrix.columns[j]
                    corr_value = correlation_matrix.iloc[i, j]
                    corr_pairs.append((col1, col2, corr_value))
            
            # Sort by absolute correlation value
            corr_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
            
            # Get top correlations
            top_correlations = corr_pairs[:10]
            
            # Generate scatter plots for top correlations
            top_corr_viz = []
            
            if len(top_correlations) > 0:
                for col1, col2, corr_val in top_correlations[:5]:  # Limit to top 5 for visualization
                    scatter_fig = px.scatter(
                        corr_data, x=col1, y=col2,
                        title=f'Correlation between {col1} and {col2} (r={corr_val:.3f})',
                        trendline='ols'
                    )
                    
                    top_corr_viz.append({
                        'pair': (col1, col2),
                        'correlation': corr_val,
                        'visualization': scatter_fig
                    })
            
            # Store results
            results = {
                'correlation_matrix': correlation_matrix.to_dict(),
                'correlation_visualization': correlation_viz,
                'top_correlations': top_correlations,
                'top_correlation_visualizations': top_corr_viz
            }
        else:
            results['error'] = "Bus data unavailable or missing bus_id column"
        
    except Exception as e:
        logger.error(f"Error in correlation analysis: {str(e)}")
        results['error'] = str(e)
        
    return results

def perform_load_forecasting(loads):
    """Perform load forecasting using time series analysis."""
    results = {}
    
    try:
        # For this example, we'll simulate load data with a timestamp
        # In a real system, you would fetch this from your database
        
        # Create simulated historical load data (past 24 hours with hourly data)
        now = datetime.now()
        periods = 24
        timestamps = [now - timedelta(hours=i) for i in range(periods, 0, -1)]
        
        # Generate load values with a realistic pattern (daily cycle + random noise)
        base_load = 1000  # Base load in MW
        amplitude = 200   # Daily variation amplitude
        noise_level = 30  # Random noise level
        
        np.random.seed(42)  # For reproducibility
        
        # Create a daily pattern with peak in afternoon
        hour_of_day = [t.hour for t in timestamps]
        daily_pattern = [amplitude * np.sin(np.pi * (h - 6) / 12) for h in hour_of_day]
        
        # Add random noise
        noise = np.random.normal(0, noise_level, periods)
        
        # Combine into final load values
        load_values = [max(base_load + pattern + n, 0) for pattern, n in zip(daily_pattern, noise)]
        
        # Create dataframe
        load_history = pd.DataFrame({
            'timestamp': timestamps,
            'load_mw': load_values
        })
        
        # Forecast future load (next 24 hours)
        forecast_periods = 24
        
        # Train a simple time series model (linear regression with hour features)
        X = pd.DataFrame({
            'hour': [t.hour for t in load_history['timestamp']],
            'hour_sin': np.sin(2 * np.pi * np.array([t.hour for t in load_history['timestamp']]) / 24),
            'hour_cos': np.cos(2 * np.pi * np.array([t.hour for t in load_history['timestamp']]) / 24)
        })
        y = load_history['load_mw']
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Create future timestamps
        future_timestamps = [now + timedelta(hours=i) for i in range(1, forecast_periods + 1)]
        
        # Create features for future hours
        future_X = pd.DataFrame({
            'hour': [t.hour for t in future_timestamps],
            'hour_sin': np.sin(2 * np.pi * np.array([t.hour for t in future_timestamps]) / 24),
            'hour_cos': np.cos(2 * np.pi * np.array([t.hour for t in future_timestamps]) / 24)
        })
        
        # Make predictions
        future_y = model.predict(future_X)
        
        # Create forecast dataframe
        forecast_df = pd.DataFrame({
            'timestamp': future_timestamps,
            'forecasted_load': future_y
        })
        
        # Create visualization with Plotly
        fig = go.Figure()
        
        # Historical data
        fig.add_trace(go.Scatter(
            x=[t.strftime('%Y-%m-%d %H:%M') for t in load_history['timestamp']],
            y=load_history['load_mw'],
            mode='lines+markers',
            name='Historical Load',
            line=dict(color='blue')
        ))
        
        # Forecast
        fig.add_trace(go.Scatter(
            x=[t.strftime('%Y-%m-%d %H:%M') for t in forecast_df['timestamp']],
            y=forecast_df['forecasted_load'],
            mode='lines+markers',
            name='Forecast',
            line=dict(color='red', dash='dash')
        ))
        
        fig.update_layout(
            title='Load Forecast (Next 24 Hours)',
            xaxis_title='Time',
            yaxis_title='Load (MW)',
            xaxis=dict(tickangle=45),
            legend=dict(x=0.01, y=0.99),
            hovermode='x unified'
        )
        
        # Store forecast results
        results = {
            'load_history': load_history.to_dict(),
            'forecast_data': forecast_df.to_dict(),
            'forecast_visualization': fig,
            'forecast_periods': forecast_periods
        }
        
    except Exception as e:
        logger.error(f"Error in load forecasting: {str(e)}")
        results['error'] = str(e)
        
    return results

def perform_reliability_analysis(graph, branches):
    """Perform reliability analysis on the power system."""
    results = {}
    
    try:
        if not graph or len(graph) == 0:
            return {"error": "Network graph is required for reliability analysis"}
        
        # Create a copy of the graph for manipulation
        G = graph.copy()
        
        # Calculate basic reliability metrics
        
        # 1. Network connectivity
        connected = nx.is_connected(G)
        
        if connected:
            avg_path_length = nx.average_shortest_path_length(G)
        else:
            components = list(nx.connected_components(G))
            largest_cc = max(components, key=len)
            largest_cc_graph = G.subgraph(largest_cc).copy()
            avg_path_length = nx.average_shortest_path_length(largest_cc_graph)
        
        # 2. Edge betweenness centrality (identifies critical lines)
        edge_betweenness = nx.edge_betweenness_centrality(G)
        
        # Sort edges by betweenness
        sorted_edges = sorted(edge_betweenness.items(), key=lambda x: x[1], reverse=True)
        critical_lines = sorted_edges[:10]  # Top 10 critical lines
        
        # 3. N-1 contingency analysis
        n_minus_1_results = []
        
        # For each of the top critical lines, remove it and check connectivity
        for i, ((u, v), betweenness) in enumerate(critical_lines):
            if i >= 5:  # Limit to top 5 for computation time
                break
                
            # Remove edge
            G_temp = G.copy()
            G_temp.remove_edge(u, v)
            
            # Check if network is still connected
            still_connected = nx.is_connected(G_temp)
            
            # If not connected, count number of isolated nodes
            if not still_connected:
                components = list(nx.connected_components(G_temp))
                largest_component = max(components, key=len)
                isolated_nodes = len(G_temp) - len(largest_component)
            else:
                isolated_nodes = 0
            
            n_minus_1_results.append({
                'line': (u, v),
                'betweenness': betweenness,
                'network_still_connected': still_connected,
                'isolated_nodes': isolated_nodes
            })
        
        # 4. Create visualization of critical lines with Plotly
        pos = nx.spring_layout(G, seed=42)
        
        # Create edge trace
        edge_x = []
        edge_y = []
        edge_traces = []
        
        # Add edges with varying width based on betweenness
        for edge in G.edges():
            betweenness = edge_betweenness.get(edge, 0)
            
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            
            # Color coding for critical lines
            if edge in [e[0] for e in critical_lines[:5]]:
                color = 'red'
                width = 3
            else:
                color = 'gray'
                width = 1
            
            trace = go.Scatter(
                x=[x0, x1, None], 
                y=[y0, y1, None],
                line=dict(width=width, color=color),
                hoverinfo='none',
                mode='lines',
                showlegend=False
            )
            
            edge_traces.append(trace)
        
        # Create node trace
        node_x = []
        node_y = []
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers',
            hoverinfo='text',
            marker=dict(
                showscale=False,
                color='lightblue',
                size=10,
                line_width=2
            )
        )
        
        # Create figure
        fig = go.Figure(data=edge_traces + [node_trace],
                      layout=go.Layout(
                          title='Network Reliability Analysis - Critical Lines Highlighted',
                          showlegend=False,
                          hovermode='closest',
                          margin=dict(b=20, l=5, r=5, t=40),
                          xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                          yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                      ))
        
        # Store results
        results = {
            'network_connected': connected,
            'average_path_length': avg_path_length,
            'critical_lines': [(u, v, b) for ((u, v), b) in critical_lines],
            'n_minus_1_analysis': n_minus_1_results,
            'reliability_visualization': fig
        }
        
    except Exception as e:
        logger.error(f"Error in reliability analysis: {str(e)}")
        results['error'] = str(e)
        
    return results

def perform_congestion_analysis(branches):
    """Perform congestion analysis to identify bottlenecks in the system."""
    results = {}
    
    try:
        if branches.empty:
            return {"error": "Branch data is required for congestion analysis"}
            
        # Check if we have loading data
        if 'rate_a' in branches.columns and 'mva' in branches.columns:
            # Calculate loading percentages
            branch_data = branches.copy()
            branch_data['loading_percent'] = branch_data.apply(
                lambda x: (x['mva'] / x['rate_a'] * 100) if x['rate_a'] > 0 else 0, axis=1
            )
            branch_data = branch_data.replace([np.inf, -np.inf], np.nan).dropna(subset=['loading_percent'])
            
            # Identify congested lines (>80% loading)
            congestion_threshold = 80.0
            congested_lines = branch_data[branch_data['loading_percent'] > congestion_threshold]
            
            # Sort by loading percentage
            congested_lines = congested_lines.sort_values('loading_percent', ascending=False)
            
            # Calculate congestion statistics
            congestion_stats = {
                'total_branches': len(branch_data),
                'congested_branches': len(congested_lines),
                'congestion_percentage': len(congested_lines) / len(branch_data) * 100 if len(branch_data) > 0 else 0,
                'average_loading': branch_data['loading_percent'].mean(),
                'max_loading': branch_data['loading_percent'].max(),
                'min_loading': branch_data['loading_percent'].min(),
            }
            
            # Create loading histogram with Plotly
            fig = go.Figure()
            
            fig.add_trace(go.Histogram(
                x=branch_data['loading_percent'],
                nbinsx=20,
                marker_color='blue',
                opacity=0.7
            ))
            
            fig.add_shape(type="line",
                x0=congestion_threshold, y0=0,
                x1=congestion_threshold, y1=1,
                yref='paper',
                line=dict(color="red", width=2, dash="dash")
            )
            
            fig.update_layout(
                title='Distribution of Line Loadings',
                xaxis_title='Line Loading (%)',
                yaxis_title='Number of Lines',
                annotations=[
                    dict(
                        x=congestion_threshold,
                        y=1,
                        yref="paper",
                        text=f"Congestion Threshold ({congestion_threshold}%)",
                        showarrow=True,
                        arrowhead=2,
                        ax=50,
                        ay=-30
                    )
                ]
            )
            
            # Store results
            results = {
                'congestion_stats': congestion_stats,
                'congested_lines': congested_lines[['from_bus', 'to_bus', 'loading_percent']].to_dict('records'),
                'loading_histogram': fig
            }
        else:
            results = {
                'error': "Missing required data columns (rate_a or mva) for congestion analysis"
            }
            
    except Exception as e:
        logger.error(f"Error in congestion analysis: {str(e)}")
        results['error'] = str(e)
        
    return results

def fig_to_base64(fig):
    """Convert a matplotlib figure to a base64 string."""
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    
    img_buf = BytesIO()
    fig.savefig(img_buf, format='png')
    img_buf.seek(0)
    img_str = base64.b64encode(img_buf.read()).decode('utf-8')
    return img_str
    
def mpl_to_plotly(fig):
    """Convert a matplotlib figure to a plotly figure."""
    import plotly.io as pio
    
    # First convert matplotlib fig to a base64 image
    img_buf = BytesIO()
    fig.savefig(img_buf, format='png')
    img_buf.seek(0)
    
    # Then create a plotly figure with the image
    from plotly.graph_objs import Figure, Image
    import plotly.graph_objects as go
    
    # Create a plotly figure with the image
    fig = go.Figure()
    
    # Add image as a layout image
    fig.add_layout_image(
        dict(
            source=f"data:image/png;base64,{base64.b64encode(img_buf.read()).decode('utf-8')}",
            xref="paper", yref="paper",
            x=0, y=1,
            sizex=1, sizey=1,
            sizing="stretch",
            layer="below"
        )
    )
    
    fig.update_layout(
        width=800,
        height=600,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    return fig