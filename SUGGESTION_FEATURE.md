# AI Suggestion Feature

## Overview
Added an intelligent AI suggestion system that analyzes the current power system state and provides actionable recommendations.

## Features Added

### 1. **Suggest Button (💡)**
- Located in the chat interface next to the input box
- Golden/yellow theme to stand out
- Click to get instant AI-powered suggestions

### 2. **Smart Analysis Function**
`generate_smart_suggestions(current_case_id, current_contingency_id, current_viz_type)`

The AI analyzes:
- **Thermal Violations**: Lines operating above 100% capacity
- **Voltage Violations**: Buses outside 0.95-1.05 p.u. range
- **Critical Loading**: Lines near capacity (90-100%)
- **Generation Overview**: Current generator status
- **Load Distribution**: High-load bus identification

### 3. **Intelligent Recommendations**

The system provides context-aware suggestions based on findings:

#### When Violations Detected:
- **Immediate actions** to resolve issues
- **Visualization changes** to view problems
- **Corrective measures** (redispatch, DLR, reactive support)

#### When System is Healthy:
- **Preventive insights** about system state
- **Exploration suggestions** for deeper analysis
- **Comparative studies** recommendations

### 4. **Auto-Visualization Switching**
When suggestions detect issues, the system can automatically recommend switching to relevant views:
- Violations detected → Suggests "Violations Analysis" view
- Voltage issues → Suggests "Voltage Analysis" view
- Critical loading → Suggests "Loading Analysis" view

## Usage

### Basic Usage:
1. Open the chat interface (🤖 button)
2. Click the **💡** button
3. Review AI-generated suggestions
4. Follow recommendations or ask follow-up questions

### Example Suggestions Output:

```
💡 Smart Suggestions for Case 42 (Base Case)

---

🚨 CRITICAL: Thermal Overloads Detected

Found 3 overloaded branch(es):
• Branch 23 → 25: 115.3% loaded
  - Flow: 230.6 MW | Rating: 200.0 MW
• Branch 45 → 46: 108.2% loaded
  - Flow: 216.4 MW | Rating: 200.0 MW

Immediate Action Required:
  → View violations in detail: Switch to 'Violations Analysis' view
  → Consider generator redispatch to reduce power flow
  → Check if DLR (Dynamic Line Rating) can help

---

⚠️ Voltage Issues Detected

Found 2 bus(es) with voltage violations:
• Bus 42 (138 kV): 0.9285 p.u. (LOW)
• Bus 58 (345 kV): 1.0623 p.u. (HIGH)

Voltage Correction Recommended:
  → Analyze voltage profile: Switch to 'Voltage Analysis' view
  → Add reactive power support (capacitors/reactors)
  → Adjust generator voltage setpoints

---

🎯 Recommendations:

  → View violations in detail: Switch to 'Violations Analysis' view
  → Consider generator redispatch to reduce power flow
  → Check if DLR (Dynamic Line Rating) can help
  → Analyze voltage profile: Switch to 'Voltage Analysis' view
  → Add reactive power support (capacitors/reactors)

---

🔍 Further Exploration:

• Compare Cases: Use 'Comparison Analysis' to see differences
• Contingency Analysis: Check how system performs under outages
• Network Visualization: See the entire system topology
• Trend Analysis: Identify patterns across multiple cases

💬 Try Asking:
• 'Show me critical lines'
• 'What are the voltage violations?'
• 'Compare base case with contingency 1'
• 'Which generators are at max capacity?'
```

## Technical Implementation

### Files Modified:
- `power_viz_with_database.py`
  - Added `generate_smart_suggestions()` function (lines ~6512)
  - Added suggest button UI component (lines ~10550)
  - Added suggest button callback (lines ~16256)

### Database Queries Used:
1. Voltage violations: `SELECT BUS_NUMBER, VM WHERE VM < 0.95 OR VM > 1.05`
2. Thermal overloads: `SELECT From_Bus, To_Bus WHERE Loading > 100%`
3. Critical loading: `SELECT From_Bus, To_Bus WHERE Loading BETWEEN 90 AND 100`
4. Generator status: `SELECT BUS_NUMBER, PG WHERE PG > 0`
5. Load distribution: `SELECT BUS_NUMBER, PD WHERE PD > 0`

### Key Functions:
```python
def generate_smart_suggestions(current_case_id, current_contingency_id, current_viz_type):
    """
    Analyzes current system state and generates intelligent suggestions.
    Returns: (suggestion_text, viz_command, case_id, contingency_id)
    """
```

## Benefits

1. **Proactive Analysis**: AI identifies issues before you ask
2. **Actionable Insights**: Specific recommendations, not just data
3. **Context-Aware**: Suggestions based on current view and case
4. **Educational**: Helps users learn what to look for
5. **Time-Saving**: Quick overview of system health
6. **Guided Navigation**: Suggests relevant visualizations

## Advanced Features (IMPLEMENTED ✅)

### 1. **🔮 Predictive Analysis for Future Violations**
- Identifies lines approaching capacity (80-90% loaded)
- Calculates margin before violation
- Predicts risk under various scenarios:
  - Load increase (10-15%)
  - Parallel path loss
  - Generator outage
- Monitors buses near voltage limits
- Provides voltage stability predictions

**Example Output:**
```
🔮 Predictive Analysis:

⚠️ 3 line(s) approaching capacity (80-90% loaded):
• Branch 15 → 17: 87.3% (HIGH RISK)
  - Only 12.7% margin before violation

Prediction: These lines may violate under:
  → Load increase of 10-15%
  → Loss of parallel transmission path
  → Generator outage causing rerouting
```

### 2. **⚡ Optimization Recommendations**
- Generator redispatch suggestions
- Load balancing recommendations
- Reactive power optimization
- Demand response strategies
- Calculates specific MW/MVAR adjustments needed

**Optimization Types:**
- **Redispatch:** Balance generation to reduce line loading
- **Load Management:** Reduce concentrated loads
- **Reactive Power:** Add capacitors/reactors at specific buses
- **Demand Response:** Estimated relief calculations

**Example Output:**
```
⚡ Optimization Recommendations:

🔧 Redispatch Optimization:
• Imbalanced generation detected:
  - High output: Buses 10, 25, 89
  - Low output: Buses 42, 65, 103

• Redispatch to fix 2 violation(s):
  - Line 23→25: Reduce flow by 30.6 MW

Optimization Strategy:
  → Shift 30.6 MW from overloaded paths
  → Use generators closer to load centers
  → Consider demand response programs
```

### 3. **🔄 Multi-Case Comparison Suggestions**
- Identifies available contingency cases
- Suggests specific case comparisons
- Ranks cases by severity
- Recommends comparison visualization
- Provides SLR vs DLR comparison insights

**Comparison Features:**
- Base case vs contingency analysis
- Violation comparison across all cases
- Worst-case scenario identification
- Pattern recognition across multiple scenarios

**Example Output:**
```
🔄 Multi-Case Comparison Suggestions:

📊 5 contingency cases available for comparison:

Violation Comparison:
• Current case has 3 violation(s)
  → Compare violations across all contingency cases
  → Identify worst-case contingency scenario
  → Use 'Contingency Ranking' view to see all cases

Recommended Comparisons:
• Base Case vs Contingency 1: See impact of first outage
• All Contingencies: Rank cases by severity
• SLR vs DLR: Compare rating methodologies
```

### 4. **⚙️ Custom Suggestion Preferences**
- Adapts to current visualization view
- Context-aware recommendations
- Adjustable analysis depth
- Customizable suggestion style
- View-specific focused suggestions

**Customization Options:**
- **Priority Focus:** Violations → Voltage → Loading → Optimization
- **Analysis Depth:** Quick overview ↔ Detailed investigation
- **Suggestion Style:** Conservative ↔ Aggressive recommendations

**View-Specific Suggestions:**
- **Voltage View:** Focus on voltage stability, reactive power
- **Loading View:** Focus on thermal limits, line capacity
- **Violations View:** Focus on critical fixes, immediate actions
- **Network View:** Focus on system structure, connectivity

**Example Output:**
```
⚙️ Custom Suggestion Preferences:

📍 You're viewing Violations Analysis
• Focused suggestions: Critical fixes, immediate actions
• Next step: Use 'Network View' to see system topology

Customization Options:
• Priority Focus: Violations → Voltage → Loading → Optimization
• Analysis Depth: Quick overview ← → Detailed investigation

💬 Customize by asking:
• 'Focus on voltage issues only'
• 'Show me optimization opportunities'
• 'Quick summary of problems'
```

## Future Enhancements

Additional potential improvements:
- [ ] Machine learning model training on historical violations
- [ ] Suggestion history and tracking
- [ ] Export suggestions as PDF/Excel reports
- [ ] Voice-activated suggestions
- [ ] Real-time monitoring with email/SMS alerts
- [ ] Automated optimization execution (with approval)
- [ ] Cost-benefit analysis for recommendations
- [ ] Integration with SCADA systems

## Integration with Existing Features

Works seamlessly with:
- ✅ Chat interface
- ✅ Visualization selector
- ✅ Database switching
- ✅ Case/contingency selection
- ✅ All analysis views

## User Tips

1. **Use suggestions as starting point** for your analysis
2. **Click suggested visualization** changes to see issues
3. **Ask follow-up questions** based on suggestions
4. **Compare suggestions** across different cases
5. **Check suggestions** after making system changes
