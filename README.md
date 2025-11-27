# Power System Visualization Project

## Quick Start Guide

### Enh### Troubleshooting

### Common Issues
- If applications don't start, ensure Python environment is activated
- If visualization doesn't load, check port availability (8054, 8056, or 8057)
- If "refused to connect" errors occur, wait a few seconds and refresh the page
- The Fall 2025 visualization may use port 8056 or 8057 depending on availability
- If export fails, ensure you have write permissions to your downloads folderVisualization (data_viz_fall.py)

```bash
C:/Projects/dlr-database-project/dlr-env/Scripts/python.exe data_viz_fall.py
```

Then open: http://127.0.0.1:8056

### Main Application (power_viz_with_database.py)

```bash
C:/Projects/dlr-database-project/dlr-env/Scripts/python.exe power_viz_with_database.py
```

Then open: http://127.0.0.1:8054

## Key Features

### Enhanced Fall 2025 Visualization (data_viz_fall.py)
- **Multiple layout options**: Switch between Grid and Radial layouts
- **SVG export**: Download high-resolution SVG visualizations for reports and presentations
- **Enhanced bus numbering**: Clear bus identification with prominent numbers
- **Voltage-based organization**: Buses grouped by voltage level in radial layout
- **Alternating transmission line colors**: Easy distinction between different lines

### Main Application (power_viz_with_database.py)
- **Multiple visualization types**: Choose from several power system visualizations
- **Real database integration**: Uses actual IEEE 118-bus system data
- **AI Assistant integration**: Smart context-aware insights
- **Launch Fall 2025 visualization**: Access enhanced visualization from dropdown

## Enhanced Visualization Features

### Grid Layout
- Traditional grid-based visualization with improved bus numbering
- Buses arranged in a grid pattern with numbers clearly visible
- Color-coded buses based on voltage magnitude
- Size of buses indicates load demand
- Transmission lines with alternating colors to distinguish connections

### Radial Layout
- Innovative circular/radial layout with voltage-level based organization
- Higher voltage buses placed closer to the center
- Buses grouped into concentric circles by voltage level
- Color-coded voltage regions for quick identification
- Easier visualization of system hierarchy and structure

## Usage Instructions

### Switching Between Layouts
1. Open data_viz_fall.py application (http://127.0.0.1:8055)
2. Use the "Select Visualization Layout" dropdown at the top of the page
3. Choose either "Grid Layout" or "Radial Layout"

### Exporting as SVG
1. Select your preferred layout (Grid or Radial)
2. Click the "Download as SVG" button
3. The SVG will be downloaded with a timestamp in the filename
4. SVG exports are larger (1800 x 1600 pixels) for high-quality printing

### Interpreting the Visualization
- **Grid Layout**: Bus numbers are shown directly on the visualization
- **Radial Layout**: Buses are organized by voltage level groups
- **Hover over buses**: See detailed information (voltage, load, kV)
- **Hover over lines**: View loading information (MVA, rating, percentage)
- **Line colors**: Alternating colors help distinguish between different transmission lines

## Troubleshooting

### Common Issues
- If applications don't start, ensure Python environment is activated
- If visualization doesn't load, check port availability (8054 and 8055)
- If export fails, ensure you have write permissions to your downloads folder

### Restarting Applications
To restart an application, stop the current process and run the Python script again:
```powershell
Stop-Process -Name python -ErrorAction SilentlyContinue
C:/Projects/dlr-database-project/dlr-env/Scripts/python.exe data_viz_fall.py
```