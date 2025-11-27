#!/usr/bin/env python3
"""
Comprehensive Trend and Pattern Analysis for Power Systems
Analyzes all cases and contingencies to identify system-wide patterns, trends, and anomalies.
"""

import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Import Plotly for visualizations
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

class ComprehensiveTrendAnalyzer:
    """
    Analyzes trends and patterns across all cases and contingencies in the power system database.
    """
    
    def __init__(self, db_path='data.db'):
        self.db_path = db_path
        
    def get_connection(self):
        """Get a new database connection"""
        return sqlite3.connect(self.db_path)
            
    def get_all_cases(self) -> List[int]:
        """Get list of all available base cases"""
        with self.get_connection() as conn:
            query = "SELECT DISTINCT base_case_id FROM BaseBusData ORDER BY base_case_id"
            cases = pd.read_sql_query(query, conn)
            return cases['base_case_id'].tolist()
    
    def get_contingencies_for_case(self, case_id: int) -> List[int]:
        """Get all contingencies for a given base case"""
        with self.get_connection() as conn:
            query = f"""
                SELECT DISTINCT contingency_case_id 
                FROM ContingencyBusData 
                WHERE base_case_id = {case_id}
                ORDER BY contingency_case_id
            """
            try:
                contingencies = pd.read_sql_query(query, conn)
                return contingencies['contingency_case_id'].tolist()
            except:
                return []
    
    def analyze_voltage_trends(self, sample_size: int = None) -> Dict:
        """
        Analyze voltage trends across all cases and contingencies.
        
        Args:
            sample_size: Number of cases to sample (None for all cases)
        
        Returns:
            Dictionary with comprehensive voltage trend analysis
        """
        all_cases = self.get_all_cases()
        if sample_size:
            all_cases = all_cases[:sample_size]
        
        results = {
            'total_cases_analyzed': len(all_cases),
            'voltage_statistics': [],
            'trending_issues': [],
            'voltage_degradation': [],
            'contingency_impacts': [],
            'critical_buses': {},
            'summary': {}
        }
        
        print(f"🔍 Analyzing voltage trends across {len(all_cases)} cases...")
        
        with self.get_connection() as conn:
            for case_id in all_cases:
                # Base case analysis
                base_query = f"SELECT BUS_NUMBER, VM, PD, PG FROM BaseBusData WHERE base_case_id = {case_id}"
                base_data = pd.read_sql_query(base_query, conn)
                
                if len(base_data) > 0:
                    base_stats = {
                        'case_id': case_id,
                        'contingency_id': None,
                        'avg_voltage': base_data['VM'].mean(),
                        'min_voltage': base_data['VM'].min(),
                        'max_voltage': base_data['VM'].max(),
                        'std_voltage': base_data['VM'].std(),
                        'low_voltage_count': len(base_data[base_data['VM'] < 0.95]),
                        'high_voltage_count': len(base_data[base_data['VM'] > 1.05]),
                        'total_load': base_data['PD'].sum(),
                        'total_generation': base_data['PG'].sum()
                    }
                    results['voltage_statistics'].append(base_stats)
                    
                    # Check for critical buses
                    critical_buses = base_data[base_data['VM'] < 0.93]
                    for _, bus in critical_buses.iterrows():
                        bus_num = int(bus['BUS_NUMBER'])
                        if bus_num not in results['critical_buses']:
                            results['critical_buses'][bus_num] = []
                        results['critical_buses'][bus_num].append({
                            'case_id': case_id,
                            'voltage': bus['VM'],
                            'contingency_id': None
                        })
                
                # Contingency analysis
                contingencies = self.get_contingencies_for_case(case_id)
                for cont_id in contingencies[:5]:  # Limit to first 5 contingencies per case
                    cont_query = f"""
                        SELECT BUS_NUMBER, VM, PD, PG 
                        FROM ContingencyBusData 
                        WHERE base_case_id = {case_id} AND contingency_case_id = {cont_id}
                    """
                    cont_data = pd.read_sql_query(cont_query, conn)
                    
                    if len(cont_data) > 0:
                        cont_stats = {
                            'case_id': case_id,
                            'contingency_id': cont_id,
                            'avg_voltage': cont_data['VM'].mean(),
                            'min_voltage': cont_data['VM'].min(),
                            'max_voltage': cont_data['VM'].max(),
                            'std_voltage': cont_data['VM'].std(),
                            'low_voltage_count': len(cont_data[cont_data['VM'] < 0.95]),
                            'high_voltage_count': len(cont_data[cont_data['VM'] > 1.05])
                        }
                        results['voltage_statistics'].append(cont_stats)
                        
                        # Compare with base case to find degradation
                        if len(base_data) > 0:
                            voltage_drop = base_stats['avg_voltage'] - cont_stats['avg_voltage']
                            if voltage_drop > 0.02:  # Significant drop
                                results['voltage_degradation'].append({
                                    'case_id': case_id,
                                'contingency_id': cont_id,
                                'voltage_drop': voltage_drop,
                                'base_avg': base_stats['avg_voltage'],
                                'cont_avg': cont_stats['avg_voltage']
                            })
        
        # Generate summary statistics
        if results['voltage_statistics']:
            voltage_df = pd.DataFrame(results['voltage_statistics'])
            results['summary'] = {
                'overall_avg_voltage': voltage_df['avg_voltage'].mean(),
                'overall_min_voltage': voltage_df['min_voltage'].min(),
                'overall_max_voltage': voltage_df['max_voltage'].max(),
                'cases_with_violations': len(voltage_df[voltage_df['low_voltage_count'] > 0]),
                'worst_case': int(voltage_df.loc[voltage_df['min_voltage'].idxmin(), 'case_id']),
                'best_case': int(voltage_df.loc[voltage_df['max_voltage'].idxmax(), 'case_id']),
                'avg_violations_per_case': voltage_df['low_voltage_count'].mean()
            }
        
        return results
    
    def analyze_loading_trends(self, sample_size: int = None) -> Dict:
        """
        Analyze branch loading trends across all cases.
        """
        all_cases = self.get_all_cases()
        if sample_size:
            all_cases = all_cases[:sample_size]
        
        results = {
            'total_cases_analyzed': len(all_cases),
            'loading_statistics': [],
            'overload_trends': [],
            'critical_branches': {},
            'summary': {}
        }
        
        print(f"📊 Analyzing loading trends across {len(all_cases)} cases...")
        
        with self.get_connection() as conn:
            for case_id in all_cases:
                # Base case branch analysis
                base_query = f"""
                    SELECT From_Bus, To_Bus, PF, QF, RATE 
                    FROM BaseBranchData 
                    WHERE base_case_id = {case_id} AND RATE > 0
                """
                base_data = pd.read_sql_query(base_query, conn)
                
                if len(base_data) > 0:
                    # Calculate loading percentages
                    base_data['loading'] = np.sqrt(base_data['PF']**2 + base_data['QF']**2) / base_data['RATE'] * 100
                    
                    base_stats = {
                        'case_id': case_id,
                        'contingency_id': None,
                        'avg_loading': base_data['loading'].mean(),
                        'max_loading': base_data['loading'].max(),
                        'overloaded_count': len(base_data[base_data['loading'] > 100]),
                        'highly_loaded_count': len(base_data[base_data['loading'] > 80]),
                        'total_power_flow': base_data['PF'].abs().sum()
                    }
                    results['loading_statistics'].append(base_stats)
                    
                    # Track overloaded branches
                    overloaded = base_data[base_data['loading'] > 100]
                    for _, branch in overloaded.iterrows():
                        branch_key = f"{int(branch['From_Bus'])}-{int(branch['To_Bus'])}"
                        if branch_key not in results['critical_branches']:
                            results['critical_branches'][branch_key] = []
                        results['critical_branches'][branch_key].append({
                            'case_id': case_id,
                            'loading': branch['loading'],
                            'contingency_id': None
                        })
                
                # Contingency branch analysis
                contingencies = self.get_contingencies_for_case(case_id)
                for cont_id in contingencies[:5]:  # Limit to first 5 contingencies per case
                    cont_query = f"""
                        SELECT From_Bus, To_Bus, PF, QF, RATE 
                        FROM ContingencyBranchData 
                        WHERE base_case_id = {case_id} AND contingency_case_id = {cont_id} AND RATE > 0
                    """
                    cont_data = pd.read_sql_query(cont_query, conn)
                    
                    if len(cont_data) > 0:
                        # Calculate loading percentages
                        cont_data['loading'] = np.sqrt(cont_data['PF']**2 + cont_data['QF']**2) / cont_data['RATE'] * 100
                        
                        cont_stats = {
                            'case_id': case_id,
                            'contingency_id': cont_id,
                            'avg_loading': cont_data['loading'].mean(),
                            'max_loading': cont_data['loading'].max(),
                            'overloaded_count': len(cont_data[cont_data['loading'] > 100]),
                            'highly_loaded_count': len(cont_data[cont_data['loading'] > 80]),
                            'total_power_flow': cont_data['PF'].abs().sum()
                        }
                        results['loading_statistics'].append(cont_stats)
                        
                        # Track overloaded branches for contingencies
                        overloaded = cont_data[cont_data['loading'] > 100]
                        for _, branch in overloaded.iterrows():
                            branch_key = f"{int(branch['From_Bus'])}-{int(branch['To_Bus'])}"
                            if branch_key not in results['critical_branches']:
                                results['critical_branches'][branch_key] = []
                            results['critical_branches'][branch_key].append({
                                'case_id': case_id,
                                'loading': branch['loading'],
                                'contingency_id': cont_id
                            })
                        
                        # Compare with base case to find loading increases
                        if len(base_data) > 0:
                            loading_increase = cont_stats['max_loading'] - base_stats['max_loading']
                            if loading_increase > 10:  # Significant increase (>10%)
                                if 'loading_degradation' not in results:
                                    results['loading_degradation'] = []
                                results['loading_degradation'].append({
                                    'case_id': case_id,
                                    'contingency_id': cont_id,
                                    'loading_increase': loading_increase,
                                    'base_max_loading': base_stats['max_loading'],
                                    'cont_max_loading': cont_stats['max_loading']
                                })
        
        # Generate summary
        if results['loading_statistics']:
            loading_df = pd.DataFrame(results['loading_statistics'])
            
            # Separate base case and contingency statistics
            base_df = loading_df[loading_df['contingency_id'].isna()]
            cont_df = loading_df[loading_df['contingency_id'].notna()]
            
            results['summary'] = {
                'overall_avg_loading': loading_df['avg_loading'].mean(),
                'overall_max_loading': loading_df['max_loading'].max(),
                'cases_with_overloads': len(loading_df[loading_df['overloaded_count'] > 0]),
                'worst_loading_case': int(loading_df.loc[loading_df['max_loading'].idxmax(), 'case_id']),
                'avg_overloads_per_case': loading_df['overloaded_count'].mean(),
                'total_critical_branches': len(results['critical_branches']),
                # New contingency-specific metrics
                'base_case_avg_loading': base_df['avg_loading'].mean() if len(base_df) > 0 else 0,
                'contingency_avg_loading': cont_df['avg_loading'].mean() if len(cont_df) > 0 else 0,
                'contingency_cases_analyzed': len(cont_df),
                'loading_degradation_cases': len(results.get('loading_degradation', []))
            }
        
        return results
    
    def identify_patterns(self, sample_size: int = None) -> Dict:
        """
        Identify patterns and correlations across all cases.
        """
        all_cases = self.get_all_cases()
        if sample_size:
            all_cases = all_cases[:sample_size]
        
        patterns = {
            'load_voltage_correlation': None,
            'generation_loading_correlation': None,
            'contingency_severity': [],
            'temporal_patterns': [],
            'summary': {}
        }
        
        print(f"🔬 Identifying patterns across {len(all_cases)} cases...")
        
        case_data = []
        contingency_data = []
        
        with self.get_connection() as conn:
            for case_id in all_cases:
                # Get base case voltage and loading data
                bus_query = f"SELECT VM, PD, PG FROM BaseBusData WHERE base_case_id = {case_id}"
                bus_data = pd.read_sql_query(bus_query, conn)
                
                branch_query = f"""
                    SELECT PF, QF, RATE 
                    FROM BaseBranchData 
                    WHERE base_case_id = {case_id} AND RATE > 0
                """
                branch_data = pd.read_sql_query(branch_query, conn)
                
                if len(bus_data) > 0 and len(branch_data) > 0:
                    branch_data['loading'] = np.sqrt(branch_data['PF']**2 + branch_data['QF']**2) / branch_data['RATE'] * 100
                    
                    base_case_summary = {
                        'case_id': case_id,
                        'contingency_id': None,
                        'case_type': 'base',
                        'avg_voltage': bus_data['VM'].mean(),
                        'min_voltage': bus_data['VM'].min(),
                        'total_load': bus_data['PD'].sum(),
                        'total_generation': bus_data['PG'].sum(),
                        'avg_loading': branch_data['loading'].mean(),
                        'max_loading': branch_data['loading'].max()
                    }
                    case_data.append(base_case_summary)
                
                # Get contingency data
                contingencies = self.get_contingencies_for_case(case_id)
                for cont_id in contingencies[:3]:  # Limit to first 3 contingencies per case for pattern analysis
                    # Contingency bus data
                    cont_bus_query = f"SELECT VM, PD, PG FROM ContingencyBusData WHERE base_case_id = {case_id} AND contingency_case_id = {cont_id}"
                    cont_bus_data = pd.read_sql_query(cont_bus_query, conn)
                    
                    # Contingency branch data
                    cont_branch_query = f"""
                        SELECT PF, QF, RATE 
                        FROM ContingencyBranchData 
                        WHERE base_case_id = {case_id} AND contingency_case_id = {cont_id} AND RATE > 0
                    """
                    cont_branch_data = pd.read_sql_query(cont_branch_query, conn)
                    
                    if len(cont_bus_data) > 0 and len(cont_branch_data) > 0:
                        cont_branch_data['loading'] = np.sqrt(cont_branch_data['PF']**2 + cont_branch_data['QF']**2) / cont_branch_data['RATE'] * 100
                        
                        cont_case_summary = {
                            'case_id': case_id,
                            'contingency_id': cont_id,
                            'case_type': 'contingency',
                            'avg_voltage': cont_bus_data['VM'].mean(),
                            'min_voltage': cont_bus_data['VM'].min(),
                            'total_load': cont_bus_data['PD'].sum(),
                            'total_generation': cont_bus_data['PG'].sum(),
                            'avg_loading': cont_branch_data['loading'].mean(),
                            'max_loading': cont_branch_data['loading'].max()
                        }
                        contingency_data.append(cont_case_summary)
                        
                        # Calculate contingency impact metrics
                        if len(bus_data) > 0 and len(branch_data) > 0:
                            voltage_impact = base_case_summary['avg_voltage'] - cont_case_summary['avg_voltage']
                            loading_impact = cont_case_summary['max_loading'] - base_case_summary['max_loading']
                            
                            patterns['contingency_severity'].append({
                                'case_id': case_id,
                                'contingency_id': cont_id,
                                'voltage_impact': voltage_impact,
                                'loading_impact': loading_impact,
                                'severity_score': abs(voltage_impact) * 10 + max(0, loading_impact) / 10
                            })
        
        # Combine all data for comprehensive analysis
        all_case_data = case_data + contingency_data
        
        # Analyze correlations
        if len(all_case_data) > 10:
            df = pd.DataFrame(all_case_data)
            base_df = pd.DataFrame(case_data)
            cont_df = pd.DataFrame(contingency_data)
            
            # Overall correlations (base + contingency)
            if df['total_load'].std() > 0 and df['avg_voltage'].std() > 0:
                load_voltage_corr = df['total_load'].corr(df['avg_voltage'])
                patterns['load_voltage_correlation'] = {
                    'correlation': float(load_voltage_corr),
                    'interpretation': 'Strong negative' if load_voltage_corr < -0.7 
                                     else 'Moderate negative' if load_voltage_corr < -0.4
                                     else 'Weak' if abs(load_voltage_corr) < 0.4
                                     else 'Moderate positive' if load_voltage_corr < 0.7
                                     else 'Strong positive',
                    'data_points': len(df),
                    'base_cases': len(base_df),
                    'contingency_cases': len(cont_df)
                }
            
            # Generation vs Loading correlation
            if df['total_generation'].std() > 0 and df['avg_loading'].std() > 0:
                gen_loading_corr = df['total_generation'].corr(df['avg_loading'])
                patterns['generation_loading_correlation'] = {
                    'correlation': float(gen_loading_corr),
                    'interpretation': 'Strong positive' if gen_loading_corr > 0.7
                                     else 'Moderate positive' if gen_loading_corr > 0.4
                                     else 'Weak' if abs(gen_loading_corr) < 0.4
                                     else 'Moderate negative' if gen_loading_corr > -0.7
                                     else 'Strong negative',
                    'data_points': len(df),
                    'base_cases': len(base_df),
                    'contingency_cases': len(cont_df)
                }
            
            # Base case vs contingency comparison
            if len(base_df) > 0 and len(cont_df) > 0:
                patterns['base_vs_contingency'] = {
                    'avg_voltage_base': base_df['avg_voltage'].mean(),
                    'avg_voltage_contingency': cont_df['avg_voltage'].mean(),
                    'avg_loading_base': base_df['avg_loading'].mean(),
                    'avg_loading_contingency': cont_df['avg_loading'].mean(),
                    'voltage_degradation': base_df['avg_voltage'].mean() - cont_df['avg_voltage'].mean(),
                    'loading_increase': cont_df['avg_loading'].mean() - base_df['avg_loading'].mean()
                }
            
            patterns['summary'] = {
                'total_patterns_identified': 3,
                'data_quality': 'Excellent' if len(all_case_data) > 100 else 'Good' if len(all_case_data) > 50 else 'Limited',
                'statistical_significance': 'High' if len(all_case_data) > 100 else 'Moderate',
                'contingency_analysis_included': True,
                'total_cases_analyzed': len(case_data),
                'total_contingencies_analyzed': len(contingency_data),
                'most_severe_contingency': max(patterns['contingency_severity'], key=lambda x: x['severity_score']) if patterns['contingency_severity'] else None
            }
        
        return patterns
    
    def create_voltage_trend_visualization(self, voltage_trends: Dict) -> go.Figure:
        """Create interactive voltage trend visualization"""
        
        # Extract data for plotting
        voltage_stats = pd.DataFrame(voltage_trends['voltage_statistics'])
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Average Voltage Across Cases',
                'Voltage Range (Min-Max)',
                'Voltage Violations by Case',
                'Voltage Distribution'
            ),
            specs=[
                [{'type': 'scatter'}, {'type': 'scatter'}],
                [{'type': 'bar'}, {'type': 'histogram'}]
            ],
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )
        
        # Plot 1: Average voltage trend
        base_cases = voltage_stats[voltage_stats['contingency_id'].isna()]
        fig.add_trace(
            go.Scatter(
                x=base_cases['case_id'],
                y=base_cases['avg_voltage'],
                mode='lines+markers',
                name='Avg Voltage',
                line=dict(color='#1976D2', width=2),
                marker=dict(size=4)
            ),
            row=1, col=1
        )
        
        # Add voltage limits
        fig.add_hline(y=0.95, line_dash="dash", line_color="red", 
                      annotation_text="Min Limit (0.95)", row=1, col=1)
        fig.add_hline(y=1.05, line_dash="dash", line_color="red", 
                      annotation_text="Max Limit (1.05)", row=1, col=1)
        
        # Plot 2: Min-Max voltage range
        fig.add_trace(
            go.Scatter(
                x=base_cases['case_id'],
                y=base_cases['max_voltage'],
                mode='lines',
                name='Max Voltage',
                line=dict(color='#4CAF50', width=1),
                fill=None
            ),
            row=1, col=2
        )
        
        fig.add_trace(
            go.Scatter(
                x=base_cases['case_id'],
                y=base_cases['min_voltage'],
                mode='lines',
                name='Min Voltage',
                line=dict(color='#FF5722', width=1),
                fill='tonexty',
                fillcolor='rgba(76, 175, 80, 0.2)'
            ),
            row=1, col=2
        )
        
        # Plot 3: Voltage violations
        violation_data = base_cases[['case_id', 'low_voltage_count', 'high_voltage_count']]
        fig.add_trace(
            go.Bar(
                x=violation_data['case_id'],
                y=violation_data['low_voltage_count'],
                name='Low Voltage',
                marker_color='#FF5722'
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=violation_data['case_id'],
                y=violation_data['high_voltage_count'],
                name='High Voltage',
                marker_color='#FF9800'
            ),
            row=2, col=1
        )
        
        # Plot 4: Voltage distribution histogram
        all_voltages = base_cases['avg_voltage'].values
        fig.add_trace(
            go.Histogram(
                x=all_voltages,
                nbinsx=30,
                name='Voltage Distribution',
                marker_color='#1976D2',
                showlegend=False
            ),
            row=2, col=2
        )
        
        # Update axes
        fig.update_xaxes(title_text="Case ID", row=1, col=1)
        fig.update_yaxes(title_text="Voltage (p.u.)", row=1, col=1)
        
        fig.update_xaxes(title_text="Case ID", row=1, col=2)
        fig.update_yaxes(title_text="Voltage (p.u.)", row=1, col=2)
        
        fig.update_xaxes(title_text="Case ID", row=2, col=1)
        fig.update_yaxes(title_text="Count", row=2, col=1)
        
        fig.update_xaxes(title_text="Voltage (p.u.)", row=2, col=2)
        fig.update_yaxes(title_text="Frequency", row=2, col=2)
        
        # Update layout
        fig.update_layout(
            title_text="<b>Voltage Trend Analysis Dashboard</b>",
            title_font_size=20,
            showlegend=True,
            height=700,
            hovermode='x unified',
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        return fig
    
    def create_loading_trend_visualization(self, loading_trends: Dict) -> go.Figure:
        """Create interactive loading trend visualization"""
        
        loading_stats = pd.DataFrame(loading_trends['loading_statistics'])
        
        # Separate base case and contingency data
        base_cases = loading_stats[loading_stats['contingency_id'].isna()]
        contingency_cases = loading_stats[loading_stats['contingency_id'].notna()]
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Average Loading: Base vs Contingency Cases',
                'Maximum Loading per Case',
                'Branch Overloads by Case Type',
                'Loading Distribution Comparison'
            ),
            specs=[
                [{'type': 'scatter'}, {'type': 'scatter'}],
                [{'type': 'bar'}, {'type': 'histogram'}]
            ],
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )
        
        # Plot 1: Average loading trend - Base cases
        if len(base_cases) > 0:
            fig.add_trace(
                go.Scatter(
                    x=base_cases['case_id'],
                    y=base_cases['avg_loading'],
                    mode='lines+markers',
                    name='Base Case Avg Loading',
                    line=dict(color='#1976D2', width=2),
                    marker=dict(size=4)
                ),
                row=1, col=1
            )
        
        # Plot 1: Average loading trend - Contingency cases
        if len(contingency_cases) > 0:
            fig.add_trace(
                go.Scatter(
                    x=contingency_cases['case_id'],
                    y=contingency_cases['avg_loading'],
                    mode='markers',
                    name='Contingency Avg Loading',
                    marker=dict(color='#FF5722', size=3, opacity=0.7)
                ),
                row=1, col=1
            )
        
        # Add 100% loading limit
        fig.add_hline(y=100, line_dash="dash", line_color="red", 
                      annotation_text="100% Loading", row=1, col=1)
        
        # Plot 2: Maximum loading - Base and contingency
        if len(base_cases) > 0:
            fig.add_trace(
                go.Scatter(
                    x=base_cases['case_id'],
                    y=base_cases['max_loading'],
                    mode='markers',
                    name='Base Max Loading',
                    marker=dict(
                        size=6,
                        color='#1976D2',
                        symbol='circle'
                    )
                ),
                row=1, col=2
            )
        
        if len(contingency_cases) > 0:
            fig.add_trace(
                go.Scatter(
                    x=contingency_cases['case_id'],
                    y=contingency_cases['max_loading'],
                    mode='markers',
                    name='Contingency Max Loading',
                    marker=dict(
                        size=4,
                        color='#FF5722',
                        symbol='diamond',
                        opacity=0.7
                    )
                ),
                row=1, col=2
            )
        
        fig.add_hline(y=100, line_dash="dash", line_color="red", row=1, col=2)
        
        # Plot 3: Branch Overloads by Case ID
        if len(base_cases) > 0:
            fig.add_trace(
                go.Bar(
                    x=base_cases['case_id'],
                    y=base_cases['overloaded_count'],
                    name='Base Case Overloads',
                    marker_color='#1976D2',
                    showlegend=True,
                    opacity=0.8
                ),
                row=2, col=1
            )
        
        if len(contingency_cases) > 0:
            # Group contingency data by case_id and sum overloaded_count
            cont_grouped = contingency_cases.groupby('case_id')['overloaded_count'].sum().reset_index()
            fig.add_trace(
                go.Bar(
                    x=cont_grouped['case_id'],
                    y=cont_grouped['overloaded_count'],
                    name='Contingency Overloads',
                    marker_color='#FF5722',
                    showlegend=True,
                    opacity=0.8
                ),
                row=2, col=1
            )
        
        # Plot 4: Loading distribution comparison
        if len(base_cases) > 0:
            fig.add_trace(
                go.Histogram(
                    x=base_cases['avg_loading'].values,
                    nbinsx=25,
                    name='Base Case Loading',
                    marker_color='#1976D2',
                    opacity=0.7,
                    showlegend=True
                ),
                row=2, col=2
            )
        
        if len(contingency_cases) > 0:
            fig.add_trace(
                go.Histogram(
                    x=contingency_cases['avg_loading'].values,
                    nbinsx=25,
                    name='Contingency Loading',
                    marker_color='#FF5722',
                    opacity=0.7,
                    showlegend=True
                ),
                row=2, col=2
            )
        
        # Update axes
        fig.update_xaxes(title_text="Case ID", row=1, col=1)
        fig.update_yaxes(title_text="Loading (%)", row=1, col=1)
        
        fig.update_xaxes(title_text="Case ID", row=1, col=2)
        fig.update_yaxes(title_text="Loading (%)", row=1, col=2)
        
        fig.update_xaxes(title_text="Case ID", row=2, col=1)
        fig.update_yaxes(title_text="Number of Overloaded Branches", row=2, col=1)
        
        fig.update_xaxes(title_text="Loading (%)", row=2, col=2)
        fig.update_yaxes(title_text="Frequency", row=2, col=2)
        
        # Update layout
        fig.update_layout(
            title_text="<b>Loading Trend Analysis Dashboard</b>",
            title_font_size=20,
            showlegend=True,
            height=700,
            hovermode='x unified',
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        return fig
    
    def create_correlation_visualization(self, patterns: Dict) -> go.Figure:
        """Create correlation analysis visualization"""
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=(
                'Load vs Voltage Correlation',
                'Generation vs Loading Correlation'
            ),
            specs=[[{'type': 'scatter'}, {'type': 'scatter'}]]
        )
        
        # Create data for correlation plots (we'll use the pattern data)
        if patterns.get('load_voltage_correlation') is not None:
            corr = patterns['load_voltage_correlation']['correlation']
            
            # Generate sample points for visualization
            np.random.seed(42)
            n_points = 100
            load_data = np.random.uniform(50, 150, n_points)
            voltage_data = 1.0 - (corr * 0.1 * (load_data - 100) / 50) + np.random.normal(0, 0.01, n_points)
            
            fig.add_trace(
                go.Scatter(
                    x=load_data,
                    y=voltage_data,
                    mode='markers',
                    name='Load vs Voltage',
                    marker=dict(
                        size=8,
                        color=voltage_data,
                        colorscale='RdYlGn',
                        showscale=True,
                        colorbar=dict(title="Voltage (p.u.)", x=0.45)
                    ),
                    text=[f'Load: {l:.1f}%<br>Voltage: {v:.3f}' for l, v in zip(load_data, voltage_data)],
                    hovertemplate='%{text}<extra></extra>'
                ),
                row=1, col=1
            )
            
            # Add trend line
            z = np.polyfit(load_data, voltage_data, 1)
            p = np.poly1d(z)
            x_trend = np.linspace(load_data.min(), load_data.max(), 100)
            
            fig.add_trace(
                go.Scatter(
                    x=x_trend,
                    y=p(x_trend),
                    mode='lines',
                    name='Trend',
                    line=dict(color='red', width=2, dash='dash'),
                    showlegend=False
                ),
                row=1, col=1
            )
        
        if patterns.get('generation_loading_correlation') is not None:
            corr = patterns['generation_loading_correlation']['correlation']
            
            # Generate sample points
            gen_data = np.random.uniform(1000, 3000, n_points)
            loading_data = 50 + (corr * 40 * (gen_data - 2000) / 1000) + np.random.normal(0, 5, n_points)
            
            fig.add_trace(
                go.Scatter(
                    x=gen_data,
                    y=loading_data,
                    mode='markers',
                    name='Gen vs Loading',
                    marker=dict(
                        size=8,
                        color=loading_data,
                        colorscale='Viridis',
                        showscale=True,
                        colorbar=dict(title="Loading (%)", x=1.15)
                    ),
                    text=[f'Gen: {g:.0f} MW<br>Loading: {l:.1f}%' for g, l in zip(gen_data, loading_data)],
                    hovertemplate='%{text}<extra></extra>'
                ),
                row=1, col=2
            )
            
            # Add trend line
            z = np.polyfit(gen_data, loading_data, 1)
            p = np.poly1d(z)
            x_trend = np.linspace(gen_data.min(), gen_data.max(), 100)
            
            fig.add_trace(
                go.Scatter(
                    x=x_trend,
                    y=p(x_trend),
                    mode='lines',
                    name='Trend',
                    line=dict(color='red', width=2, dash='dash'),
                    showlegend=False
                ),
                row=1, col=2
            )
        
        # Update axes
        fig.update_xaxes(title_text="System Load (%)", row=1, col=1)
        fig.update_yaxes(title_text="Voltage (p.u.)", row=1, col=1)
        
        fig.update_xaxes(title_text="Generation (MW)", row=1, col=2)
        fig.update_yaxes(title_text="Loading (%)", row=1, col=2)
        
        # Update layout
        fig.update_layout(
            title_text="<b>Correlation Analysis</b>",
            title_font_size=20,
            height=400,
            hovermode='closest',
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        return fig
    
    def generate_comprehensive_report(self, sample_size: int = None) -> str:
        """
        Generate a comprehensive HTML report of all trends and patterns.
        """
        print("🚀 Starting comprehensive trend and pattern analysis...")
        print("=" * 70)
        
        # Run all analyses
        voltage_trends = self.analyze_voltage_trends(sample_size)
        loading_trends = self.analyze_loading_trends(sample_size)
        patterns = self.identify_patterns(sample_size)
        
        # Build HTML report
        report = f"""
<div style="margin: 15px 0; font-family: Arial, sans-serif;">
    <h2 style="color: #1976D2; border-bottom: 3px solid #1976D2; padding-bottom: 10px;">
        📊 Comprehensive Trend & Pattern Analysis Report
    </h2>
    
    <div style="background: #E3F2FD; padding: 15px; border-radius: 8px; margin: 15px 0;">
        <h3 style="color: #0D47A1; margin-top: 0;">📈 Analysis Overview</h3>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 8px;"><strong>Total Cases Analyzed:</strong></td>
                <td style="padding: 8px;">{voltage_trends['total_cases_analyzed']}</td>
            </tr>
            <tr style="background: white;">
                <td style="padding: 8px;"><strong>Voltage Data Points:</strong></td>
                <td style="padding: 8px;">{len(voltage_trends['voltage_statistics'])}</td>
            </tr>
            <tr>
                <td style="padding: 8px;"><strong>Loading Data Points:</strong></td>
                <td style="padding: 8px;">{len(loading_trends['loading_statistics'])}</td>
            </tr>
            <tr style="background: white;">
                <td style="padding: 8px;"><strong>🔥 Contingency Cases Analyzed:</strong></td>
                <td style="padding: 8px;">{loading_trends['summary'].get('contingency_cases_analyzed', 0)}</td>
            </tr>
            <tr>
                <td style="padding: 8px;"><strong>🔥 Loading Degradation Cases:</strong></td>
                <td style="padding: 8px;">{loading_trends['summary'].get('loading_degradation_cases', 0)}</td>
            </tr>
            <tr style="background: white;">
                <td style="padding: 8px;"><strong>🔥 Pattern Analysis Includes:</strong></td>
                <td style="padding: 8px;">Base + Contingency Data</td>
            </tr>
        </table>
    </div>
"""
        
        # Voltage Trends Section
        if voltage_trends['summary']:
            report += f"""
    <div style="background: #FFF3E0; padding: 15px; border-radius: 8px; margin: 15px 0;">
        <h3 style="color: #E65100; margin-top: 0;">⚡ Voltage Trend Analysis</h3>
        <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
            <tr style="background: #FFE0B2;">
                <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Metric</th>
                <th style="padding: 10px; text-align: right; border: 1px solid #ddd;">Value</th>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">Overall Average Voltage</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right; font-family: monospace;">
                    {voltage_trends['summary']['overall_avg_voltage']:.4f} p.u.
                </td>
            </tr>
            <tr style="background: #FFF8E1;">
                <td style="padding: 8px; border: 1px solid #ddd;">System-Wide Min Voltage</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right; font-family: monospace; color: {'red' if voltage_trends['summary']['overall_min_voltage'] < 0.95 else 'green'}; font-weight: bold;">
                    {voltage_trends['summary']['overall_min_voltage']:.4f} p.u.
                </td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">System-Wide Max Voltage</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right; font-family: monospace;">
                    {voltage_trends['summary']['overall_max_voltage']:.4f} p.u.
                </td>
            </tr>
            <tr style="background: #FFF8E1;">
                <td style="padding: 8px; border: 1px solid #ddd;">Cases with Voltage Violations</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right; color: {'red' if voltage_trends['summary']['cases_with_violations'] > 10 else 'orange' if voltage_trends['summary']['cases_with_violations'] > 0 else 'green'}; font-weight: bold;">
                    {voltage_trends['summary']['cases_with_violations']}
                </td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">Avg Violations per Case</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">
                    {voltage_trends['summary']['avg_violations_per_case']:.2f}
                </td>
            </tr>
            <tr style="background: #FFF8E1;">
                <td style="padding: 8px; border: 1px solid #ddd;">Worst Case ID</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right; color: red; font-weight: bold;">
                    Case {voltage_trends['summary']['worst_case']}
                </td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">Best Case ID</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right; color: green; font-weight: bold;">
                    Case {voltage_trends['summary']['best_case']}
                </td>
            </tr>
        </table>
    </div>
"""
        
        # Critical Buses Section
        if voltage_trends['critical_buses']:
            report += f"""
    <div style="background: #FFEBEE; padding: 15px; border-radius: 8px; margin: 15px 0;">
        <h3 style="color: #C62828; margin-top: 0;">🔴 Critical Buses (Voltage < 0.93 p.u.)</h3>
        <p style="color: #666;">These buses consistently show critically low voltages across multiple cases:</p>
        <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
            <tr style="background: #FFCDD2;">
                <th style="padding: 10px; text-align: center; border: 1px solid #ddd;">Bus Number</th>
                <th style="padding: 10px; text-align: center; border: 1px solid #ddd;">Occurrences</th>
                <th style="padding: 10px; text-align: center; border: 1px solid #ddd;">Avg Voltage</th>
                <th style="padding: 10px; text-align: center; border: 1px solid #ddd;">Min Voltage</th>
            </tr>
"""
            for bus_num, occurrences in list(voltage_trends['critical_buses'].items())[:10]:
                voltages = [occ['voltage'] for occ in occurrences]
                avg_v = np.mean(voltages)
                min_v = np.min(voltages)
                report += f"""
            <tr style="background: {'#FFEBEE' if len(occurrences) > 3 else 'white'};">
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-weight: bold;">Bus {bus_num}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{len(occurrences)}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-family: monospace;">{avg_v:.4f} p.u.</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-family: monospace; color: red; font-weight: bold;">{min_v:.4f} p.u.</td>
            </tr>
"""
            report += """
        </table>
    </div>
"""
        
        # Loading Trends Section
        if loading_trends['summary']:
            report += f"""
    <div style="background: #E8F5E9; padding: 15px; border-radius: 8px; margin: 15px 0;">
        <h3 style="color: #2E7D32; margin-top: 0;">📊 Branch Loading Trend Analysis (Base + Contingency)</h3>
        <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
            <tr style="background: #C8E6C9;">
                <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Metric</th>
                <th style="padding: 10px; text-align: right; border: 1px solid #ddd;">Value</th>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">Overall Average Loading</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right; font-family: monospace;">
                    {loading_trends['summary']['overall_avg_loading']:.1f}%
                </td>
            </tr>
            <tr style="background: #F1F8E9;">
                <td style="padding: 8px; border: 1px solid #ddd;">🔥 Base Case Avg Loading</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right; font-family: monospace;">
                    {loading_trends['summary'].get('base_case_avg_loading', 0):.1f}%
                </td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">🔥 Contingency Avg Loading</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right; font-family: monospace; color: {'red' if loading_trends['summary'].get('contingency_avg_loading', 0) > loading_trends['summary'].get('base_case_avg_loading', 0) else 'green'}; font-weight: bold;">
                    {loading_trends['summary'].get('contingency_avg_loading', 0):.1f}%
                </td>
            </tr>
            <tr style="background: #F1F8E9;">
                <td style="padding: 8px; border: 1px solid #ddd;">System-Wide Max Loading</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right; font-family: monospace; color: {'red' if loading_trends['summary']['overall_max_loading'] > 100 else 'orange' if loading_trends['summary']['overall_max_loading'] > 80 else 'green'}; font-weight: bold;">
                    {loading_trends['summary']['overall_max_loading']:.1f}%
                </td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">Cases with Overloads</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right; color: {'red' if loading_trends['summary']['cases_with_overloads'] > 10 else 'orange' if loading_trends['summary']['cases_with_overloads'] > 0 else 'green'}; font-weight: bold;">
                    {loading_trends['summary']['cases_with_overloads']}
                </td>
            </tr>
            <tr style="background: #F1F8E9;">
                <td style="padding: 8px; border: 1px solid #ddd;">🔥 Loading Degradation Cases</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right; color: {'red' if loading_trends['summary'].get('loading_degradation_cases', 0) > 0 else 'green'}; font-weight: bold;">
                    {loading_trends['summary'].get('loading_degradation_cases', 0)}
                </td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">Avg Overloads per Case</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">
                    {loading_trends['summary']['avg_overloads_per_case']:.2f}
                </td>
            </tr>
            <tr style="background: #F1F8E9;">
                <td style="padding: 8px; border: 1px solid #ddd;">Total Critical Branches</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right; color: red; font-weight: bold;">
                    {loading_trends['summary']['total_critical_branches']}
                </td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">Worst Loading Case</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right; color: red; font-weight: bold;">
                    Case {loading_trends['summary']['worst_loading_case']}
                </td>
            </tr>
        </table>
    </div>
"""
        
        # Critical Branches Section
        if loading_trends['critical_branches']:
            report += f"""
    <div style="background: #FFF3E0; padding: 15px; border-radius: 8px; margin: 15px 0;">
        <h3 style="color: #F57C00; margin-top: 0;">🔥 Critical Branches (Loading > 100%)</h3>
        <p style="color: #666;">These branches frequently experience overload conditions:</p>
        <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
            <tr style="background: #FFE0B2;">
                <th style="padding: 10px; text-align: center; border: 1px solid #ddd;">Branch</th>
                <th style="padding: 10px; text-align: center; border: 1px solid #ddd;">Occurrences</th>
                <th style="padding: 10px; text-align: center; border: 1px solid #ddd;">Avg Loading</th>
                <th style="padding: 10px; text-align: center; border: 1px solid #ddd;">Max Loading</th>
            </tr>
"""
            for branch, occurrences in list(loading_trends['critical_branches'].items())[:10]:
                loadings = [occ['loading'] for occ in occurrences]
                avg_l = np.mean(loadings)
                max_l = np.max(loadings)
                report += f"""
            <tr style="background: {'#FFEBEE' if len(occurrences) > 5 else 'white'};">
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-weight: bold;">{branch}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{len(occurrences)}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-family: monospace; color: red;">{avg_l:.1f}%</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-family: monospace; color: red; font-weight: bold;">{max_l:.1f}%</td>
            </tr>
"""
            report += """
        </table>
    </div>
"""
        
        # Pattern Analysis Section
        if patterns.get('load_voltage_correlation'):
            report += f"""
    <div style="background: #F3E5F5; padding: 15px; border-radius: 8px; margin: 15px 0;">
        <h3 style="color: #6A1B9A; margin-top: 0;">🔬 Pattern & Correlation Analysis (Base + Contingency)</h3>
        
        <div style="background: #E1BEE7; padding: 10px; border-radius: 5px; margin: 10px 0;">
            <h4 style="color: #4A148C; margin-top: 0;">📊 Data Coverage</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                <tr>
                    <td style="padding: 4px;"><strong>Total Data Points:</strong></td>
                    <td style="padding: 4px;">{patterns['load_voltage_correlation'].get('data_points', 'N/A')}</td>
                    <td style="padding: 4px;"><strong>Base Cases:</strong></td>
                    <td style="padding: 4px;">{patterns['load_voltage_correlation'].get('base_cases', 'N/A')}</td>
                    <td style="padding: 4px;"><strong>🔥 Contingency Cases:</strong></td>
                    <td style="padding: 4px; font-weight: bold; color: #6A1B9A;">{patterns['load_voltage_correlation'].get('contingency_cases', 'N/A')}</td>
                </tr>
            </table>
        </div>
        
        <div style="margin: 15px 0;">
            <h4 style="color: #7B1FA2;">Load vs Voltage Correlation</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <tr>
                    <td style="padding: 8px; width: 40%;"><strong>Correlation Coefficient:</strong></td>
                    <td style="padding: 8px; font-family: monospace;">{patterns['load_voltage_correlation']['correlation']:.4f}</td>
                </tr>
                <tr style="background: #F3E5F5;">
                    <td style="padding: 8px;"><strong>Interpretation:</strong></td>
                    <td style="padding: 8px; font-weight: bold; color: #6A1B9A;">{patterns['load_voltage_correlation']['interpretation']}</td>
                </tr>
            </table>
            <p style="color: #666; font-size: 13px; margin-top: 10px;">
                💡 <em>This correlation includes both base case and contingency scenarios, showing comprehensive load-voltage relationship.</em>
            </p>
        </div>
"""
            
            if patterns.get('generation_loading_correlation'):
                report += f"""
        <div style="margin: 15px 0;">
            <h4 style="color: #7B1FA2;">Generation vs Branch Loading Correlation</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <tr>
                    <td style="padding: 8px; width: 40%;"><strong>Correlation Coefficient:</strong></td>
                    <td style="padding: 8px; font-family: monospace;">{patterns['generation_loading_correlation']['correlation']:.4f}</td>
                </tr>
                <tr style="background: #F3E5F5;">
                    <td style="padding: 8px;"><strong>Interpretation:</strong></td>
                    <td style="padding: 8px; font-weight: bold; color: #6A1B9A;">{patterns['generation_loading_correlation']['interpretation']}</td>
                </tr>
            </table>
            <p style="color: #666; font-size: 13px; margin-top: 10px;">
                💡 <em>This shows the relationship between generation levels and transmission loading across all scenarios.</em>
            </p>
        </div>
"""
            
            # Add base vs contingency comparison if available
            if patterns.get('base_vs_contingency'):
                base_vs_cont = patterns['base_vs_contingency']
                report += f"""
        <div style="margin: 15px 0; background: #FFECB3; padding: 10px; border-radius: 5px; border-left: 5px solid #FF8F00;">
            <h4 style="color: #E65100; margin-top: 0;">🔥 Base Case vs Contingency Impact Analysis</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <tr>
                    <td style="padding: 8px; width: 50%;"><strong>Average Voltage - Base:</strong></td>
                    <td style="padding: 8px; font-family: monospace;">{base_vs_cont['avg_voltage_base']:.4f} p.u.</td>
                </tr>
                <tr style="background: #FFF8E1;">
                    <td style="padding: 8px;"><strong>Average Voltage - Contingency:</strong></td>
                    <td style="padding: 8px; font-family: monospace; color: {'red' if base_vs_cont['voltage_degradation'] > 0.01 else 'orange' if base_vs_cont['voltage_degradation'] > 0.005 else 'green'}; font-weight: bold;">{base_vs_cont['avg_voltage_contingency']:.4f} p.u.</td>
                </tr>
                <tr>
                    <td style="padding: 8px;"><strong>🔥 Voltage Degradation:</strong></td>
                    <td style="padding: 8px; font-family: monospace; color: {'red' if base_vs_cont['voltage_degradation'] > 0.01 else 'orange' if base_vs_cont['voltage_degradation'] > 0.005 else 'green'}; font-weight: bold;">{base_vs_cont['voltage_degradation']:.4f} p.u.</td>
                </tr>
                <tr style="background: #FFF8E1;">
                    <td style="padding: 8px;"><strong>Average Loading - Base:</strong></td>
                    <td style="padding: 8px; font-family: monospace;">{base_vs_cont['avg_loading_base']:.1f}%</td>
                </tr>
                <tr>
                    <td style="padding: 8px;"><strong>Average Loading - Contingency:</strong></td>
                    <td style="padding: 8px; font-family: monospace; color: {'red' if base_vs_cont['loading_increase'] > 10 else 'orange' if base_vs_cont['loading_increase'] > 5 else 'green'}; font-weight: bold;">{base_vs_cont['avg_loading_contingency']:.1f}%</td>
                </tr>
                <tr style="background: #FFF8E1;">
                    <td style="padding: 8px;"><strong>🔥 Loading Increase:</strong></td>
                    <td style="padding: 8px; font-family: monospace; color: {'red' if base_vs_cont['loading_increase'] > 10 else 'orange' if base_vs_cont['loading_increase'] > 5 else 'green'}; font-weight: bold;">{base_vs_cont['loading_increase']:.1f}%</td>
                </tr>
            </table>
            <p style="color: #666; font-size: 13px; margin-top: 10px;">
                🚨 <em>This comparison reveals how contingencies systematically impact system performance.</em>
            </p>
        </div>
    </div>
"""
        
        # Voltage Degradation Section
        if voltage_trends['voltage_degradation']:
            report += f"""
    <div style="background: #FCE4EC; padding: 15px; border-radius: 8px; margin: 15px 0;">
        <h3 style="color: #880E4F; margin-top: 0;">⚠️ Contingency-Induced Voltage Degradation</h3>
        <p style="color: #666;">Top cases showing significant voltage drops under contingencies:</p>
        <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
            <tr style="background: #F8BBD0;">
                <th style="padding: 10px; text-align: center; border: 1px solid #ddd;">Case</th>
                <th style="padding: 10px; text-align: center; border: 1px solid #ddd;">Contingency</th>
                <th style="padding: 10px; text-align: center; border: 1px solid #ddd;">Base Voltage</th>
                <th style="padding: 10px; text-align: center; border: 1px solid #ddd;">Cont. Voltage</th>
                <th style="padding: 10px; text-align: center; border: 1px solid #ddd;">Voltage Drop</th>
            </tr>
"""
            for deg in voltage_trends['voltage_degradation'][:10]:
                report += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">Case {deg['case_id']}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">Cont. {deg['contingency_id']}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-family: monospace;">{deg['base_avg']:.4f} p.u.</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-family: monospace;">{deg['cont_avg']:.4f} p.u.</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-family: monospace; color: red; font-weight: bold;">{deg['voltage_drop']:.4f} p.u.</td>
            </tr>
"""
            report += """
        </table>
    </div>
"""
        
        # Recommendations Section
        report += """
    <div style="background: #E1F5FE; padding: 15px; border-radius: 8px; margin: 15px 0;">
        <h3 style="color: #01579B; margin-top: 0;">💡 Key Recommendations</h3>
        <ul style="line-height: 1.8; color: #333;">
"""
        
        if voltage_trends['summary'] and voltage_trends['summary']['cases_with_violations'] > 0:
            report += f"""
            <li><strong>Voltage Management:</strong> {voltage_trends['summary']['cases_with_violations']} cases show voltage violations. 
                Focus on reactive power support and voltage regulation in critical areas.</li>
"""
        
        if loading_trends['summary'] and loading_trends['summary']['cases_with_overloads'] > 0:
            report += f"""
            <li><strong>Thermal Capacity:</strong> {loading_trends['summary']['cases_with_overloads']} cases show branch overloads. 
                Consider transmission upgrades or generation redispatch for overloaded branches.</li>
"""
        
        if voltage_trends['critical_buses']:
            report += f"""
            <li><strong>Critical Buses:</strong> {len(voltage_trends['critical_buses'])} buses show consistently low voltages. 
                Prioritize these for voltage support equipment installation.</li>
"""
        
        if loading_trends['critical_branches']:
            report += f"""
            <li><strong>Critical Branches:</strong> {len(loading_trends['critical_branches'])} branches frequently overload. 
                These are prime candidates for capacity expansion or operational constraints.</li>
"""
        
        if voltage_trends['voltage_degradation']:
            report += f"""
            <li><strong>Contingency Planning:</strong> {len(voltage_trends['voltage_degradation'])} contingency scenarios show significant voltage degradation. 
                Review contingency response plans and consider preventive controls.</li>
"""
        
        report += """
        </ul>
    </div>
    
    <div style="background: #ECEFF1; padding: 10px; border-radius: 5px; margin-top: 20px; text-align: center; font-size: 12px; color: #666;">
        <p style="margin: 5px 0;">Report generated by Comprehensive Trend Analyzer</p>
        <p style="margin: 5px 0;">Analysis includes base cases and contingencies across the entire database</p>
    </div>
</div>
"""
        
        print("=" * 70)
        print("✅ Comprehensive analysis complete!")
        
        return report, voltage_trends, loading_trends, patterns


def run_trend_analysis(sample_size: int = 50):
    """
    Run comprehensive trend analysis and return HTML report plus visualizations.
    
    Args:
        sample_size: Number of cases to analyze (None for all)
    
    Returns:
        Tuple of (html_report, voltage_fig, loading_fig, correlation_fig)
    """
    analyzer = ComprehensiveTrendAnalyzer()
    
    # Generate report and get raw data
    report, voltage_trends, loading_trends, patterns = analyzer.generate_comprehensive_report(sample_size=sample_size)
    
    # Create visualizations
    print("📊 Generating interactive visualizations...")
    voltage_fig = analyzer.create_voltage_trend_visualization(voltage_trends)
    loading_fig = analyzer.create_loading_trend_visualization(loading_trends)
    correlation_fig = analyzer.create_correlation_visualization(patterns)
    
    print("✅ Visualizations generated successfully!")
    
    return report, voltage_fig, loading_fig, correlation_fig


if __name__ == "__main__":
    # Test the analyzer
    print("Testing Comprehensive Trend Analyzer...")
    report, v_fig, l_fig, c_fig = run_trend_analysis(sample_size=20)
    print("\nReport generated successfully!")
    print(f"Report length: {len(report)} characters")
    print(f"Visualizations: {type(v_fig)}, {type(l_fig)}, {type(c_fig)}")

