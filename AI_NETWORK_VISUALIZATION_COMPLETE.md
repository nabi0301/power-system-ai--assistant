# AI Assistant Network Graph Visualization - Complete Guide

## Overview
The AI assistant can now automatically trigger network graph visualizations when users request them through natural language. This provides a seamless, intuitive way to view power system topology without manually selecting from dropdowns.

## Features

### 1. Natural Language Detection
The AI assistant understands multiple ways users might request network graphs:
- "show network graph"
- "display network"
- "network topology"
- "show topology"  
- "network diagram"
- "network view"
- "show me the network"
- "can I see the network?"
- And many more variations...

### 2. Automatic Visualization Switching
When the AI detects a network graph request:
1. ✅ Recognizes the intent from user's message
2. ✅ Automatically changes the dropdown to "Network View"
3. ✅ Triggers the network visualization
4. ✅ Uses first available case if none specified
5. ✅ Provides helpful response message

### 3. Case-Specific Requests
Users can also request specific cases:
- "show network for case 5"
- "display network graph case 10"
- "network topology for case 0"

The AI will extract the case number and display that specific case.

## Technical Implementation

### Components

#### 1. Enhanced Network Detection (`enhanced_network_graphs.py`)
```python
# Detects network requests with 25+ keyword patterns
has_network_graph_request(user_message)

# Extracts case/contingency IDs
extract_network_graph_request(user_message)

# Generates contextual responses
generate_network_graph_response(request_info, available_cases)
```

#### 2. AI Response Handler (`get_ai_response()`)
```python
# Priority check for enhanced network detection
if ENHANCED_NETWORK_GRAPHS_AVAILABLE and has_network_graph_request(user_message):
    response, viz_type, case_id, contingency_id = generate_network_graph_response(...)
    return response, viz_type, case_id, contingency_id

# Fallback for simple keyword matching
network_keywords = ['network graph', 'show network', 'display network', ...]
if any(keyword in message_lower for keyword in network_keywords):
    return response, 'network_view', None, None
```

#### 3. Chat Message Handler (`handle_chat_message()`)
- Receives user message
- Calls `get_ai_response()` to analyze intent
- Extracts visualization command (viz_type, case_id, contingency_id)
- Stores command in hidden div (`viz-command-store`)
- Displays AI response to user

#### 4. Visualization Update Callback (`update_viz_selector_from_ai()`)
- Listens to `viz-command-store`
- Parses JSON with visualization info
- Validates visualization type against allowed types:
  ```python
  valid_viz_types = [
      'voltage', 'loading', 'violations', 'comparison',
      'generators', 'network', 'network_view', 'fall_network', 'network_comparison',
      'case_analysis', 'branch_analysis', 'bus_analysis'
  ]
  ```
- Updates dropdown selector value
- Passes case_id and contingency_id to visualization renderer

#### 5. Dynamic Plot Update (`update_dynamic_plot()`)
- Receives selected visualization type and case IDs from dropdown or AI
- For network visualizations without case_id:
  - Automatically assigns first available case
  - Uses dynamic case management
- Calls `update_visualization()` to render the graph

## Usage Examples

### Basic Network Request
**User:** "show network graph"

**AI Response:**
```
🌐 Network Graph Visualization

I'll display the power system network topology for you. The network graph shows:
• All buses (nodes) in the system
• Transmission lines (branches) connecting them
• Color-coded loading levels on branches
• Voltage levels at each bus

You can interact with the graph to zoom, pan, and see detailed information about each component.
```

**Action:** Dropdown automatically changes to "Network View", network graph displays with case 0

### Case-Specific Request
**User:** "show me network for case 5"

**AI Response:**
```
🌐 Network Graph for Case 5

Displaying network topology for Case 5...
[Network visualization appears]
```

**Action:** Network graph displays for the specified case

### Variations That Work
All of these will trigger network visualization:
- "network"
- "show topology"
- "can you display the network?"
- "I want to see the network diagram"
- "network view please"
- "show me the power system network"

## Testing

### Test Steps
1. **Start Application:**
   ```bash
   python power_viz_with_database.py
   ```

2. **Open Browser:**
   http://127.0.0.1:8054

3. **Click Robot Icon** (bottom-left) to open AI chat

4. **Test Basic Request:**
   - Type: "show network graph"
   - Press Send
   - Verify dropdown changes to "Network View"
   - Verify network graph appears

5. **Test Case-Specific Request:**
   - Type: "show network for case 5"
   - Verify graph displays case 5

6. **Test Natural Variations:**
   - "network topology"
   - "display network"
   - "show me the network"

### Expected Console Output
```
AI Assistant: Detected simple network graph request
AI visualization command received: network_view, case_id: None
DEBUG: Received visualization command: 'network_view'
INFO: Network visualization requested without case_id, using first available: 0
Changing visualization to: network_view, case_id: 0

=== Creating Network Graph for network_view ===
Using case_id=0, contingency_id=None
✅ Successfully imported direct_network_integration module
Creating network graph with direct_network_integration...
✅ Successfully created network graph with direct_network_integration
```

## Files Modified

### 1. `power_viz_with_database.py`
**Line 3203:** Added `'network_view'` to valid visualization types
```python
valid_viz_types = [
    'voltage', 'loading', 'violations', 'comparison', 
    'generators', 'network', 'network_view', 'fall_network', 'network_comparison',
    'case_analysis', 'branch_analysis', 'bus_analysis'
]
```

**Lines 2260-2280:** Added automatic case_id assignment for network visualizations
```python
# For network visualizations, ensure we have a valid case_id
if selected_viz in ['network_view', 'network', 'fall_network', 'network_comparison']:
    if case_id is None:
        # Try to use first available case from dynamic case management
        if 'DYNAMIC_CASE_MANAGEMENT_AVAILABLE' in globals() and DYNAMIC_CASE_MANAGEMENT_AVAILABLE:
            first_available = get_first_available_case_id()
            if first_available is not None:
                print(f"INFO: Network visualization requested without case_id, using first available: {first_available}")
                case_id = first_available
```

## Architecture Flow

```
User Types Message
       ↓
[handle_chat_message callback]
       ↓
[get_ai_response()] ← Analyzes intent
       ↓
[has_network_graph_request()] ← Detects network keywords
       ↓
Returns: (response, 'network_view', case_id, contingency_id)
       ↓
[Stores in viz-command-store as JSON]
       ↓
[update_viz_selector_from_ai callback] ← Triggered by store change
       ↓
[Validates viz_type in valid_viz_types]
       ↓
[Updates dropdown to 'network_view']
       ↓
[update_dynamic_plot callback] ← Triggered by dropdown change
       ↓
[Assigns default case_id if None]
       ↓
[update_visualization()] ← Renders network graph
       ↓
[direct_network_integration.create_network_graph()]
       ↓
Network Graph Displayed! 🎉
```

## Benefits

1. **Natural Interaction:** Users don't need to know UI structure
2. **Faster Workflow:** No manual dropdown selection needed
3. **Intuitive:** Works how users expect it to work
4. **Flexible:** Handles many variations of requests
5. **Smart Defaults:** Automatically selects valid case when none specified
6. **Context-Aware:** AI understands intent from natural language

## Troubleshooting

### Issue: Network graph not appearing
**Check:**
1. Console shows: `"AI Assistant: Detected simple network graph request"` or `"Detected enhanced network graph request"`
2. Console shows: `"AI visualization command received: network_view..."`
3. Console shows: `"Changing visualization to: network_view..."`
4. Dropdown actually changes to "Network View"

**Solutions:**
- Ensure `'network_view'` is in `valid_viz_types` list
- Check that AI is returning exactly `'network_view'` as viz_type
- Verify case_id is being assigned (check console logs)

### Issue: Wrong case displayed
**Check:**
- What case_id AI extracted from message
- Console shows: `"using first available: X"`

**Solutions:**
- Be specific: "show network for case 5"
- Verify dynamic case management is working
- Check database has the requested case

### Issue: AI doesn't detect network request
**Check:**
- Message contains network-related keywords
- `ENHANCED_NETWORK_GRAPHS_AVAILABLE` is True
- Fallback keyword matching is working

**Solutions:**
- Use explicit keywords: "network graph", "show network"
- Check `enhanced_network_graphs.py` is loaded
- Review console for detection logs

## Future Enhancements

Possible improvements:
1. **Voice Commands:** "Hey assistant, show network"
2. **Comparative Requests:** "compare network for case 1 and case 5"
3. **Filtered Views:** "show network for high voltage buses only"
4. **Animated Transitions:** Smooth visualization changes
5. **Network Diff:** "show what changed in network between cases"
6. **Subset Selection:** "show network around bus 50"
7. **Time-Series:** "show network evolution over time"

## Related Documentation

- `NETWORK_GRAPH_FIX.md` - How automatic case assignment works
- `NETWORK_GRAPH_AI_INTEGRATION.md` - Enhanced detection system
- `TABLE_FORMAT_UPDATE.md` - HTML response formatting
- `VISUALIZATION_FIX.md` - Default case handling fix

## Summary

✅ AI assistant can now visualize network graphs on request  
✅ Natural language understanding for multiple request variations  
✅ Automatic dropdown switching  
✅ Smart case ID assignment  
✅ Seamless user experience  
✅ Production-ready implementation  

**The power system visualization is now truly AI-powered!** 🤖⚡
