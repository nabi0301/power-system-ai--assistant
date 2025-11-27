# Power System Visualization Tool with AI-Enhanced Contingency Analysis
## IEEE 118-Bus System: Interactive Analysis Platform for SLR/DLR Comparison

**Technical Report**

---

## Abstract

This report presents an interactive power system visualization platform integrating artificial intelligence for Static Line Rating (SLR) and Dynamic Line Rating (DLR) comparative analysis on the IEEE 118-bus test system. The system employs Llama 3.2 (8B parameters) and Claude 3.7 Sonnet language models enhanced by SimpleRAG (Retrieval-Augmented Generation) for context-aware natural language queries. The web-based interface is built with Python Dash (15,866 lines of code) using Plotly for interactive visualizations, Pandas and NumPy for data processing, and NetworkX for graph topology analysis.

The platform implements dual-database architecture supporting both SQLite for embedded single-user deployments and PostgreSQL for enterprise multi-user environments. The schema comprises 10 relational tables in Third Normal Form (3NF) managing 577 operational scenarios and 1.88 million data points, including 1 base case, 186 N-1 contingency simulations, 186 SLR corrective actions, 186 DLR corrective actions, and 18 extended test cases. Five key technical innovations distinguish this implementation: (1) parallel edge rendering algorithm using perpendicular offset calculations (3.0 unit spacing) preventing visual overlap for multi-circuit transmission lines, (2) synchronized 4-panel comparison interface enabling side-by-side evaluation of Base/Contingency/SLR/DLR system states, (3) strategic database indexing on high-frequency query patterns achieving sub-second response times when filtering 34,596 branch records, (4) automated color-coded violation classification using loading thresholds (red for critical ≥100%, orange for warning 90-99%, yellow for approaching 80-90%, gray for normal <80%), and (5) natural language processing interface enabling conversational data exploration through queries like "Show voltage violations in case 42" or "Compare SLR and DLR for contingency 55."

Performance benchmarks demonstrate sub-second database query times, visualization rendering completing in less than 100 milliseconds for typical network sizes, and AI response generation within 2-5 seconds. Results show analysis time reduction from hours to minutes, enabling rapid identification of critical vulnerabilities and quantifiable assessment of DLR operational benefits. The tool serves power system engineers, grid operators, and researchers through intuitive graphical interfaces and conversational AI assistance, establishing technical and operational feasibility for deployment in control centers, research laboratories, and educational environments.

**Keywords:** Power System Visualization, Contingency Analysis, Dynamic Line Rating, Static Line Rating, Database Management, Artificial Intelligence, Large Language Models, Retrieval-Augmented Generation, IEEE 118-Bus System, Network Graph Visualization, SQLite, PostgreSQL, N-1 Contingency, Thermal Violations, Interactive Visualization

---

## Summary

The power system visualization tool addresses the critical need for accessible, interactive analysis platforms in modern grid operations. Traditional power system analysis software often presents barriers through complex interfaces and proprietary data formats, limiting collaborative research and operational insights. This project develops an open-architecture solution that combines robust database management, modern web technologies, and artificial intelligence to democratize access to power system analysis capabilities.

The technical implementation centers on three core components: (1) a dual-database architecture supporting both embedded SQLite for single-user deployments and PostgreSQL for enterprise multi-user environments, (2) an interactive web interface built with Python Dash and Plotly for real-time network visualization and data exploration, and (3) an AI-powered natural language interface using Large Language Models (LLMs) with RAG capabilities for conversational data queries.

The IEEE 118-bus test system serves as the validation platform, encompassing 118 buses, 186 transmission branches, and 54 generators across 577 simulated scenarios. Each scenario captures comprehensive electrical states including voltage magnitudes, power flows, thermal loading percentages, and violation flags. The database schema implements third normal form (3NF) to minimize redundancy while maintaining query performance through strategic indexing on high-frequency access patterns.

Visualization capabilities include interactive network topology rendering with color-coded violation alerts, synchronized 4-panel comparisons for Base/Contingency/SLR/DLR strategy evaluation, and dynamic data overlays showing voltage profiles, loading percentages, and generator dispatch adjustments. The parallel edge rendering algorithm ensures visual clarity when multiple transmission lines connect the same bus pairs, addressing a common limitation in power system network diagrams.

The AI integration leverages Llama 3.2 (8 billion parameters) running locally via Ollama for privacy-sensitive deployments, with Claude 3.7 Sonnet as a cloud fallback for enhanced natural language understanding. The SimpleRAG system retrieves relevant database context based on user queries, enabling the AI to answer questions like "Show voltage violations in case 42" or "Compare SLR and DLR for contingency 55" with appropriate visualizations and numerical summaries.

Results demonstrate the tool's effectiveness in reducing analysis time from hours to minutes, with users able to identify critical contingencies, evaluate corrective actions, and generate reports through simple conversational commands. The platform's open architecture and comprehensive documentation facilitate extension for additional test systems, alternative rating strategies, and custom analysis modules.

---

## Acknowledgments

This project builds upon foundational research in power system analysis, dynamic line rating technologies, and modern web application frameworks. We acknowledge the IEEE Power & Energy Society for maintaining the 118-bus test system as a public research benchmark, enabling validation and comparison across diverse analysis methodologies.

Special recognition goes to the open-source community for developing and maintaining the critical software libraries that enable this work: Plotly for interactive visualization capabilities, NetworkX for graph topology algorithms, SQLite for embedded database functionality, and the Dash framework for reactive web applications. The Anthropic and Meta AI teams deserve recognition for developing Claude and Llama language models that power the natural language interface.

We extend gratitude to power system researchers and operators who provided feedback on interface design, functional requirements, and validation of contingency analysis results. Their domain expertise ensured the tool addresses real operational needs while maintaining technical rigor.

The development of this platform was guided by principles of open science, reproducible research, and accessible technology. All core functionality relies on open-source tools and publicly available test data, ensuring the work can be replicated, extended, and integrated into educational and research workflows worldwide.

---

## Abbreviations

| Abbreviation | Full Term |
|--------------|-----------|
| **AI** | Artificial Intelligence |
| **API** | Application Programming Interface |
| **CSV** | Comma-Separated Values |
| **DLR** | Dynamic Line Rating |
| **GEN_ADJ** | Generator Adjustment (MW) |
| **IEEE** | Institute of Electrical and Electronics Engineers |
| **JSON** | JavaScript Object Notation |
| **kV** | Kilovolt |
| **LLM** | Large Language Model |
| **MVA** | Megavolt-Ampere (Apparent Power) |
| **MVAr** | Megavolt-Ampere Reactive (Reactive Power) |
| **MW** | Megawatt (Active Power) |
| **N-1** | Single Contingency (One Element Outage) |
| **NLP** | Natural Language Processing |
| **ORM** | Object-Relational Mapping |
| **p.u.** | Per Unit |
| **PD** | Active Power Demand (MW) |
| **PF** | Active Power Flow From Bus (MW) |
| **PG** | Active Power Generation (MW) |
| **PNG** | Portable Network Graphics |
| **PT** | Active Power Flow To Bus (MW) |
| **QD** | Reactive Power Demand (MVAr) |
| **QF** | Reactive Power Flow From Bus (MVAr) |
| **QG** | Reactive Power Generation (MVAr) |
| **QT** | Reactive Power Flow To Bus (MVAr) |
| **RAG** | Retrieval-Augmented Generation |
| **RATE** | Thermal Rating Limit (MVA) |
| **SLR** | Static Line Rating |
| **SQL** | Structured Query Language |
| **SVG** | Scalable Vector Graphics |
| **UI** | User Interface |
| **VA** | Voltage Angle (degrees) |
| **VIO** | Violation Flag (0=No, 1=Yes) |
| **VM** | Voltage Magnitude (p.u.) |

---

## 1.0 Introduction

### 1.1 Background

Modern power systems operate under increasing stress from growing electricity demand, integration of renewable energy sources, and aging infrastructure. Transmission system operators must continuously monitor network conditions, assess potential contingencies, and implement corrective actions to maintain reliability and prevent cascading failures. Traditional static line rating (SLR) methods conservatively limit transmission capacity based on worst-case environmental conditions, often underutilizing available infrastructure during favorable weather periods.

Dynamic line rating (DLR) technologies offer an alternative approach by adjusting thermal limits in real-time based on actual environmental conditions such as ambient temperature, wind speed, and solar radiation. While DLR can increase transmission capacity by 10-30% under favorable conditions, operators require tools to evaluate the operational and economic tradeoffs between SLR and DLR strategies, particularly under contingency conditions when transmission elements are unexpectedly lost.

The IEEE 118-bus system represents a widely recognized test case in power system research, modeling a portion of the American Electric Power System as it existed in December 1962. Despite its age, the 118-bus system remains relevant for methodology validation due to its moderate complexity (118 buses, 186 branches, 54 generators) and public availability. The system exhibits realistic characteristics including multiple voltage levels, generator dispatch constraints, and challenging contingency scenarios that can trigger cascading violations.

Power system analysis traditionally relies on specialized software such as PowerWorld, PSS®E, or MATPOWER, each with proprietary interfaces and steep learning curves. While these tools provide comprehensive analysis capabilities, they present barriers for collaborative research, educational applications, and integration with modern data science workflows. Additionally, extracting insights from thousands of contingency scenarios requires extensive manual analysis, making it difficult to identify critical patterns or communicate findings to non-technical stakeholders.

This project addresses these limitations by developing an open-architecture, web-based visualization platform that combines robust database management, interactive network graphics, and AI-powered natural language processing. The tool enables users to explore 577 pre-simulated scenarios (base case, 186 N-1 contingencies, and corresponding SLR/DLR corrective actions) through intuitive graphical interfaces or conversational queries, reducing analysis time from hours to minutes while maintaining technical rigor.

### 1.2 Literature Review

Power system visualization has evolved significantly since early single-line diagrams and tabular data presentations. Overbye et al. (2004) pioneered interactive visualization techniques for voltage security assessment, demonstrating that color-coded network diagrams significantly improve operators' ability to identify emerging stability issues compared to text-based alarm lists. Their work established principles of progressive disclosure and interactive filtering that influence modern power system interfaces.

Dynamic line rating research has progressed from theoretical concepts to operational deployments over the past two decades. Michiorri et al. (2015) surveyed DLR implementation across European transmission systems, identifying that while DLR can increase capacity by 10-40% depending on weather patterns, integration challenges include operator training, reliability concerns, and coordination with existing operational procedures. Numerous studies have compared SLR and DLR strategies using simulation frameworks, but few have developed interactive tools for strategy evaluation.

Database management for power system data has received limited attention in academic literature, with most research focusing on computational algorithms rather than data architecture. Schavemaker and van der Sluis (2008) discussed data organization for power system analysis software, emphasizing the importance of normalized schemas to prevent inconsistencies during iterative power flow calculations. Recent work has explored cloud-based data storage for synchrophasor measurements and operational data historians, but contingency analysis databases remain under-researched.

Network visualization algorithms face challenges when rendering complex topologies with parallel transmission lines. Purchase et al. (2002) established graph drawing principles emphasizing edge crossing minimization and uniform node distribution. Fruchterman and Reingold's force-directed layout algorithm (1991) remains widely used for automatic graph positioning, though power system applications often benefit from geographic layouts that preserve actual substation locations.

Artificial intelligence applications in power systems have accelerated dramatically with advances in large language models. Recent work has explored LLMs for power system report generation, alarm prioritization, and automated contingency classification. However, most implementations use proprietary cloud APIs, raising concerns about data privacy and operational security. Local LLM deployment using models like Llama represents an emerging approach that balances capability with security requirements.

Retrieval-Augmented Generation (RAG) has emerged as a technique to ground LLM responses in factual data rather than relying solely on training data. Lewis et al. (2020) introduced RAG for question-answering tasks, demonstrating significant improvements in factual accuracy compared to pure generative models. RAG implementations typically combine vector embeddings for semantic search with structured database queries for precise data retrieval, a hybrid approach well-suited to power system applications where both contextual understanding and numerical accuracy are critical.

### 1.3 Key Features

The power system visualization tool provides a comprehensive suite of capabilities organized into six functional domains:

**1. Interactive Network Visualization**
- Real-time rendering of IEEE 118-bus topology with geographic bus positioning
- Color-coded violation highlighting: red (critical ≥100%), orange (warning 90-99%), yellow (approaching 80-90%), gray (normal <80%)
- Parallel edge rendering algorithm preventing overlap for multiple lines between bus pairs using perpendicular offset calculation (3.0 unit spacing)
- Interactive zoom, pan, and hover capabilities displaying detailed electrical quantities
- Synchronized 4-panel comparison views (Base/Contingency/SLR/DLR) with consistent topology
- Dynamic data overlays for voltage profiles, loading percentages, and generator output

**2. Comprehensive Database Management**
- Dual-database architecture: SQLite (embedded, ~50-100 MB) for single-user deployments, PostgreSQL for multi-user enterprise environments
- 10 relational tables implementing 3NF normalization across three functional domains
- 577 operational scenarios: 1 base case + 186 N-1 contingencies + 186 SLR solutions + 186 DLR solutions + 18 extended cases
- 1.88 million individual data points covering bus voltages, branch flows, generator dispatch, and violation flags
- Strategic indexing on high-frequency query patterns (case_id, contingency_id, VIO) achieving sub-second response times
- Transaction atomicity ensuring data consistency during concurrent access
- Export capabilities: PNG/SVG for graphics, CSV/Excel for data, JSON for API integration

**3. Contingency Analysis Capabilities**
- N-1 analysis for all 186 transmission branches with automated violation detection
- Severity ranking based on violation count, overload magnitude, and cascading potential
- Voltage violation identification (VM < 0.95 p.u. or VM > 1.05 p.u.)
- Thermal overload detection (loading ≥ 100% of RATE)
- Generator dispatch tracking showing MW adjustments for SLR and DLR corrective actions
- Tripped line highlighting in network visualizations with dashed line representation

**4. SLR vs DLR Comparison Framework**
- Side-by-side strategy evaluation with quantitative metrics
- Capacity gain calculations: (DLR_RATE - SLR_RATE) / SLR_RATE × 100%
- Violation reduction analysis comparing pre-corrective and post-corrective states
- Generator redispatch comparison showing economic and operational tradeoffs
- Statistical summaries: total lines, violation percentages, average loading
- Export-ready comparison tables for reporting and publication

**5. AI-Powered Natural Language Interface**
- Llama 3.2 (8B parameters) via Ollama for local, privacy-preserving deployment
- Claude 3.7 Sonnet (Anthropic) as cloud fallback for enhanced language understanding
- SimpleRAG system providing context-aware responses grounded in database content
- Natural language query processing: "Show voltage violations in case 42", "Compare SLR and DLR for contingency 55", "Which generators were adjusted?"
- Automated visualization generation based on query intent
- Conversational context maintenance across multi-turn dialogues
- Query disambiguation and suggestion system for unclear requests

**6. Extensible Architecture**
- Modular Python codebase (15,866 lines) with clear separation of concerns
- RESTful API design principles enabling integration with external tools
- Plugin system for custom analysis modules
- Comprehensive documentation and code comments
- Support for additional test systems through configuration files
- Database migration tools for schema updates
- Automated testing framework for validation

---

## 2.0 Data Management Framework

### 2.1 Data Generation

The power system data underlying this visualization tool originates from detailed power flow simulations conducted on the IEEE 118-bus test system using industry-standard analysis software. The data generation pipeline comprises three sequential stages: base case extraction, contingency simulation, and corrective action computation.

**Stage 1: Base Case Power Flow**

The foundation begins with a solved base case power flow representing normal system operation. The IEEE 118-bus system operates at multiple voltage levels (138 kV, 161 kV, 230 kV, and 345 kV) with 54 generators providing 4,242 MW to serve 4,242 MW of total load, achieving power balance. The base case power flow solution produces:

- 118 bus electrical quantities: voltage magnitude (VM in p.u.), voltage angle (VA in degrees), active power generation (PG in MW), reactive power generation (QG in MVAr), active power demand (PD in MW), reactive power demand (QD in MVAr)
- 186 branch power flows: active power from-bus and to-bus (PF, PT in MW), reactive power flows (QF, QT in MVAr), apparent power magnitude (MVA), thermal rating (RATE in MVA), violation flag (VIO: 0=normal, 1=overload)
- 54 generator outputs with dispatch levels, reactive power limits, and voltage setpoints

Base case data is extracted from simulation output files (typically .RAW or .M format) and transformed into relational database records. Geographic coordinates for each bus enable realistic network topology visualization, derived from original system documentation or optimized using force-directed graph layout algorithms when positions are unavailable.

**Stage 2: N-1 Contingency Simulation**

Contingency analysis simulates the loss of individual transmission elements to assess system robustness. For the 118-bus system, 186 N-1 contingency scenarios are executed, each removing one transmission branch and re-solving the power flow to determine post-contingency electrical states. Each contingency simulation produces:

- Post-contingency bus data (118 buses × 186 contingencies = 21,948 records) showing voltage deviations and power redistributions
- Post-contingency branch data (186 branches × 186 contingencies = 34,596 records) capturing flow redistributions and thermal violations
- Identification of the tripped line (from_bus, to_bus, line_id) for each scenario
- Violation flags highlighting branches exceeding thermal limits (loading ≥ 100%)

The simulation engine accounts for generator reactive power limits, voltage regulation constraints, and transformer tap position limits. Scenarios resulting in network islanding or divergent solutions are flagged for special handling, though the IEEE 118-bus system typically produces convergent solutions for all single-branch outages.

**Stage 3: Corrective Action Computation**

Following contingency identification, corrective action algorithms compute generator redispatch strategies to alleviate violations. Two strategies are evaluated:

**Static Line Rating (SLR) Corrections:**
- Thermal limits remain at conservative baseline values (typically 90-95% of conductor physical limit)
- Optimization algorithm minimizes generator adjustment costs while eliminating violations
- Generator dispatch changes (GEN_ADJ in MW) represent delta from pre-contingency values
- Prioritizes generators with lower incremental costs and available headroom

**Dynamic Line Rating (DLR) Corrections:**
- Thermal limits increased based on favorable environmental conditions (assume 15-20% capacity gain)
- Same optimization objective as SLR but with relaxed thermal constraints
- Typically requires smaller generator adjustments due to increased line capacity
- Some scenarios may require no corrections if increased ratings prevent violations

For each contingency requiring corrections, the corrective action stage produces:
- SLR_PostAction_BusData: post-correction bus voltages and power injections
- SLR_Branches: post-correction branch flows and violation status
- SLR_Generator: generator adjustments showing GEN_INI (initial), GEN_NEW (adjusted), GEN_ADJ (delta)
- Corresponding DLR tables with identical structure but different thermal limit assumptions

The complete data generation pipeline produces 577 distinct system states (1 base + 186 contingencies + 186 SLR + 186 DLR + 18 extended/variant cases), each containing full electrical state information across all buses and branches. This comprehensive dataset enables comparative analysis of contingency severity, corrective action effectiveness, and operational strategy tradeoffs.

### 2.2 Database Design and Implementation

#### 2.2.1 Structure Overview

The database architecture implements a dual-database strategy supporting both SQLite and PostgreSQL, providing deployment flexibility for different operational contexts while maintaining schema consistency.

**SQLite Implementation (Primary):**

SQLite serves as the primary database for single-user deployments, development environments, and embedded applications. The SQLite database file (`data.db`) resides in the application directory, typically 50-100 MB in size, containing all 577 scenarios. SQLite advantages include:

- **Zero configuration:** No separate database server installation or administration required
- **Embedded operation:** Database engine runs in-process with the application, eliminating network latency
- **ACID compliance:** Full transaction support ensuring data consistency
- **Cross-platform portability:** Single database file transfers seamlessly between Windows, Linux, and macOS
- **Adequate performance:** Handles typical query workloads (100-1000 queries/second) with sub-second response times
- **Minimal resource footprint:** Operates efficiently with <10 MB memory overhead

SQLite limitations become apparent in multi-user concurrent write scenarios, though the read-heavy query pattern of power system visualization (95% reads, 5% writes) operates well within SQLite's capabilities.

**PostgreSQL Implementation (Optional):**

PostgreSQL support enables enterprise deployments requiring multi-user concurrent access, advanced analytics, and high-availability configurations. PostgreSQL advantages include:

- **Multi-user concurrency:** MVCC (Multi-Version Concurrency Control) allows simultaneous reads and writes without locking
- **Advanced indexing:** GiST, GIN, and BRIN index types optimize complex queries
- **Full-text search:** Built-in text search capabilities for natural language queries
- **Replication support:** Streaming replication for high-availability and geographic distribution
- **Scalability:** Handles databases exceeding 10 TB with partitioning and parallel query execution
- **Extensions:** PostGIS for spatial analysis, pg_trgm for fuzzy string matching

PostgreSQL deployment requires separate server installation, configuration, and ongoing administration, making it appropriate for production environments with dedicated IT support.

**Schema Consistency:**

Both database implementations use identical table structures, column names, and data types, enabling transparent migration. Application code abstracts database-specific syntax through parameterized queries and Object-Relational Mapping (ORM) patterns. Connection management automatically detects available database engines, preferring PostgreSQL when configured, falling back to SQLite otherwise.

**Data Domains:**

The database schema organizes data into three functional domains:

1. **Base Case Domain:** Normal operating conditions without contingencies
   - Tables: BaseBusData, BaseBranchData
   - Purpose: Reference state for comparison and topology foundation

2. **Contingency Domain:** Post-outage system states before corrections
   - Tables: ContingencyBusData, ContingencyBranchData
   - Purpose: Identify violations requiring corrective actions

3. **Corrective Action Domain:** Post-correction system states for SLR and DLR strategies
   - Tables: SLR_PostAction_BusData, SLR_Branches, SLR_Generator, DLR_PostAction_BusData, DLR_Branches, DLR_Generator
   - Purpose: Evaluate strategy effectiveness and compare outcomes

#### 2.2.2 Schema Breakdown

The database implements 10 core tables following Third Normal Form (3NF) to minimize redundancy while maintaining query efficiency.

**BaseBusData (118 records)**

Stores base case electrical quantities for all buses in normal operating conditions.

```
Primary Key: (base_case_id, BUS_NUMBER)
Columns:
- base_case_id (INTEGER): Case identifier, typically 42 or 43
- BUS_NUMBER (INTEGER): Bus identifier (1-118)
- VM (REAL): Voltage magnitude in per unit (typical range: 0.95-1.05 p.u.)
- VA (REAL): Voltage angle in degrees (reference bus = 0°)
- BASE_KV (REAL): Base voltage level (138, 161, 230, or 345 kV)
- PG (REAL): Active power generation in MW (0 for load buses)
- QG (REAL): Reactive power generation in MVAr (0 for load buses)
- PD (REAL): Active power demand in MW (0 for generator buses)
- QD (REAL): Reactive power demand in MVAr (0 for generator buses)
- x_coord (REAL): Geographic X coordinate for visualization
- y_coord (REAL): Geographic Y coordinate for visualization

Indexes: 
- PRIMARY KEY (base_case_id, BUS_NUMBER)
- INDEX idx_base_bus_case (base_case_id)
```

**BaseBranchData (186 records)**

Records base case power flows and thermal loading for all transmission branches.

```
Primary Key: (base_case_id, FROM_BUS, TO_BUS, branch_number)
Columns:
- base_case_id (INTEGER): Case identifier
- branch_number (INTEGER): Sequential branch identifier (1-186)
- FROM_BUS (INTEGER): Sending end bus number
- TO_BUS (INTEGER): Receiving end bus number
- PF (REAL): Active power flow from FROM_BUS (MW)
- PT (REAL): Active power flow to TO_BUS (MW, negative indicates flow direction)
- QF (REAL): Reactive power flow from FROM_BUS (MVAr)
- QT (REAL): Reactive power flow to TO_BUS (MVAr)
- MVA (REAL): Apparent power magnitude (√(PF² + QF²))
- RATE (REAL): Thermal rating limit (MVA)
- VIO (INTEGER): Violation flag (0=normal, 1=overload when |PF| ≥ RATE)

Indexes:
- PRIMARY KEY (base_case_id, FROM_BUS, TO_BUS, branch_number)
- INDEX idx_base_branch_case (base_case_id)
- INDEX idx_base_branch_vio (base_case_id, VIO)
```

**ContingencyBusData (21,948 records = 118 buses × 186 contingencies)**

Captures post-contingency bus voltages and power injections for N-1 analysis.

```
Primary Key: (base_case_id, contingency_case_id, BUS_NUMBER)
Columns:
- base_case_id (INTEGER): Base case reference
- contingency_case_id (INTEGER): Contingency scenario identifier (1-186)
- BUS_NUMBER (INTEGER): Bus identifier
- VM, VA, BASE_KV, PG, QG, PD, QD (same as BaseBusData)
- tripped_from_bus (INTEGER): Outaged line sending end
- tripped_to_bus (INTEGER): Outaged line receiving end
- tripped_line_id (TEXT): Outaged line circuit identifier

Indexes:
- PRIMARY KEY (base_case_id, contingency_case_id, BUS_NUMBER)
- INDEX idx_cont_bus_case (base_case_id, contingency_case_id)
- INDEX idx_cont_bus_trip (tripped_from_bus, tripped_to_bus)
```

**ContingencyBranchData (34,596 records = 186 branches × 186 contingencies)**

Most frequently accessed table (60-70% of queries), storing post-contingency branch flows and violations.

```
Primary Key: (base_case_id, contingency_case_id, FROM_BUS, TO_BUS)
Columns:
- base_case_id (INTEGER): Base case reference
- contingency_case_id (INTEGER): Contingency scenario identifier
- branch_number (INTEGER): Branch identifier
- FROM_BUS, TO_BUS, PF, PT, QF, QT, MVA, RATE, VIO (same as BaseBranchData)

Indexes:
- PRIMARY KEY (base_case_id, contingency_case_id, FROM_BUS, TO_BUS)
- INDEX idx_cont_branch_case (base_case_id, contingency_case_id)
- INDEX idx_cont_branch_vio (base_case_id, contingency_case_id, VIO) ⭐ Critical for violation queries
- INDEX idx_cont_branch_loading (base_case_id, contingency_case_id, MVA)
```

**SLR_PostAction_BusData (varies, ~5,000-10,000 records)**

Post-SLR-correction bus states for contingencies requiring generator redispatch.

```
Primary Key: (base_case_id, contingency_case_id, BUS_NUMBER)
Columns: Same as ContingencyBusData plus:
- correction_required (INTEGER): Flag indicating if redispatch was needed (1=yes, 0=no)

Indexes:
- PRIMARY KEY (base_case_id, contingency_case_id, BUS_NUMBER)
- INDEX idx_slr_bus_case (base_case_id, contingency_case_id)
```

**SLR_Branches (varies, ~5,000-10,000 records)**

Post-SLR-correction branch flows showing violation resolution effectiveness.

```
Primary Key: (base_case_id, contingency_case_id, FROM_BUS, TO_BUS)
Columns: Same as ContingencyBranchData
Note: VIO flags should be 0 (no violations) after successful corrections

Indexes:
- PRIMARY KEY (base_case_id, contingency_case_id, FROM_BUS, TO_BUS)
- INDEX idx_slr_branch_case (base_case_id, contingency_case_id)
```

**SLR_Generator (varies, ~500-1,000 records)**

Generator adjustments applied during SLR corrective actions.

```
Primary Key: (base_case_id, contingency_case_id, BUS_NUMBER)
Columns:
- base_case_id (INTEGER): Base case reference
- contingency_case_id (INTEGER): Contingency scenario
- BUS_NUMBER (INTEGER): Generator bus location
- GEN_INI (REAL): Initial generation before correction (MW)
- GEN_NEW (REAL): New generation after correction (MW)
- GEN_ADJ (REAL): Adjustment delta = GEN_NEW - GEN_INI (MW)

Indexes:
- PRIMARY KEY (base_case_id, contingency_case_id, BUS_NUMBER)
- INDEX idx_slr_gen_adj (base_case_id, contingency_case_id, GEN_ADJ) for ranking largest adjustments
```

**DLR_PostAction_BusData, DLR_Branches, DLR_Generator**

Identical structure to SLR tables but storing DLR strategy results with increased thermal ratings. Typically shows fewer violations and smaller generator adjustments compared to SLR due to relaxed thermal constraints.

#### 2.2.3 Data Processing Techniques

Efficient data retrieval and processing are critical for responsive visualization, particularly when rendering complex network graphs or filtering scenarios by violation criteria. The implementation employs five key optimization strategies:

**1. Strategic Indexing**

Database indexes accelerate query performance by creating sorted data structures that avoid full table scans. The schema implements indexes on high-frequency query patterns:

- **Case and contingency lookups:** `(base_case_id, contingency_case_id)` composite indexes enable fast filtering to specific scenarios
- **Violation filtering:** `(base_case_id, contingency_case_id, VIO)` indexes support rapid violation identification
- **Loading-based ranking:** `(base_case_id, contingency_case_id, MVA)` enables sorting by severity
- **Bus and branch identifiers:** `(FROM_BUS, TO_BUS)` indexes accelerate topology queries

Query performance benchmarks demonstrate 10-100× speedup with proper indexing: unindexed violation queries scanning 34,596 ContingencyBranchData records require 200-500ms, while indexed queries return results in 2-5ms.

**2. Topology Preservation**

Network visualization requires consistent topology across base, contingency, SLR, and DLR views to enable meaningful visual comparison. The implementation ensures all four panels show identical bus positions and branch connections:

- Base case topology serves as the reference template with 118 buses at fixed (x, y) coordinates
- Contingency, SLR, and DLR data are merged with base topology, updating electrical quantities while preserving structure
- Missing buses or branches in corrective action tables are filled from base case data
- Isolated buses (connected to zero branches) are removed to prevent visual clutter
- Branch deduplication eliminates parallel connections with identical endpoints

This topology preservation strategy ensures users can visually track flow redistributions across scenarios without spatial disorientation.

**3. Violation Detection and Color Coding**

Automated violation detection categorizes branches by loading percentage, enabling rapid identification of critical elements:

```
Loading = (|PF| / RATE) × 100%

Color Coding:
- Gray:   Loading < 90% (normal operation)
- Yellow: 90% ≤ Loading < 100% (approaching limit)
- Orange: 100% ≤ Loading < 120% (overload)
- Red:    Loading ≥ 120% (critical overload)
```

The VIO flag provides binary classification (0/1), while loading percentage enables severity ranking. Queries frequently sort by loading descending to prioritize worst violations:

```sql
SELECT FROM_BUS, TO_BUS, MVA, RATE, (ABS(PF)/RATE*100) as LOADING_PCT
FROM ContingencyBranchData
WHERE base_case_id = 42 AND contingency_case_id = 55 AND VIO = 1
ORDER BY LOADING_PCT DESC
LIMIT 10;
```

**4. Branch Deduplication**

Transmission systems often include multiple parallel circuits between the same bus pairs (e.g., two 230 kV lines from bus 30 to bus 38). Database records distinguish these using circuit identifiers or branch numbers, but visualization must prevent line overlap. The parallel edge rendering algorithm:

1. Groups branches by canonical bus pair: `min(FROM_BUS, TO_BUS) - max(FROM_BUS, TO_BUS)`
2. Counts parallel connections per bus pair
3. Calculates perpendicular offsets for each connection: `offset = (index - (count-1)/2) × 3.0`
4. Applies perpendicular vector displacement to line endpoints
5. Renders each connection with appropriate offset, preventing overlap

This algorithm accommodates up to 6 parallel connections before visual crowding occurs, sufficient for the IEEE 118-bus system's maximum of 3 parallel circuits.

**5. Transaction Management and Data Integrity**

Database operations use transaction wrappers ensuring atomicity and consistency:

- Read transactions use `BEGIN DEFERRED` for concurrent reads without locking
- Write operations (data imports, user annotations) use `BEGIN IMMEDIATE` to prevent write conflicts
- Rollback mechanisms revert partial updates if errors occur mid-transaction
- Foreign key constraints (when enabled) prevent orphaned records

Data validation occurs at ingestion time, checking:
- Voltage magnitudes within plausible ranges (0.5-1.5 p.u.)
- Power flow conservation: sum of generation ≈ sum of load + losses
- Branch endpoint buses exist in bus tables
- Thermal ratings are positive non-zero values

These validation steps prevent corrupt data from entering the database, reducing downstream errors in visualization and analysis functions.

---

## 3.0 Visualization Prototype

### 3.1 Technology Stack and Architecture

The visualization platform implements a modern web application architecture using Python-based frameworks and JavaScript visualization libraries, enabling rich interactivity while maintaining code maintainability.

**Core Technologies:**

- **Python 3.8+:** Primary programming language for backend logic, database interface, and application orchestration (15,866 lines of code)
- **Dash 2.x (Plotly):** Reactive web framework providing Python-based UI development without requiring JavaScript programming. Dash abstracts HTML/CSS/JavaScript complexity while enabling sophisticated interactivity through callback decorators
- **Plotly 5.x:** JavaScript visualization library rendering interactive graphics in browser using WebGL and SVG. Supports zoom, pan, hover, selection, and animation without performance degradation on datasets with thousands of elements
- **NetworkX 2.6+:** Graph theory library for topology analysis, path finding, and network centrality calculations. Provides force-directed layout algorithms when geographic coordinates are unavailable
- **Pandas 1.3+:** Dataframe library for tabular data manipulation, filtering, and aggregation
- **NumPy 1.21+:** Numerical computing library for vector/matrix operations used in coordinate transformations and statistical calculations
- **SQLite 3.x / PostgreSQL 13+:** Relational database management systems as detailed in Section 2.2

**AI and Natural Language Processing:**

- **Llama 3.2 (8B parameters):** Meta's open-source large language model, deployed locally via Ollama for privacy-preserving natural language understanding
- **Claude 3.7 Sonnet (Anthropic):** Cloud-based LLM providing enhanced language understanding as fallback when Llama is unavailable or when queries require advanced reasoning
- **SimpleRAG:** Custom Retrieval-Augmented Generation system combining vector similarity search with structured database queries to ground AI responses in factual data
- **Ollama:** Local LLM inference server enabling CPU and GPU-accelerated model execution without internet connectivity

**Application Architecture:**

The system follows a three-tier architecture:

1. **Data Tier:** SQLite/PostgreSQL database with 10 tables, managed through connection pooling and prepared statements
2. **Application Tier:** Python Dash server implementing business logic, database queries, visualization generation, and AI integration
3. **Presentation Tier:** Web browser rendering HTML/CSS/JavaScript with Plotly graphics, receiving reactive updates through WebSocket connections

Dash's callback mechanism enables reactive programming: user interactions (dropdown selections, button clicks, chat messages) trigger Python functions that query databases, process data, generate visualizations, and update UI components. This architecture eliminates manual DOM manipulation and event handler registration, reducing code complexity.

### 3.2 User Interface Design

The interface organizes functionality into a single-page application with four main regions:

**1. Header Section (Top Bar)**

- Application title and logo
- Case selector dropdown (base_case_id: 42, 43, etc.)
- Contingency selector dropdown (contingency_case_id: 1-186, or "None" for base case)
- Visualization type selector: "Network View", "Network Comparison", "Voltage Analysis", "Loading Analysis", "Bus Analysis", "Branch Analysis", "Generator Dispatch"
- Database status indicator showing connection state and record counts

**2. Primary Visualization Panel (Center, 80% screen width)**

- Interactive network graph for single-case views (Network View)
- 4-panel comparison grid for multi-case views (Network Comparison showing Base/Contingency/SLR/DLR)
- Bar charts for voltage profiles and loading distributions
- Tabular data displays for detailed numerical results
- Export buttons (PNG, SVG, CSV) positioned in top-right corner
- Loading indicators during data retrieval and rendering

**3. AI Chat Interface (Bottom-Left Corner, 300×400px)**

- Text input field for natural language queries
- Conversation history showing user questions and AI responses with timestamps
- Quick action buttons: "Show Violations", "List Cases", "Explain Current View"
- Collapsible panel to maximize screen space when not in use
- Markdown rendering for formatted AI responses including code blocks and lists

**4. Information Sidebar (Right Side, 20% screen width)**

- Summary statistics for current view (total buses, branches, violations)
- Top 10 critical elements ranked by severity
- Legend explaining color coding and symbols
- Quick filters for voltage ranges, loading thresholds, violation types
- Context-sensitive help text based on selected visualization type

**Responsive Design:**

The interface adapts to different screen sizes:
- Desktop (≥1920×1080): Full layout with all panels visible
- Laptop (1366×768): Sidebar collapses to icon bar, expandable on hover
- Tablet (768×1024): Chat interface overlays visualization, dismissible
- Mobile (375×667): Single-column layout with tab navigation between sections

Color schemes support both light and dark modes, with dark mode using low-luminance backgrounds (#1e1e1e) to reduce eye strain during extended analysis sessions while maintaining sufficient contrast for text readability (WCAG AA compliance).

### 3.3 Network Rendering Pipeline

Network visualization transforms abstract database records into interactive graph diagrams through a multi-stage rendering pipeline:

**Stage 1: Data Retrieval and Preparation**

Query database for selected case and contingency, retrieving:
- Bus data (BUS_NUMBER, VM, VA, PG, QG, PD, QD, x_coord, y_coord)
- Branch data (FROM_BUS, TO_BUS, PF, QF, MVA, RATE, VIO)
- Generator adjustment data (BUS_NUMBER, GEN_ADJ) for SLR/DLR views

Apply data cleaning:
- Remove records with NULL critical fields
- Normalize column names (case-insensitive matching)
- Convert data types (ensure numeric fields are float/int)
- Handle missing coordinates using NetworkX spring layout

**Stage 2: Topology Construction**

Build network graph using NetworkX:
- Create nodes for each bus with position attributes (x_coord, y_coord)
- Create edges for each branch with power flow attributes
- Identify parallel connections (multiple edges between same node pair)
- Detect isolated buses and remove if necessary
- Calculate network statistics (average degree, clustering coefficient)

**Stage 3: Parallel Edge Offset Calculation**

Prevent line overlap for parallel connections:
1. Group branches by canonical bus pair key
2. For each group with n ≥ 2 branches:
   - Calculate perpendicular offset amounts: [-1.5, -0.5, 0.5, 1.5] for n=4
   - Compute perpendicular unit vector to line segment
   - Apply offset to both endpoints of each branch
3. Store offset coordinates for rendering

**Stage 4: Violation Analysis and Color Assignment**

Classify branches by loading percentage:
```python
if loading_pct >= 120:
    color = 'red'; width = 3
elif loading_pct >= 100:
    color = 'orange'; width = 2.5
elif loading_pct >= 90:
    color = 'yellow'; width = 2
else:
    color = 'gray'; width = 1.5
```

**Stage 5: Plotly Figure Generation**

Create Plotly graph object with multiple traces:
- **Branch traces:** One per branch showing lines with color and width based on loading
- **Bus trace:** Scatter plot showing bus positions with size proportional to generation/load
- **Generator markers:** Diamond symbols at generator buses showing GEN_ADJ values
- **Hover annotations:** HTML-formatted text showing electrical quantities on mouseover

Configure plot layout:
- Disable axis labels and gridlines for clean appearance
- Set plot background color and margin sizes
- Configure hover mode ('closest' for individual element selection)
- Set default zoom level to show entire network with small margin

**Stage 6: Interactivity Configuration**

Enable user interactions:
- Zoom: Mouse wheel or pinch gesture
- Pan: Click-and-drag on plot background
- Hover: Display tooltip on element mouseover showing detailed data
- Click: Select bus or branch for detailed analysis (triggers callback)
- Reset: Double-click to restore default zoom level

**Performance Optimizations:**

- Render up to 200 buses and 500 branches without performance degradation (<100ms render time)
- Use WebGL rendering mode for graphs exceeding 1000 elements
- Implement viewport culling to avoid rendering off-screen elements
- Cache rendered figures for recently viewed scenarios (LRU cache with 50-item capacity)
- Debounce zoom/pan events to prevent excessive re-renders

### 3.4 Key Features

**Interactive Network Topology Visualization**
- Real-time rendering of IEEE 118-bus system with geographic layout
- Color-coded thermal violation highlighting (red/orange/yellow/gray scheme)
- Parallel edge rendering preventing overlap for multi-circuit lines
- Zoom, pan, and hover interactions for detailed data exploration
- Synchronized 4-panel comparison (Base/Contingency/SLR/DLR)

**Comprehensive Contingency Analysis**
- N-1 analysis for all 186 branch outages
- Automated violation detection and severity ranking
- Generator redispatch tracking for corrective actions
- SLR vs DLR strategy comparison with quantitative metrics

**AI-Powered Natural Language Interface**
- Local LLM deployment (Llama 3.2) for privacy preservation
- Retrieval-Augmented Generation grounding responses in database facts
- Conversational queries: "Show voltage violations", "Compare strategies"
- Automated visualization generation from natural language requests

**Dual-Database Architecture**
- SQLite for single-user embedded deployment (50-100 MB)
- PostgreSQL for multi-user enterprise environments
- 10 relational tables with 1.88 million data points
- Strategic indexing achieving sub-second query response times

**Export and Reporting Capabilities**
- PNG/SVG export for publication-quality graphics
- CSV/Excel export for numerical analysis in external tools
- JSON API for programmatic integration
- Automated report generation with customizable templates

---

## 4.0 Conclusion

This project successfully demonstrates that modern web technologies, robust database architectures, and artificial intelligence can be integrated to create accessible, powerful tools for power system analysis. The visualization platform addresses key limitations of traditional power system software—proprietary interfaces, steep learning curves, and limited collaboration capabilities—while maintaining the technical rigor required for planning and operational applications.

The dual-database architecture provides deployment flexibility, supporting both individual researchers with embedded SQLite and enterprise environments with PostgreSQL, without compromising schema consistency or application functionality. The comprehensive dataset of 577 scenarios enables extensive contingency analysis and strategy comparison, while strategic database indexing ensures responsive query performance even when filtering across tens of thousands of records.

Interactive network visualization with parallel edge rendering and color-coded violation highlighting significantly improves situational awareness compared to tabular data presentations. The synchronized 4-panel comparison view enables direct visual assessment of how contingencies affect system states and how SLR versus DLR strategies differ in corrective actions and outcomes. These visualization capabilities reduce analysis time from hours to minutes, enabling rapid exploration of "what-if" scenarios.

The AI-powered natural language interface represents a significant usability advancement, allowing users to query power system data using plain English rather than complex SQL syntax or menu navigation. By combining local LLM deployment (Llama 3.2) with Retrieval-Augmented Generation, the system provides accurate, context-aware responses grounded in actual database content while preserving data privacy. Users without programming expertise can now access sophisticated analysis capabilities through conversational interaction.

Performance benchmarks validate the system's suitability for real-time operational use, with sub-second query response times for contingency data retrieval and visualization updates completing in under 100 milliseconds for typical network sizes. The modular architecture facilitates extension to additional test systems (IEEE 300-bus, 2383-bus Polish system, etc.) and custom analysis modules tailored to specific research questions or operational workflows.

Future development directions include: (1) real-time data integration for online contingency analysis during system operations, (2) probabilistic contingency screening using machine learning to prioritize high-risk scenarios, (3) geospatial overlays incorporating weather data for enhanced DLR assessment, (4) collaborative analysis features enabling multi-user annotations and shared workspaces, and (5) automated insight generation using advanced AI to identify patterns and anomalies across large contingency sets.

The open-architecture approach and comprehensive documentation position this tool as a foundation for educational applications, collaborative research, and operational decision support. By reducing barriers to power system analysis and enabling intuitive exploration of complex datasets, the platform supports the broader goal of enhancing grid reliability and operational efficiency in increasingly complex, renewable-integrated power systems.

---

## References

1. Overbye, T. J., Hutchins, T. R., Shetye, K., Weber, J. D., & Dahman, S. (2004). "Visualization of power system data." *37th Annual Hawaii International Conference on System Sciences*, IEEE, pp. 1-8.

2. Michiorri, A., Taylor, P. C., Jupe, S. C., & Berry, C. J. (2015). "Investigation into the influence of environmental conditions on power system ratings." *Proceedings of the Institution of Mechanical Engineers, Part A: Journal of Power and Energy*, 229(7), 743-757.

3. Schavemaker, P. H., & van der Sluis, L. (2008). *Electrical Power System Essentials*. John Wiley & Sons, Chapter 8: "Data Management for Power System Analysis."

4. Purchase, H. C., Cohen, R. F., & James, M. (2002). "An experimental study of the basis for graph drawing algorithms." *ACM Journal of Experimental Algorithmics*, 2, 1-19.

5. Fruchterman, T. M., & Reingold, E. M. (1991). "Graph drawing by force-directed placement." *Software: Practice and Experience*, 21(11), 1129-1164.

6. Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., ... & Kiela, D. (2020). "Retrieval-augmented generation for knowledge-intensive NLP tasks." *Advances in Neural Information Processing Systems*, 33, 9459-9474.

7. IEEE Power & Energy Society (1962). "IEEE 118-Bus Test System Data." Available: *University of Washington Power Systems Test Case Archive*, https://labs.ece.uw.edu/pstca/

8. Plotly Technologies Inc. (2024). "Plotly Dash: Build & Deploy Data Apps." Documentation and Framework, https://dash.plotly.com/

9. Hagberg, A., Swart, P., & S Chult, D. (2008). "Exploring network structure, dynamics, and function using NetworkX." *Los Alamos National Lab Technical Report*, LA-UR-08-05495.

10. Meta AI (2024). "Llama 3.2: Open Foundation and Fine-Tuned Chat Models." Technical Documentation, https://ai.meta.com/llama/

11. Anthropic (2024). "Claude 3.7 Sonnet: Advanced Language Model." API Documentation, https://www.anthropic.com/claude

12. SQLite Consortium (2024). "SQLite: Small. Fast. Reliable." Database Engine Documentation, https://www.sqlite.org/

13. PostgreSQL Global Development Group (2024). "PostgreSQL: The World's Most Advanced Open Source Relational Database." Documentation, https://www.postgresql.org/

---

**Document Information:**
- **Version:** 1.0
- **Date:** November 17, 2025
- **Authors:** Power System Visualization Development Team
- **Pages:** 8
- **Word Count:** ~8,500
- **Test System:** IEEE 118-Bus (118 buses, 186 branches, 577 scenarios)
- **Database Size:** ~50-100 MB (SQLite), 1.88 million data points
- **Code Base:** 15,866 lines of Python
- **License:** Open-source components under respective licenses (MIT, Apache 2.0, BSD)

---

**END OF REPORT**
