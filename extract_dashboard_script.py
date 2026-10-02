import re

with open(r'C:\Users\Pasindu\Pictures\stitch_cropguard_tactical_field_commander_os\code.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.rfind('<script>')
script_content = text[idx:]

with open('original_dashboard_script.js', 'w', encoding='utf-8') as sf:
    sf.write(script_content)

print(f"Extracted original dashboard script, length: {len(script_content)} chars")
