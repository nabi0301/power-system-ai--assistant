# 🚀 Quick Start - Dual Network Graph

## What You Get

Two network graphs displayed **side-by-side**:
- **Left**: Base case network (before contingency)
- **Right**: Contingency case network (after contingency)

Both styled identically to `data_viz_fall.py` with:
- 🔷 Curved branches (Bezier paths)
- 🎨 Color-coded violations (Red/Orange/Blue)
- 📏 Variable widths (2-8px)
- 💬 Hover tooltips with details

## How to Use

### 1. Start the Application
```bash
python power_viz_with_database.py
```

Wait for startup messages:
```
✅ Direct network integration loaded successfully
✅ Dual network graph module loaded successfully
✅ Cached 68085 base bus records
...
Running on http://127.0.0.1:8050/
```

### 2. Open Browser
Navigate to: **http://127.0.0.1:8050/**

### 3. Select Data
1. **Case ID Dropdown**: Select a base case (0-576)
   - Example: Select `0` for first case
   
2. **Contingency ID Dropdown**: Select a contingency (1-100+)
   - Example: Select `1` for first contingency
   
3. **Visualization Dropdown**: Select network view
   - Choose: `Network View` or `Fall Network`

### 4. View Result
The main plot area will show:
```
┌──────────────────────┬──────────────────────┐
│  Base Case Network   │ Contingency Network  │
│                      │                      │
│    🔺 Generators     │    🔺 Generators     │
│    ⭕ Buses/Loads    │    ⭕ Buses/Loads    │
│    ─── Branches      │    ─── Branches      │
│                      │                      │
│  🔵 Normal (90%)     │  🟠 Warning (95%)    │
│                      │  🔴 Violation (105%) │
└──────────────────────┴──────────────────────┘
     Base Case (Left)    Contingency (Right)
```

### 5. Interact
- **Hover**: Move mouse over buses/branches to see details
- **Zoom**: Scroll wheel or pinch to zoom
- **Pan**: Click and drag to move around
- **Legend**: Click legend items to show/hide categories

## Example Scenarios

### Scenario 1: Normal Operation
**Inputs**: Case ID = 0, Contingency ID = 1
**Result**: 
- Left graph: All blue (normal operation)
- Right graph: Maybe some orange (warnings after contingency)

### Scenario 2: Severe Contingency
**Inputs**: Case ID = 5, Contingency ID = 10
**Result**:
- Left graph: All blue/green (normal)
- Right graph: Red branches (violations), voltage issues

### Scenario 3: Comparison
**Action**: Try different contingencies with same base case
- Change Contingency ID: 1 → 2 → 3 → ...
- See which contingencies cause most violations

## Troubleshooting

### Issue: "Dual network visualization not available"
**Fix**: Check that `network_graph_dual_view.py` exists in project folder

### Issue: Both graphs look the same
**Check**: 
- Verify contingency_id is different from 0
- Try contingency_id = 10 for more obvious differences

### Issue: Graphs are blank
**Check**:
- Console for error messages
- Database has data for selected case/contingency
- Run test: `python network_graph_dual_view.py`

### Issue: Slow loading (>5 seconds)
**First Load**: Normal (building cache)
**Second Load**: Should be fast (<1 second)
**Still Slow**: Check network size in console

## Console Output (What to Expect)

### Successful Load
```
=== Creating Dual Network Graph for network_view ===
Using case_id=0, contingency_id=1
✅ Using network_graph_dual_view module (data_viz_fall.py style)
Creating dual network view: base case 0 + contingency 1
Creating base case graph: 118 buses, 185 branches
Creating contingency graph: 118 buses, 186 branches
✅ Successfully created dual network graph (362 traces)
```

### With Caching
```
Base case query: 0.5ms (from static cache) ✅
Contingency query: 0.05ms (from LRU cache) ✅
```

## Features Explained

### Color Coding
- **🔴 Red**: Critical violation (>100% loading)
  - Branch overloaded, immediate action needed
- **🟠 Orange**: Warning (90-100% loading)
  - Approaching limit, monitor closely
- **🔵 Blue**: Normal (0-90% loading)
  - Safe operation, intensity shows loading level

### Width Coding
- **Thick (8px)**: Violations - highly loaded
- **Medium (6px)**: Warnings - moderately loaded
- **Thin (2-4px)**: Normal - lightly loaded

### Node Symbols
- **🔺 Triangle**: Generator (produces power)
  - Yellow intensity = voltage magnitude
- **⭕ Circle**: Load/Bus (consumes power)
  - Yellow intensity = voltage magnitude

### Tooltips
**Bus Hover**:
```
Bus 15
Voltage: 1.025 pu
Angle: 5.32°
Generation: 125 MW
Load: 50 MW
```

**Branch Hover**:
```
From: Bus 10 → To: Bus 15
Apparent Power: 85.3 MVA
Loading: 94.7%
Rate A: 90.0 MVA
From Bus V: 1.020 pu
To Bus V: 1.025 pu
```

## Tips

### Best Practices
1. **Start Simple**: Begin with Case 0, Contingency 1
2. **Compare**: Keep base case, change contingencies
3. **Identify Patterns**: Which contingencies cause most violations?
4. **Use Hover**: Get exact values from tooltips
5. **Export**: Right-click graph → Save as PNG

### Performance Tips
1. **First Load**: May take 2-3 seconds (building cache)
2. **Subsequent Loads**: <1 second (using cache)
3. **Different Case**: Will rebuild cache (~2 seconds)
4. **Same Case, Different Contingency**: Fast (~0.5 seconds)

### Keyboard Shortcuts
- **Double Click**: Reset zoom
- **Shift + Drag**: Zoom to region
- **Ctrl + Scroll**: Zoom in/out

## What Makes This Special?

### Versus Single Graph
- ❌ **Old**: See base OR contingency (not both)
- ✅ **New**: See base AND contingency (compare directly)

### Versus Data Viz Fall
- ❌ **Old**: 6754 lines, complex, single graph
- ✅ **New**: 318 lines, streamlined, dual graphs, same style

### Versus Simple Visualization
- ❌ **Simple**: Just nodes and lines, no context
- ✅ **New**: Color-coded violations, variable widths, comprehensive tooltips

## Success Indicators

You'll know it's working when you see:
- ✅ Two graphs side-by-side
- ✅ Different node positions between graphs
- ✅ Color differences (base = blue, contingency = red/orange)
- ✅ Hover tooltips show electrical parameters
- ✅ Shared legend at bottom
- ✅ Graphs load in <2 seconds (first time) or <1 second (cached)

## Support

Need help?
1. Check console output for debug messages
2. Review `DUAL_NETWORK_INTEGRATION_GUIDE.md`
3. Test standalone: `python network_graph_dual_view.py`
4. Verify data: `python list_tables.py`

---

**Ready to go!** Just run `python power_viz_with_database.py` and follow steps 1-5 above. 🚀
