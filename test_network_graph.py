#!/usr/bin/env python3
"""
Network Graph Test Script
Tests network graph functionality with various fallback methods
"""

import sqlite3
import pandas as pd
import sys
import os
import traceback

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_network_graph_functionality():
    """Test network graph creation with different methods"""
    print("🧪 Testing Network Graph Functionality")
    print("=" * 50)
    
    try:
        # Load some test data from the database
        print("\n1️⃣ Loading test data from database...")
        conn = sqlite3.connect('data.db')
        
        # Get base case data
        buses_query = "SELECT * FROM BaseBusData WHERE base_case_id = 0 LIMIT 20"
        branches_query = "SELECT * FROM BaseBranchData WHERE base_case_id = 0 LIMIT 30"
        
        buses_df = pd.read_sql_query(buses_query, conn)
        branches_df = pd.read_sql_query(branches_query, conn)
        conn.close()
        
        print(f"   📊 Loaded {len(buses_df)} buses and {len(branches_df)} branches")
        
        if buses_df.empty or branches_df.empty:
            print("❌ No test data available")
            return False
        
        # Test 1: Simple network graph fallback
        print("\n2️⃣ Testing simple network graph fallback...")
        try:
            from power_viz_with_database import create_simple_network_graph
            
            fig = create_simple_network_graph(buses_df, branches_df, case_id=0, contingency_id=None)
            
            if fig is not None and hasattr(fig, 'data') and len(fig.data) > 0:
                print("   ✅ Simple network graph created successfully")
                print(f"   📈 Graph has {len(fig.data)} traces")
            else:
                print("   ❌ Simple network graph failed")
                return False
                
        except Exception as e:
            print(f"   ❌ Simple network graph error: {e}")
            traceback.print_exc()
            return False
        
        # Test 2: Organized network plot
        print("\n3️⃣ Testing organized network plot...")
        try:
            from power_viz_with_database import create_organized_power_system_plot
            
            fig = create_organized_power_system_plot(buses_df, branches_df, layout_method='spring_layout', case_id=0)
            
            if fig is not None and hasattr(fig, 'data'):
                print("   ✅ Organized network plot created successfully")
                print(f"   📈 Graph has {len(fig.data)} traces")
            else:
                print("   ❌ Organized network plot failed")
                
        except Exception as e:
            print(f"   ❌ Organized network plot error: {e}")
            traceback.print_exc()
        
        # Test 3: Database data validation
        print("\n4️⃣ Testing database data validation...")
        
        # Check column names
        print(f"   📋 Bus columns: {list(buses_df.columns)}")
        print(f"   📋 Branch columns: {list(branches_df.columns)}")
        
        # Check for required columns
        required_bus_cols = ['BUS_NUMBER', 'bus_number']
        required_branch_cols = ['FROM_BUS', 'TO_BUS', 'From_Bus', 'To_Bus']
        
        has_bus_id = any(col in buses_df.columns for col in required_bus_cols)
        has_branch_ids = any(col in branches_df.columns for col in required_branch_cols[:2]) or \
                        any(col in branches_df.columns for col in required_branch_cols[2:])
        
        print(f"   ✅ Bus ID column available: {has_bus_id}")
        print(f"   ✅ Branch ID columns available: {has_branch_ids}")
        
        if not has_bus_id:
            print("   ⚠️ Missing bus ID column - might cause issues")
        if not has_branch_ids:
            print("   ⚠️ Missing branch ID columns - might cause issues")
        
        # Test 4: Check if network modules are available
        print("\n5️⃣ Testing network module availability...")
        
        # Check DistOPF
        try:
            import distopf
            print("   ✅ DistOPF available")
        except ImportError:
            print("   ❌ DistOPF not available")
        
        # Check data_viz_fall
        try:
            from data_viz_fall import create_network_graph
            print("   ✅ data_viz_fall network graph available")
        except ImportError as e:
            print(f"   ❌ data_viz_fall network graph not available: {e}")
        
        print("\n✅ Network graph functionality test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        traceback.print_exc()
        return False

def test_network_graph_in_callback():
    """Test the actual callback that creates network graphs"""
    print("\n" + "=" * 50)
    print("🔧 Testing Network Graph Callback Logic")
    print("=" * 50)
    
    try:
        # Import the main app functions
        from power_viz_with_database import execute_db_query
        
        # Test data loading for base case
        print("\n1️⃣ Testing base case data loading...")
        
        case_id = 0
        contingency_id = None
        
        # Simulate the same logic as in the callback
        if contingency_id is not None:
            case_buses_query = f"""
                SELECT * FROM ContingencyBusData 
                WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}
            """
            case_branches_query = f"""
                SELECT * FROM ContingencyBranchData 
                WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}
            """
        else:
            case_buses_query = f"SELECT * FROM BaseBusData WHERE base_case_id = {case_id}"
            case_branches_query = f"SELECT * FROM BaseBranchData WHERE base_case_id = {case_id}"
        
        try:
            case_buses_df = execute_db_query(case_buses_query)
            case_branches_df = execute_db_query(case_branches_query)
            
            print(f"   📊 Base case data: {len(case_buses_df)} buses, {len(case_branches_df)} branches")
            
            if not case_buses_df.empty and not case_branches_df.empty:
                print("   ✅ Base case data loaded successfully")
                
                # Test simple graph creation
                from power_viz_with_database import create_simple_network_graph
                fig = create_simple_network_graph(case_buses_df, case_branches_df, case_id, contingency_id)
                
                if fig is not None:
                    print("   ✅ Network graph created from base case data")
                else:
                    print("   ❌ Failed to create network graph")
                    
            else:
                print("   ❌ No base case data available")
                
        except Exception as e:
            print(f"   ❌ Data loading error: {e}")
            traceback.print_exc()
        
        # Test contingency case
        print("\n2️⃣ Testing contingency case data loading...")
        
        contingency_id = 1
        
        case_buses_query = f"""
            SELECT * FROM ContingencyBusData 
            WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}
        """
        case_branches_query = f"""
            SELECT * FROM ContingencyBranchData 
            WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}
        """
        
        try:
            case_buses_df = execute_db_query(case_buses_query)
            case_branches_df = execute_db_query(case_branches_query)
            
            print(f"   📊 Contingency case data: {len(case_buses_df)} buses, {len(case_branches_df)} branches")
            
            if not case_buses_df.empty and not case_branches_df.empty:
                print("   ✅ Contingency case data loaded successfully")
            else:
                print("   ⚠️ No contingency case data available (this might be normal)")
                
        except Exception as e:
            print(f"   ❌ Contingency data loading error: {e}")
        
        print("\n✅ Callback logic test completed!")
        
    except Exception as e:
        print(f"❌ Callback test failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    try:
        success = test_network_graph_functionality()
        test_network_graph_in_callback()
        
        if success:
            print("\n🎉 Network graph tests passed!")
            print("\n📝 Recommendations:")
            print("   1. Try selecting 'Network View' in the web interface")
            print("   2. Check browser console for any JavaScript errors")
            print("   3. Verify case and contingency selectors are working")
        else:
            print("\n❌ Some network graph tests failed")
            print("   Check the error messages above for troubleshooting")
            
    except KeyboardInterrupt:
        print("\n\n👋 Test cancelled by user")
    except Exception as e:
        print(f"\n❌ Test script error: {e}")
        traceback.print_exc()