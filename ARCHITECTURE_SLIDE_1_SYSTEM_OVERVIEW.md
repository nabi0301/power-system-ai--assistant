# Slide 1: System Overview & Architecture
## DLR Database Visualization Platform - Technical Architecture

---

## 🎯 System Purpose
**Web-based interactive dashboard for analyzing and comparing Static Line Rating (SLR) vs Dynamic Line Rating (DLR) across 577 power system contingency scenarios**

---

## 🏗️ Architecture Pattern
**Model-View-Controller (MVC) with Event-Driven Architecture**

```
┌─────────────────────────────────────────────────────┐
│         USER INTERFACE (Browser)                    │
│  • Network Graphs  • Loading Analysis  • AI Chat   │
│         Plotly Dash (React.js + Python)             │
└─────────────────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│       APPLICATION LAYER (Python Callbacks)          │
│  • 20+ Dash Callbacks  • 15+ Visualization Funcs   │
│  • NLP Processing      • Statistical Analytics      │
└─────────────────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│       DATA LAYER (SQLite/PostgreSQL)                │
│  • 5 Tables  • 118 Buses  • 186 Branches           │
│  • 577 Contingency Scenarios                        │
└─────────────────────────────────────────────────────┘
```

---

## 💻 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Plotly Dash 2.x | Web UI framework |
| **Visualization** | Plotly.js 5.x | Interactive charts |
| **Backend** | Python 3.8+ | Application logic |
| **Data Processing** | pandas + NumPy | Analytics engine |
| **Database** | SQLite/PostgreSQL | Data storage |
| **Network Analysis** | NetworkX | Graph layouts |

---

## 📊 Key Metrics
- **Code Size:** 15,981 lines of Python
- **Data Volume:** 577 scenarios × 118 buses × 186 branches
- **Visualization Types:** 10+ chart types (network, bar, scatter, table, histogram)
- **Analysis Modes:** 8 distinct analysis views
- **Concurrent Users:** 50+ (single server deployment)

---

## 🎨 Core Features
✅ **Real-time Interactive Visualizations**  
✅ **SLR vs DLR Comparison Engine**  
✅ **Contingency Severity Ranking**  
✅ **AI-Powered Natural Language Queries**  
✅ **Multi-scenario Trend Analysis**  
✅ **Automated Violation Detection**  

---

## 🚀 Deployment Options
- **Local:** Python server (localhost:8055)
- **Cloud:** Heroku, AWS EC2+RDS, Docker containers
- **Access:** Browser-based (Chrome, Firefox, Safari, Edge)
