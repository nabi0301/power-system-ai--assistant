-- Sample SQL Queries for Power System Analysis in Datasette
-- Copy and paste these into the Datasette SQL interface

-- Top 10 Most Loaded Lines
SELECT From_Bus, To_Bus, loading_percentage, loading_status
            FROM loading_analysis 
            ORDER BY loading_percentage DESC 
            LIMIT 10;

-- Voltage Violations by Severity
SELECT voltage_status, COUNT(*) as violation_count, 
                   AVG(deviation_from_nominal) as avg_deviation
            FROM voltage_violations 
            GROUP BY voltage_status
            ORDER BY avg_deviation DESC;

-- DLR vs SLR Benefits
SELECT advantage_type, COUNT(*) as line_count,
                   AVG(Rating_Improvement) as avg_improvement
            FROM slr_dlr_comparison 
            GROUP BY advantage_type;

-- Critical Equipment Summary
SELECT equipment_type, COUNT(*) as equipment_count,
                   AVG(current_value - limit_value) as avg_severity
            FROM critical_equipment 
            GROUP BY equipment_type;

-- High Load Buses
SELECT BUS_NUMBER, VM as voltage, PD as load_mw, BASE_KV
            FROM BaseBusData 
            WHERE PD > 50 
            ORDER BY PD DESC;

-- Power Flow Stability Analysis
SELECT stability_indicator, COUNT(*) as line_count,
                   AVG(voltage_angle_diff) as avg_angle_diff,
                   AVG(loading_percentage) as avg_loading
            FROM power_flow_analysis 
            GROUP BY stability_indicator;

