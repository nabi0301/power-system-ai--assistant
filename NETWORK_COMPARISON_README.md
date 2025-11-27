# Network Comparison Visualization

This feature provides a comprehensive side-by-side comparison of four network visualizations:
1. Base Case
2. Contingency Case
3. Static Line Rating (SLR) Case
4. Dynamic Line Rating (DLR) Case

## Features

- **Quadrant View**: All four network visualizations shown in a single view
- **Consistent Scaling**: All networks use the same coordinate system and color scales for easy comparison
- **Case-specific Visualization**: Select any base case and contingency combination
- **AI Assistant Integration**: Request comparisons using natural language
- **Interactive Elements**: Hover over buses and lines to see detailed information
- **Data Availability Check**: Automatically verifies data exists before visualization
- **Graceful Error Handling**: Shows placeholders with explanations when data is missing
- **Smart Suggestions**: Recommends cases with complete data when requested data is missing

## How to Use

### Via the User Interface:

1. Select "Network Comparison (Base, Cont, SLR, DLR)" from the visualization dropdown
2. Enter a base case ID (e.g., 5)
3. Optionally enter a contingency ID (e.g., 2)
4. Click the "Update" button to generate the comparison

### Via the AI Assistant:

Simply ask for a network comparison using natural language. Examples:

- "Compare network graphs for case 5"
- "Show network comparison for case 10, contingency 3"
- "Compare base, contingency, SLR and DLR networks for case 42"
- "Show all four network views for case 7"
- "Compare network graphs for SLR vs DLR in case 15"

## What You'll See

Each quadrant shows a different aspect of the power system:

**Top Left: Base Case**
- The original power system without any contingencies
- Standard network topology and loading conditions

**Top Right: Contingency Case**
- Shows how the system looks with a specified contingency
- Highlights changes in topology and loading due to the contingency

**Bottom Left: SLR (Static Line Rating) Case**
- Shows the system with standard static thermal limits
- Identifies potentially overloaded lines using conservative ratings

## Data Availability

The visualization system automatically checks for data availability across all four required datasets:

1. **Base Case Data**: Required for all visualizations (tables: `BaseBusData`, `BaseBranchData`)
2. **Contingency Data**: Required for contingency visualization (tables: `ContingencyBusData`, `ContingencyBranchData`)
3. **SLR Data**: Required for SLR visualization (table: `SLR_Branches`)
4. **DLR Data**: Required for DLR visualization (table: `DLR_Branches`)

### Handling Missing Data

When data is missing, the system:

- Provides clear feedback about which datasets are available/missing
- Shows informative placeholders in place of missing visualizations
- Updates the visualization title to indicate data availability (e.g., "Network Comparison (3/4 datasets available)")
- Offers suggestions for cases that have complete data

### Finding Complete Cases

If you encounter missing data, you can:

1. Ask the AI Assistant: "What cases have complete network comparison data?"
2. Run the test script: `test_network_comparison.bat`
3. Use the API: `from data_availability import get_available_cases`

**Bottom Right: DLR (Dynamic Line Rating) Case**
- Shows the system with weather-adjusted dynamic thermal limits
- Demonstrates how DLR can increase line capacity and reduce congestion

## Technical Implementation

This feature leverages the `create_network_graph` function from `data_viz_fall.py` and combines it with a new quadrant-based visualization system. The implementation:

1. Loads data for all four scenarios from the database
2. Creates individual network visualizations for each scenario
3. Combines them into a synchronized 2×2 grid visualization
4. Ensures consistent scaling, coloring, and coordinate systems

## Testing

Run the `test_network_comparison.bat` script to test this feature.