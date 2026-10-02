import re

with open(r'C:\Users\Pasindu\Pictures\stitch_cropguard_tactical_field_commander_os\code.html', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'<select[^>]*id="crop-model-select"[^>]*>(.*?)</select>', text, re.DOTALL)
if m:
    print("Crop selector options:\n", m.group(1).strip())
