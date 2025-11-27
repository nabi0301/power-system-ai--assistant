#!/usr/bin/env python3
"""
Quick verification that the application is working correctly
"""

import requests
import time

def test_application():
    """Test if the application is accessible and responding"""
    print("=" * 60)
    print("Testing Power Visualization Application")
    print("=" * 60)
    
    url = "http://127.0.0.1:8054"
    
    print(f"\n1. Testing connection to {url}...")
    try:
        # Wait a moment for the server to be fully ready
        time.sleep(2)
        
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print("   ✅ SUCCESS: Application is running and accessible!")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response Size: {len(response.content)} bytes")
            
            # Check if the response contains expected elements
            content = response.text.lower()
            checks = {
                'Power System Visualization': 'power system visualization' in content,
                'Network View option': 'network view' in content or 'network_view' in content,
                'Chat interface': 'chat' in content or 'assistant' in content,
                'Graph component': 'graph' in content or 'plotly' in content
            }
            
            print("\n2. Checking page content:")
            for check_name, result in checks.items():
                status = "✅" if result else "❌"
                print(f"   {status} {check_name}: {result}")
            
            all_passed = all(checks.values())
            if all_passed:
                print("\n" + "=" * 60)
                print("🎉 ALL TESTS PASSED!")
                print("=" * 60)
                print(f"\n✨ Open your browser and visit: {url}")
                print("✨ The power system visualization should be displayed!")
                print("✨ Click the robot icon (🤖) to chat with the AI assistant!")
                return True
            else:
                print("\n⚠️ Some content checks failed, but the app is running")
                return False
        else:
            print(f"   ❌ FAILED: Got status code {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ❌ FAILED: Could not connect to the application")
        print("   Make sure the application is running!")
        print("   Run: python power_viz_with_database.py")
        return False
    except requests.exceptions.Timeout:
        print("   ❌ FAILED: Request timed out")
        return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_application()
    
    if success:
        print("\n📌 Quick Tips:")
        print("   • Use the dropdown to switch visualizations")
        print("   • Ask the AI: 'show network graph'")
        print("   • Try: 'show voltage analysis'")
        print("   • Explore: 'show loading analysis'")
    else:
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure the application is running")
        print("   2. Check if port 8054 is available")
        print("   3. Review the terminal output for errors")
