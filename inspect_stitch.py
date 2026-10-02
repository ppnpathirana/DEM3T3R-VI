import re

with open(r'C:\Users\Pasindu\Pictures\stitch_cropguard_tactical_field_commander_os\code.html', 'r', encoding='utf-8') as f:
    text = f.read()

scripts = re.findall(r'<script.*?</script>', text, re.DOTALL)
print('Number of scripts:', len(scripts))

ids = re.findall(r'id="([^"]+)"', text)
print('IDs found:', ids)
