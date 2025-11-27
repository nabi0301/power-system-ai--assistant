# Schemdraw One-Line Diagram Integration

## Overview
Enhanced the power system visualization to use **schemdraw** for creating professional, organized one-line diagrams with minimal overlapping.

## Features

### ✅ Professional One-Line Diagram Symbols
- **⚡ Generators**: SourceSin symbol with generator ID
- **🏭 Loads**: Resistor symbol with load value (MW)
- **🔵 Transit Buses**: Simple bus bar with voltage display
- **— Transmission Lines**: Color-coded lines with loading percentages

### ✅ Organized Hierarchical Layout
- **Voltage Level Grouping**: Buses organized by voltage level (345kV, 138kV, 69kV, etc.)
- **Top-Down Hierarchy**: Higher voltage levels at top, lower at bottom
- **Dynamic Spacing**: Automatic spacing based on number of buses at each level
- **Zero Overlapping**: Hierarchical layout ensures clear separation

### ✅ Color Logic (Same as Network View)
**Bus Colors (Voltage-based):**
- 🔴 Red: Critical violations (< 0.90 or > 1.10 pu)
- 🟠 Orange: Low voltage (< 0.95 pu)
- 🟡 Yellow: High voltage (> 1.05 pu)
- 🔵 Light Blue: Normal (0.95-1.05 pu)

**Line Colors (Loading-based):**
- 🔴 Red: **Violations** (MVA > RATE or VIO ≥ 99.99)
- 🟠 Orange: Heavy loading (> 90%)
- 🟡 Yellow: Moderate loading (> 70%)
- ⚪ Gray: Normal loading (< 70%)

## Installation

```bash
# Install schemdraw
pip install schemdraw

# Or with conda
conda install -c conda-forge schemdraw
```

## Usage

The one-line diagram is automatically used when:
1. Schemdraw is installed and available
2. Network view is selected
3. Valid bus and branch data exists

**Fallback**: If schemdraw is not available, the system automatically falls back to the standard Plotly network graph.

## Technical Details

### Function: `create_schemdraw_one_line_diagram()`
**Location**: `power_viz_with_database.py` (after `classify_bus_type()` function)

**Parameters:**
- `buses_df`: Bus data with columns [BUS_NUMBER, VM, VA, PG, PD, BASE_KV]
- `branches_df`: Branch data with columns [FROM_BUS, TO_BUS, MVA, RATE, VIO]
- `case_id`: Case identifier
- `contingency_id`: Contingency identifier (optional)

**Returns:**
- Plotly Figure with schemdraw diagram as embedded image

### Layout Algorithm

1. **Topology Analysis**: Uses NetworkX to analyze network connectivity
2. **Voltage Grouping**: Groups buses by BASE_KV voltage level
3. **Hierarchical Placement**: 
   - Sorts voltage levels (highest to lowest)
   - Places buses horizontally at each voltage level
   - Dynamic spacing: `x_spacing = max(3, 20 / num_buses_at_level)`
   - Vertical spacing: 4 units between levels

4. **Symbol Selection**:
   - `PG > 0, PD = 0`: Generator (SourceSin symbol)
   - `PD > 0`: Load (Resistor symbol)
   - Otherwise: Transit bus (Dot symbol)

5. **Line Drawing**: Direct connections between bus positions with color-coded loading

### Image Export
- Renders schemdraw drawing to PNG at 150 DPI
- Converts to base64 for embedding in Plotly
- Displays as layout image with legend annotations

## Advantages Over Standard Network Graph

| Feature | Schemdraw One-Line | Standard Plotly Graph |
|---------|-------------------|----------------------|
| Symbol Standards | ✅ IEEE standard symbols | ❌ Generic nodes |
| Layout | ✅ Hierarchical by voltage | ⚠️ Force-directed |
| Overlapping | ✅ Zero overlap | ⚠️ Some overlap |
| Readability | ✅ Professional diagram | ⚠️ Abstract network |
| Scalability | ✅ Handles large systems | ⚠️ Cluttered at scale |
| Color Logic | ✅ Maintained | ✅ Maintained |

## Integration Points

### Modified Function: `update_visualization()`
**Location**: Line ~12380 in `power_viz_with_database.py`

```python
# Try schemdraw one-line diagram first
if SCHEMDRAW_AVAILABLE:
    schemdraw_fig = create_schemdraw_one_line_diagram(...)
    if schemdraw_fig is not None:
        return schemdraw_fig

# Fallback to standard network graph
network_fig = create_network_graph(...)
```

## Example Output

```
📐 Creating schemdraw one-line diagram for case 42, contingency None
✅ Schemdraw one-line diagram created with 118 buses and 186 branches

Hierarchical Layout:
- 345 kV Level: 15 buses (top)
- 138 kV Level: 65 buses (middle)
- 69 kV Level: 38 buses (bottom)

Color Distribution:
- 🔵 Normal voltage buses: 112
- 🟠 Low voltage buses: 4
- 🔴 Violations: 2
- 🟠 Heavy loaded lines: 8
- 🔴 Violated lines: 3
```

## Benefits

1. **Zero Overlapping**: Hierarchical layout eliminates node overlap
2. **Professional Appearance**: Uses standard power system symbols
3. **Clear Hierarchy**: Voltage levels clearly separated
4. **Maintained Logic**: All existing color coding preserved
5. **Automatic Fallback**: Gracefully handles missing schemdraw installation
6. **Scalable**: Works well for IEEE 14-bus to IEEE 300-bus systems

## Future Enhancements

- Add zone/area grouping for multi-area systems
- Interactive element selection
- Export to SVG/PDF formats
- Configurable symbol styles
- Automatic substation grouping

---

**Created**: November 12, 2025
**Author**: Power System Visualization Enhancement
**Status**: ✅ Active and Working
