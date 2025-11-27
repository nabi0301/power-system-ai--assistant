# Use Case Diagram
## Power System Visualization Tool with AI-Enhanced Contingency Analysis

---

## System Overview

Interactive visualization tool for IEEE 118-bus power system analysis with AI-powered natural language interface, supporting contingency analysis, SLR/DLR comparison, and real-time operational insights.

---

## Use Case Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│         Power System Visualization Tool - Functional Workflow           │
│                      (IEEE 118-Bus System)                              │
└─────────────────────────────────────────────────────────────────────────┘


    DATA INPUT              CORE FUNCTIONS              OUTPUT/RESULTS
         
┌─────────────┐         ┌───────────────────┐        ┌──────────────┐
│   SQLite/   │         │ UC-1: Network     │        │  Interactive │
│ PostgreSQL  │────────>│    Topology       │───────>│   Network    │
│  Database   │         │ • 118-bus system  │        │ Visualization│
│ (577 cases) │         │ • Zoom/Pan/Hover  │        └──────────────┘
└─────────────┘         └───────────────────┘                
      │                          │                    ┌──────────────┐
      │                          │                    │   Voltage    │
      │                 ┌───────────────────┐        │   Profiles   │
      │                 │ UC-2: Voltage     │───────>│  & Violation │
      │                 │    Analysis       │        │   Reports    │
      │                 │ • VM magnitude    │        └──────────────┘
      │                 │ • Violation check │                
      │                 └───────────────────┘        ┌──────────────┐
      │                          │                    │   Loading    │
      │                 ┌───────────────────┐        │ Percentages  │
      │                 │ UC-3: Loading     │───────>│  & Overload  │
      │                 │    Analysis       │        │   Alerts     │
      │                 │ • Thermal limits  │        └──────────────┘
      │                 │ • MVA/RATE calc   │                
      │                 └───────────────────┘        ┌──────────────┐
      │                          │                    │  Generation  │
      ├─────────────────┐ ┌───────────────────┐     │   Dispatch   │
      │                 │ │ UC-4: Generator   │────>│  & Redispatch│
      │                 │ │    Dispatch       │     │   Comparison │
      │                 └>│ • PG/QG levels    │     └──────────────┘
      │                   │ • GEN_ADJ (SLR/DLR)│              
      │                   └───────────────────┘     ┌──────────────┐
      │                          │                   │ Contingency  │
      │                   ┌───────────────────┐     │   Ranking    │
      │                   │ UC-5: Contingency │────>│  & Critical  │
      │                   │    Analysis (N-1) │     │   Scenarios  │
      │                   │ • 186 outages     │     └──────────────┘
      │                   │ • Severity rank   │              
      │                   └───────────────────┘     ┌──────────────┐
      │                          │                   │   4-Panel    │
      │                   ┌───────────────────┐     │  Comparison  │
      └──────────────────>│ UC-6: SLR vs DLR  │────>│ Base/Cont/   │
                          │    Comparison     │     │  SLR/DLR     │
                          │ • Thermal limits  │     └──────────────┘
                          │ • Cost analysis   │              
                          └───────────────────┘              
                                   │                          
┌─────────────┐                   │                 ┌──────────────┐
│  Llama 3.2  │         ┌───────────────────┐      │  Contextual  │
│   (8B) +    │────────>│ UC-7: Natural     │─────>│   Answers    │
│ Claude 3.7  │         │    Language AI    │      │  & Auto-viz  │
│  AI Engine  │         │ • Plain English   │      │   Updates    │
└─────────────┘         │ • RAG context     │      └──────────────┘
                        └───────────────────┘              
                                 │                  ┌──────────────┐
                        ┌───────────────────┐      │  PNG/SVG/CSV │
                        │ UC-8: Export &    │─────>│    Files &   │
                        │    Reporting      │      │   Reports    │
                        │ • Multi-format    │      └──────────────┘
                        └───────────────────┘              


           WORKFLOW: Data → Analysis → Visualization → Export
```

---

## Functional Roles & Tool Operations

| Role | Purpose | Key Operations | Output |
|---|---|---|---|
| **Visualization Engine** | Render power system topology and data | • Network graph generation (118-bus layout)<br>• Bus/branch positioning<br>• Color-coded violation mapping<br>• Interactive zoom/pan/hover | Interactive network diagrams with real-time data overlays |
| **Analysis Engine** | Process power system metrics | • Voltage violation detection (VM < 0.95 or > 1.05 p.u.)<br>• Thermal loading calculation (MVA/RATE %)<br>• Contingency severity ranking (N-1 analysis)<br>• Generator dispatch tracking | Numerical reports, violation alerts, severity rankings |
| **Comparison Engine** | Evaluate corrective strategies | • Base vs contingency delta comparison<br>• SLR vs DLR side-by-side analysis<br>• 4-panel synchronized view<br>• Cost-benefit evaluation | Comparative visualizations showing strategy effectiveness |
| **AI Query Interface** | Natural language processing | • Parse plain English queries<br>• RAG-based context retrieval from database<br>• Dynamic visualization updates<br>• Contextual answer generation | Smart responses with auto-generated visualizations |
| **Data Management** | Store and retrieve system data | • SQLite/PostgreSQL query optimization<br>• Index 577 scenarios across 10 tables<br>• Topology preservation<br>• Transaction integrity | Structured datasets (bus, branch, generator, contingency data) |
| **Export Module** | Generate deliverables | • PNG/SVG graph rendering<br>• CSV/Excel data extraction<br>• Report compilation<br>• Multi-format support | Files ready for documentation and external analysis tools |

---

## Use Case Operations

| ID | Use Case | Input | Processing | Output |
|---|---|---|---|---|
| **UC-1** | **Network Topology** | Case/Contingency selection | Retrieve bus/branch data → Layout 118-bus network → Apply color coding | Interactive graph with violations highlighted |
| **UC-2** | **Voltage Analysis** | Voltage magnitude data | Calculate VM p.u. → Detect violations (VM < 0.95 or > 1.05) → Rank by severity | Voltage profile charts + violation list |
| **UC-3** | **Loading Analysis** | Branch MVA, RATE data | Calculate loading % (MVA/RATE) → Identify overloads (≥100%) → Color-code branches | Loading bar charts + overload alerts |
| **UC-4** | **Generator Dispatch** | PG, QG, GEN_ADJ data | Extract generation levels → Compare SLR vs DLR dispatch → Calculate deltas | Generation bar charts + redispatch comparison |
| **UC-5** | **Contingency (N-1)** | 186 branch outage scenarios | Simulate each outage → Count violations → Rank by severity | Contingency ranking table + critical scenarios |
| **UC-6** | **SLR vs DLR** | Base/Cont/SLR/DLR datasets | Generate 4 synchronized networks → Calculate strategy metrics → Highlight differences | 4-panel comparison view with delta statistics |
| **UC-7** | **AI Natural Query** | Plain English text | Parse query → Retrieve context via RAG → Generate SQL → Update visualization | Contextual answer + auto-updated graphs |
| **UC-8** | **Export & Report** | Current visualization state | Render to PNG/SVG → Extract data to CSV → Compile report document | Downloadable files (images, data, reports) |

---

## System Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Database** | SQLite (~50MB) / PostgreSQL | Store 577 scenarios (1.88M data points) |
| **AI Engine** | Llama 3.2 (8B) + Claude 3.7 | Natural language processing with RAG |
| **Frontend** | Plotly Dash + Plotly 5.x | Interactive visualization |
| **Network** | NetworkX 2.6+ | Topology analysis & graph processing |

---

## Key Features

| Category | Capabilities | Benefits |
|----------|--------------|----------|
| **Visualization** | Network topology, 4-panel comparison, color-coded alerts | Real-time operational insights |
| **Analysis** | Voltage, loading, generator, contingency (N-1) | Identify vulnerabilities and violations |
| **AI Interface** | Natural language queries, contextual responses | Simplified interaction for all users |
| **Comparison** | SLR vs DLR strategy evaluation | Optimize corrective actions |
| **Data** | 577 scenarios, 1.88M data points, dual database | Comprehensive power system coverage |

---

## Example AI Queries

```
💬 "Show me case 5 with contingency 10"
💬 "What are the voltage violations?"
💬 "Compare SLR and DLR for contingency 55"
💬 "Analyze bus 42"
💬 "Which lines are overloaded?"
💬 "List all available cases"
```

---

**Document Version:** 1.0 | **Created:** November 17, 2025 | **IEEE 118-Bus System with 577 Scenarios**
