#!/usr/bin/env python3
"""
Fix the power_viz_with_database.py file by removing leftover broken code
"""

def fix_app_file():
    """Remove problematic code sections"""
    
    # Read the file
    with open('power_viz_with_database.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the start and end of the problematic section
    start_marker = "# APP STYLING AND CHAT POSITIONING\n# ============================================================================="
    end_marker = "def create_minimal_chat_component():"
    
    start_pos = content.find(start_marker)
    end_pos = content.find(end_marker)
    
    if start_pos != -1 and end_pos != -1:
        # Keep everything before the problematic section and after the end marker
        before = content[:start_pos]
        after = content[end_pos:]
        
        # Insert the cleaned section
        fixed_content = before + start_marker + "\n\n" + after
        
        # Write the fixed content back
        with open('power_viz_with_database.py', 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print("✅ Fixed the app file by removing problematic code")
        return True
    else:
        print("❌ Could not find the problematic section markers")
        return False

if __name__ == "__main__":
    fix_app_file()