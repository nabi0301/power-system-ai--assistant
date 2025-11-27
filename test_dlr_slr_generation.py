"""
Test script for DLR/SLR data generation functionality
"""

from intelligent_data_completion import generate_dlr_slr_missing_data, enhance_existing_analysis_with_completion

def test_dlr_slr_generation():
    """Test the DLR/SLR data generation functionality"""
    
    print("🧪 Testing DLR/SLR Data Generation...")
    print("=" * 50)
    
    try:
        # Test 1: Generate missing DLR/SLR data
        print("📊 Test 1: Generating missing DLR/SLR data...")
        results = generate_dlr_slr_missing_data()
        print(results['summary'])
        
        # Test 2: Analyze specific case
        print("\n📊 Test 2: Analyzing specific case completion...")
        case_result = enhance_existing_analysis_with_completion('SLR_Branches', 42, 56)
        
        print(f"• Original missing data: {case_result['completion_report']['original_missing_count']}")
        print(f"• Completion success rate: {case_result['completion_report']['completion_success_rate']:.1f}%")
        print(f"• Average confidence: {case_result['completion_report']['average_confidence']:.2f}")
        
        # Test 3: Show insights
        print("\n💡 Generated Insights:")
        for insight in case_result['insights'][:3]:
            print(f"• {insight}")
        
        print("\n✅ DLR/SLR data generation test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in DLR/SLR generation test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dlr_slr_generation()