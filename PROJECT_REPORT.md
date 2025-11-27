# Power System Visualization and Analysis Platform
## Comprehensive Project Report

---

## Executive Summary

This project represents a sophisticated web-based power system visualization and analysis platform designed for analyzing IEEE 118-bus test systems with advanced Dynamic Line Rating (DLR) and Static Line Rating (SLR) optimization capabilities. The platform integrates real-time database querying, interactive network visualizations, artificial intelligence-powered assistance, and comprehensive multi-scenario analysis tools. Built using modern Python web frameworks and leveraging both SQLite and PostgreSQL databases, the system provides engineers and researchers with powerful tools to analyze power grid behavior under various operating conditions and contingencies.

## 1. Introduction and Project Overview

### 1.1 Purpose and Scope

The Power System Visualization Platform was developed to address the critical need for intuitive, interactive analysis of complex power system optimization results. Modern power grids face increasing complexity due to renewable energy integration, dynamic loading conditions, and the need for real-time operational decisions. This platform specifically focuses on comparing Static Line Rating (SLR) approaches with more advanced Dynamic Line Rating (DLR) methodologies, which account for real-time environmental conditions affecting transmission line capacity.

The system analyzes the IEEE 118-bus test case, a standard benchmark in power systems research, containing 118 buses (nodes), approximately 186 transmission branches (lines), and multiple generators and loads distributed across the network. The platform enables detailed examination of how generator redispatch strategies differ between SLR and DLR optimization approaches when the system experiences various contingency scenarios such as transmission line failures.

### 1.2 Key Features

The platform offers seven distinct visualization modes including Network View, Network Graph Comparison, Loading Analysis, SLR vs DLR comparison, Generator Analysis, Case Analysis, and Trend Analysis. It supports multi-database connectivity, allowing simultaneous access to SQLite and PostgreSQL data sources. An integrated AI assistant powered by local Large Language Models provides natural language querying capabilities, while real-time interactive visualizations enable deep exploration of power system states.

## 2. Technical Architecture

### 2.1 Technology Stack

The application is built on Dash, a Python framework for building analytical web applications, with Plotly providing interactive visualization capabilities. The backend utilizes both SQLite (data.db) for local storage and PostgreSQL for enterprise-scale data management. Data processing leverages Pandas for dataframe operations and NumPy for numerical computations. NetworkX handles graph-theoretic network analysis, while the AI component employs Ollama with Llama 3.2 (3B parameter model) for natural language processing.

### 2.2 Database Schema and Data Model

The database architecture encompasses multiple interconnected tables organizing power system data hierarchically. Base case tables (BaseBusData, BaseBranchData, BaseCaseFiles) store original system configurations including bus voltages, branch power flows, and impedances. Contingency tables (ContingencyCases, ContingencyBusData, ContingencyBranchData) capture system states after specific failure events. Optimization result tables for both SLR (SLR_Cases, SLR_Buses, SLR_Branches, SLR_Generator, SLR_Load) and DLR (DLR_Cases, DLR_Buses, DLR_Branches, DLR_Generator, DLR_Load) store the outcomes of different optimization approaches.

Each base case is identified by a base_case_id, with Case 42 serving as the primary focus for analysis. Contingency scenarios are numbered 1 through 5, representing different transmission line failures. The SLR and DLR optimization results for these contingencies are stored with case IDs 56, 90, 123, 124, and 158, creating a systematic mapping between contingency scenarios and their corresponding optimization solutions.

### 2.3 Application Architecture

The platform follows a modular architecture with clear separation of concerns. The main application file (power_viz_with_database.py) serves as the orchestration layer, coordinating between various specialized modules. Data visualization functions (data_viz_fall.py) handle network graph generation with sophisticated layout algorithms. Database management modules (database_manager.py, multi_database_manager.py) abstract database connectivity and query execution. Analysis modules (branch_analysis.py, bus_analysis.py, generator_analysis.py) provide specialized analytical capabilities. The RAG system (simple_rag.py) integrates AI-powered querying with database retrieval, while network comparison utilities (network_comparison.py) enable side-by-side visualization of different system states.

## 3. Core Functionality

### 3.1 Network Visualization

The network visualization system represents the power grid as a graph where buses are nodes and transmission lines are edges. The layout algorithm positions buses using either predefined coordinates or force-directed graph algorithms to minimize edge crossings and optimize visual clarity. Color coding conveys critical information: buses are colored by voltage magnitude (VM) using gradient scales from blue (low voltage) to red (high voltage), while branches are colored by power flow levels and loading percentages relative to thermal limits.

The Network Graph Comparison mode, a flagship feature, displays four subplots in a 2×2 grid configuration. The top-left shows the original Base Case network, the top-right displays the Contingency Case after a line failure, the bottom-left presents the SLR optimization results, and the bottom-right shows the DLR optimization results. This arrangement enables direct visual comparison of how different optimization approaches respond to the same contingency event.

### 3.2 Generator Redispatch Visualization

A critical innovation in the platform is the visualization of generator redispatch through diamond-shaped overlay markers. When the system experiences a contingency, certain generators must adjust their output to maintain system balance and respect transmission constraints. The platform extracts GEN_ADJ (generator adjustment) values from the database, which represent the change in generator output from the initial condition.

For SLR optimization results, blue diamond markers (20 pixels, 0.9 opacity, white 2-pixel border) are overlaid precisely on bus positions where generators have been redispatched. Similarly, green diamond markers indicate DLR generator adjustments. The positioning system extracts exact coordinates from the underlying node trace data, ensuring diamonds appear directly on top of their corresponding buses rather than scattered randomly across the network. This visual encoding allows analysts to immediately identify which generators were activated or deactivated and where in the network these changes occurred.

### 3.3 Multi-Scenario Analysis

The platform supports comprehensive comparison across five contingency scenarios for each base case. Users select a base case (e.g., Case 42) and then choose from contingencies 1 through 5, each representing the failure of a specific transmission line. The system dynamically loads the appropriate contingency data along with corresponding SLR and DLR optimization results.

Generator Analysis visualizations provide histogram distributions of generator outputs, scatter plots showing generator locations versus output levels, output versus capacity comparisons highlighting utilization rates, and statistical summary tables presenting key metrics including total generation, average output, and active generator counts. The SLR vs DLR comparison specifically focuses on how generator redispatch differs between the two approaches, showing side-by-side bar charts of adjusted generation, utilization analysis scatter plots, cost/efficiency comparisons, and comprehensive summary statistics.

### 3.4 Loading and Trend Analysis

Loading Analysis examines transmission branch utilization through multiple perspectives. Histograms show the distribution of branch loading percentages across the network. Scatter plots correlate power flow with thermal limits, identifying heavily loaded lines. Time-series or scenario-based trends reveal how loading patterns change across different contingencies. Violation detection highlights branches exceeding safe operating limits.

Trend Analysis provides longitudinal insights across multiple cases or scenarios. Voltage trend plots show how bus voltages evolve, loading trend plots track branch utilization changes, and correlation plots identify relationships between different system variables. This multi-chart approach enables pattern recognition and anomaly detection across large datasets.

## 4. Artificial Intelligence Integration

### 4.1 RAG System Architecture

The Retrieval-Augmented Generation (RAG) system combines database querying with natural language processing to enable conversational interaction with power system data. When a user poses a question, the system first analyzes the query to identify key entities (bus numbers, case IDs, metrics) and intent (information retrieval, visualization request, comparison).

The retrieval component executes SQL queries against the database to fetch relevant data. For example, asking "What is the voltage at bus 50 in case 42?" triggers a query to BaseBusData filtering by base_case_id=42 and BUS_NUMBER=50. The retrieved data is then formatted into natural language responses or structured tables depending on the query complexity.

### 4.2 Local LLM Deployment

The platform employs Ollama to run Llama 3.2, a 3-billion parameter language model, locally on the user's machine. This approach ensures data privacy, eliminates cloud API dependencies, and provides low-latency responses. The model is fine-tuned through prompt engineering to understand power system terminology and respond appropriately to domain-specific queries.

The chat interface is positioned at the bottom-left of the screen in a floating, collapsible panel. Users can type natural language queries or use the Enter key for quick submission. The system maintains conversation context, allowing follow-up questions that reference previous exchanges.

### 4.3 Visualization Command Detection

A sophisticated prompt engineering system enables the AI to detect visualization change requests within user queries. Regular expressions and keyword matching identify phrases like "show network graph," "compare case X with contingency Y," or "display generator analysis." When detected, the system updates the visualization selector dropdowns and triggers the appropriate callback to render the requested view.

The viz-command-store component acts as a bridge between the chat system and the visualization engine. When the AI identifies a visualization command, it stores metadata including the requested visualization type (network_view, dual_network, generators, etc.), the target case_id, and contingency_id in this hidden div. Callback functions monitor this store and update the main plot accordingly.

## 5. Implementation Challenges and Solutions

### 5.1 Subplot Update Issue

A significant technical challenge emerged with the Network Graph Comparison feature. When users changed contingency selections, the Base Case and Contingency Case subplots (positions 1 and 2 in the 2×2 grid) updated correctly, but the SLR and DLR subplots (positions 3 and 4) remained frozen displaying data from the first loaded contingency.

Extensive debugging revealed that the backend Python code was functioning correctly—terminal logs confirmed that new figures were being created with the correct data for each contingency change. The issue was identified as a client-side Dash/Plotly.js rendering problem. Dash's diffing algorithm, which normally optimizes updates by only re-rendering changed elements, was failing to detect changes in complex subplot structures.

Multiple solution approaches were attempted including using uirevision parameters to force layout updates, adding datarevision keys with timestamps to signal data changes, implementing deep copying of figure objects to break reference chains, adding invisible marker traces with unique names as refresh triggers, and setting clear_on_unhover=True in the graph configuration.

The final solution implemented a clientside JavaScript callback that bypasses Dash's diffing algorithm entirely. Using Plotly.purge() to completely destroy the existing plot followed by Plotly.newPlot() to recreate it from scratch, this "nuclear option" ensures that every figure update results in a complete redraw. A revision tracking system prevents unnecessary redraws when the data hasn't actually changed.

### 5.2 Data Mapping Complexity

Mapping between base cases, contingencies, and optimization results required careful database design. The ContingencyCases table links base_case_id to contingency scenarios, while SLR and DLR tables use different case ID ranges. Helper functions like get_contingencies_for_case() and mapping dictionaries ensure correct data retrieval across these related but separately stored datasets.

### 5.3 Position Accuracy for Overlays

Placing diamond markers exactly on bus positions required extracting coordinates from the underlying node trace rather than recalculating them. The bus_to_pos dictionary maps each bus number to its (x, y) coordinates by iterating through the node trace's x and y arrays. This approach guarantees pixel-perfect alignment between buses and their overlay markers.

## 6. Future Enhancements

Potential improvements include real-time data streaming for live grid monitoring, advanced optimization algorithm integration for what-if analysis, enhanced AI capabilities with larger models and domain-specific fine-tuning, mobile-responsive design for tablet and smartphone access, export functionality for reports and datasets, collaborative features for multi-user analysis sessions, and integration with SCADA systems for real operational data.

## 7. Conclusion

This Power System Visualization Platform represents a significant advancement in making complex power system analysis accessible and intuitive. By combining interactive visualizations, multi-database support, AI-powered assistance, and comprehensive analytical tools, it empowers engineers and researchers to understand and optimize power grid operations more effectively. The platform's modular architecture and open-source foundation position it for continued evolution as power system analysis needs advance.

---

**Project Statistics:**
- Lines of Code: ~11,328 (main application)
- Supported Database Systems: SQLite, PostgreSQL
- Visualization Types: 7 main modes
- Test System: IEEE 118-bus (118 buses, 186 branches)
- AI Model: Llama 3.2 (3B parameters)
- Technology Stack: Python, Dash, Plotly, Pandas, NetworkX
- Data Tables: 22+ specialized tables
- Contingency Scenarios: 5 per base case
- Optimization Approaches: SLR and DLR comparison

**Development Timeline:**
The project evolved through multiple phases including initial data loading and visualization, network graph implementation with layout algorithms, multi-database integration, AI assistant integration with RAG, comparative analysis features, generator redispatch visualization, and ongoing debugging and optimization.

This platform demonstrates the power of modern web technologies, open-source AI models, and thoughtful software architecture in creating tools that advance power systems engineering research and operational practice.
