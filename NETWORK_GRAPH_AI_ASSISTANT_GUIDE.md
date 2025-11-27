# Network Graph AI Assistant Integration

## Overview

This document provides instructions for using the AI assistant with network graph visualization capabilities in the Power Systems Analysis Tool.

## Using Network Graphs with the AI Assistant

The AI assistant can now show network graphs when requested. You can use the following commands:

1. **Show basic network graph**: 
   - "Show network graph for case 42"
   - "Display network diagram"
   - "Show power system network"

2. **Show network graph with contingency**:
   - "Show network graph for case 42, contingency 5"
   - "Display network with contingency 3"

3. **Show network comparison**:
   - "Compare network graphs"
   - "Show network comparison for case 42"
   - "Display SLR vs DLR network comparison"

## Troubleshooting

If the AI assistant is not able to show network graphs:

1. Make sure you're using the `start_power_viz.py` script to start the application
2. Check that all required packages are installed
3. Verify that `data_viz_fall.py` and `direct_network_integration.py` are in the same directory

## Technical Details

The network graph integration uses:
- `direct_network_integration.py` as a bridge between the AI assistant and visualization
- `data_viz_fall.py` for the actual network graph rendering
- Column name mapping to ensure compatibility between database schemas

## Quick Start

To start the application with full network graph capabilities:

```bash
python start_power_viz.py
```

Then use the AI assistant to request network visualizations.