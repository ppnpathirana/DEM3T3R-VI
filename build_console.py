import re

with open(r'C:\Users\Pasindu\Pictures\stitch_cropguard_tactical_field_commander_os\code.html', 'r', encoding='utf-8') as sf:
    full_html = sf.read()

print('Loaded full_html len:', len(full_html))
