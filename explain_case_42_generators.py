#!/usr/bin/env python3
"""
Detailed analysis of generator data for case 42 to explain what the user sees
"""

import sqlite3
import pandas as pd
import numpy as np

def analyze_case_42_generators():
    """Provide detailed analysis of what the generator analysis shows for case 42"""
    print("🔍 Analyzing Generator Data for Case 42...")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect('data.db')
        
        # Get SLR and DLR generator data for case 42
        slr_df = pd.read_sql_query("SELECT * FROM SLR_Generator WHERE base_case_id = 42", conn)
        dlr_df = pd.read_sql_query("SELECT * FROM DLR_Generator WHERE base_case_id = 42", conn)
        
        conn.close()
        
        print(f"📊 Data Overview:")
        print(f"   • SLR Generators: {len(slr_df)} units")
        print(f"   • DLR Generators: {len(dlr_df)} units")
        print()
        
        # Analyze SLR data
        print("🔵 SLR (Static Line Rating) Generator Analysis:")
        print("-" * 50)
        if not slr_df.empty:
            print(f"📋 Columns available: {', '.join(slr_df.columns)}")
            print()
            
            # Show generator adjustment statistics
            gen_adj_stats = slr_df['GEN_ADJ'].describe()
            print("📈 GEN_ADJ Statistics (Generator Adjustments):")
            print(f"   • Count: {gen_adj_stats['count']:.0f} generators")
            print(f"   • Mean adjustment: {gen_adj_stats['mean']:.2f} MW")
            print(f"   • Min adjustment: {gen_adj_stats['min']:.2f} MW")
            print(f"   • Max adjustment: {gen_adj_stats['max']:.2f} MW")
            print(f"   • Std deviation: {gen_adj_stats['std']:.2f} MW")
            print()
            
            # Show bus locations and adjustments
            print("🏭 SLR Generator Adjustments by Bus:")
            slr_summary = slr_df[['BUS_NUMBER', 'contingency_case_id', 'GEN_INI', 'GEN_NEW', 'GEN_ADJ']].copy()
            slr_summary['GEN_CHANGE'] = slr_summary['GEN_NEW'] - slr_summary['GEN_INI']
            
            for _, row in slr_summary.iterrows():
                direction = "↑" if row['GEN_ADJ'] > 0 else "↓" if row['GEN_ADJ'] < 0 else "="
                print(f"   Bus {row['BUS_NUMBER']:3.0f} (Contingency {row['contingency_case_id']:3.0f}): "
                      f"Initial={row['GEN_INI']:6.1f} MW → New={row['GEN_NEW']:6.1f} MW | "
                      f"Adjustment={row['GEN_ADJ']:+7.1f} MW {direction}")
            print()
        
        # Analyze DLR data
        print("🟢 DLR (Dynamic Line Rating) Generator Analysis:")
        print("-" * 50)
        if not dlr_df.empty:
            print(f"📋 Columns available: {', '.join(dlr_df.columns)}")
            print()
            
            # Show generator adjustment statistics
            gen_adj_stats = dlr_df['GEN_ADJ'].describe()
            print("📈 GEN_ADJ Statistics (Generator Adjustments):")
            print(f"   • Count: {gen_adj_stats['count']:.0f} generators")
            print(f"   • Mean adjustment: {gen_adj_stats['mean']:.2f} MW")
            print(f"   • Min adjustment: {gen_adj_stats['min']:.2f} MW")
            print(f"   • Max adjustment: {gen_adj_stats['max']:.2f} MW")
            print(f"   • Std deviation: {gen_adj_stats['std']:.2f} MW")
            print()
            
            # Show bus locations and adjustments
            print("🏭 DLR Generator Adjustments by Bus:")
            dlr_summary = dlr_df[['BUS_NUMBER', 'contingency_case_id', 'GEN_INI', 'GEN_NEW', 'GEN_ADJ']].copy()
            dlr_summary['GEN_CHANGE'] = dlr_summary['GEN_NEW'] - dlr_summary['GEN_INI']
            
            for _, row in dlr_summary.iterrows():
                direction = "↑" if row['GEN_ADJ'] > 0 else "↓" if row['GEN_ADJ'] < 0 else "="
                print(f"   Bus {row['BUS_NUMBER']:3.0f} (Contingency {row['contingency_case_id']:3.0f}): "
                      f"Initial={row['GEN_INI']:6.1f} MW → New={row['GEN_NEW']:6.1f} MW | "
                      f"Adjustment={row['GEN_ADJ']:+7.1f} MW {direction}")
            print()
        
        # Compare SLR vs DLR
        print("⚖️  SLR vs DLR Comparison:")
        print("-" * 50)
        
        # Find common buses
        if not slr_df.empty and not dlr_df.empty:
            slr_buses = set(slr_df['BUS_NUMBER'].unique())
            dlr_buses = set(dlr_df['BUS_NUMBER'].unique())
            common_buses = slr_buses.intersection(dlr_buses)
            slr_only = slr_buses - dlr_buses
            dlr_only = dlr_buses - slr_buses
            
            print(f"🏭 Bus Analysis:")
            print(f"   • Common buses: {len(common_buses)} - {sorted(common_buses) if common_buses else 'None'}")
            print(f"   • SLR only buses: {len(slr_only)} - {sorted(slr_only) if slr_only else 'None'}")
            print(f"   • DLR only buses: {len(dlr_only)} - {sorted(dlr_only) if dlr_only else 'None'}")
            print()
            
            # Compare adjustments for common buses
            if common_buses:
                print("📊 Adjustment Comparison for Common Buses:")
                for bus in sorted(common_buses):
                    slr_adj = slr_df[slr_df['BUS_NUMBER'] == bus]['GEN_ADJ'].values
                    dlr_adj = dlr_df[dlr_df['BUS_NUMBER'] == bus]['GEN_ADJ'].values
                    
                    if len(slr_adj) > 0 and len(dlr_adj) > 0:
                        slr_val = slr_adj[0]
                        dlr_val = dlr_adj[0]
                        diff = dlr_val - slr_val
                        
                        comparison = "DLR > SLR" if diff > 0 else "DLR < SLR" if diff < 0 else "DLR = SLR"
                        print(f"   Bus {bus:3.0f}: SLR={slr_val:+7.1f} MW, DLR={dlr_val:+7.1f} MW, "
                              f"Diff={diff:+7.1f} MW ({comparison})")
                print()
        
        # Summary insights
        print("💡 What This Means:")
        print("-" * 50)
        print("🔵 SLR (Static Line Rating):")
        print("   • Uses fixed, conservative line capacity ratings")
        print("   • Generator adjustments show how much each generator")
        print("     output was changed from initial to meet constraints")
        print("   • Negative GEN_ADJ = generator output reduced")
        print("   • Positive GEN_ADJ = generator output increased")
        print()
        
        print("🟢 DLR (Dynamic Line Rating):")
        print("   • Uses real-time, weather-dependent line capacity")
        print("   • Generally allows higher line capacities")
        print("   • May require different generator dispatch patterns")
        print("   • Often results in more efficient generator utilization")
        print()
        
        print("⚖️  Comparison Insights:")
        print("   • Different adjustment patterns indicate how DLR")
        print("     optimization differs from SLR")
        print("   • Larger adjustments may indicate more constraint violations")
        print("   • Pattern differences show economic dispatch optimization")
        print("     under different line rating scenarios")
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False

if __name__ == "__main__":
    print("📊 CASE 42 GENERATOR ANALYSIS EXPLANATION")
    print("=" * 60)
    analyze_case_42_generators()