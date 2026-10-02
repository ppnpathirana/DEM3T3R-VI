import re

with open(r'C:\Users\Pasindu\Pictures\stitch_cropguard_tactical_field_commander_os\code.html', 'r', encoding='utf-8') as f:
    text = f.read()

scripts = re.findall(r'<script(?:\s+type="([^"]*)")?[^>]*>(.*?)</script>', text, re.DOTALL)
for i, (stype, body) in enumerate(scripts):
    print(f"--- Script {i} (type={stype}) ---")
    if 'tailwind' not in body and len(body.strip()) > 0:
        print(body[:2000])
        with open(f'stitch_script_{i}.js', 'w', encoding='utf-8') as sf:
            sf.write(body)
