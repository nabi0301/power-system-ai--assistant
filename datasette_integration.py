#!/usr/bin/env python3
"""
Datasette Integration for Power System Analysis
Provides enhanced data exploration capabilities for the IEEE 118-bus system
"""

import subprocess
import sys
import sqlite3
import pandas as pd
import webbrowser
import time
from pathlib import Path

def check_datasette_installation():
    """Check if Datasette is installed"""
    try:
        import datasette
        print("✅ Datasette is installed")
        return True
    except ImportError:
        print("❌ Datasette not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "datasette", "datasette-vega", "datasette-cluster-map"])
        return True

def create_enhanced_views():
    """Create additional views optimized for power system analysis"""
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    
    # Advanced Power Flow Analysis View
    advanced_view = """
    CREATE VIEW IF NOT EXISTS power_flow_analysis AS
    SELECT 
        b.base_case_id,
        b.From_Bus,
        b.To_Bus,
        b.MVA as apparent_power,
        b.PF as active_power,
        b.QF as reactive_power,
        b.RATE as thermal_rating,
        bus_from.VM as from_bus_voltage,
        bus_to.VM as to_bus_voltage,
        ABS(bus_from.VA - bus_to.VA) as voltage_angle_diff,
        CASE 
            WHEN b.RATE > 0 THEN (b.MVA / b.RATE * 100)
            ELSE 0 
        END as loading_percentage,
        CASE
            WHEN ABS(bus_from.VA - bus_to.VA) > 30 THEN 'High Angle Difference'
            WHEN ABS(bus_from.VA - bus_to.VA) > 15 THEN 'Medium Angle Difference'
            ELSE 'Normal Angle Difference'
        END as stability_indicator
    FROM BaseBranchData b
    LEFT JOIN BaseBusData bus_from ON b.From_Bus = bus_from.BUS_NUMBER AND b.base_case_id = bus_from.base_case_id
    LEFT JOIN BaseBusData bus_to ON b.To_Bus = bus_to.BUS_NUMBER AND b.base_case_id = bus_to.base_case_id
    WHERE b.base_case_id = 0;
    """
    
    # Contingency Impact Analysis
    contingency_view = """
    CREATE VIEW IF NOT EXISTS contingency_impact AS
    SELECT 
        s.base_case_id,
        s.contingency_case_id,
        COUNT(*) as total_lines_analyzed,
        AVG(s.VIO) as avg_slr_violation,
        AVG(d.VIO) as avg_dlr_violation,
        SUM(CASE WHEN s.VIO > 100 THEN 1 ELSE 0 END) as slr_violations_count,
        SUM(CASE WHEN d.VIO > 100 THEN 1 ELSE 0 END) as dlr_violations_count,
        AVG(d.RATE - s.RATE) as avg_rating_improvement,
        MAX(d.RATE - s.RATE) as max_rating_improvement
    FROM SLR_Branches s
    JOIN DLR_Branches d ON s.From_Bus = d.From_Bus 
        AND s.To_Bus = d.To_Bus 
        AND s.base_case_id = d.base_case_id
        AND s.contingency_case_id = d.contingency_case_id
    GROUP BY s.base_case_id, s.contingency_case_id;
    """
    
    try:
        cursor.execute(advanced_view)
        cursor.execute(contingency_view)
        conn.commit()
        print("✅ Enhanced views created successfully")
    except Exception as e:
        print(f"⚠️ Error creating views: {e}")
    finally:
        conn.close()

def generate_sample_queries():
    """Generate useful SQL queries for power system analysis"""
    queries = {
        "Top 10 Most Loaded Lines": """
            SELECT From_Bus, To_Bus, loading_percentage, loading_status
            FROM loading_analysis 
            ORDER BY loading_percentage DESC 
            LIMIT 10;
        """,
        
        "Voltage Violations by Severity": """
            SELECT voltage_status, COUNT(*) as violation_count, 
                   AVG(deviation_from_nominal) as avg_deviation
            FROM voltage_violations 
            GROUP BY voltage_status
            ORDER BY avg_deviation DESC;
        """,
        
        "DLR vs SLR Benefits": """
            SELECT advantage_type, COUNT(*) as line_count,
                   AVG(Rating_Improvement) as avg_improvement
            FROM slr_dlr_comparison 
            GROUP BY advantage_type;
        """,
        
        "Critical Equipment Summary": """
            SELECT equipment_type, COUNT(*) as equipment_count,
                   AVG(current_value - limit_value) as avg_severity
            FROM critical_equipment 
            GROUP BY equipment_type;
        """,
        
        "High Load Buses": """
            SELECT BUS_NUMBER, VM as voltage, PD as load_mw, BASE_KV
            FROM BaseBusData 
            WHERE PD > 50 
            ORDER BY PD DESC;
        """,
        
        "Power Flow Stability Analysis": """
            SELECT stability_indicator, COUNT(*) as line_count,
                   AVG(voltage_angle_diff) as avg_angle_diff,
                   AVG(loading_percentage) as avg_loading
            FROM power_flow_analysis 
            GROUP BY stability_indicator;
        """
    }
    
    # Save queries to file for easy access
    with open('datasette_sample_queries.sql', 'w') as f:
        f.write("-- Sample SQL Queries for Power System Analysis in Datasette\n")
        f.write("-- Copy and paste these into the Datasette SQL interface\n\n")
        
        for title, query in queries.items():
            f.write(f"-- {title}\n")
            f.write(query.strip())
            f.write("\n\n")
    
    print("✅ Sample queries saved to 'datasette_sample_queries.sql'")
    return queries

def start_datasette_server(port=8001, auto_open=True):
    """Start Datasette server with power system database"""
    try:
        print(f"🚀 Starting Datasette server on port {port}...")
        print(f"📊 Database: data.db")
        print(f"⚙️ Configuration: datasette_config.json")
        print(f"🌐 URL: http://localhost:{port}")
        
        # Prepare command
        cmd = [
            "datasette", 
            "data.db",
            "--config", "datasette_config.json",
            "--port", str(port),
            "--host", "0.0.0.0"
        ]
        
        if auto_open:
            cmd.append("--open")
        
        # Start server
        process = subprocess.Popen(cmd)
        
        if not auto_open:
            time.sleep(2)  # Give server time to start
            webbrowser.open(f"http://localhost:{port}")
        
        print("\n📋 Available Features:")
        print("• Browse all tables and views")
        print("• Execute custom SQL queries")
        print("• Export data as JSON/CSV")
        print("• Create visualizations")
        print("• Filter and facet data")
        
        print("\n🔍 Useful Starting Points:")
        print(f"• System Overview: http://localhost:{port}/data/system_summary")
        print(f"• Voltage Violations: http://localhost:{port}/data/voltage_violations")
        print(f"• Loading Analysis: http://localhost:{port}/data/loading_analysis")
        print(f"• SLR vs DLR: http://localhost:{port}/data/slr_dlr_comparison")
        print(f"• Critical Equipment: http://localhost:{port}/data/critical_equipment")
        
        print("\n⏹️ Press Ctrl+C to stop the server")
        
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping Datasette server...")
            process.terminate()
            
    except Exception as e:
        print(f"❌ Error starting Datasette: {e}")

def main():
    """Main function to set up and start Datasette for power system analysis"""
    print("🏭 IEEE 118-Bus Power System - Datasette Integration")
    print("=" * 55)
    
    # Check installation
    if not check_datasette_installation():
        return
    
    # Create enhanced views
    create_enhanced_views()
    
    # Generate sample queries
    sample_queries = generate_sample_queries()
    
    print("\n📊 Ready to explore your power system data!")
    print("\n🎯 Quick Start Guide:")
    print("1. Browse tables: BaseBusData, BaseBranchData, SLR_Branches, DLR_Branches")
    print("2. Use custom views: voltage_violations, loading_analysis, slr_dlr_comparison")
    print("3. Try sample queries from 'datasette_sample_queries.sql'")
    print("4. Export data using the built-in export features")
    
    # Start server
    start_datasette_server(port=8001, auto_open=True)

if __name__ == "__main__":
    main()