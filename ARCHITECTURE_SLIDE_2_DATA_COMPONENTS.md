# Slide 2: Data Architecture & Components
## Database Schema & Core Components

---

## 🗄️ Database Schema (Star Schema Design)

### Core Tables

**1. SLR_Generator / DLR_Generator**
```sql
• base_case_id, contingency_case_id (keys)
• bus_number, gen_ini, gen_adj, gen_new
• pmax, pmin (capacity limits)
```

**2. ContingencyBranchData**
```sql
• from_bus, to_bus (connectivity)
• pf, qf, mva (power flows)
• rate (line limit), vio (violation flag)
```

**3. ContingencyBusData**
```sql
• bus_number, vm, va (voltage)
• pg, qg, pd, qd (generation/load)
• base_kv (voltage level)
```

**4. IEEE_118_Bus_Coordinates**
```sql
• bus_number, x_coord, y_coord (layout)
```

---

## 📈 Data Flow Pipeline

```
Power Flow Simulation → CSV/Excel Files → Import Scripts
                                              ↓
                        SQLite/PostgreSQL Database
                                              ↓
                    SQL Queries → pandas DataFrames
                                              ↓
               Column Normalization → Calculations
                                              ↓
                    Plotly Figure Generation
                                              ↓
                      Dash Component Update
                                              ↓
                        Browser Display
```

---

## 🔧 Core Visualization Components

### 1. Network Graph Generator
- **Function:** `create_network_graph()`
- **Technology:** NetworkX + Plotly
- **Features:** Force-directed layout, color-coded branches, interactive zoom

### 2. SLR vs DLR Comparison
- **Function:** `create_slr_dlr_comparison()`
- **Panels:** 4-panel dashboard (violations, loading, voltage, stats)
- **Color Scheme:** Blue=SLR, Green=DLR, Red=Violations

### 3. Contingency Ranking
- **Function:** `create_contingency_ranking_plot()`
- **Algorithm:** Weighted severity scoring (5 metrics)
- **Output:** Ranked list with visual breakdown

### 4. Generator Analysis
- **Function:** `create_generator_analysis_plot()`
- **Modes:** SLR vs DLR comparison OR single analysis
- **Metrics:** Redispatch MW, capacity utilization

### 5. Branch/Bus Analysis
- **Functions:** `create_branch_analysis_plot()`, `create_bus_analysis_plot()`
- **Views:** Loading profiles, voltage analysis, individual component stats

---

## 🧮 Key Algorithms

### Loading Percentage Calculation
```python
loading_pct = (MVA / RATE) * 100
MVA = sqrt(PF² + QF²)
```

### Weighted Severity Score
```python
severity = (violations × 30%) + (max_loading × 25%) +
           (voltage_dev × 20%) + (redispatch × 15%) +
           (load_shedding × 10%)
```

### Violation Detection
```python
Red:    loading ≥ 100%  (Critical)
Orange: loading 90-99%  (High)
Yellow: loading 80-89%  (Moderate)
Gray:   loading < 80%   (Normal)
```

---

## 🔄 Callback Architecture

### Event-Driven System (20+ Callbacks)

**Primary Callbacks:**
1. `update_dynamic_plot()` - Main visualization updates
2. `update_ai_response()` - Chatbot interactions
3. `generate_figure_summary()` - Statistical summaries
4. `update_trend_analysis()` - Multi-scenario trends
5. `toggle_comparison_mode()` - SLR/DLR switching

**Trigger Flow:**
```
User Action → Input Component → Callback Function →
Database Query → Data Processing → Visualization →
Output Component → Browser Re-render
```

---

## 🔐 Data Handling Features

✅ **Column Normalization** (FROM_BUS vs from_bus vs From_Bus)  
✅ **NaN/Inf Error Handling** (replace(0, np.nan), fillna(0))  
✅ **Multiple Query Fallbacks** (robust error recovery)  
✅ **Dual Database Support** (SQLite local, PostgreSQL cloud)  
✅ **Global DataFrame Caching** (performance optimization)
