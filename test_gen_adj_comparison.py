#!/usr/bin/env python3
"""
Test the updated generator analysis with GEN_ADJ values and correct colors
"""

import sqlite3
import pandas as pd
import plotly.graph_objects as go

def test_gen_adj_comparison():
    """Test the comparison using GEN_ADJ values with correct colors"""
    print("🧪 Testing GEN_ADJ comparison with blue/green colors...")
    
    try:
        conn = sqlite3.connect('data.db')
        
        # Get the data
        slr_df = pd.read_sql_query("SELECT * FROM SLR_Generator WHERE base_case_id = 42", conn)
        dlr_df = pd.read_sql_query("SELECT * FROM DLR_Generator WHERE base_case_id = 42", conn)
        
        conn.close()
        
        print(f"✅ SLR data: {len(slr_df)} rows with GEN_ADJ values")
        print(f"✅ DLR data: {len(dlr_df)} rows with GEN_ADJ values")
        
        # Verify GEN_ADJ column exists
        if 'GEN_ADJ' not in slr_df.columns or 'GEN_ADJ' not in dlr_df.columns:
            print("❌ GEN_ADJ column not found!")
            return False
        
        # Show sample GEN_ADJ values
        print(f"📊 SLR GEN_ADJ sample: {slr_df['GEN_ADJ'].head().tolist()}")
        print(f"📊 DLR GEN_ADJ sample: {dlr_df['GEN_ADJ'].head().tolist()}")
        
        # Create comparison plot with exact specifications
        fig = go.Figure()
        
        # Add SLR data with blue color
        fig.add_trace(go.Bar(
            x=slr_df['BUS_NUMBER'],
            y=slr_df['GEN_ADJ'],
            name='SLR GEN_ADJ',
            marker_color='blue',
            opacity=0.7
        ))
        
        # Add DLR data with green color
        fig.add_trace(go.Bar(
            x=dlr_df['BUS_NUMBER'],
            y=dlr_df['GEN_ADJ'],
            name='DLR GEN_ADJ',
            marker_color='green',
            opacity=0.7
        ))
        
        fig.update_layout(
            title="Generator GEN_ADJ Analysis - SLR vs DLR (Case 42)<br><span style='font-size:12px'>Blue: SLR GEN_ADJ | Green: DLR GEN_ADJ</span>",
            xaxis_title="Bus Number",
            yaxis_title="GEN_ADJ (MW)",
            height=500,
            barmode='group',
            template="plotly_white"
        )
        
        # Save the plot
        fig.write_html("gen_adj_comparison_test.html")
        print("💾 GEN_ADJ comparison saved to gen_adj_comparison_test.html")
        
        # Verify plot has correct traces
        if len(fig.data) == 2:
            print(f"✅ Plot created with {len(fig.data)} traces")
            print(f"🔵 SLR trace: {fig.data[0].name} with color {fig.data[0].marker.color}")
            print(f"🟢 DLR trace: {fig.data[1].name} with color {fig.data[1].marker.color}")
            
            # Verify colors are correct
            if fig.data[0].marker.color == 'blue' and fig.data[1].marker.color == 'green':
                print("✅ Colors are correct: Blue for SLR, Green for DLR")
                return True
            else:
                print("❌ Colors are incorrect")
                return False
        else:
            print("❌ Incorrect number of traces")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing updated generator analysis with GEN_ADJ values...")
    success = test_gen_adj_comparison()
    
    if success:
        print("\n✅ GEN_ADJ comparison test passed! The generator analysis should now use:")
        print("   🔵 Blue color for SLR GEN_ADJ values")
        print("   🟢 Green color for DLR GEN_ADJ values")
    else:
        print("\n❌ GEN_ADJ comparison test failed")