# Quick Reference: Network Graph AI Commands

## ✅ Status: OPERATIONAL

The network graph visualization is now fully integrated with the AI assistant!

## How to Use

### Simply ask the AI assistant using natural language:

#### Basic Commands:
- "show network graph"
- "display network"
- "show the network"
- "network topology"
- "show me the network diagram"

#### Advanced Commands:
- "show network for case 42"
- "display network with contingency 5"
- "show network topology for case 100"
- "I want to see the network"

## What Happens

1. **You type**: "show network graph"
2. **AI responds**: Explains what it will show
3. **System switches**: Automatically to network visualization
4. **Graph displays**: Interactive network topology appears

## Features

### The network graph shows:
- ✅ All buses (nodes) in the system
- ✅ Transmission lines (branches)
- ✅ Color-coded loading levels
- ✅ Voltage information
- ✅ Interactive zoom and pan
- ✅ Hover details for each component

### You can:
- 🖱️ Zoom in/out
- 👆 Click and drag to pan
- 📌 Hover over components for details
- 💾 Export as image (using Plotly controls)

## System Status Indicators

### On Startup:
Look for this message:
```
✅ Enhanced network graphs system loaded successfully
```

### When You Make a Request:
Console will show one of:
```
AI Assistant: Detected enhanced network graph request
```
or
```
AI Assistant: Detected simple network graph request
```

## Troubleshooting

### Network graph not showing?
1. Check the dropdown is set to "Network View"
2. Try refreshing the page
3. Check console for error messages

### Want a specific case?
Include the case number in your request:
- "show network for case 42"
- "display case 50 network"

## Technical Info

- **Module**: `enhanced_network_graphs.py`
- **Integration**: `power_viz_with_database.py`
- **Visualization**: `direct_network_integration.py` → `data_viz_fall.py`
- **Case Management**: `dynamic_case_management.py`

## Application URL

Once running, access at:
**http://127.0.0.1:8054**

---

**Ready to use!** Just start the application and ask for the network graph! 🎉
