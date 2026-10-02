import re

with open('dist/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

dom_ids = set(re.findall(r'id=["\']([^"\']+)["\']', html))
js_ids = set(re.findall(r'document\.getElementById\(["\']([^"\']+)["\']\)', html))

missing = js_ids - dom_ids
print(f"Total DOM IDs: {len(dom_ids)}")
print(f"Total JS getElementById IDs: {len(js_ids)}")
print(f"Missing IDs accessed by JS: {missing}")
