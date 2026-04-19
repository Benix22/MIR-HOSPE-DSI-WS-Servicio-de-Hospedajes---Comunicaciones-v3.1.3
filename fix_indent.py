def fix_indentation():
    with open('app.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    out = []
    i = 0
    in_col_left = False
    
    while i < len(lines):
        line = lines[i]
        
        if 'with col_left:' in line:
            in_col_left = True
            out.append(line)
            i += 1
            continue
            
        if '# --- Right Column: Summary & Status ---' in line:
            in_col_left = False
            out.append(line)
            i += 1
            continue
            
        if in_col_left:
            # If line is already indented, keep it, if not, indent it.
            # But wait, some lines might be indented 4, some 8.
            # We want to add 4 spaces to everything that is currently at column 0.
            # No, we want to make sure everything between col_left start and right_start is indented at least 4 spaces.
            if line.strip() == "":
                out.append("\n")
            elif not line.startswith("    "):
                out.append("    " + line)
            else:
                out.append("    " + line) # Add another level if it's already a block? 
                # Actually, the logic is simpler: everything in the middle should be shifted.
        else:
            out.append(line)
        i += 1
        
    with open('app.py', 'w', encoding='utf-8') as f:
        f.writelines(out)

fix_indentation()
