# Power Visualization Integration Guide

This guide explains how to integrate the power visualization system from `power_viz_with_database.py` into `data_viz_fall.py` as a replacement for the Statistical Analysis tab.

## Files Overview

1. `power_viz_component.py` - The main component that encapsulates power visualization functionality
2. `power_viz_integration.py` - Integration helpers to incorporate the component into data_viz_fall.py
3. `integrate_power_viz.py` - Script to automate the integration process 
4. `run_integrated_app.py` - Helper to run the integrated application
5. `integrate_and_run.bat` - Windows batch file to integrate and run in one step

## Integration Process

### Option 1: Automatic Integration (Recommended)

1. Run the integration script to automatically replace the Statistical Analysis tab:

```bash
python integrate_power_viz.py
```

2. After successful integration, run the application:

```bash
python run_integrated_app.py
```

Alternatively, you can run the batch file to do both steps:

```bash
integrate_and_run.bat
```

### Option 2: Manual Integration

If the automatic integration fails, follow these manual steps:

1. Open `data_viz_fall.py` and locate the import section
2. Add the following import:

```python
# Import power visualization integration
from power_viz_integration import get_power_viz_tab, integrate_power_viz_into_dataviz_fall
```

3. Find the Statistical Analysis tab definition (around line 5200)
4. Replace:

```python
dbc.Tab(
    label="Statistical Analysis",
    tab_id="stats-tab",
    children=[
        # ... existing content ...
    ]
),
```

with:

```python
dbc.Tab(
    label="Power Visualization",
    tab_id="stats-tab",
    children=[
        # Power Visualization tab content from power_viz_component.py
        get_power_viz_tab().children
    ],
),
```

5. Find the server initialization section at the end of the file and add:

```python
# Integrate power visualization component
integrate_power_viz_into_dataviz_fall(app)
```

before `app.run_server(...)`

## Features

The integrated power visualization system provides:

- Network visualization with real-time database data
- Voltage analysis tools
- Loading analysis tools 
- Violation detection and visualization
- SLR vs DLR comparison capabilities
- Generator dispatch analysis
- AI Assistant for power system insights (optional)

## Troubleshooting

If you encounter issues:

- Check that all required files exist in the project directory
- Ensure the database path is correct (default is 'data.db')
- Look for any Python import errors in the console output
- If the integration fails, restore from the backup file `data_viz_fall.py.bak`

## Reverting Changes

To revert the integration, simply copy the backup file back to the original:

```bash
copy data_viz_fall.py.bak data_viz_fall.py
```