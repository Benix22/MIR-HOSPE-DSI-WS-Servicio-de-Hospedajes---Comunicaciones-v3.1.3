import os

def final_refactor():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # We need to move session state and functions BEFORE the columns
    # Find where columns start
    col_start_marker = '# --- New Layout: Header & Columns ---'
    
    # Extract functions and session state logic
    # It starts around "# --- Session State ---" and ends at "return mapping"
    session_logic_pattern = r'# --- Session State ---.*?return mapping'
    import re
    match = re.search(session_logic_pattern, content, flags=re.DOTALL)
    if not match:
        print("Could not find session logic block")
        return
        
    session_logic = match.group(0)
    # Remove it from its current position
    content = content.replace(session_logic, "")
    
    # Insert it before the columns
    content = content.replace(col_start_marker, session_logic + "\n\n" + col_start_marker)
    
    # Now, ensure everything from "Configuración" to the end of the tabs is inside "with col_left:"
    # Currently "with col_left:" ends early.
    
    # Let's just rewrite the whole main section for clarity.
    
    # 1. Fix the "with col_left:" to encompass everything.
    # We'll find where col_left starts and col_right starts.
    
    left_start = content.find('with col_left:')
    right_start = content.find('# --- Right Column: Summary & Status ---')
    
    if left_start == -1 or right_start == -1:
        print("Could not find column markers")
        return
        
    # Content between left_start and right_start
    main_body = content[left_start:right_start]
    # Remove the existing "with col_left:" line and its indentation
    # Actually, let's just re-indent everything in main_body
    
    # But wait, there are already some parts indented.
    # It's better to just reconstruct the file.
    
final_refactor()
