# Visual Flow Diagram - How the Code Works

## 🔄 Complete Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE                              │
│                    (Web Browser - Port 8054)                         │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Case ID: [0▼]│  │Contingency:  │  │Visualization:│              │
│  │              │  │      [5▼]    │  │ Branch Anal▼ │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              📊 CHART AREA (4 plots)                         │   │
│  │  Case 0, Contingency 5: Branch Loading Distribution         │   │
│  │                                                               │   │
│  │  [Histogram]      [Scatter Plot]                            │   │
│  │  [Bar Chart]      [Data Table]                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 💬 AI CHAT                                                   │   │
│  │ User: "Show branch analysis for contingency 10"             │   │
│  │ AI: "Loading case 0, contingency 10... [updates above]"     │   │
│  └─────────────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            │ HTTP Request
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   DASH WEB SERVER (Flask)                            │
│                  power_viz_with_database.py                          │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  @app.callback (Line 2428)                                  │    │
│  │  def update_dynamic_plot(selected_viz, case_id,            │    │
│  │                          contingency_id):                   │    │
│  │      # User selected: case_id=0, contingency_id=5           │    │
│  │      # selected_viz='branch_analysis'                       │    │
│  └────────────────────────────────────────────────────────────┘    │
│                            │                                          │
│                            ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  🔍 Check if case-specific data needed (Line 2474)         │    │
│  │  if selected_viz in ['branch_analysis', 'bus_analysis']:   │    │
│  │      # YES - need case-specific data                        │    │
│  └────────────────────────────────────────────────────────────┘    │
│                            │                                          │
│                            ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  📊 Load Case Data (Lines 2838-2867)                       │    │
│  │                                                             │    │
│  │  if contingency_id is not None:                            │    │
│  │      query = "SELECT * FROM ContingencyBranchData          │    │
│  │               WHERE base_case_id = 0                        │    │
│  │               AND contingency_case_id = 5"                  │    │
│  │  else:                                                       │    │
│  │      query = "SELECT * FROM BaseBranchData                  │    │
│  │               WHERE base_case_id = 0"                       │    │
│  └────────────────────────────────────────────────────────────┘    │
│                            │                                          │
│                            ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  🔧 Column Normalization (Lines 2869-2878) ⭐ NEW!         │    │
│  │                                                             │    │
│  │  # Fix column name differences                             │    │
│  │  if 'bus_number' in df.columns:                            │    │
│  │      df['BUS_NUMBER'] = df['bus_number']                   │    │
│  │                                                             │    │
│  │  Result: data is now compatible!                           │    │
│  └────────────────────────────────────────────────────────────┘    │
│                            │                                          │
│                            ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  📈 Call Analysis Function (Line 3029) ⭐ NEW!             │    │
│  │                                                             │    │
│  │  return create_branch_analysis_plot(                       │    │
│  │      case_branches_df,                                      │    │
│  │      case_id=0,                                             │    │
│  │      contingency_id=5                                       │    │
│  │  )                                                          │    │
│  └────────────────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   DATABASE LAYER                                     │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  🗄️ SQLite Database (data.db)                              │    │
│  │                                                             │    │
│  │  ┌──────────────────────────────────────────────────┐     │    │
│  │  │ ContingencyBranchData (19.7M rows)               │     │    │
│  │  │ ┌────────────────────────────────────────────┐   │     │    │
│  │  │ │ base_case_id | contingency_case_id | ...  │   │     │    │
│  │  │ │      0       |         5           | ...  │   │     │    │
│  │  │ │      0       |         5           | ...  │   │     │    │
│  │  │ │     ...      |        ...          | ...  │   │     │    │
│  │  │ └────────────────────────────────────────────┘   │     │    │
│  │  └──────────────────────────────────────────────────┘     │    │
│  │                                                             │    │
│  │  Query Result: 186 rows for case 0, contingency 5          │    │
│  └────────────────────────────────────────────────────────────┘    │
│                            │                                          │
│                            ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  ⚡ Cache Layer (direct_network_integration.py) ⭐ NEW!    │    │
│  │                                                             │    │
│  │  @lru_cache(maxsize=128)                                   │    │
│  │  def _fetch_case_data_cached(case_id, contingency_id):    │    │
│  │                                                             │    │
│  │  First request (case=0, contingency=5):                    │    │
│  │  ├─ Query database (1.5 seconds)                           │    │
│  │  └─ Store in cache                                         │    │
│  │                                                             │    │
│  │  Second request (same case=0, contingency=5):              │    │
│  │  ├─ Read from cache (0.05 seconds) ⚡                      │    │
│  │  └─ Skip database query!                                   │    │
│  └────────────────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            │ Returns: pandas DataFrame
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   VISUALIZATION LAYER                                │
│                    branch_analysis.py                                │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  def create_branch_analysis_plot(branches_df,              │    │
│  │                                  case_id=0,                 │    │
│  │                                  contingency_id=5):         │    │
│  │                                                             │    │
│  │      # Build title                                          │    │
│  │      title = f"Case {case_id}, Contingency {contingency_id}"│   │
│  │                                                             │    │
│  │      # Calculate metrics                                    │    │
│  │      loading = (branches_df['MVA'] / branches_df['RATE'])  │    │
│  │      overloaded = branches_df[loading > 1.0]               │    │
│  │                                                             │    │
│  │      # Create 4 subplots                                    │    │
│  │      fig = make_subplots(rows=2, cols=2)                   │    │
│  │                                                             │    │
│  │      # Plot 1: Histogram                                    │    │
│  │      fig.add_trace(go.Histogram(x=loading))                │    │
│  │                                                             │    │
│  │      # Plot 2: Scatter                                      │    │
│  │      fig.add_trace(go.Scatter(x=PF, y=QF, color=loading))  │    │
│  │                                                             │    │
│  │      # Plot 3: Bar chart of top 10                         │    │
│  │      top10 = branches_df.nlargest(10, 'loading')           │    │
│  │      fig.add_trace(go.Bar(x=branch_id, y=loading))         │    │
│  │                                                             │    │
│  │      # Plot 4: Summary table                                │    │
│  │      stats = {                                              │    │
│  │          'Total Branches': len(branches_df),               │    │
│  │          'Overloaded': len(overloaded),                    │    │
│  │          'Avg Loading': loading.mean()                     │    │
│  │      }                                                       │    │
│  │      fig.add_trace(go.Table(values=stats))                 │    │
│  │                                                             │    │
│  │      return fig  # Plotly Figure object                    │    │
│  └────────────────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            │ Returns: Plotly Figure (JSON)
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    BACK TO BROWSER                                   │
│                                                                       │
│  Dash sends JSON representation of figure:                          │
│  {                                                                    │
│    "data": [                                                          │
│      {"type": "histogram", "x": [45, 67, 89, ...], ...},            │
│      {"type": "scatter", "x": [12, 34, ...], "y": [56, 78, ...]},   │
│      {"type": "bar", "x": ["1-2", "3-4", ...], "y": [105, 98, ...]},│
│      {"type": "table", "cells": {...}}                               │
│    ],                                                                 │
│    "layout": {                                                        │
│      "title": "Case 0, Contingency 5: Branch Loading Distribution"   │
│    }                                                                  │
│  }                                                                    │
│                                                                       │
│  Plotly.js renders the interactive chart in the browser              │
└─────────────────────────────────────────────────────────────────────┘
```

## 🎯 Key Points

### 1. Column Normalization (Your Fix!)
```
Database has: bus_number (lowercase)
                    ↓
           [Normalization Step]
                    ↓
Analysis needs: BUS_NUMBER (uppercase)

Without this: ❌ KeyError: 'BUS_NUMBER'
With this: ✅ Works perfectly!
```

### 2. Performance Caching (Your Optimization!)
```
Request Timeline:

First Request (case=0, contingency=5):
├─ 0.0s: User clicks "Branch Analysis"
├─ 0.1s: Database query starts
├─ 1.5s: Query completes (186 rows)
├─ 1.6s: Create visualization
└─ 1.8s: Display to user

Second Request (same case=0, contingency=5):
├─ 0.0s: User clicks again
├─ 0.0s: Check cache → HIT! ⚡
├─ 0.05s: Create visualization
└─ 0.1s: Display to user

Speed increase: 18x faster! 🚀
```

### 3. Data Flow Summary
```
User Input → Callback → Database Query → Normalization → 
Analysis → Visualization → JSON → Browser → Interactive Chart
```

## 📊 What Each Component Does

| Component | Purpose | Lines | Your Changes |
|-----------|---------|-------|--------------|
| **Dash App** | Web server & UI | 2260-2400 | None |
| **Callback** | Handle user actions | 2428-2470 | Debug logging |
| **Data Loading** | Query database | 2838-2867 | Column normalization |
| **Analysis Call** | Create visualization | 3029-3034 | Pass case IDs |
| **branch_analysis.py** | Generate plots | 1-205 | None (already worked) |
| **Caching** | Speed optimization | direct_network_integration.py | Added lru_cache |

## 🔄 Contingency vs Base Case

```
┌─────────────────────────────────────────────────────┐
│              Base Case (Normal Operation)            │
├─────────────────────────────────────────────────────┤
│  All 185 branches operating                         │
│  Line 1-2: 45 MW (45% loaded)                       │
│  Line 3-4: 67 MW (67% loaded)                       │
│  All voltages: 0.98-1.04 p.u. ✅                    │
└─────────────────────────────────────────────────────┘
                        │
                        │ What if Line 1-2 fails?
                        ▼
┌─────────────────────────────────────────────────────┐
│         Contingency 5 (Line 1-2 Removed)            │
├─────────────────────────────────────────────────────┤
│  Only 184 branches operating (1 removed)            │
│  Line 1-2: 0 MW (OUT OF SERVICE) ⚠️                │
│  Line 3-4: 105 MW (105% loaded) ❌ OVERLOAD!       │
│  Bus 5 voltage: 0.93 p.u. ❌ VIOLATION!            │
└─────────────────────────────────────────────────────┘
```

Your code now shows both scenarios correctly! 🎉
