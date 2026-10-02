import re

with open(r'C:\Users\Pasindu\Pictures\stitch_cropguard_tactical_field_commander_os\code.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Search for live-stream-img
m = re.search(r'<img[^>]*id="live-stream-img"[^>]*>', text)
if m:
    print("Found live-stream-img:", m.group(0))

# 2. Check head for Socket.IO
print("Socket.io in head:", "socket.io" in text)
