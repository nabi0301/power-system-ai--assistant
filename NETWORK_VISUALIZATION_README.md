# Network Graph Visualization Integration

This document explains the network graph visualization components in the DLR Database Project and how they work together.

## Overview

The system uses the following components to provide network graph visualizations:

1. **data_viz_fall.py** - Core network graph visualization module with advanced visualization capabilities
2. **direct_network_integration.py** - Bridge module for reliable integration between main app and visualization
3. **network_comparison.py** - Creates 4-panel comparison visualizations of different case types
4. **power_viz_with_database.py** - Main application that incorporates network visualization

## Key Features

The network graph visualization system provides:

- **Network topology visualization** with buses and branches
- **Violation highlighting** with red lines for branches over 100% loading
- **Warning highlighting** with orange lines for branches over 90% loading
- **Network comparison** between Base, Contingency, SLR, and DLR cases
- **Contingency visualization** with indicators for tripped branches

## Component Integration

### How the Components Work Together

1. The **power_viz_with_database.py** application uses the `direct_network_integration.py` module to create network visualizations
2. The **direct_network_integration.py** module imports and uses `data_viz_fall.py` functions
3. The **network_comparison.py** module also uses `direct_network_integration.py` to create comparison visualizations

### Integration Flow

```
power_viz_with_database.py
    ↓ imports
direct_network_integration.py
    ↓ imports
data_viz_fall.py
```

This ensures proper error handling and reliable integration between components.

## Using Network Visualizations

### In the UI

1. Select "Enhanced Network Graph (With Violation Detection)" from the visualization dropdown
2. Optionally specify a case ID and contingency ID
3. The visualization will display with proper violation highlighting

### In the Chat Interface

You can request network visualizations by asking:
- "Show me a network graph for case 42"
- "Display a network diagram for contingency 1 in case 42"
- "Show network comparison between base case and contingency"

## Troubleshooting

If network visualizations are not displaying properly:

1. Run `test_network_integration.py` to verify all components are working
2. Check that `data_viz_fall.py`, `direct_network_integration.py`, and `network_comparison.py` are in the project directory
3. Make sure the database has proper data for the cases you're trying to visualize

## Development Notes

When modifying network visualization components:

1. Any changes to `data_viz_fall.py` will be automatically used by the integration module
2. Updates to visualization logic should focus on the core `create_network_graph` function
3. Error handling in the integration modules ensures graceful failure if visualization components have issues
4. New visualization types should be added to both the direct integration module and the main application