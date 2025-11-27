import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from plotly.subplots import make_subplots

def create_bus_analysis_plot(buses_df, case_id=None, contingency_id=None):
    """Create a comprehensive bus analysis visualization showing voltage profiles,
    generation/load distribution, and bus statistics.
    
    Parameters:
    buses_df: DataFrame containing bus data
    case_id: ID of the base case
    contingency_id: ID of the contingency case (None for base case analysis)
    """
    
    try:
        # Create a figure with 2x2 subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Bus Voltage Profile",
                "Voltage Distribution Histogram",
                "Generation and Load Distribution",
                "System Summary"
            ),
            specs=[
                [{"type": "scatter"}, {"type": "histogram"}],
                [{"type": "bar"}, {"type": "table"}]
            ],
            vertical_spacing=0.1,
            horizontal_spacing=0.1
        )
        
        # Ensure we have the needed columns
        if 'BUS_NUMBER' not in buses_df.columns or 'VM' not in buses_df.columns:
            raise ValueError("Bus data missing required columns (BUS_NUMBER or VM)")
            
        # Sort the dataframe by bus number for consistent plotting
        buses_df = buses_df.sort_values('BUS_NUMBER')
        
        # 1. Bus Voltage Profile (top-left)
        # Color mapping based on voltage levels
        colors = [
            'red' if v < 0.95 else 
            'orange' if v > 1.05 else 
            'green' for v in buses_df['VM']
        ]
        
        fig.add_trace(
            go.Scatter(
                x=buses_df['BUS_NUMBER'],
                y=buses_df['VM'],
                mode='markers',
                marker=dict(
                    color=colors,
                    size=10
                ),
                name="Bus Voltage",
                text=[f"Bus: {int(row['BUS_NUMBER'])}<br>Voltage: {row['VM']:.4f} p.u.<br>Gen: {row['PG']} MW<br>Load: {row['PD']} MW" 
                      for _, row in buses_df.iterrows()],
                hoverinfo="text"
            ),
            row=1, col=1
        )
        
        # Add reference lines for voltage limits
        fig.add_shape(
            type="line", line=dict(dash="dash", color="red"),
            x0=buses_df['BUS_NUMBER'].min(), x1=buses_df['BUS_NUMBER'].max(), y0=0.95, y1=0.95,
            row=1, col=1
        )
        fig.add_shape(
            type="line", line=dict(dash="dash", color="red"),
            x0=buses_df['BUS_NUMBER'].min(), x1=buses_df['BUS_NUMBER'].max(), y0=1.05, y1=1.05,
            row=1, col=1
        )
        
        # Update layout for voltage profile
        fig.update_xaxes(title_text="Bus Number", row=1, col=1)
        fig.update_yaxes(title_text="Voltage (p.u.)", range=[0.9, 1.1], row=1, col=1)
        
        # 2. Voltage Distribution Histogram (top-right)
        fig.add_trace(
            go.Histogram(
                x=buses_df['VM'],
                nbinsx=20,
                marker_color='royalblue',
                name="Voltage Distribution"
            ),
            row=1, col=2
        )
        
        # Add reference lines for voltage limits in histogram
        fig.add_vline(x=0.95, line_dash="dash", line_color="red", 
                     annotation_text="0.95 p.u.", row=1, col=2)
        fig.add_vline(x=1.05, line_dash="dash", line_color="red", 
                     annotation_text="1.05 p.u.", row=1, col=2)
        
        # Update layout for histogram
        fig.update_xaxes(title_text="Voltage (p.u.)", row=1, col=2)
        fig.update_yaxes(title_text="Number of Buses", row=1, col=2)
        
        # 3. Generation and Load Distribution (bottom-left)
        # Filter for buses with generation or load
        gen_buses = buses_df[buses_df['PG'] > 0].copy()
        load_buses = buses_df[buses_df['PD'] > 0].copy()
        
        if not gen_buses.empty:
            # Sort generators by capacity
            gen_buses = gen_buses.sort_values('PG', ascending=False).head(10)
            
            fig.add_trace(
                go.Bar(
                    x=[f"Bus {int(row['BUS_NUMBER'])}" for _, row in gen_buses.iterrows()],
                    y=gen_buses['PG'],
                    marker_color='green',
                    name="Generation (MW)",
                    text=[f"{val:.1f} MW" for val in gen_buses['PG']],
                    textposition='outside'
                ),
                row=2, col=1
            )
        
        if not load_buses.empty:
            # Sort loads by demand and get top 10
            load_buses = load_buses.sort_values('PD', ascending=False).head(10)
            
            fig.add_trace(
                go.Bar(
                    x=[f"Bus {int(row['BUS_NUMBER'])}" for _, row in load_buses.iterrows()],
                    y=[-row['PD'] for _, row in load_buses.iterrows()],  # Negative to show below x-axis
                    marker_color='red',
                    name="Load (MW)",
                    text=[f"{val:.1f} MW" for val in load_buses['PD']],
                    textposition='outside'
                ),
                row=2, col=1
            )
        
        # Update layout for generation/load chart
        fig.update_xaxes(title_text="Bus Number", tickangle=45, row=2, col=1)
        fig.update_yaxes(title_text="Power (MW)", row=2, col=1)
        
        # 4. System Summary Table (bottom-right)
        # Calculate bus statistics
        total_buses = len(buses_df)
        low_voltage_buses = len(buses_df[buses_df['VM'] < 0.95])
        high_voltage_buses = len(buses_df[buses_df['VM'] > 1.05])
        normal_voltage_buses = total_buses - low_voltage_buses - high_voltage_buses
        total_generation = buses_df['PG'].sum()
        total_load = buses_df['PD'].sum()
        avg_voltage = buses_df['VM'].mean()
        min_voltage = buses_df['VM'].min()
        max_voltage = buses_df['VM'].max()
        
        # Create summary data for table
        summary_data = {
            "Metric": ["Total Buses", "Low Voltage Buses (<0.95 p.u.)", "High Voltage Buses (>1.05 p.u.)", 
                      "Normal Voltage Buses", "Average Voltage (p.u.)", "Voltage Range (p.u.)",
                      "Total Generation (MW)", "Total Load (MW)"],
            "Value": [f"{total_buses}", f"{low_voltage_buses}", f"{high_voltage_buses}", 
                     f"{normal_voltage_buses}", f"{avg_voltage:.4f}", f"{min_voltage:.4f} - {max_voltage:.4f}",
                     f"{total_generation:.2f}", f"{total_load:.2f}"]
        }
        
        fig.add_trace(
            go.Table(
                header=dict(
                    values=["<b>Metric</b>", "<b>Value</b>"],
                    fill_color='royalblue',
                    align='center',
                    font=dict(color='white', size=12)
                ),
                cells=dict(
                    values=[summary_data["Metric"], summary_data["Value"]],
                    fill_color='lavender',
                    align=['left', 'center'],
                    height=25
                )
            ),
            row=2, col=2
        )
        
        # Update overall layout
        title_prefix = ""
        if case_id is not None:
            title_prefix = f"Case {case_id}"
            if contingency_id is not None:
                title_prefix += f", Contingency {contingency_id}"
            title_prefix += " - "
            
        fig.update_layout(
            title=f"{title_prefix}Bus Analysis",
            height=800,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=50, r=50, t=100, b=50),
            template="plotly_white",
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(color='black')
        )
        
        return fig
        
    except Exception as e:
        print(f"Error creating bus analysis plot: {str(e)}")
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error creating bus analysis plot: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(color='red')
        )
        fig.update_layout(
            height=600,
            template="plotly_white",
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        return fig