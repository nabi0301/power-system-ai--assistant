# AI Assistant with Network Graph Visualization

This enhancement enables the AI assistant to display network graphs for specific cases based on user requests.

## Features Added

- AI assistant can now recognize requests to show network graphs
- Support for case-specific network visualization requests
- **Contingency visualization support** - view network graphs for specific contingency scenarios
- Integration with data_viz_fall.py's advanced network visualization
- Natural language processing to extract case IDs and visualization preferences
- Enhanced entity extraction to detect network graph related keywords
- Smart suggestions for follow-up analyses based on current visualization

## How to Use

1. Run the application using the `run_network_ai_assistant.bat` script
2. In the AI chat interface, you can ask for network visualizations in several ways:

### Example Commands:

#### For Base Cases:
- "Show me the network graph for case 5"
- "Display network diagram of case 10"
- "I want to see the fall network visualization for case 7"
- "Network graph for case 15"
- "Show me the data_viz_fall network for case 20"

#### For Contingency Cases:
- "Show network graph for case 42, contingency 3"
- "Display network diagram for contingency 5 of case 10"
- "Show me the contingency network for case 7, contingency 2"
- "Network graph for case 15 with contingency 8"
- "I need to see contingency 4 network diagram for case 30"

## Implementation Details

The implementation includes:

1. Enhanced entity extraction in `entity_extraction.py` to detect network visualization requests
2. Updated visualization commands in `power_viz_with_database.py` to include "fall_network" visualization
3. New AI response handling in `get_ai_response()` for network graph requests
4. Integration with the existing `create_power_system_plot()` function that uses data_viz_fall.py's advanced visualization

## Troubleshooting

If you encounter issues with the network visualization:

1. Ensure data_viz_fall.py is in the same directory as power_viz_with_database.py
2. Check that the required data is available in the database for the requested case
3. Verify that the AI assistant correctly extracts the case ID from your request
4. Check the console output for any error messages during visualization rendering