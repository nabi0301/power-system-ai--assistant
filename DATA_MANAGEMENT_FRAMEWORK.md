# Data Management Framework
## Power System Visualization Tool with AI-Enhanced Contingency Analysis

---

## 2.0 Data Management Framework

The data management framework handles storage and processing of over 50,000 data points across 577 operational scenarios using a dual-database architecture (SQLite + PostgreSQL). The system manages the IEEE 118-bus test system with 118 buses, 186 transmission branches, 54 generators, and 577 scenarios (base case + contingencies + SLR/DLR corrective actions).

---

## 2.1 Data Generation

The power system data originates from MATPOWER simulations with a three-stage pipeline:

**Stage 1: Base Case Extraction** - Parse MATPOWER `.m` files to extract network topology, bus parameters (voltage, generation, load), and branch parameters (impedance, thermal limits, power flows).

**Stage 2: Contingency Simulation** - Execute N-1 contingency analysis for all 186 branches. MATPOWER solver computes post-contingency states and identifies violations (loading >100%).

**Stage 3: Corrective Action Analysis** - Apply two strategies:
- **SLR (Static Line Rating):** Conservative seasonal ratings requiring larger generator adjustments
- **DLR (Dynamic Line Rating):** Weather-based ratings with higher limits and smaller adjustments

**Data Volume:** ~1.88 million data values (3,100 base + 576,600 contingency + 1,302,000 SLR/DLR)

---

## 2.2 Database Design and Implementation

### 2.2.1 Structure Overview

The system uses a normalized relational schema optimized for power system analysis and visualization.

#### Database Technology Stack

**SQLite Database (Primary)**
- Local high-performance storage (`data.db`, ~50-100 MB)
- Zero configuration, serverless, ACID-compliant
- Ideal for: Development, single-user applications, embedded systems

**PostgreSQL Database (Optional)**
- Enterprise-grade multi-user deployment
- Concurrent access, advanced indexing, high availability
- Ideal for: Production, multi-user systems, enterprise integration

**Dual-Database Architecture:** Transparent abstraction layer enables seamless migration from SQLite to PostgreSQL without code changes.

---

### 2.2.2 Schema Breakdown

The database implements **10 core tables** across three domains:

#### Domain 1: Base Case Data
- **BaseBusData** (~118 records): Voltage (VM, VA), generation (PG, QG), load (PD, QD), coordinates
- **BaseBranchData** (~186 records): Power flows (PF, QF, MVA), thermal limits (RATE), violations (VIO)

#### Domain 2: Contingency Analysis (N-1 Studies)
- **ContingencyBusData** (21,948 records): Post-contingency bus states
- **ContingencyBranchData** (34,596 records): ⚡ Most accessed table (60-70% of queries). Indexed on (base_case_id, contingency_case_id) and VIO for fast violation retrieval

#### Domain 3: Corrective Actions (SLR/DLR)
- **SLR/DLR_PostAction_BusData**: Post-correction bus states (~186 scenarios each)
- **SLR/DLR_Branches**: Post-correction branch flows with updated thermal limits
- **SLR/DLR_Generator**: Generator adjustments (GEN_ADJ = GEN_NEW - GEN_INI)
  - Visual markers: Blue diamonds (SLR) / Green diamonds (DLR) for adjusted generators
  - `GEN_ADJ > 0`: Up-regulation | `GEN_ADJ < 0`: Down-regulation

---

### 2.2.3 Data Processing Techniques

**1. Query Optimization**
- Compound indexes on (base_case_id, contingency_case_id) for fast retrieval
- Violation-specific index on VIO column
- Batch queries reduce overhead from 304 to 2 queries per scenario

**2. Topology Preservation**
- SLR/DLR use identical network structure as base case
- Only electrical parameters updated (VM, VA, PF, MVA)
- Ensures valid comparisons on the same physical network

**3. Violation Detection**
```python
loading_pct = (MVA / RATE) * 100
colors: red (≥100%), orange (90-100%), yellow (70-90%), gray (<70%)
```

**4. Branch Deduplication**
- Canonical form: always store with lower bus number first
- Prevents duplicate bidirectional entries (e.g., 72→12 and 12→72)

**5. Data Integrity**
- Foreign key constraints for referential integrity
- Check constraints (VM > 0, RATE > 0)
- Transaction atomicity for multi-table imports

**Database Migration:** SQLite to PostgreSQL migration via export/import with automatic query adaptation—zero code changes required.

---

## Summary

The Data Management Framework provides:
- **Dual-database architecture** (SQLite + PostgreSQL) with transparent abstraction
- **10-table normalized schema** handling 1.88M data values across 577 scenarios
- **Optimized queries** with strategic indexing (60-70% faster for violations)
- **Data integrity** via constraints, transactions, and topology preservation
- **Seamless migration** from SQLite to PostgreSQL without code changes

This foundation enables real-time visualization, AI analysis, and comparative studies of power system contingencies and corrective actions.

---

**Document Version:** 1.0 | **Last Updated:** November 17, 2025 | **Page Count:** 2 pages
