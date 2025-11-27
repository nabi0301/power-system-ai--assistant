-- Power System Analysis Views for Datasette
-- These views provide useful insights into the IEEE 118-bus system

-- View 1: Voltage Violations Summary
CREATE VIEW IF NOT EXISTS voltage_violations AS
SELECT 
    base_case_id,
    BUS_NUMBER,
    VM as voltage_pu,
    BASE_KV,
    CASE 
        WHEN VM < 0.95 THEN 'Low Voltage'
        WHEN VM > 1.05 THEN 'High Voltage' 
        ELSE 'Normal'
    END as voltage_status,
    ABS(VM - 1.0) as deviation_from_nominal
FROM BaseBusData
WHERE VM < 0.95 OR VM > 1.05
ORDER BY ABS(VM - 1.0) DESC;

-- View 2: Loading Analysis Summary  
CREATE VIEW IF NOT EXISTS loading_analysis AS
SELECT 
    b.base_case_id,
    b.From_Bus,
    b.To_Bus,
    b.MVA,
    b.RATE,
    CASE 
        WHEN b.RATE > 0 THEN (b.MVA / b.RATE * 100)
        ELSE 0 
    END as loading_percentage,
    CASE
        WHEN b.RATE > 0 AND (b.MVA / b.RATE * 100) > 100 THEN 'Overloaded'
        WHEN b.RATE > 0 AND (b.MVA / b.RATE * 100) > 90 THEN 'High Loading'
        WHEN b.RATE > 0 AND (b.MVA / b.RATE * 100) > 75 THEN 'Medium Loading'
        ELSE 'Normal Loading'
    END as loading_status
FROM BaseBranchData b
WHERE b.RATE > 0
ORDER BY loading_percentage DESC;

-- View 3: SLR vs DLR Comparison
CREATE VIEW IF NOT EXISTS slr_dlr_comparison AS
SELECT 
    s.base_case_id,
    s.contingency_case_id,
    s.From_Bus,
    s.To_Bus,
    s.MVA as SLR_MVA,
    d.MVA as DLR_MVA,
    s.RATE as SLR_Rating,
    d.RATE as DLR_Rating,
    s.VIO as SLR_Violation,
    d.VIO as DLR_Violation,
    (d.RATE - s.RATE) as Rating_Improvement,
    CASE 
        WHEN d.RATE > s.RATE THEN 'DLR Advantage'
        WHEN d.RATE = s.RATE THEN 'No Difference'
        ELSE 'SLR Advantage'
    END as advantage_type
FROM SLR_Branches s
JOIN DLR_Branches d ON s.From_Bus = d.From_Bus 
    AND s.To_Bus = d.To_Bus 
    AND s.base_case_id = d.base_case_id
    AND s.contingency_case_id = d.contingency_case_id;

-- View 4: System Summary Statistics
CREATE VIEW IF NOT EXISTS system_summary AS
SELECT 
    'Base Case Analysis' as analysis_type,
    COUNT(*) as total_buses,
    AVG(VM) as avg_voltage,
    MIN(VM) as min_voltage,
    MAX(VM) as max_voltage,
    SUM(PD) as total_load_mw,
    SUM(PG) as total_generation_mw
FROM BaseBusData
WHERE base_case_id = 0

UNION ALL

SELECT 
    'Branch Analysis' as analysis_type,
    COUNT(*) as total_branches,
    AVG(CASE WHEN RATE > 0 THEN MVA/RATE*100 ELSE 0 END) as avg_loading_pct,
    MIN(MVA) as min_flow_mva,
    MAX(MVA) as max_flow_mva,
    SUM(CASE WHEN RATE > 0 AND MVA/RATE > 1.0 THEN 1 ELSE 0 END) as overloaded_lines,
    NULL as total_generation_mw
FROM BaseBranchData
WHERE base_case_id = 0;

-- View 5: Critical Equipment Monitoring
CREATE VIEW IF NOT EXISTS critical_equipment AS
SELECT 
    'High Voltage Bus' as equipment_type,
    BUS_NUMBER as equipment_id,
    VM as current_value,
    1.05 as limit_value,
    'Voltage p.u.' as unit,
    'Voltage exceeds upper limit' as issue
FROM BaseBusData 
WHERE VM > 1.05

UNION ALL

SELECT 
    'Low Voltage Bus' as equipment_type,
    BUS_NUMBER as equipment_id, 
    VM as current_value,
    0.95 as limit_value,
    'Voltage p.u.' as unit,
    'Voltage below lower limit' as issue
FROM BaseBusData
WHERE VM < 0.95

UNION ALL

SELECT 
    'Overloaded Line' as equipment_type,
    (From_Bus || '-' || To_Bus) as equipment_id,
    CASE WHEN RATE > 0 THEN MVA/RATE*100 ELSE 0 END as current_value,
    100.0 as limit_value,
    'Loading %' as unit,
    'Line loading exceeds thermal limit' as issue  
FROM BaseBranchData
WHERE RATE > 0 AND MVA/RATE > 1.0;