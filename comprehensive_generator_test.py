#!/usr/bin/env python3
"""
Comprehensive test of the generator analysis functionality
"""

import sqlite3
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

def test_generator_query_directly():
    """Test just the database queries to see what data we get"""
    print("🔍 Testing direct database queries...")
    
    try:
        conn = sqlite3.connect('data.db')
        
        # Test the exact query that's working in the main function
        slr_query = "SELECT * FROM SLR_Generator WHERE base_case_id = 42"
        dlr_query = "SELECT * FROM DLR_Generator WHERE base_case_id = 42"
        
        print(f"🧪 Running SLR query: {slr_query}")
        slr_df = pd.read_sql_query(slr_query, conn)
        print(f"✅ SLR data: {len(slr_df)} rows")
        print(f"📋 SLR columns: {slr_df.columns.tolist()}")
        if not slr_df.empty:
            print(f"📊 SLR sample data:\n{slr_df.head()}")
        
        print(f"\n🧪 Running DLR query: {dlr_query}")
        dlr_df = pd.read_sql_query(dlr_query, conn)
        print(f"✅ DLR data: {len(dlr_df)} rows")
        print(f"📋 DLR columns: {dlr_df.columns.tolist()}")
        if not dlr_df.empty:
            print(f"📊 DLR sample data:\n{dlr_df.head()}")
        
        conn.close()
        
        # Now create a simple comparison plot manually
        print("\n🎨 Creating simple comparison plot...")
        fig = go.Figure()
        
        if not slr_df.empty and 'GEN_NEW' in slr_df.columns and 'BUS_NUMBER' in slr_df.columns:
            fig.add_trace(go.Bar(
                x=slr_df['BUS_NUMBER'],
                y=slr_df['GEN_NEW'],
                name='SLR Generation',
                marker_color='blue',
                opacity=0.7
            ))
        
        if not dlr_df.empty and 'GEN_NEW' in dlr_df.columns and 'BUS_NUMBER' in dlr_df.columns:
            fig.add_trace(go.Bar(
                x=dlr_df['BUS_NUMBER'],
                y=dlr_df['GEN_NEW'],
                name='DLR Generation',
                marker_color='green',
                opacity=0.7
            ))
        
        fig.update_layout(
            title="Generator Analysis - SLR vs DLR (Manual Test)",
            xaxis_title="Bus Number",
            yaxis_title="Generation (MW)",
            height=500,
            barmode='group'
        )
        
        # Save the plot
        fig.write_html("manual_generator_test.html")
        print("💾 Manual plot saved to manual_generator_test.html")
        
        # Check if we can display meaningful data
        if len(fig.data) > 0:
            print("✅ Successfully created figure with data")
            return True
        else:
            print("⚠️ Figure created but no data traces")
            return False
        
    except Exception as e:
        print(f"❌ Direct query test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def simple_comparison_function(slr_df, dlr_df, case_id):
    """Simple version of the comparison function"""
    print(f"🎨 Creating comparison for case {case_id}")
    print(f"📊 SLR data: {len(slr_df)} rows, DLR data: {len(dlr_df)} rows")
    
    fig = go.Figure()
    
    # SLR data
    if not slr_df.empty:
        if 'GEN_NEW' in slr_df.columns:
            slr_gen = slr_df['GEN_NEW'].values
        elif 'GEN_ADJ' in slr_df.columns:
            slr_gen = slr_df['GEN_ADJ'].values
        else:
            slr_gen = []
        
        slr_buses = slr_df['BUS_NUMBER'].values if 'BUS_NUMBER' in slr_df.columns else range(len(slr_gen))
        
        if len(slr_gen) > 0:
            fig.add_trace(go.Bar(
                x=slr_buses,
                y=slr_gen,
                name='SLR Generator Output',
                marker_color='blue',
                opacity=0.7
            ))
            print(f"✅ Added SLR trace with {len(slr_gen)} generators")
    
    # DLR data
    if not dlr_df.empty:
        if 'GEN_NEW' in dlr_df.columns:
            dlr_gen = dlr_df['GEN_NEW'].values
        elif 'GEN_ADJ' in dlr_df.columns:
            dlr_gen = dlr_df['GEN_ADJ'].values
        else:
            dlr_gen = []
        
        dlr_buses = dlr_df['BUS_NUMBER'].values if 'BUS_NUMBER' in dlr_df.columns else range(len(dlr_gen))
        
        if len(dlr_gen) > 0:
            fig.add_trace(go.Bar(
                x=dlr_buses,
                y=dlr_gen,
                name='DLR Generator Output',
                marker_color='green',
                opacity=0.7
            ))
            print(f"✅ Added DLR trace with {len(dlr_gen)} generators")
    
    fig.update_layout(
        title=f"Generator Analysis Comparison - Case {case_id}",
        xaxis_title="Bus Number",
        yaxis_title="Generation Output (MW)",
        height=500,
        barmode='group'
    )
    
    return fig

def test_simple_comparison():
    """Test the simple comparison function"""
    print("\n🧪 Testing simple comparison function...")
    
    try:
        conn = sqlite3.connect('data.db')
        
        # Get the data
        slr_df = pd.read_sql_query("SELECT * FROM SLR_Generator WHERE base_case_id = 42", conn)
        dlr_df = pd.read_sql_query("SELECT * FROM DLR_Generator WHERE base_case_id = 42", conn)
        
        conn.close()
        
        # Create comparison
        fig = simple_comparison_function(slr_df, dlr_df, 42)
        
        # Save it
        fig.write_html("simple_generator_comparison.html")
        print("💾 Simple comparison saved to simple_generator_comparison.html")
        
        if len(fig.data) > 0:
            print(f"✅ Comparison successful with {len(fig.data)} traces")
            return True
        else:
            print("⚠️ Comparison created but no data")
            return False
        
    except Exception as e:
        print(f"❌ Simple comparison failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Starting comprehensive generator analysis test...")
    
    # Test 1: Direct queries
    test1_success = test_generator_query_directly()
    
    # Test 2: Simple comparison
    test2_success = test_simple_comparison()
    
    if test1_success and test2_success:
        print("\n✅ All tests passed! Generator analysis should work in the app.")
    else:
        print("\n⚠️ Some tests failed. Check the issues above.")