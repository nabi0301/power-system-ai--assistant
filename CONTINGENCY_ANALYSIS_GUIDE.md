# Quick Start Guide: Contingency Case Analysis

## How to Use Branch and Bus Analysis for Contingency Cases

### Step 1: Access the Application
Open your browser and navigate to: **http://127.0.0.1:8054**

### Step 2: Select a Case
In the interface, you'll find dropdown selectors:
1. **Case Selector**: Choose a base case ID (e.g., 0, 1, 2, etc.)
2. **Contingency Selector**: Choose a contingency case ID (e.g., 1, 2, 3, etc.)
   - Select "Base Case" or leave blank to view base case data
   - Select a number to view a specific contingency case

### Step 3: Choose Analysis Type
From the **Visualization Selector** dropdown, select:
- **Branch Analysis** - For comprehensive branch/transmission line analysis
- **Bus Analysis** - For comprehensive bus/node voltage analysis

### Step 4: View Results
The visualization will display with a title indicating the case and contingency:
- Example: "Case 0, Contingency 1: Branch Loading Distribution"
- Example: "Case 0: Bus Voltage Profile" (for base case)

## What You'll See

### Branch Analysis (4 Interactive Plots)
1. **Branch Loading Distribution**
   - Histogram showing distribution of branch loading percentages
   - Reference lines at 80% (high) and 100% (critical)
   
2. **Power Flow Analysis (PF vs QF)**
   - Scatter plot of active vs reactive power flow
   - Color-coded by loading percentage
   - Hover to see branch details
   
3. **Most Loaded Branches**
   - Bar chart of top 10 most loaded branches
   - Color-coded: green (normal), orange (high), red (overloaded)
   - Shows branch names (From-To)
   
4. **System Summary**
   - Statistical table with key metrics
   - Total branches, average loading, violations
   - Min/max loading values

### Bus Analysis (4 Interactive Plots)
1. **Bus Voltage Profile**
   - Scatter plot showing voltage at each bus
   - Reference lines at 0.95 p.u. and 1.05 p.u. (limits)
   - Color-coded: green (normal), orange/red (violation)
   
2. **Voltage Distribution Histogram**
   - Distribution of voltage levels across all buses
   - Reference lines at voltage limits
   
3. **Generation and Load Distribution**
   - Bar chart comparing generation (PG) and load (PD)
   - Shows power balance across buses
   
4. **System Summary**
   - Statistical table with voltage statistics
   - Count of buses at different voltage levels
   - Violations and average voltage

## Performance Features

### Caching
- **First Load**: May take 1-3 seconds (queries database)
- **Subsequent Loads**: < 0.1 seconds (uses cached data)
- Cache stores up to 128 different case/contingency combinations

### Timing Information
Check the terminal/console for performance metrics:
```
⏱️ Data fetch took 0.35 seconds
⏱️ Visualization took 0.12 seconds
⏱️ Total time: 0.47 seconds
```

## Available Contingency Data

### Database Statistics
- **Total Contingency Bus Records**: 12.5 million
- **Total Contingency Branch Records**: 19.7 million
- **Cases Available**: 577 base cases
- **Contingencies per Case**: ~186 contingency scenarios

### Typical Case Structure
- **Base Case 0**: Original system configuration
- **Contingency 1-186**: Various N-1 contingency scenarios
  - Line outages
  - Transformer outages
  - Generator outages
  - Load variations

## Tips for Analysis

### Comparing Cases
1. Load Branch Analysis for **Base Case 0**
2. Note the loading levels and violations
3. Switch to **Contingency 1** (same case, different contingency)
4. Compare the changes in branch loading
5. Use the cached data feature to quickly switch between views

### Finding Critical Contingencies
1. Use the AI chat to ask: "Which contingencies have the most violations?"
2. Or manually browse through contingency IDs
3. Look for high loading percentages (> 100%) in red
4. Check for voltage violations outside 0.95-1.05 p.u. range

### Understanding Results
- **Branch Loading > 100%**: Overloaded line (potential failure)
- **Voltage < 0.95 p.u.**: Low voltage violation
- **Voltage > 1.05 p.u.**: High voltage violation
- **Green indicators**: System within limits
- **Red indicators**: Violations requiring attention

## Troubleshooting

### No Data Displayed
- **Check case ID**: Make sure the case exists in the database
- **Check contingency ID**: Ensure contingency exists for that case
- **Check console**: Look for error messages in the terminal

### Slow Loading
- **First load is normal**: Database query takes time
- **Check cache**: Subsequent loads should be fast
- **Large datasets**: 12M+ rows requires indexing (see optimization guide)

### Column Errors
- **Auto-normalized**: System automatically converts bus_number to BUS_NUMBER
- **If errors persist**: Check the terminal for debug output
- **Report issues**: Include case_id and contingency_id with error

## Advanced Features

### AI Chat Integration
Ask questions like:
- "Show branch analysis for case 5 contingency 10"
- "Compare bus voltages between base case and contingency 1"
- "What are the most critical contingencies?"

### Network Graph Integration
- Select "Network View" to see visual topology
- Combined with Branch/Bus Analysis for comprehensive understanding
- Color-coded nodes and edges show violations

### Export Options
- Right-click on any plot to:
  - Download as PNG
  - Zoom/Pan for detailed view
  - Toggle traces on/off
  - Reset axes

## Next Steps

1. **Try the test cases**: Start with Case 0, Contingency 1
2. **Explore different cases**: See how contingencies affect the system
3. **Use AI assistant**: Ask for specific analysis or comparisons
4. **Check documentation**: See CONTINGENCY_ANALYSIS_IMPLEMENTATION.md for technical details

## Need Help?
- Check the terminal output for detailed debug information
- Look for log messages starting with ✅, ⚠️, or ❌
- Review CONTINGENCY_ANALYSIS_IMPLEMENTATION.md for technical details
- Test with the provided test_contingency_analysis.py script
