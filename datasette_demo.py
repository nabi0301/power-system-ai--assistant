#!/usr/bin/env python3
"""
Power System Data Insights with Datasette
Demonstrates advanced queries and analysis capabilities
"""

import sqlite3
import pandas as pd
import json

def demonstrate_datasette_capabilities():
    """Show examples of insights you can extract using Datasette"""
    
    print("🔍 **DATASETTE POWER SYSTEM ANALYSIS CAPABILITIES**")
    print("=" * 60)
    
    # Connect to database
    conn = sqlite3.connect('data.db')
    
    print("\n📊 **1. VOLTAGE ANALYSIS INSIGHTS**")
    print("-" * 40)
    
    # Voltage distribution analysis
    voltage_query = """
    SELECT 
        CASE 
            WHEN VM < 0.95 THEN 'Low (< 0.95 p.u.)'
            WHEN VM > 1.05 THEN 'High (> 1.05 p.u.)'
            ELSE 'Normal (0.95-1.05 p.u.)'
        END as voltage_category,
        COUNT(*) as bus_count,
        ROUND(AVG(VM), 4) as avg_voltage,
        ROUND(MIN(VM), 4) as min_voltage,
        ROUND(MAX(VM), 4) as max_voltage
    FROM BaseBusData 
    WHERE base_case_id = 0
    GROUP BY voltage_category
    ORDER BY avg_voltage;
    """
    
    voltage_df = pd.read_sql_query(voltage_query, conn)
    print(voltage_df.to_string(index=False))
    
    print("\n📈 **2. LOADING ANALYSIS INSIGHTS**")
    print("-" * 40)
    
    # Loading distribution analysis
    loading_query = """
    SELECT 
        CASE 
            WHEN RATE = 0 THEN 'No Rating'
            WHEN (MVA/RATE*100) > 100 THEN 'Overloaded (>100%)'
            WHEN (MVA/RATE*100) > 90 THEN 'High Loading (90-100%)'
            WHEN (MVA/RATE*100) > 75 THEN 'Medium Loading (75-90%)'
            ELSE 'Normal Loading (<75%)'
        END as loading_category,
        COUNT(*) as line_count,
        ROUND(AVG(CASE WHEN RATE > 0 THEN MVA/RATE*100 ELSE 0 END), 2) as avg_loading_pct,
        ROUND(MAX(CASE WHEN RATE > 0 THEN MVA/RATE*100 ELSE 0 END), 2) as max_loading_pct
    FROM BaseBranchData 
    WHERE base_case_id = 0
    GROUP BY loading_category
    ORDER BY avg_loading_pct DESC;
    """
    
    loading_df = pd.read_sql_query(loading_query, conn)
    print(loading_df.to_string(index=False))
    
    print("\n⚡ **3. POWER FLOW INSIGHTS**")
    print("-" * 40)
    
    # Power flow analysis
    power_flow_query = """
    SELECT 
        ROUND(SUM(PD), 2) as total_load_mw,
        ROUND(SUM(PG), 2) as total_generation_mw,
        ROUND(SUM(PG) - SUM(PD), 2) as power_balance_mw,
        COUNT(CASE WHEN PD > 0 THEN 1 END) as load_buses,
        COUNT(CASE WHEN PG > 0 THEN 1 END) as generator_buses,
        ROUND(AVG(VM), 4) as avg_system_voltage
    FROM BaseBusData 
    WHERE base_case_id = 0;
    """
    
    power_flow_df = pd.read_sql_query(power_flow_query, conn)
    print(power_flow_df.to_string(index=False))
    
    print("\n🔄 **4. SLR vs DLR COMPARISON INSIGHTS**")
    print("-" * 40)
    
    # Check if comparison data exists
    comparison_check = """
    SELECT COUNT(*) as slr_records FROM SLR_Branches WHERE base_case_id = 42;
    """
    slr_count = pd.read_sql_query(comparison_check, conn).iloc[0]['slr_records']
    
    if slr_count > 0:
        comparison_query = """
        SELECT 
            COUNT(*) as total_comparisons,
            ROUND(AVG(d.RATE - s.RATE), 2) as avg_rating_improvement_mva,
            ROUND(MAX(d.RATE - s.RATE), 2) as max_rating_improvement_mva,
            COUNT(CASE WHEN d.RATE > s.RATE THEN 1 END) as dlr_advantage_lines,
            COUNT(CASE WHEN s.VIO > 100 THEN 1 END) as slr_violations,
            COUNT(CASE WHEN d.VIO > 100 THEN 1 END) as dlr_violations
        FROM SLR_Branches s
        JOIN DLR_Branches d ON s.From_Bus = d.From_Bus 
            AND s.To_Bus = d.To_Bus 
            AND s.base_case_id = d.base_case_id
            AND s.contingency_case_id = d.contingency_case_id
        WHERE s.base_case_id = 42;
        """
        comparison_df = pd.read_sql_query(comparison_query, conn)
        print(comparison_df.to_string(index=False))
    else:
        print("No SLR/DLR comparison data available for analysis")
    
    print("\n🎯 **5. CRITICAL EQUIPMENT IDENTIFICATION**")
    print("-" * 40)
    
    # Critical equipment
    critical_query = """
    SELECT 'Voltage Violations' as issue_type, 
           COUNT(*) as equipment_count,
           GROUP_CONCAT(BUS_NUMBER, ', ') as affected_equipment
    FROM BaseBusData 
    WHERE (VM < 0.95 OR VM > 1.05) AND base_case_id = 0
    
    UNION ALL
    
    SELECT 'Overloaded Lines' as issue_type,
           COUNT(*) as equipment_count,
           GROUP_CONCAT(From_Bus || '-' || To_Bus, ', ') as affected_equipment
    FROM BaseBranchData 
    WHERE RATE > 0 AND (MVA/RATE > 1.0) AND base_case_id = 0;
    """
    
    critical_df = pd.read_sql_query(critical_query, conn)
    print(critical_df.to_string(index=False))
    
    print("\n🌐 **DATASETTE WEB INTERFACE BENEFITS**")
    print("-" * 50)
    print("✅ Interactive SQL Query Editor with auto-complete")
    print("✅ Visual data browsing with filtering and sorting")
    print("✅ Export data as JSON, CSV for external analysis")
    print("✅ Custom views for power system specific analysis")
    print("✅ Real-time data exploration without coding")
    print("✅ Shareable URLs for specific queries and results")
    print("✅ Plugin ecosystem for advanced visualizations")
    
    print("\n🚀 **ACCESS YOUR DATA**")
    print("-" * 25)
    print("🌐 Open: http://localhost:8001")
    print("📊 Tables: BaseBusData, BaseBranchData, SLR_Branches, DLR_Branches")
    print("📈 Custom Views: voltage_violations, loading_analysis, slr_dlr_comparison")
    
    conn.close()

def create_sample_datasette_queries():
    """Create a file with useful Datasette queries"""
    
    queries = {
        "Find buses with highest power demand": """
SELECT BUS_NUMBER, VM as voltage_pu, PD as load_mw, BASE_KV
FROM BaseBusData 
WHERE base_case_id = 0 AND PD > 0
ORDER BY PD DESC 
LIMIT 10;
        """,
        
        "Identify transmission bottlenecks": """
SELECT From_Bus, To_Bus, 
       ROUND(MVA, 2) as current_flow_mva,
       ROUND(RATE, 2) as thermal_rating_mva,
       ROUND((MVA/RATE*100), 2) as loading_percentage
FROM BaseBranchData 
WHERE base_case_id = 0 AND RATE > 0
ORDER BY (MVA/RATE) DESC 
LIMIT 15;
        """,
        
        "Voltage profile by base voltage level": """
SELECT BASE_KV as voltage_level_kv,
       COUNT(*) as bus_count,
       ROUND(AVG(VM), 4) as avg_voltage_pu,
       ROUND(MIN(VM), 4) as min_voltage_pu,
       ROUND(MAX(VM), 4) as max_voltage_pu
FROM BaseBusData 
WHERE base_case_id = 0
GROUP BY BASE_KV
ORDER BY BASE_KV DESC;
        """,
        
        "Power balance analysis": """
SELECT 
    ROUND(SUM(CASE WHEN PG > 0 THEN PG ELSE 0 END), 2) as total_generation_mw,
    ROUND(SUM(CASE WHEN PD > 0 THEN PD ELSE 0 END), 2) as total_load_mw,
    ROUND(SUM(PG) - SUM(PD), 2) as net_injection_mw,
    COUNT(CASE WHEN PG > 0 THEN 1 END) as generator_count,
    COUNT(CASE WHEN PD > 0 THEN 1 END) as load_count
FROM BaseBusData 
WHERE base_case_id = 0;
        """,
        
        "Lines operating near thermal limits": """
SELECT From_Bus, To_Bus,
       ROUND(MVA, 2) as flow_mva,
       ROUND(RATE, 2) as rating_mva,
       ROUND((MVA/RATE*100), 2) as loading_pct,
       CASE 
           WHEN (MVA/RATE*100) > 95 THEN 'Critical'
           WHEN (MVA/RATE*100) > 85 THEN 'High'
           ELSE 'Normal'
       END as status
FROM BaseBranchData 
WHERE base_case_id = 0 AND RATE > 0 AND (MVA/RATE*100) > 80
ORDER BY (MVA/RATE) DESC;
        """
    }
    
    with open('datasette_power_system_queries.md', 'w') as f:
        f.write("# Power System Analysis Queries for Datasette\n\n")
        f.write("Copy and paste these queries into the Datasette SQL interface at http://localhost:8001\n\n")
        
        for title, query in queries.items():
            f.write(f"## {title}\n\n")
            f.write("```sql\n")
            f.write(query.strip())
            f.write("\n```\n\n")
    
    print("✅ Sample queries saved to 'datasette_power_system_queries.md'")

if __name__ == "__main__":
    demonstrate_datasette_capabilities()
    create_sample_datasette_queries()