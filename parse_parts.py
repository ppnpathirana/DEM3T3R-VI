import os
import re

with open("stitch_body_dump.html", "r", encoding="utf-8") as f:
    html = f.read()

# Find header, main, footer, overlay
h_start = html.find("<header")
h_end = html.find("</header>") + 9
header = html[h_start:h_end]

m_start = html.find("<main")
m_end = html.find("</main>") + 7
main = html[m_start:m_end]

f_start = html.find("<footer")
f_end = html.find("</footer>") + 9
footer = html[f_start:f_end]

o_start = html.find("id=\"full-estop-overlay\"")
div_before = html.rfind("<div", 0, o_start)
o_end = html.find("</script>", o_start)
o_end = html.rfind("</div>", 0, o_end) + 6
overlay = html[div_before:o_end]

print("Header:", len(header), "Main:", len(main), "Footer:", len(footer), "Overlay:", len(overlay))
with open("parsed_components.py", "w", encoding="utf-8") as out:
    out.write(f"HEADER = {repr(header)}\nMAIN = {repr(main)}\nFOOTER = {repr(footer)}\nOVERLAY = {repr(overlay)}\n")
print("Wrote parsed_components.py")