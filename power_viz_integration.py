"""
Integration Module for data_viz_fall.py
--------------------------------------
This file provides functions to integrate power_viz_component.py
into data_viz_fall.py as a replacement for the statistical analysis tab.
"""

import dash
from dash import html, dcc, Input, Output, callback_context
import dash_bootstrap_components as dbc
import os
import sys
import importlib.util

# Import the PowerVizComponent from power_viz_component.py
def load_power_viz_component():
    """Dynamically load the PowerVizComponent from power_viz_component.py"""
    try:
        module_path = os.path.join(os.path.dirname(__file__), 'power_viz_component.py')
        spec = importlib.util.spec_from_file_location("power_viz_component", module_path)
        power_viz_comp = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(power_viz_comp)
        print("✅ Successfully loaded power_viz_component module")
        return power_viz_comp.PowerVizComponent(), power_viz_comp.register_power_viz_callbacks
    except Exception as e:
        print(f"❌ Error loading power_viz_component module: {e}")
        return None, None

def get_power_viz_tab():
    """Get the power visualization tab to replace the statistical analysis tab"""
    try:
        # Load PowerVizComponent
        power_viz_component, _ = load_power_viz_component()
        
        if power_viz_component:
            # Create tab with the PowerVizComponent's layout
            power_viz_tab = dbc.Tab(
                power_viz_component.get_layout(),
                label="Power Visualization",
                tab_id="power-viz-tab",
                className="mt-1"
            )
            return power_viz_tab
        else:
            # Return a placeholder tab if component couldn't be loaded
            error_tab = dbc.Tab(
                dbc.Container([
                    html.H3("Error Loading Power Visualization Component", 
                           className="text-center text-danger mb-4"),
                    html.P("There was an error loading the Power Visualization component. Please check the console for details.",
                          className="text-center")
                ]),
                label="Power Visualization",
                tab_id="power-viz-tab",
                className="mt-1"
            )
            return error_tab
    except Exception as e:
        print(f"Error creating power visualization tab: {e}")
        # Return a placeholder tab if there was an error
        error_tab = dbc.Tab(
            dbc.Container([
                html.H3("Error Loading Power Visualization", 
                       className="text-center text-danger mb-4"),
                html.P(f"Error: {str(e)}",
                      className="text-center")
            ]),
            label="Power Visualization",
            tab_id="power-viz-tab",
            className="mt-1"
        )
        return error_tab

def integrate_power_viz_into_dataviz_fall(app):
    """
    Register the PowerVizComponent callbacks with the provided app
    
    Parameters:
    app (dash.Dash): The Dash application instance from data_viz_fall.py
    """
    try:
        # Load the registration function for callbacks
        _, register_callbacks = load_power_viz_component()
        
        if register_callbacks:
            # Register callbacks with the app
            register_callbacks(app)
            print("✅ Successfully registered Power Visualization callbacks")
            return True
        else:
            print("❌ Failed to register Power Visualization callbacks")
            return False
    except Exception as e:
        print(f"Error registering power visualization callbacks: {e}")
        return False