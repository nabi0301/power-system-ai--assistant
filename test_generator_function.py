#!/usr/bin/env python3
"""
Test the actual generator analysis function from the main app
"""

import sys
import sqlite3
import pandas as pd
import plotly.graph_objects as go

# Add the current directory to path to import the function
sys.path.append('.')

def test_actual_generator_function():
    """Test the create_generator_analysis_plot function directly"""
    try:
        # Read and execute the function definition from the main file
        with open('power_viz_with_database.py', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Extract just the function we need
        # Find the function definition
        start_marker = "def create_generator_analysis_plot"
        end_marker = "\ndef "  # Next function definition
        
        start_pos = content.find(start_marker)
        if start_pos == -1:
            print("❌ Function not found")
            return False
        
        # Find the end of the function (next function definition or end of file)
        end_pos = content.find(end_marker, start_pos + 1)
        if end_pos == -1:
            # Look for other markers that might indicate end of function
            other_markers = ["\nclass ", "\nif __name__", "# End of"]
            for marker in other_markers:
                temp_end = content.find(marker, start_pos + 1)
                if temp_end != -1:
                    end_pos = temp_end
                    break
            if end_pos == -1:
                end_pos = len(content)
        
        function_code = content[start_pos:end_pos]
        
        # Also need imports
        imports = """
import sqlite3
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
"""
        
        # Execute the function definition
        exec(imports + function_code)
        
        # Now test the function
        print("🧪 Testing create_generator_analysis_plot with case 42...")
        fig = locals()['create_generator_analysis_plot'](case_id=42)
        
        if fig and hasattr(fig, 'data'):
            print("✅ Function executed successfully")
            print(f"📊 Figure has {len(fig.data)} traces")
            
            # Save the plot
            fig.write_html("test_generator_plot.html")
            print("💾 Plot saved to test_generator_plot.html")
            
            # Try with comparison type
            print("\n🧪 Testing with comparison type...")
            fig2 = locals()['create_generator_analysis_plot'](case_id=42, comparison_type='slr_vs_dlr')
            
            if fig2 and hasattr(fig2, 'data'):
                print("✅ Comparison function executed successfully")
                print(f"📊 Comparison figure has {len(fig2.data)} traces")
                
                # Save the comparison plot
                fig2.write_html("test_generator_comparison_plot.html")
                print("💾 Comparison plot saved to test_generator_comparison_plot.html")
            
            return True
        else:
            print("❌ Function returned invalid figure")
            return False
        
    except Exception as e:
        print(f"❌ Function test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing actual generator analysis function...")
    success = test_actual_generator_function()
    
    if success:
        print("\n✅ Generator function test completed successfully")
    else:
        print("\n❌ Generator function test failed")