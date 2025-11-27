# 🔌 Power System Visualization Application - Setup Guide

## 📋 **Quick Start Summary**

This is a comprehensive power system analysis application with AI assistant, network visualization, and DLR vs SLR comparison capabilities.

**🌐 Application URL**: `http://127.0.0.1:8054` (after setup)

---

## 🎯 **What This Application Does**

### **Core Features**
- **Interactive Network Visualization**: IEEE 118-bus power system topology
- **SLR vs DLR Comparison**: Static vs Dynamic Line Rating analysis for 5 scenarios
- **AI Assistant**: Chat interface with power system knowledge and data completion
- **Multi-Case Analysis**: Base case 42 with contingencies 56, 90, 123, 124, 158
- **Real-Time Analysis**: Voltage, loading, violations, and generator analysis

### **Key Capabilities**
- 🔍 **Intelligent Data Completion**: AI fills missing data using physics-based algorithms
- 📊 **5-Scenario Comparison**: Individual analysis for different contingency cases
- 🤖 **Smart AI Chat**: Answers questions about power systems with confidence levels
- 🌐 **Network Graphs**: Interactive topology visualization with cross marks for violations
- 📈 **Trend Analysis**: Historical and comparative analysis across scenarios

---

## 🚀 **Installation & Setup**

### **Step 1: Prerequisites**
```bash
# Required: Python 3.8+ and pip
python --version  # Should be 3.8 or higher
pip --version
```

### **Step 2: Download Required Files**
You need these **essential files** to run the application:

#### **Core Application Files** (Required)
```
📁 Main Application
├── power_viz_with_database.py          # Main application
├── data.db                             # SQLite database (118-bus system data)
└── config.json                         # Configuration file

📁 Visualization Components
├── data_viz_fall.py                    # Network graph visualization
├── branch_analysis.py                  # Branch/line analysis
├── bus_analysis.py                     # Bus voltage analysis
├── generator_analysis_functions.py     # Generator analysis
└── enhanced_network_graphs.py          # Enhanced network visualizations

📁 Data Management
├── database_manager.py                 # Database operations
├── multi_database_manager.py           # Multi-database support
├── dynamic_case_management.py          # Case ID management
└── data_availability.py                # Data availability checking

📁 AI Features (Optional but Recommended)
├── simple_rag.py                       # AI chat system
├── intelligent_data_completion.py      # Smart data completion
├── case_comparison.py                  # Case comparison
├── network_comparison.py               # Network comparison
├── entity_extraction.py                # Entity extraction
├── comprehensive_trend_analyzer.py     # Trend analysis
└── individual_analysis.py              # Individual analysis
```

### **Step 3: Install Python Dependencies**
```bash
# Install required packages
pip install dash plotly pandas sqlite3 numpy networkx

# Optional for enhanced features
pip install scikit-learn chromadb langchain
```

### **Step 4: Verify Setup**
```python
# Quick verification script
import os

essential_files = [
    'power_viz_with_database.py',
    'data_viz_fall.py', 
    'branch_analysis.py',
    'bus_analysis.py',
    'generator_analysis_functions.py',
    'dynamic_case_management.py',
    'data_availability.py',
    'database_manager.py',
    'multi_database_manager.py',
    'data.db'
]

missing = [f for f in essential_files if not os.path.exists(f)]
if missing:
    print("❌ Missing files:", missing)
else:
    print("✅ All essential files present!")
```

---

## 🏃‍♂️ **Running the Application**

### **Method 1: Direct Run**
```bash
# Navigate to the project directory
cd path/to/dlr-database-project

# Run the application
python power_viz_with_database.py
```

### **Method 2: Using Virtual Environment (Recommended)**
```bash
# Create virtual environment
python -m venv dlr-env

# Activate (Windows)
dlr-env\Scripts\activate

# Activate (Mac/Linux)
source dlr-env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run application
python power_viz_with_database.py
```

### **Expected Output**
```
✅ Data visualization functions loaded successfully
✅ Multi-database manager loaded - Multiple database support available
✅ Simple RAG system loaded successfully
✅ Intelligent data completion system loaded successfully
...
🚀 Starting Power System Visualization with Real Database Data
🤖 AI Assistant: Local Llama 3.2 (8B) with Network Graphs
📊 Data Source: Real IEEE 118-bus database
🌐 Open: http://127.0.0.1:8054
```

---

## 🎮 **How to Use the Application**

### **1. Basic Navigation**
1. **Open Browser**: Go to `http://127.0.0.1:8054`
2. **Select Visualization**: Use dropdown to choose analysis type
3. **Select Case**: Choose Base Case 42 for SLR vs DLR comparison
4. **Explore**: Click different visualizations and interact with graphs

### **2. Key Features to Try**

#### **SLR vs DLR Comparison**
1. Select **Base Case 42** from dropdown
2. Choose **"🔄 SLR vs DLR (5 Scenarios)"**
3. View individual scenario analysis and summary

#### **AI Assistant**
1. Click the **🤖 chat icon** (bottom-left)
2. Ask questions like:
   - "Check data quality"
   - "Explain SLR vs DLR comparison"
   - "Generate missing data"
   - "Tell me a power system joke"

#### **Network Visualization**
1. Select **"🌐 Network Graph"**
2. Choose different cases and contingencies
3. Look for **red crosses** indicating violations

### **3. Data Availability**
- **Base Case 42**: Full SLR vs DLR data available
- **Contingencies**: 56, 90, 123, 124, 158
- **Other Cases**: Basic bus/branch data only (no SLR/DLR comparison)

---

## 🗃️ **Database Information**

### **Database Structure**
```sql
-- Main Tables
- BaseBusData: 118 buses across 577 base cases
- BaseBranchData: 186 branches per case
- SLR_Branches: Static Line Rating data (Case 42 only)
- DLR_Branches: Dynamic Line Rating data (Case 42 only)
- ContingencyBusData: Contingency analysis results
- ContingencyBranchData: Branch data under contingencies
```

### **Key Data Points**
- **Total Buses**: 118 (IEEE standard test system)
- **Total Branches**: 186 transmission lines
- **Base Cases**: 577 different operating scenarios
- **SLR/DLR Cases**: 5 contingency scenarios for comparison
- **Database Size**: ~50MB with comprehensive power flow data

---

## 🔧 **Troubleshooting**

### **Common Issues**

#### **Port Already in Use**
```bash
# Error: Address already in use
# Solution: Change port in power_viz_with_database.py
app.run_server(debug=False, host='0.0.0.0', port=8055)  # Use different port
```

#### **Missing Dependencies**
```bash
# Error: ModuleNotFoundError
# Solution: Install missing packages
pip install [missing-package-name]
```

#### **Database Connection Error**
```bash
# Error: database is locked
# Solution: Close other applications using the database
# Or copy data.db to a new location
```

#### **AI Features Not Working**
```bash
# Warning: RAG system not available
# This is normal - AI features are optional
# Application will work without them
```

### **Reduced Functionality Mode**
If some files are missing, the app runs with reduced features:
- **Missing AI files**: No chat assistant, but core visualization works
- **Missing analysis files**: Basic plots only
- **Missing network files**: No network visualization

---

## 🎯 **Key Use Cases**

### **For Power System Engineers**
- **Capacity Planning**: Compare SLR vs DLR benefits
- **Contingency Analysis**: Analyze system response to failures
- **Thermal Management**: Identify violation patterns
- **Operational Planning**: Understand system limitations

### **For Researchers**
- **Algorithm Testing**: Test data completion algorithms
- **Visualization Development**: Explore network visualization techniques
- **AI Integration**: Study power system AI applications
- **Comparative Analysis**: Benchmark different rating approaches

### **For Students**
- **Learn Power Systems**: Interactive IEEE 118-bus system
- **Understand Concepts**: Visual explanation of SLR vs DLR
- **Explore Data**: Real power system database
- **AI Integration**: See AI applied to engineering problems

---

## 📞 **Support & Contact**

### **Getting Help**
1. **Check Console**: Look for error messages in terminal
2. **Verify Files**: Ensure all required files are present
3. **Check Dependencies**: Install missing Python packages
4. **Database Issues**: Verify data.db file is accessible

### **Application Features**
- **Data Quality Analysis**: Click "🔍 Analyze Data Quality" button
- **Intelligent Completion**: Ask AI to "generate missing data"
- **Multi-Scenario Analysis**: Use Base Case 42 for full features
- **Interactive Visualization**: All plots are interactive (zoom, pan, hover)

---

## 🚀 **Quick Start Checklist**

```
□ Python 3.8+ installed
□ All essential files downloaded
□ Dependencies installed (dash, plotly, pandas, etc.)
□ data.db file present
□ Run: python power_viz_with_database.py
□ Open: http://127.0.0.1:8054
□ Select Base Case 42
□ Try SLR vs DLR comparison
□ Test AI chat assistant
```

**🎉 Ready to explore power system analysis with AI-enhanced visualization!**