import re
import os

with open(r'C:\Users\Pasindu\Pictures\stitch_cropguard_tactical_field_commander_os\code.html', 'r', encoding='utf-8') as sf:
    html = sf.read()

# Let's extract the body content
body_start = html.find('<body')
body_tag_end = html.find('>', body_start) + 1
script_start = html.rfind('<script>')
body_html = html[body_tag_end:script_start].strip()

# Cleanup trailing
if body_html.endswith('</body>'):
    body_html = body_html[:-7].strip()
if body_html.endswith('</html>'):
    body_html = body_html[:-7].strip()

print('Extracted body_html len:', len(body_html))
with open('extracted_body.html', 'w', encoding='utf-8') as out:
    out.write(body_html)
