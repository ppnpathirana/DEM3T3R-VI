import re

with open(r"C:\\Users\\Pasindu\\Pictures\\stitch_cropguard_tactical_field_commander_os\\code.html", "r", encoding="utf-8") as sf:
    raw_html = sf.read()

b_start = raw_html.find("<body")
b_tag_end = raw_html.find(">", b_start) + 1
f_end = raw_html.find("</footer>") + 9
dom = raw_html[b_tag_end:f_end]

print("Extracted pure DOM len:", len(dom))
with open("pure_dom.html", "w", encoding="utf-8") as out:
    out.write(dom)
print("Wrote pure_dom.html")