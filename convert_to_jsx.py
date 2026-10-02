import re
from bs4 import BeautifulSoup, Comment

with open('pure_dom.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

def convert_html_to_jsx(html_str):
    # Replace comments
    # Convert inline styles
    def style_replacer(match):
        style_str = match.group(1)
        styles = []
        for part in style_str.split(';'):
            part = part.strip()
            if not part:
                continue
            if ':' in part:
                k, v = part.split(':', 1)
                k = k.strip()
                v = v.strip()
                # CamelCase key
                k_camel = re.sub(r'-([a-z])', lambda m: m.group(1).upper(), k)
                # Handle quotes in value
                v_clean = v.replace('"', '\\"')
                styles.append(f"{k_camel}: '{v_clean}'")
        return f"style={{{{{', '.join(styles)}}}}}"

    # Replace style="..."
    res = re.sub(r'style="([^"]*)"', style_replacer, html_str)

    # Replace class=" -> className="
    res = re.sub(r'\bclass="', 'className="', res)

    # Replace for=" -> htmlFor="
    res = re.sub(r'\bfor="', 'htmlFor="', res)

    # SVG attribute conversions
    svg_attrs = {
        'stroke-width': 'strokeWidth',
        'stroke-linecap': 'strokeLinecap',
        'stroke-linejoin': 'strokeLinejoin',
        'clip-rule': 'clipRule',
        'fill-rule': 'fillRule',
        'stroke-dasharray': 'strokeDasharray',
        'stroke-dashoffset': 'strokeDashoffset',
        'stop-color': 'stopColor',
        'stop-opacity': 'stopOpacity',
        'fill-opacity': 'fillOpacity',
        'stroke-opacity': 'strokeOpacity',
        'stroke-miterlimit': 'strokeMiterlimit',
        'font-family': 'fontFamily',
        'font-size': 'fontSize',
        'font-weight': 'fontWeight',
        'text-anchor': 'textAnchor',
    }
    for k, v in svg_attrs.items():
        res = re.sub(r'\b' + k + '=', v + '=', res)

    # Self closing tags
    void_tags = ['input', 'img', 'br', 'hr', 'path', 'circle', 'rect', 'line', 'polygon', 'stop']
    for tag in void_tags:
        # Match unclosed void tags
        res = re.sub(r'(<' + tag + r'(\s+[^>]*)?)(?<!/)>', r'\1 />', res)

    return res

jsx_body = convert_html_to_jsx(html_content)
with open('converted_jsx.txt', 'w', encoding='utf-8') as f:
    f.write(jsx_body)

print("Converted JSX body written to converted_jsx.txt, length:", len(jsx_body))
