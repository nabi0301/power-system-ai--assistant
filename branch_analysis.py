import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from plotly.subplots import make_subplots

def create_branch_analysis_plot(branches_df, case_id=None, contingency_id=None):
    """Create a comprehensive branch analysis visualization showing power flow, loading levels,
    and violations in the system's branches."""
    
    try:
        # Create a title prefix with case information
        title_prefix = ""
        if case_id is not None:
            title_prefix = f"Case {case_id}"
            if contingency_id is not None:
                title_prefix += f", Contingency {contingency_id}"
            title_prefix += ": "
        
        # Create a figure with 2x2 subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                f"{title_prefix}Branch Loading Distribution",
                f"{title_prefix}Power Flow Analysis (PF vs QF)",
                f"{title_prefix}Most Loaded Branches",
                f"{title_prefix}System Summary"
            ),
            specs=[
                [{"type": "histogram"}, {"type": "scatter"}],
                [{"type": "bar"}, {"type": "table"}]
            ],
            vertical_spacing=0.1,
            horizontal_spacing=0.1
        )
        
        # Ensure we have the needed columns
        if 'MVA' not in branches_df.columns or 'RATE' not in branches_df.columns:
            raise ValueError("Branch data missing MVA or RATE columns")
            
        # Calculate loading percentage
        branches_df['loading_percent'] = (branches_df['MVA'] / branches_df['RATE'] * 100).fillna(0)
        
        # 1. Branch Loading Distribution Histogram (top-left)
        fig.add_trace(
            go.Histogram(
                x=branches_df['loading_percent'],
                nbinsx=20,
                marker_color='royalblue',
                name="Branch Loading Distribution",
                hovertemplate="Loading: %{x:.1f}%<br>Count: %{y}<extra></extra>"
            ),
            row=1, col=1
        )
        
        # Add reference lines for critical loading levels
        fig.add_vline(x=100, line_dash="dash", line_color="red", 
                     annotation_text="100% (Critical)", row=1, col=1)
        fig.add_vline(x=80, line_dash="dash", line_color="orange", 
                     annotation_text="80% (High)", row=1, col=1)
        
        # Update layout for the histogram
        fig.update_xaxes(title_text="Loading Percentage (%)", range=[0, max(150, branches_df['loading_percent'].max()*1.1)], row=1, col=1)
        fig.update_yaxes(title_text="Number of Branches", row=1, col=1)
        
        # 2. Power Flow Analysis Scatter Plot (top-right)
        fig.add_trace(
            go.Scatter(
                x=branches_df['PF'],
                y=branches_df['QF'],
                mode='markers',
                marker=dict(
                    size=8,
                    color=branches_df['loading_percent'],
                    colorscale='Viridis',
                    colorbar=dict(
                        title="Loading %",
                        thickness=15,
                        len=0.5,
                        y=0.8,
                        yanchor="top"
                    ),
                    showscale=True
                ),
                text=[f"From: {int(row['From_Bus'])} To: {int(row['To_Bus'])}<br>PF: {row['PF']:.2f} MW<br>QF: {row['QF']:.2f} MVAR<br>Loading: {row['loading_percent']:.1f}%" 
                      for _, row in branches_df.iterrows()],
                hoverinfo="text",
                name="Branch Power Flow"
            ),
            row=1, col=2
        )
        
        # Update layout for the scatter plot
        fig.update_xaxes(title_text="Active Power Flow (MW)", row=1, col=2)
        fig.update_yaxes(title_text="Reactive Power Flow (MVAR)", row=1, col=2)
        
        # 3. Most Loaded Branches Bar Chart (bottom-left)
        # Sort by loading percentage and get top 10
        top_branches = branches_df.sort_values('loading_percent', ascending=False).head(10)
        branch_labels = [f"{int(row['From_Bus'])}-{int(row['To_Bus'])}" for _, row in top_branches.iterrows()]
        loading_values = top_branches['loading_percent']
        
        # Color based on loading
        bar_colors = ['red' if load > 100 else 
                     'orange' if load > 80 else 
                     'green' for load in loading_values]
        
        fig.add_trace(
            go.Bar(
                x=branch_labels,
                y=loading_values,
                marker_color=bar_colors,
                text=[f"{val:.1f}%" for val in loading_values],
                textposition='outside',
                name="Most Loaded Branches"
            ),
            row=2, col=1
        )
        
        # Add reference line for 100% loading
        fig.add_shape(
            type="line", line=dict(dash="dash", color="red"),
            x0=-0.5, x1=len(branch_labels) - 0.5, y0=100, y1=100,
            row=2, col=1
        )
        
        # Update layout for the bar chart
        fig.update_xaxes(title_text="Branch (From-To)", tickangle=45, row=2, col=1)
        fig.update_yaxes(title_text="Loading (%)", range=[0, max(150, loading_values.max()*1.1)], row=2, col=1)
        
        # 4. System Summary Table (bottom-right)
        # Calculate branch statistics
        total_branches = len(branches_df)
        overloaded_branches = len(branches_df[branches_df['loading_percent'] > 100])
        highly_loaded_branches = len(branches_df[(branches_df['loading_percent'] > 80) & (branches_df['loading_percent'] <= 100)])
        avg_loading = branches_df['loading_percent'].mean()
        max_loading = branches_df['loading_percent'].max()
        min_loading = branches_df['loading_percent'].min()
        total_mw_flow = abs(branches_df['PF']).sum()
        total_mvar_flow = abs(branches_df['QF']).sum()
        
        # Create summary data for table
        summary_data = {
            "Metric": ["Total Branches", "Overloaded Branches", "Highly Loaded Branches", 
                      "Average Loading (%)", "Maximum Loading (%)", "Minimum Loading (%)",
                      "Total MW Flow", "Total MVAR Flow"],
            "Value": [f"{total_branches}", f"{overloaded_branches}", f"{highly_loaded_branches}", 
                     f"{avg_loading:.2f}%", f"{max_loading:.2f}%", f"{min_loading:.2f}%",
                     f"{total_mw_flow:.2f}", f"{total_mvar_flow:.2f}"]
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
        
        # Update overall layout with case and contingency information
        title_prefix = ""
        if case_id is not None:
            title_prefix = f"Case {case_id}"
            if contingency_id is not None:
                title_prefix += f", Contingency {contingency_id}"
            title_prefix += " - "
            
        fig.update_layout(
            title=f"{title_prefix}Branch Power Flow Analysis",
            height=800,
            showlegend=False,
            margin=dict(l=50, r=50, t=100, b=50),
            template="plotly_white",
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(color='black')
        )
        
        return fig
        
    except Exception as e:
        error_msg = f"Error creating branch analysis plot: {str(e)}"
        case_info = ""
        if case_id is not None:
            case_info = f"Case {case_id}"
            if contingency_id is not None:
                case_info += f", Contingency {contingency_id}"
            error_msg = f"Error creating branch analysis for {case_info}: {str(e)}"
            
        print(error_msg)
        fig = go.Figure()
        fig.add_annotation(
            text=error_msg,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(color='red')
        )
        fig.update_layout(
            height=600, 
            title=f"Branch Analysis Error - {case_info}" if case_info else "Branch Analysis Error",
            template="plotly_white",
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        return fig