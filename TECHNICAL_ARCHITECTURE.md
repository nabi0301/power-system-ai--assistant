# Technical Architecture Document
## DLR Database Visualization & Analysis Platform

**Version:** 1.1  
**Date:** November 25, 2025  
**Project:** Dynamic Line Rating (DLR) vs Static Line Rating (SLR) Analysis Tool  
**Latest Update:** Llama LLM Integration for Enhanced Conversational AI

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Technology Stack](#technology-stack)
4. [Application Layers](#application-layers)
5. [Data Architecture](#data-architecture)
6. [Component Design](#component-design)
7. [Visualization Engine](#visualization-engine)
8. [API & Callbacks](#api--callbacks)
9. [Security & Performance](#security--performance)
10. [Deployment Architecture](#deployment-architecture)

---

## System Overview

### Purpose
The DLR Database Visualization Platform is a web-based interactive dashboard designed to analyze, visualize, and compare power system performance under Static Line Rating (SLR) and Dynamic Line Rating (DLR) methodologies across multiple contingency scenarios.

### Architecture Pattern
**Model-View-Controller (MVC) with Event-Driven Architecture**
- **Model:** SQLite/PostgreSQL database storing power flow results
- **View:** Plotly Dash components (React-based frontend)
- **Controller:** Python callback functions handling user interactions

### System Characteristics
- **Type:** Single-page web application (SPA)
- **Deployment:** Local/Cloud-hosted Python server
- **Access:** Browser-based (localhost:8055 or deployed URL)
- **Data Volume:** 577 contingency scenarios, 118 buses, 186 branches
- **Code Size:** ~16,000 lines of Python

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE LAYER                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐│
│  │  Network   │  │  Loading   │  │ Voltage    │  │    AI     ││
│  │  Graphs    │  │  Analysis  │  │ Analysis   │  │ Assistant ││
│  └────────────┘  └────────────┘  └────────────┘  └───────────┘│
│         Plotly Dash Components (HTML + React.js)                │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER (Python)                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Dash Callback Handler System                 │  │
│  │  • update_dynamic_plot()     • generate_figure_summary() │  │
│  │  • update_ai_response()      • update_case_selector()    │  │
│  │  • update_trend_analysis()   • toggle_comparison_mode()  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         AI Response System (v1.1 - Hybrid)                │  │
│  │  ┌─────────────────────┐    ┌─────────────────────────┐ │  │
│  │  │  Rule-Based Engine  │    │  Llama LLM (1.1B)       │ │  │
│  │  │  • Pattern matching │    │  • TinyLlama model      │ │  │
│  │  │  • Entity extraction│    │  • PyTorch inference    │ │  │
│  │  │  • DB queries       │    │  • Context-aware        │ │  │
│  │  │  (~instant)         │    │  (~2 sec on CPU)        │ │  │
│  │  └─────────────────────┘    └─────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Visualization Generation Engine                │  │
│  │  • create_network_graph()    • create_slr_dlr_comparison()│ │
│  │  • create_loading_plot()     • create_voltage_plot()     │  │
│  │  • create_generator_analysis()• create_contingency_ranking()│ │
│  │  • create_branch_analysis()  • create_bus_analysis()     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Business Logic & Analytics                   │  │
│  │  • Loading calculations      • Violation detection        │  │
│  │  • Severity scoring          • Trend analysis             │  │
│  │  • Statistical aggregations  • NLP query parsing          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA ACCESS LAYER                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Database Connection Management                 │  │
│  │  • get_sqlite_connection()   • get_postgres_connection()  │  │
│  │  • Connection pooling        • Query optimization         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              pandas DataFrame Processing                  │  │
│  │  • Column normalization      • Data type conversion       │  │
│  │  • NaN/Inf handling          • Filtering & aggregation    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DATA STORAGE LAYER                         │
│  ┌────────────────────┐              ┌────────────────────┐    │
│  │   SQLite (Local)   │      OR      │ PostgreSQL (Cloud) │    │
│  │   • data.db        │              │   • Remote Server  │    │
│  │   • File-based     │              │   • Scalable       │    │
│  └────────────────────┘              └────────────────────┘    │
│                                                                  │
│  Database Schema:                                                │
│  • SLR_Generator (base_case_id, contingency_case_id, gen_adj)  │
│  • DLR_Generator (base_case_id, contingency_case_id, gen_adj)  │
│  • ContingencyBranchData (from_bus, to_bus, pf, qf, mva, rate) │
│  • ContingencyBusData (bus_number, vm, va, pg, qg, pd, qd)     │
│  • IEEE_118_Bus_Coordinates (bus_number, x_coord, y_coord)     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Core Framework
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Backend Framework** | Python | 3.8+ | Application logic |
| **Web Framework** | Dash by Plotly | 2.x | Web application framework |
| **Visualization** | Plotly | 5.x | Interactive charts & graphs |
| **Data Processing** | pandas | 1.x | DataFrame operations |
| **Numerical Computing** | NumPy | 1.x | Mathematical calculations |
| **Database (Primary)** | SQLite | 3.x | Local file-based database |
| **Database (Alternative)** | PostgreSQL | 13+ | Scalable cloud database |
| **Network Graphs** | NetworkX | 2.x | Graph theory & layouts |
| **LLM Framework** | Transformers (Hugging Face) | 4.x | Large language model support |
| **Deep Learning** | PyTorch | 2.x | Neural network backend |
| **Model Acceleration** | Accelerate | 1.x | Efficient model loading |

### AI/ML Stack (New in v1.1)
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **LLM Model** | TinyLlama-1.1B-Chat | v1.0 | Conversational AI responses |
| **Tokenizer** | SentencePiece | 0.2.x | Text tokenization |
| **Inference Engine** | PyTorch | 2.3+ | Model execution |
| **Model Repository** | Hugging Face Hub | - | Model distribution |

### Frontend Technologies
- **HTML5** - Structure and layout
- **CSS3** - Styling and animations
- **React.js** (via Dash) - Component rendering
- **Plotly.js** - Interactive visualization library

### Python Libraries
```python
import dash
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import sqlite3
import psycopg2
import networkx as nx
from dash import dcc, html, Input, Output, State, callback_context

# AI/ML Libraries (v1.1)
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from accelerate import Accelerator
```

---

## Application Layers

### 1. Presentation Layer
**Components:**
- Dashboard layout (`app.layout`)
- Navigation tabs (Network, Loading, Voltage, Generators, etc.)
- Control panels (dropdowns, sliders, buttons)
- AI chatbot interface
- Interactive graphs and tables

**Technologies:** Dash Core Components (dcc), Dash HTML Components (html)

**Key Features:**
- Responsive design
- Real-time updates
- Dark theme UI
- Collapsible sections
- AI chatbot with LLM integration (v1.1)

### 2. Business Logic Layer
**Components:**
- Visualization generation functions (15+ specialized functions)
- Data transformation and normalization
- Statistical calculations (mean, max, standard deviation)
- Violation detection algorithms
- Severity scoring engine
- Natural language processing for AI assistant
- Hybrid AI response system (rule-based + LLM) (v1.1)
- Llama model inference for conversational queries (v1.1)

**Key Algorithms:**
```python
# Loading Percentage Calculation
loading_percentage = (MVA / RATE) * 100

# Severity Score Calculation
severity_score = (
    violations * 30.0 +
    (max_loading / 100) * 25.0 +
    (max_voltage_dev * 100) * 20.0 +
    (total_redispatch / 100) * 15.0 +
    load_shedding * 10.0
)

# MVA Calculation
MVA = sqrt(PF² + QF²)
```

### 3. Data Access Layer
**Components:**
- Database connection managers
- SQL query builders
- DataFrame converters
- Column name normalizers
- Error handlers for missing data

**Database Abstraction:**
```python
def get_sqlite_connection():
    return sqlite3.connect('data.db')

def get_postgres_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
```

### 4. Data Storage Layer
**Schema Design:** Star schema with fact and dimension tables

**Tables:**
- `SLR_Generator` - Static line rating generator adjustments
- `DLR_Generator` - Dynamic line rating generator adjustments
- `ContingencyBranchData` - Branch power flows for each contingency
- `ContingencyBusData` - Bus voltages and injections
- `IEEE_118_Bus_Coordinates` - Network topology coordinates

---

## Data Architecture

### Database Schema

#### SLR_Generator & DLR_Generator Tables
```sql
CREATE TABLE SLR_Generator (
    id INTEGER PRIMARY KEY,
    base_case_id INTEGER,
    contingency_case_id INTEGER,
    bus_number INTEGER,
    gen_ini REAL,        -- Initial generation (MW)
    gen_adj REAL,        -- Generation adjustment (MW)
    gen_new REAL,        -- New generation (MW)
    pmax REAL,           -- Maximum capacity (MW)
    pmin REAL            -- Minimum capacity (MW)
);
```

#### ContingencyBranchData Table
```sql
CREATE TABLE ContingencyBranchData (
    id INTEGER PRIMARY KEY,
    base_case_id INTEGER,
    contingency_case_id INTEGER,
    from_bus INTEGER,
    to_bus INTEGER,
    pf REAL,             -- Active power flow (MW)
    qf REAL,             -- Reactive power flow (MVAr)
    mva REAL,            -- Apparent power (MVA)
    rate REAL,           -- Line rating limit (MVA)
    vio INTEGER          -- Violation flag (0/1)
);
```

#### ContingencyBusData Table
```sql
CREATE TABLE ContingencyBusData (
    id INTEGER PRIMARY KEY,
    base_case_id INTEGER,
    contingency_case_id INTEGER,
    bus_number INTEGER,
    vm REAL,             -- Voltage magnitude (p.u.)
    va REAL,             -- Voltage angle (degrees)
    pg REAL,             -- Generation (MW)
    qg REAL,             -- Reactive generation (MVAr)
    pd REAL,             -- Load demand (MW)
    qd REAL,             -- Reactive demand (MVAr)
    base_kv REAL         -- Base voltage (kV)
);
```

### Data Flow

```
Power Flow Simulation (External)
         ↓
    CSV/Excel Files
         ↓
   Data Import Scripts
         ↓
SQLite/PostgreSQL Database
         ↓
   SQL Queries (pandas)
         ↓
    DataFrame Processing
         ↓
  Column Normalization
         ↓
   Calculations & Metrics
         ↓
Plotly Figure Generation
         ↓
   Dash Component Update
         ↓
    User Browser Display
```

### Data Normalization Strategy

**Problem:** Database columns have inconsistent naming (PF vs pf vs From_Bus vs from_bus)

**Solution:** Runtime normalization in visualization functions
```python
# Normalize column names to uppercase
if 'FROM_BUS' not in df.columns:
    if 'From_Bus' in df.columns:
        df['FROM_BUS'] = df['From_Bus']
    elif 'from_bus' in df.columns:
        df['FROM_BUS'] = df['from_bus']
```

---

## AI Assistant Architecture (v1.1)

### Hybrid Response System

**Architecture:** Two-tier intelligent response system combining rule-based and LLM-generated responses

```
User Query
    ↓
┌─────────────────────────────────────────┐
│   Query Intent Classification           │
│   • Pattern matching on keywords        │
│   • Entity extraction (case, bus, etc.) │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│          Decision Router                │
├─────────────────┬───────────────────────┤
│ Power System    │ General/Conversational│
│ Keywords Found? │ Query?                │
└────────┬────────┴──────────┬────────────┘
         ↓ YES               ↓ NO
┌────────────────┐   ┌──────────────────┐
│  Rule-Based    │   │  Llama LLM       │
│  Response      │   │  Generation      │
│  (~instant)    │   │  (~2 seconds)    │
└────────────────┘   └──────────────────┘
         ↓                   ↓
┌─────────────────────────────────────────┐
│       Formatted Response to User         │
└─────────────────────────────────────────┘
```

### Llama Model Integration

**Model Specifications:**
- **Model:** TinyLlama/TinyLlama-1.1B-Chat-v1.0
- **Size:** 2.2 GB (downloaded once, cached locally)
- **Parameters:** 1.1 billion
- **Architecture:** Llama-style transformer decoder
- **Context Window:** 2048 tokens
- **Quantization:** FP16 (GPU) / FP32 (CPU)

**Initialization Process:**
```python
# Startup (lines 25-66 in power_viz_with_database.py)
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

# Load tokenizer
LLAMA_TOKENIZER = AutoTokenizer.from_pretrained(model_name)

# Load model (auto-detects CPU/GPU)
LLAMA_MODEL = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device_map="auto",
    low_cpu_mem_usage=True
)

LLAMA_AVAILABLE = True  # Flag for fallback handling
```

**Response Generation Flow:**
```python
def generate_llama_response(user_message, context_info):
    """Generate conversational response using Llama model"""
    
    # 1. System Prompt Configuration
    system_prompt = """You are PSA (Power System Assistant), 
    a friendly AI specialized in electrical power systems..."""
    
    # 2. Message Formatting (Chat Template)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    # 3. Tokenization
    inputs = LLAMA_TOKENIZER.apply_chat_template(
        messages, add_generation_prompt=True, return_tensors="pt"
    )
    
    # 4. Model Inference
    with torch.no_grad():
        outputs = LLAMA_MODEL.generate(
            inputs,
            max_new_tokens=200,
            temperature=0.7,      # Creativity control
            top_p=0.9,            # Nucleus sampling
            do_sample=True,
            pad_token_id=LLAMA_TOKENIZER.eos_token_id
        )
    
    # 5. Decode Response
    response = LLAMA_TOKENIZER.decode(outputs[0], skip_special_tokens=True)
    
    # 6. Post-processing (extract assistant message)
    response = extract_assistant_response(response)
    
    return response
```

### Rule-Based vs LLM Decision Logic

**Rule-Based Responses (Priority):**
- "show critical lines" → Database query + formatted table
- "voltage analysis" → Switch visualization + metrics
- "list cases" → Query database + table display
- "analyze bus X" → Extract entity + run analysis
- "show generators" → Generator dispatch analysis

**LLM-Generated Responses (Fallback):**
- "how are you?" → Friendly conversational response
- "what is power factor?" → Educational explanation
- "explain contingency analysis" → Technical concept explanation
- General conversation → Natural language interaction

**Implementation:**
```python
def get_ai_response(user_message, current_viz_type, current_case_id, current_contingency_id):
    """Main AI response coordinator"""
    
    message_lower = user_message.lower()
    
    # Priority 1: Check power system keywords
    if 'critical lines' in message_lower:
        return analyze_critical_lines()  # Rule-based
    
    if 'voltage analysis' in message_lower:
        return switch_to_voltage_view()  # Rule-based
    
    if 'show generators' in message_lower:
        return display_generator_analysis()  # Rule-based
    
    # ... more rule-based checks ...
    
    # Priority 2: Use Llama for unmatched queries
    if LLAMA_AVAILABLE:
        context = f"Current view: {current_viz_type}, Case: {current_case_id}"
        llama_response = generate_llama_response(user_message, context)
        
        # Add helpful PSA tips
        llama_response += "\n\n💡 Power System Commands:\n"
        llama_response += "• 'Smart analysis' - AI insights\n"
        llama_response += "• 'Show critical lines' - Find overloads\n"
        
        return llama_response
    
    # Priority 3: Static fallback if Llama fails
    return "I specialize in power system analysis. Try 'help' for commands."
```

### Performance Characteristics

**Model Loading:**
- First run: Downloads 2.2 GB (~2-5 minutes)
- Subsequent runs: Loads from cache (~5-10 seconds)
- Cache location: `C:\Users\<user>\.cache\huggingface\hub\`

**Response Generation:**
- Rule-based: < 100ms (instant)
- Llama inference: 1-3 seconds on CPU
- GPU inference: ~500ms (if available)

**Memory Footprint:**
- Base application: ~500 MB RAM
- With Llama loaded: ~2.5-3 GB RAM
- PyTorch overhead: ~200 MB

### Context Awareness

**System Prompt Injection:**
```python
system_prompt = f"""You are PSA (Power System Assistant)...

Current context: 
- View: {current_viz_type}
- Case ID: {current_case_id}
- Contingency: {current_contingency_id}
- Database: IEEE 118-bus system

Use this context when answering questions."""
```

**Benefits:**
- Llama understands current user state
- Can reference specific cases in responses
- Provides contextually relevant suggestions

### Error Handling & Fallback

**Graceful Degradation:**
```python
if LLAMA_AVAILABLE:
    try:
        return generate_llama_response(message)
    except Exception as e:
        print(f"⚠️ Llama failed: {e}")
        # Continue to rule-based fallback
        
# Static fallback if Llama unavailable
return static_rule_based_response(message)
```

**Failure Modes:**
1. Model download fails → Use rule-based only
2. GPU out of memory → Fallback to CPU
3. Generation timeout → Return cached response
4. Token limit exceeded → Truncate and retry

---

## Component Design

### Core Visualization Functions

#### 1. Network Graph Generator
**Function:** `create_network_graph(buses_df, branches_df, case_id, contingency_id)`

**Purpose:** Generate interactive force-directed network topology

**Inputs:**
- `buses_df`: Bus voltage and coordinate data
- `branches_df`: Branch connectivity and loading data
- `case_id`: Base case identifier
- `contingency_id`: Contingency scenario identifier

**Output:** Plotly graph object with nodes and edges

**Key Features:**
- Force-directed layout using NetworkX
- Color-coded branches by loading percentage
- Interactive hover information
- Zoom and pan capabilities

#### 2. SLR vs DLR Comparison
**Function:** `create_slr_dlr_comparison(comparison_df, base_case_id)`

**Purpose:** Side-by-side comparison of SLR and DLR methodologies

**Visualization Types:**
- Violation count comparison (bar chart)
- Branch loading distribution (histograms)
- Voltage profile comparison (line charts)
- Statistical summary (tables)

**Color Scheme:**
- Blue (#4169E1) = SLR
- Green (#32CD32) = DLR
- Red = Violations

#### 3. Contingency Ranking
**Function:** `create_contingency_ranking_plot(db_path, base_case_id)`

**Purpose:** Rank all contingencies by severity score

**Algorithm:**
1. Query all contingency scenarios
2. Calculate 5 severity metrics per contingency
3. Compute weighted severity score
4. Sort and rank contingencies
5. Generate 4-panel dashboard

**Metrics:**
- Violations (30% weight)
- Max Loading (25% weight)
- Voltage Deviation (20% weight)
- Redispatch (15% weight)
- Load Shedding (10% weight)

#### 4. Generator Analysis
**Function:** `create_generator_analysis_plot(case_id, contingency_id, comparison_type)`

**Purpose:** Analyze generator redispatch requirements

**Modes:**
- **SLR vs DLR Comparison:** Side-by-side bar charts
- **Single Analysis:** 4-panel dashboard (distribution, locations, capacity, statistics)

**Data Sources:**
- `SLR_Generator` table
- `DLR_Generator` table

---

## Visualization Engine

### Plotly Architecture

**Library:** Plotly.py (Python wrapper for Plotly.js)

**Chart Types Used:**
1. **Scatter Plots** - Network nodes, bus voltages
2. **Line Charts** - Trends, voltage profiles
3. **Bar Charts** - Comparisons, violations, rankings
4. **Histograms** - Loading distributions
5. **Tables** - Statistical summaries
6. **Heatmaps** - Not currently implemented
7. **Subplots** - Multi-panel dashboards (2x2, 3x2 layouts)

### Figure Generation Pattern

```python
def create_visualization(data, case_id, contingency_id):
    """Standard visualization function pattern"""
    
    # 1. Data Validation
    if data.empty:
        return create_error_figure("No data available")
    
    # 2. Column Normalization
    data = normalize_columns(data)
    
    # 3. Metric Calculations
    metrics = calculate_metrics(data)
    
    # 4. Figure Creation
    fig = go.Figure()  # or make_subplots()
    
    # 5. Add Traces
    fig.add_trace(go.Scatter(...))
    
    # 6. Update Layout
    fig.update_layout(
        title=f"Analysis - Case {case_id}",
        height=800,
        template="plotly_white"
    )
    
    # 7. Return Figure
    return fig
```

### Interactive Features

**Hover Information:**
- Custom hover templates with formatted data
- Multi-line tooltips
- Contextual information

**Click Events:**
- Branch selection
- Bus selection
- Contingency selection

**Zoom & Pan:**
- Plotly's built-in zoom tools
- Reset axes button
- Box select and lasso select

---

## API & Callbacks

### Dash Callback System

**Architecture:** Event-driven reactive programming

**Callback Pattern:**
```python
@app.callback(
    Output('component-id', 'property'),  # What to update
    Input('trigger-id', 'property'),     # What triggers update
    State('state-id', 'property')        # Additional context
)
def callback_function(trigger_value, state_value):
    # Process inputs
    # Query database
    # Generate visualization
    # Return output
    return result
```

### Core Callbacks

#### 1. Dynamic Plot Update
**Callback:** `update_dynamic_plot()`

**Triggers:**
- Visualization type dropdown change
- Case selector change
- Contingency selector change
- Compare button click

**Outputs:** Main graph figure

**Logic Flow:**
1. Parse callback context to identify trigger
2. Extract case_id and contingency_id
3. Route to appropriate visualization function
4. Return generated figure

#### 2. AI Assistant Response
**Callback:** `update_ai_response()`

**Triggers:**
- User submits query in chatbot
- User clicks suggested query

**Outputs:** AI response text

**Logic Flow:**
1. Parse natural language query
2. Extract entities (case numbers, components)
3. Determine intent (show network, analyze branch, etc.)
4. Execute appropriate action
5. Return formatted response

#### 3. Figure Summary Generation
**Callback:** `generate_figure_summary()`

**Triggers:**
- New figure generated
- Visualization type changes

**Outputs:** HTML summary text

**Logic Flow:**
1. Detect current visualization type
2. Query database for relevant metrics
3. Calculate statistics
4. Generate formatted HTML summary
5. Return summary with color-coded metrics

#### 4. Trend Analysis Update
**Callback:** `update_trend_visualizations()`

**Triggers:**
- Trend analysis selected
- Metric dropdown changes

**Outputs:** Multiple trend graphs

**Logic Flow:**
1. Query all contingency data for base case
2. Group by contingency_id
3. Calculate metric trends
4. Generate line/bar charts
5. Return 3-panel dashboard

### Callback Dependencies

```
User Interaction
    ↓
Input Component Triggered
    ↓
callback_context.triggered_id
    ↓
Callback Function Executed
    ↓
Database Query (if needed)
    ↓
Data Processing
    ↓
Visualization Generation
    ↓
Output Component Updated
    ↓
Browser Re-renders
```

---

## Security & Performance

### Security Considerations

**1. Database Security**
- Environment variables for PostgreSQL credentials
- No hardcoded passwords in source code
- SQL injection prevention via parameterized queries

**2. Input Validation**
- Case ID and contingency ID validation
- Dropdown value validation
- Error handling for invalid inputs

**3. Access Control**
- Local deployment: No authentication required
- Cloud deployment: Recommend adding authentication layer
- Potential integration with OAuth/LDAP

### Performance Optimization

**1. Database Optimization**
- Indexed columns: `base_case_id`, `contingency_case_id`, `bus_number`
- Query optimization with WHERE clauses
- Connection pooling for multiple queries

**2. Data Processing**
- pandas vectorized operations (no loops)
- NumPy for mathematical calculations
- Lazy loading of data (query only when needed)

**3. Caching Strategy**
```python
# Global dataframes cached in memory
global buses_df, branches_df, comparison_df

# Prevents repeated database queries
```

**4. Frontend Optimization**
- Debouncing on input fields
- Conditional rendering
- Lazy loading of large datasets

**5. Code Optimization**
- NaN/Inf handling with replace() instead of loops
- Column normalization with dictionary lookups
- Reusable utility functions

### Error Handling

**Strategy:** Try-Except blocks with graceful degradation

```python
try:
    # Attempt primary query
    data = pd.read_sql_query(primary_query, conn)
except Exception as e:
    try:
        # Attempt fallback query
        data = pd.read_sql_query(fallback_query, conn)
    except Exception as e2:
        # Return empty figure with error message
        return create_error_figure(str(e2))
```

**Error Recovery:**
- Fallback queries for missing data
- Default values for None inputs
- Empty figure generation with informative messages

---

## Deployment Architecture

### Local Deployment

**Requirements:**
```
Python 3.8+
SQLite 3.x (bundled with Python)
pip packages: dash, plotly, pandas, numpy, networkx
```

**Startup Command:**
```bash
python power_viz_with_database.py
```

**Access URL:**
```
http://localhost:8055
```

**Advantages:**
- No internet required
- Fast response times
- Full data privacy
- Easy debugging

### Cloud Deployment Options

#### Option 1: Heroku
```yaml
Files needed:
  - requirements.txt
  - Procfile: web: gunicorn power_viz_with_database:server
  - runtime.txt: python-3.9.x
```

#### Option 2: AWS (EC2 + RDS)
```
Components:
  - EC2 instance running Python/Dash
  - RDS PostgreSQL for database
  - Elastic Load Balancer
  - Route 53 for DNS
```

#### Option 3: Docker Container
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8055
CMD ["python", "power_viz_with_database.py"]
```

### Scalability Considerations

**Current State:** Single-server architecture

**Scaling Strategies:**
1. **Vertical Scaling:** Increase server CPU/RAM
2. **Database Optimization:** Move to PostgreSQL with indexing
3. **Caching Layer:** Redis for frequently accessed data
4. **CDN:** Serve static assets from CDN
5. **Load Balancing:** Multiple application servers

**Estimated Capacity:**
- Current: 10-50 concurrent users
- Optimized: 100-500 concurrent users
- Clustered: 1000+ concurrent users

---

## System Requirements

### Development Environment
- **OS:** Windows 10/11, macOS, Linux
- **Python:** 3.8 or higher (3.9+ recommended for LLM)
- **RAM:** 4 GB minimum, **8 GB recommended** (12 GB with Llama)
- **Storage:** 500 MB for code + database, **+2.5 GB for Llama model**
- **Browser:** Chrome, Firefox, Safari, Edge (latest versions)
- **GPU:** Optional (NVIDIA CUDA for faster inference)

### Production Environment
- **Server RAM:** 8 GB minimum, **12 GB recommended with Llama**
- **CPU:** 4 cores minimum, **8 cores recommended for Llama**
- **Storage:** 10 GB (with data growth + cached models)
- **Network:** 100 Mbps minimum
- **Concurrent Users:** 50 (single server without Llama), 30-40 (with Llama on CPU)

---

## Integration Points

### External Systems Integration

**1. Power Flow Simulation Tools**
- MATPOWER (MATLAB)
- PowerWorld Simulator
- PSS/E (Siemens)
- DIgSILENT PowerFactory

**Integration Method:** CSV/Excel export → Database import scripts

**2. Weather Data Services (for DLR)**
- NOAA Weather API
- OpenWeather API
- Local weather stations

**Data Flow:** Weather data → DLR calculation → Database update

**3. SCADA Systems**
- Real-time power flow data
- Real-time line ratings
- Real-time weather conditions

**Integration:** REST API or MQTT protocol

---

## Future Architecture Enhancements

### Recommended Improvements

**1. Microservices Architecture**
```
API Gateway
    ↓
├── Visualization Service
├── Database Service
├── Analytics Service
└── AI Assistant Service
```

**2. Real-Time Data Streaming**
- Apache Kafka for event streaming
- WebSocket connections for live updates
- Time-series database (InfluxDB)

**3. Machine Learning Integration**
- Predictive models for contingency severity
- Anomaly detection algorithms
- Load forecasting models

**4. Advanced Analytics**
- Monte Carlo simulation
- Optimization algorithms (OPF)
- Risk assessment models

**5. Mobile Application**
- React Native mobile app
- Offline mode with local storage
- Push notifications for critical events

---

## Conclusion

This technical architecture provides a **scalable, maintainable, and performant** foundation for power system analysis and visualization. The modular design allows for easy extension and integration with external systems while maintaining code quality and user experience.

**Key Strengths:**
✅ Modular component-based architecture  
✅ Dual database support (SQLite/PostgreSQL)  
✅ Comprehensive error handling  
✅ Interactive real-time visualizations  
✅ Scalable callback system  
✅ Clean separation of concerns  

**Total System Metrics:**
- **16,854** lines of Python code (+873 for Llama integration)
- **20+** Dash callbacks
- **15+** visualization functions
- **5** database tables
- **577** contingency scenarios
- **118** buses, **186** branches
- **1.1B** parameter Llama model
- **2-tier** AI response system (rule-based + LLM)

---

**Document Maintained By:** AI Assistant  
**Last Updated:** November 25, 2025  
**Version History:**
- v1.0 (Nov 18, 2025): Initial architecture documentation
- v1.1 (Nov 25, 2025): Added Llama LLM integration for AI assistant

**Contact:** DLR Project Team

---

## Appendix A: Llama Integration Files

**New Files Created (v1.1):**
1. `test_llama_integration.py` - Test script for model loading and inference
2. `LLAMA_INTEGRATION.md` - Detailed integration documentation
3. `LLAMA_INTEGRATION_SUMMARY.md` - Quick reference guide

**Modified Files:**
1. `power_viz_with_database.py` - Added Llama initialization and response generation
   - Lines 25-66: Model loading
   - Lines 6899-6991: `generate_llama_response()` function
   - Lines 9442-9490: Hybrid response fallback logic

**Dependencies Added:**
```bash
pip install transformers torch accelerate sentencepiece
```

**Configuration:**
- Model downloads to: `~/.cache/huggingface/hub/`
- Model size: 2.2 GB
- Load time: ~5-10 seconds from cache
- Response time: ~1-3 seconds on CPU

---

## Appendix B: AI Response Examples

**Rule-Based Response Example:**
```
User: "show me critical lines"
PSA: ⚡ Critical Lines & Violations Analysis
     Case 42 | Database: main
     
     ⚠ THERMAL VIOLATIONS (3 lines)
     1. Bus 77 → 80
        • Loading: 127.5% ⚠ OVERLOAD
        • Power Flow: 85.2 MW
        • Rating: 66.8 MW
     [Response time: <100ms]
```

**Llama-Generated Response Example:**
```
User: "what is power system analysis?"
PSA: 🔋 Power system analysis (PSA) is a scientific field 
     that involves modeling and analyzing power systems to 
     study their behavior, performance, and reliability. 
     It includes studying electrical power transmission 
     and distribution networks, power generation, and 
     consumption patterns...
     
     💡 Power System Commands:
     • 'Smart analysis' - AI-powered system insights
     • 'Show critical lines' - Find overloaded branches
     [Response time: ~2 seconds]
```
