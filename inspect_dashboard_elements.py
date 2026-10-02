import re

with open('dist/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

ids = re.findall(r'id=["\']([^"\']+)["\']', html)
print("--- ALL ELEMENT IDs in dist/index.html ---")
for i in sorted(ids):
    print(f"  #{i}")
