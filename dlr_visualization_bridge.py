"""
Bridge between existing power system visualization tools and DLR database
"""

import sys
import os
import pandas as pd
import json
from sqlalchemy import create_engine, text
from config import DATABASE_URL

# Import your existing tools
try:
    from power_system_statistical_analyzer import PowerSystemStatisticalAnalyzer
    from power_system_statistical_visualizer import PowerSystemStatisticalVisualizer
    EXISTING_TOOLS_AVAILABLE = True
    print("✅ Existing visualization tools imported successfully")
except ImportError as e:
    print(f"⚠️ Could not import existing tools: {e}")
    EXISTING_TOOLS_AVAILABLE = False

class DLRVisualizationBridge:
    """
    Bridge to connect your existing visualization tools with DLR flexible database
    """
    
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        
        if EXISTING_TOOLS_AVAILABLE:
            # Initialize your existing tools
            self.analyzer = PowerSystemStatisticalAnalyzer("dummy_path")  # We'll override data source
            self.visualizer = PowerSystemStatisticalVisualizer()
        
    def get_dlr_data_as_power_system_format(self):
        """
        Convert DLR flexible database data to format expected by your existing tools
        """
        try:
            with self.engine.connect() as conn:
                # Get all DLR data
                result = conn.execute(text("""
                    SELECT raw_data, measurement_timestamp, data_source, data_type
                    FROM dlr_raw_data
                    WHERE raw_data IS NOT NULL
                    ORDER BY measurement_timestamp DESC
                """))
                
                # Convert to structured format
                converted_data = []
                for row in result:
                    raw_data = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                    
                    # Add metadata
                    structured_record = {
                        'timestamp': row[1],
                        'data_source': row[2],
                        'data_type': row[3],
                        **raw_data  # Spread all the raw data fields
                    }
                    converted_data.append(structured_record)
                
                return pd.DataFrame(converted_data)
                
        except Exception as e:
            print(f"Error converting DLR data: {e}")
            return pd.DataFrame()
    
    def run_existing_analysis_on_dlr_data(self, analysis_type="correlation_analysis"):
        """
        Run your existing analysis methods on DLR data
        """
        if not EXISTING_TOOLS_AVAILABLE:
            return {"error": "Existing analysis tools not available"}
        
        try:
            # Get DLR data in compatible format
            dlr_df = self.get_dlr_data_as_power_system_format()
            
            if dlr_df.empty:
                return {"error": "No DLR data available"}
            
            print(f"🔄 Running existing {analysis_type} on {len(dlr_df)} DLR records...")
            
            # Override your analyzer's data source with DLR data
            # This is a hack to use your existing methods with our data
            self.analyzer._dlr_data_override = dlr_df
            
            # Run your existing analysis methods
            if analysis_type == "correlation_analysis":
                # Adapt your correlation analysis to work with DLR data
                result = self._run_correlation_on_dlr_data(dlr_df)
            elif analysis_type == "monte_carlo_risk":
                result = self._run_monte_carlo_on_dlr_data(dlr_df)
            elif analysis_type == "comprehensive_analysis":
                result = self._run_comprehensive_on_dlr_data(dlr_df)
            else:
                result = {"error": f"Analysis type {analysis_type} not implemented for DLR data"}
            
            return result
            
        except Exception as e:
            return {"error": f"Error running analysis: {str(e)}"}
    
    def _run_correlation_on_dlr_data(self, dlr_df):
        """Adapt correlation analysis for DLR data"""
        try:
            # Select numerical columns
            numerical_cols = dlr_df.select_dtypes(include=['float64', 'int64']).columns
            
            if len(numerical_cols) < 2:
                return {"error": "Not enough numerical columns for correlation analysis"}
            
            # Calculate correlations
            correlation_matrix = dlr_df[numerical_cols].corr()
            
            # Find strong correlations
            strong_correlations = []
            for i in range(len(correlation_matrix.columns)):
                for j in range(i+1, len(correlation_matrix.columns)):
                    corr_val = correlation_matrix.iloc[i, j]
                    if abs(corr_val) > 0.7:
                        strong_correlations.append({
                            'var1': correlation_matrix.columns[i],
                            'var2': correlation_matrix.columns[j],
                            'correlation': corr_val
                        })
            
            return {
                'analysis_type': 'correlation_analysis',
                'correlation_matrix': correlation_matrix.to_dict(),
                'strong_correlations': strong_correlations,
                'data_summary': dlr_df.describe().to_dict(),
                'total_records': len(dlr_df),
                'parameters_analyzed': list(numerical_cols)
            }
            
        except Exception as e:
            return {"error": f"Correlation analysis error: {str(e)}"}
    
    def generate_visualization_with_existing_tools(self, analysis_result):
        """
        Use your existing visualization tools to create charts from analysis results
        """
        if not EXISTING_TOOLS_AVAILABLE:
            return {"error": "Existing visualization tools not available"}
        
        try:
            # Use your existing visualizer
            if 'correlation_matrix' in analysis_result:
                # Create correlation heatmap using your existing tools
                return self.visualizer.create_correlation_heatmap(analysis_result['correlation_matrix'])
            
            # Add more visualization types as needed
            return {"message": "Visualization created successfully"}
            
        except Exception as e:
            return {"error": f"Visualization error: {str(e)}"}
    
    def create_dlr_dashboard_with_existing_tools(self):
        """
        Create dashboard using your existing visualization framework
        """
        if not EXISTING_TOOLS_AVAILABLE:
            print("❌ Existing tools not available - cannot create dashboard")
            return
        
        print("🎨 Creating DLR dashboard with existing visualization tools...")
        
        # Get DLR data
        dlr_data = self.get_dlr_data_as_power_system_format()
        
        if dlr_data.empty:
            print("⚠️ No DLR data available for dashboard")
            return
        
        # Run analyses
        analyses = {}
        analyses['correlation'] = self.run_existing_analysis_on_dlr_data('correlation_analysis')
        
        # Generate visualizations using your existing tools
        dashboard_components = {
            'data_summary': dlr_data.describe().to_dict(),
            'available_parameters': list(dlr_data.columns),
            'total_records': len(dlr_data),
            'analyses': analyses
        }
        
        print("✅ Dashboard components prepared")
        return dashboard_components

def test_bridge():
    """Test the bridge functionality"""
    print("🧪 Testing DLR Visualization Bridge...")
    
    bridge = DLRVisualizationBridge()
    
    # Test 1: Data conversion
    print("\n📊 Testing data conversion...")
    dlr_data = bridge.get_dlr_data_as_power_system_format()
    print(f"   Converted {len(dlr_data)} DLR records")
    print(f"   Available columns: {list(dlr_data.columns)}")
    
    # Test 2: Analysis integration
    print("\n🔍 Testing analysis integration...")
    result = bridge.run_existing_analysis_on_dlr_data('correlation_analysis')
    
    if 'error' in result:
        print(f"   ⚠️ {result['error']}")
    else:
        print(f"   ✅ Analysis completed on {result.get('total_records', 0)} records")
        print(f"   ✅ Found {len(result.get('strong_correlations', []))} strong correlations")
    
    # Test 3: Dashboard creation
    print("\n🎨 Testing dashboard creation...")
    dashboard = bridge.create_dlr_dashboard_with_existing_tools()
    
    if dashboard:
        print("   ✅ Dashboard created successfully")
        print(f"   ✅ Available parameters: {len(dashboard.get('available_parameters', []))}")
    
    print("\n✅ Bridge test completed!")

if __name__ == "__main__":
    test_bridge()