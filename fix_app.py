import sys

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Line 70 (index 69) is the broken one
# It should be:
# 69: # --- Custom Styles ---
# 70: st.markdown("""
# 71:     <style>

# Let's find where the broken part starts
for i, line in enumerate(lines):
    if '# --- Custom Styles ---' in line and '<style>' in line:
        lines[i] = '# --- Custom Styles ---\nst.markdown(\"\"\"\n    <style>\n'
        break

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
