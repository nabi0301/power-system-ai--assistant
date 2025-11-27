#!/usr/bin/env python3
"""
Comprehensive test script to verify all enhanced power system analysis methods
"""

import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

def test_comprehensive_analyzer():
    """Test all the comprehensive analysis methods"""
    
    try:
        from power_system_statistical_analyzer import PowerSystemStatisticalAnalyzer
        
        print("🧪 Testing COMPREHENSIVE Power System Statistical Analyzer")
        print("=" * 80)
        
        # Initialize the analyzer
        db_path = "data.db"  # Use the main database
        analyzer = PowerSystemStatisticalAnalyzer(db_path)
        
        print("✅ Analyzer initialized successfully")
        
        print("\n🔹 BUS-LEVEL ANALYSIS TESTS:")
        print("-" * 50)
        
        # Test bus-level analyses
        bus_tests = [
            ("Voltage Profile Analysis", lambda: analyzer.voltage_profile_analysis()),
            ("Load Analysis", lambda: analyzer.load_analysis()),
            ("Generation Analysis", lambda: analyzer.generation_analysis()),
            ("Enhanced Voltage Violation Count", lambda: analyzer.enhanced_voltage_violation_count())
        ]
        
        for test_name, test_func in bus_tests:
            try:
                result = test_func()
                if "error" in result:
                    print(f"  ⚠️ {test_name}: {result['error']}")
                else:
                    print(f"  ✅ {test_name}: Success")
            except Exception as e:
                print(f"  ❌ {test_name}: {e}")
        
        print("\n🔹 BRANCH-LEVEL ANALYSIS TESTS:")
        print("-" * 50)
        
        # Test branch-level analyses
        branch_tests = [
            ("Power Flow Analysis", lambda: analyzer.power_flow_analysis()),
            ("Line Loading Analysis", lambda: analyzer.line_loading_analysis()),
            ("Loss Analysis", lambda: analyzer.loss_analysis()),
            ("Branch Violation Detection", lambda: analyzer.branch_violation_detection())
        ]
        
        for test_name, test_func in branch_tests:
            try:
                result = test_func()
                if "error" in result:
                    print(f"  ⚠️ {test_name}: {result['error']}")
                else:
                    print(f"  ✅ {test_name}: Success")
            except Exception as e:
                print(f"  ❌ {test_name}: {e}")
        
        print("\n🔹 SYSTEM-LEVEL ANALYSIS TESTS:")
        print("-" * 50)
        
        # Test system-level analyses
        system_tests = [
            ("Power Balance Analysis", lambda: analyzer.power_balance_analysis()),
            ("System Losses Analysis", lambda: analyzer.system_losses_analysis()),
            ("System Reliability Indices", lambda: analyzer.system_reliability_indices()),
            ("N-1 Analysis", lambda: analyzer.n_minus_1_analysis())
        ]
        
        for test_name, test_func in system_tests:
            try:
                result = test_func()
                if "error" in result:
                    print(f"  ⚠️ {test_name}: {result['error']}")
                else:
                    print(f"  ✅ {test_name}: Success")
            except Exception as e:
                print(f"  ❌ {test_name}: {e}")
        
        print("\n🔹 COMPARATIVE ANALYSIS TESTS:")
        print("-" * 50)
        
        # Test comparative analyses
        comparative_tests = [
            ("DLR Benefits Analysis", lambda: analyzer.dlr_benefits_analysis()),
            ("Stress Points Analysis", lambda: analyzer.stress_points_analysis())
        ]
        
        for test_name, test_func in comparative_tests:
            try:
                result = test_func()
                if "error" in result:
                    print(f"  ⚠️ {test_name}: {result['error']}")
                else:
                    print(f"  ✅ {test_name}: Success")
            except Exception as e:
                print(f"  ❌ {test_name}: {e}")
        
        print("\n🔹 STATISTICAL ANALYSIS TESTS:")
        print("-" * 50)
        
        # Test statistical analyses
        statistical_tests = [
            ("Correlation Analysis", lambda: analyzer.correlation_analysis()),
            ("Distribution Analysis", lambda: analyzer.distribution_analysis()),
            ("Outlier Detection", lambda: analyzer.outlier_detection())
        ]
        
        for test_name, test_func in statistical_tests:
            try:
                result = test_func()
                if "error" in result:
                    print(f"  ⚠️ {test_name}: {result['error']}")
                else:
                    print(f"  ✅ {test_name}: Success")
            except Exception as e:
                print(f"  ❌ {test_name}: {e}")
        
        print("\n🔹 COMPREHENSIVE SUITE TEST:")
        print("-" * 50)
        
        try:
            print("  📊 Running comprehensive analysis suite...")
            comprehensive_result = analyzer.comprehensive_analysis_suite()
            
            if "error" in comprehensive_result:
                print(f"  ⚠️ Comprehensive Suite: {comprehensive_result['error']}")
            else:
                summary = comprehensive_result.get('comprehensive_summary', {})
                total = summary.get('total_analyses_run', 0)
                successful = summary.get('successful_analyses', 0)
                failed = summary.get('failed_analyses', 0)
                
                print(f"  ✅ Comprehensive Suite: {successful}/{total} analyses successful")
                print(f"  📈 Success Rate: {(successful/total*100):.1f}%" if total > 0 else "  📈 Success Rate: N/A")
                
                if summary.get('critical_issues'):
                    print(f"  🚨 Critical Issues Found: {len(summary['critical_issues'])}")
                    for issue in summary['critical_issues'][:3]:  # Show first 3 issues
                        print(f"    - {issue}")
                
                system_health = summary.get('system_health_overview', {})
                if 'health_score' in system_health:
                    print(f"  💊 System Health Score: {system_health['health_score']:.1f}/100")
                    print(f"  📊 Assessment: {system_health.get('assessment', 'Unknown')}")
                
        except Exception as e:
            print(f"  ❌ Comprehensive Suite: {e}")
        
        print("\n" + "=" * 80)
        print("🎉 COMPREHENSIVE Analysis Testing Complete!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test Error: {e}")
        return False

if __name__ == "__main__":
    success = test_comprehensive_analyzer()
    sys.exit(0 if success else 1)