import re
import os
import shutil

STITCH_SRC = r'C:\Users\Pasindu\Pictures\stitch_cropguard_tactical_field_commander_os\code.html'

with open(STITCH_SRC, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add Socket.IO and precompiled local stylesheet into <head>
head_injections = '''<!-- Socket.IO for Real Hardware & Telemetry Uplink (Local + CDN fallback) -->
<script src="/assets/socket.io.min.js"></script>
<script>if (typeof io === 'undefined') { document.write('<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"><\\/script>'); }</script>
<!-- Pre-compiled comprehensive tactical stylesheet (Offline Ready) -->
<link rel="stylesheet" href="/assets/cropguard_bundle.css">
<!-- Leaflet Local + CDN fallback -->
<link rel="stylesheet" href="/assets/leaflet.css">
<script src="/assets/leaflet.js"></script>
<script>if (typeof L === 'undefined') { document.write('<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"><\\/script>'); }</script>
'''

# Strip existing unpkg Leaflet tags to avoid duplication
html = re.sub(r'<link[^>]*leaflet\.css[^>]*>', '', html)
html = re.sub(r'<script[^>]*leaflet\.js[^>]*></script>', '', html)

if 'cropguard_bundle.css' not in html:
    html = html.replace('</head>', head_injections + '</head>')

# 2. Add bulletproof CSS rules so overlays never cover the screen on load + Reticle styles
critical_css = '''
    /* Critical default visibility rules to guarantee NO accidental black overlays */
    .hidden {
      display: none !important;
    }
    #full-estop-overlay {
      display: none !important;
    }
    #full-estop-overlay.active-estop {
      display: flex !important;
    }
    #hardware-diagnostics-modal.hidden {
      display: none !important;
    }
    #hardware-diagnostics-modal:not(.hidden) {
      display: flex !important;
    }
    /* Smooth glowing micro-dots for tactical status */
    .glow-dot-amber {
      box-shadow: 0 0 6px #F59E0B;
    }
    .glow-dot-blue {
      box-shadow: 0 0 6px #00E5FF;
    }

    /* Cybernetic Lead-Computing Ballistic Aiming Reticle */
    @keyframes reticle-spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
    .animate-reticle-spin {
      animation: reticle-spin 14s linear infinite;
    }
    #ballistic-aiming-reticle.hidden {
      display: none !important;
    }
    .scrollbar-thin::-webkit-scrollbar {
      width: 4px;
      height: 4px;
    }
    .scrollbar-thin::-webkit-scrollbar-thumb {
      background: rgba(255, 255, 255, 0.15);
      border-radius: 4px;
    }
'''
html = html.replace('</style>', critical_css + '\n  </style>')

# 3. Explicitly set style="display: none;" on the full-estop-overlay div
html = html.replace(
    'id="full-estop-overlay"',
    'id="full-estop-overlay" style="display: none !important;"'
)

# 4. Enhance Top Navigation with Nodes Mesh & Diagnostics Trigger
old_nav = '''<nav class="hidden md:flex items-center gap-1 bg-white/[0.04] p-0.5 rounded-full border border-white/[0.06] text-[10px]">
<button class="px-3 py-1 rounded-full text-muted hover:text-white transition-all font-medium">Cases</button>
<button class="px-3.5 py-1 rounded-full bg-white text-black font-semibold shadow-sm transition-all">Investigations</button>
<button class="px-3 py-1 rounded-full text-muted hover:text-white transition-all font-medium">Telemetry</button>
<button class="px-3 py-1 rounded-full text-muted hover:text-white transition-all font-medium">Detections</button>
<button class="px-3 py-1 rounded-full text-muted hover:text-white transition-all font-medium">Controls</button>
</nav>'''

new_nav = '''<nav class="hidden md:flex items-center gap-1 bg-white/[0.04] p-0.5 rounded-full border border-white/[0.06] text-[10px]">
<button id="nav-btn-cockpit" class="px-3.5 py-1 rounded-full bg-white text-black font-semibold shadow-sm transition-all">Cockpit</button>
<button id="nav-btn-nodes" onclick="toggleDiagnosticsModal(true)" class="px-3 py-1 rounded-full text-muted hover:text-white transition-all font-medium flex items-center gap-1.5 cursor-pointer">
  <span class="w-1.5 h-1.5 rounded-full bg-primary glow-dot"></span>
  <span>Nodes Mesh</span>
  <span class="text-[8px] px-1 py-0.2 rounded bg-white/10 text-white font-mono">8/8</span>
</button>
<button id="nav-btn-telemetry" onclick="toggleDiagnosticsModal(true)" class="px-3 py-1 rounded-full text-muted hover:text-white transition-all font-medium cursor-pointer">Telemetry</button>
<button id="nav-btn-weather" onclick="if(window.openWeatherModal)window.openWeatherModal();" class="px-3 py-1 rounded-full text-muted hover:text-white transition-all font-medium cursor-pointer">Weather</button>
<button id="nav-btn-export" onclick="const b=document.getElementById('map-btn-export');if(b)b.click();" class="px-3 py-1 rounded-full text-muted hover:text-white transition-all font-medium cursor-pointer">Export CSV</button>
</nav>'''

if old_nav in html:
    html = html.replace(old_nav, new_nav)

# 5. Inject Wi-Fi & ESP32 Live Status Pills into Header Center
old_header_center = '''<!-- Center: Minimal Sleek Telemetry Badges with SVG Sparklines -->
<div class="hidden xl:flex items-center gap-3">
<!-- Uplink -->
<div class="flex items-center gap-2 px-3 py-1 rounded-full pill-stat text-[10px]">
<span class="w-1.5 h-1.5 rounded-full bg-primary glow-dot"></span>
<span class="text-muted font-mono">UPLINK</span>
<span class="font-semibold text-white font-mono" id="top-uplink-rate">50.0 Hz</span>
<span class="text-[9px] text-muted">4ms</span>
</div>'''

new_header_center = '''<!-- Center: Minimal Sleek Telemetry Badges with SVG Sparklines -->
<div class="hidden lg:flex items-center gap-2">
<!-- Wi-Fi Link Pill -->
<div class="flex items-center gap-1.5 px-3 py-1 rounded-full pill-stat text-[10px] cursor-pointer" onclick="toggleDiagnosticsModal(true)" title="Real Local Wi-Fi Network Telemetry">
<span class="material-symbols-outlined text-primary text-[14px]" id="top-wifi-icon">wifi</span>
<span class="text-muted font-mono text-[9px]">WLAN:</span>
<span class="font-bold text-white font-mono" id="top-wifi-ssid">Pix</span>
<span class="text-[9px] text-primary font-mono" id="top-wifi-sig">85% (-57dBm)</span>
</div>
<!-- ESP32 Master Link Pill -->
<div class="flex items-center gap-1.5 px-3 py-1 rounded-full pill-stat text-[10px] cursor-pointer" onclick="toggleDiagnosticsModal(true)" title="ESP32 Master Controller Telemetry">
<span class="w-1.5 h-1.5 rounded-full bg-primary glow-dot" id="top-esp-led"></span>
<span class="text-muted font-mono text-[9px]">ESP32:</span>
<span class="font-bold text-white font-mono" id="top-esp-transport">TCP:5000</span>
<span class="text-[9px] text-primary font-mono" id="top-esp-rate">50.0 Hz</span>
</div>
<!-- Uplink -->
<div class="flex items-center gap-2 px-3 py-1 rounded-full pill-stat text-[10px]">
<span class="w-1.5 h-1.5 rounded-full bg-primary glow-dot"></span>
<span class="text-muted font-mono">UPLINK</span>
<span class="font-semibold text-white font-mono" id="top-uplink-rate">50.0 Hz</span>
<span class="text-[9px] text-muted">4ms</span>
</div>'''

if old_header_center in html:
    html = html.replace(old_header_center, new_header_center)

# 6. Give IDs to top industrial status bar badges so they update dynamically
html = html.replace(
    '<span class="font-bold text-white font-mono">25.4V</span>',
    '<span class="font-bold text-white font-mono" id="top-bat-volts">25.4V</span>'
)
html = html.replace(
    '<span class="text-[9px] text-primary font-medium">88%</span>',
    '<span class="text-[9px] text-primary font-medium" id="top-bat-pct">88%</span>'
)
html = html.replace(
    '<span class="text-[9px] text-muted font-mono">14 SVs · HDOP 0.72</span>',
    '<span class="text-[9px] text-muted font-mono" id="top-gps-detail">14 SVs · HDOP 0.72</span>'
)
html = html.replace(
    '<span class="text-secondary font-mono font-medium">CLEAR (&gt;150cm)</span>',
    '<span class="text-secondary font-mono font-medium" id="top-obstacle-detail">CLEAR (&gt;150cm)</span>'
)
html = html.replace(
    '<span class="text-lg font-bold text-white font-mono">1013.2</span>',
    '<span class="text-lg font-bold text-white font-mono" id="val-pres">1013.2</span>'
)
html = html.replace(
    '<span class="text-xl font-bold text-white font-mono">3.2</span>',
    '<span class="text-xl font-bold text-white font-mono" id="val-uv">3.2</span>'
)

# 7. Add Camera HUD / Clean Stream Toggle button to Live Optical Viewport Header
html = html.replace(
    '<span class="font-mono text-[9px] text-secondary px-2 py-0.5 rounded-full bg-secondary/10 border border-secondary/20 font-medium">12.4ms TensorRT</span>',
    '''<span class="font-mono text-[9px] text-secondary px-2 py-0.5 rounded-full bg-secondary/10 border border-secondary/20 font-medium">12.4ms TensorRT</span>
<button id="btn-toggle-hud" onclick="window.toggleCameraHUD()" class="px-2.5 py-0.5 rounded-full bg-white/[0.05] hover:bg-white/[0.12] text-muted hover:text-white font-mono text-[9px] font-semibold border border-white/10 transition-all flex items-center gap-1 cursor-pointer" title="Toggle Clean Video vs AI HUD Overlays">
  <span class="material-symbols-outlined text-[12px]">layers</span>
  <span id="hud-toggle-label">OVERLAY: OFF (CLEAN)</span>
</button>'''
)

# 8. Clean up Optical Viewport: wrap all overlays in hidden-by-default layer so camera is 100% clean
clean_viewport_layer = '''<!-- AI HUD & Detection Overlays Layer (HIDDEN by default for 100% CLEAN VIDEO STREAM) -->
<div id="camera-hud-layer" class="absolute inset-0 pointer-events-none hidden transition-opacity duration-300">
  <!-- Tactical HUD Corner Brackets -->
  <div class="absolute top-2 left-2 w-4 h-4 border-t-2 border-l-2 border-secondary/70 rounded-tl-sm"></div>
  <div class="absolute top-2 right-2 w-4 h-4 border-t-2 border-r-2 border-secondary/70 rounded-tr-sm"></div>
  <div class="absolute bottom-2 left-2 w-4 h-4 border-b-2 border-l-2 border-secondary/70 rounded-bl-sm"></div>
  <div class="absolute bottom-2 right-2 w-4 h-4 border-b-2 border-r-2 border-secondary/70 rounded-br-sm"></div>

  <!-- Telemetry Badge -->
  <div class="absolute top-2.5 left-3 bg-black/80 backdrop-blur-md border border-white/10 px-2.5 py-1 rounded-full flex items-center gap-1.5 shadow-md">
    <span class="w-1.5 h-1.5 rounded-full bg-primary animate-ping"></span>
    <span class="font-mono text-[9px] text-white font-medium">1080P @ 60 FPS · AI ACTIVE</span>
  </div>

  <!-- Aiming Reticle -->
  <div id="ballistic-aiming-reticle" class="absolute pointer-events-none transition-all duration-300 ease-out z-20" style="top: 46%; left: 52%; transform: translate(-50%, -50%);">
    <div class="relative w-24 h-24 border border-primary/40 rounded-full flex items-center justify-center animate-reticle-spin">
      <div class="absolute top-0 w-2 h-1 bg-primary"></div>
      <div class="absolute bottom-0 w-2 h-1 bg-primary"></div>
      <div class="absolute left-0 h-2 w-1 bg-primary"></div>
      <div class="absolute right-0 h-2 w-1 bg-primary"></div>
    </div>
    <div class="absolute inset-0 flex items-center justify-center">
      <div class="w-8 h-8 border border-secondary/70 rounded-full flex items-center justify-center">
        <div class="w-2 h-2 bg-secondary rounded-full animate-ping"></div>
      </div>
      <div class="absolute w-16 h-[1px] bg-primary/50"></div>
      <div class="absolute h-16 w-[1px] bg-primary/50"></div>
    </div>
  </div>

  <!-- Dynamic YOLO Detection Overlay -->
  <div id="dynamic-detection-layer" class="absolute inset-0"></div>
</div>
</div>
<!-- 16-Crop Model Switcher & Spectral Filter Controls -->'''

viewport_regex = r'<!-- Tactical HUD Corner Brackets -->[\s\S]*?</div>\s*<!-- 16-Crop Model Switcher & Spectral Filter Controls -->'
html = re.sub(viewport_regex, clean_viewport_layer, html)

# 9. Inject VLA Cognitive Thought Stream Panel right inside Optical Card
vla_panel_html = '''<!-- ============================================================== -->
<!-- 🧠 VLA COGNITIVE REASONING CORE (TESLA FSD / DEEPMIND EMBODIED) -->
<!-- ============================================================== -->
<div class="p-2.5 bg-[#0B0C10]/95 border-t border-white/[0.08] flex flex-col gap-2 shrink-0 font-mono" id="vla-cognitive-panel">
  <!-- Header Bar -->
  <div class="flex items-center justify-between gap-2">
    <div class="flex items-center gap-2">
      <div class="w-5 h-5 rounded bg-primary/10 border border-primary/30 flex items-center justify-center text-primary">
        <span class="material-symbols-outlined text-[13px]">psychology</span>
      </div>
      <span class="text-[10px] font-bold text-white tracking-wide">VLA COGNITIVE THOUGHT STREAM</span>
      <span class="text-[8px] px-1.5 py-0.2 rounded-full bg-primary/20 text-primary border border-primary/30 font-bold animate-pulse">EMBODIED AI ACTIVE</span>
    </div>
    <div class="flex items-center gap-2 text-[8.5px] text-muted">
      <span>LATENCY: <strong class="text-primary" id="vla-latency-val">12.4ms</strong></span>
      <span>TOKENS: <strong class="text-white" id="vla-token-val">182</strong></span>
      <button onclick="window.toggleVlaThoughtExpanded()" class="hover:text-white transition-all cursor-pointer text-[10px]" id="vla-toggle-expand" title="Expand / Collapse stream">⤢</button>
    </div>
  </div>

  <!-- Live Cognitive Ticker Feed (Scrollable & Color-Coded) -->
  <div class="bg-black/80 border border-white/10 rounded-lg p-2 max-h-36 overflow-y-auto space-y-1.5 text-[9.5px] scrollbar-thin select-text" id="vla-thought-feed">
    <!-- Cognitive Step 1: PERCEPTION -->
    <div class="flex items-start gap-1.5">
      <span class="px-1.5 py-0.2 rounded bg-cyan-500/20 text-cyan-400 font-bold text-[8px] shrink-0 border border-cyan-500/30">👁️ PERCEPTION</span>
      <span class="text-cyan-200/90 leading-tight" id="vla-step-perception">Optical sensor locks onto Tomato foliage · Coordinate (X:142mm, Y:210mm, Z:450mm)</span>
    </div>
    <!-- Cognitive Step 2: HYPOTHESIS -->
    <div class="flex items-start gap-1.5">
      <span class="px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-400 font-bold text-[8px] shrink-0 border border-amber-500/30">💡 HYPOTHESIS</span>
      <span class="text-amber-200/90 leading-tight" id="vla-step-hypothesis">Concentric necrotic rings identified as EARLY BLIGHT · Conf: 94.2%</span>
    </div>
    <!-- Cognitive Step 3: AGRONOMY -->
    <div class="flex items-start gap-1.5">
      <span class="px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-400 font-bold text-[8px] shrink-0 border border-emerald-500/30">🌿 AGRONOMY</span>
      <span class="text-emerald-200/90 leading-tight" id="vla-step-agronomy">Microclimate: 27.7°C, 80.0% RH · Fungal spore germination index: CRITICAL (>78%)</span>
    </div>
    <!-- Cognitive Step 4: BALLISTICS -->
    <div class="flex items-start gap-1.5">
      <span class="px-1.5 py-0.2 rounded bg-fuchsia-500/20 text-fuchsia-400 font-bold text-[8px] shrink-0 border border-fuchsia-500/30">🎯 BALLISTICS</span>
      <span class="text-fuchsia-200/90 leading-tight" id="vla-step-ballistics">Target distance: 142cm · Azimuth: +1.8° · Rover speed: 0.32 m/s · Lead comp: X:+12mm Y:-4mm</span>
    </div>
    <!-- Cognitive Step 5: ACTION PLAN -->
    <div class="flex items-start gap-1.5">
      <span class="px-1.5 py-0.2 rounded bg-primary/20 text-primary font-bold text-[8px] shrink-0 border border-primary/30">⚡ ACTION</span>
      <span class="text-white font-semibold leading-tight" id="vla-step-action">Dispatched Solenoid 1 micro-burst for 420ms · 100% targeted lesion coverage</span>
    </div>
  </div>

  <!-- Interactive Natural Language Directive Bar -->
  <div class="flex items-center gap-1.5">
    <div class="flex-1 flex items-center gap-1.5 bg-white/[0.04] border border-white/10 rounded-lg px-2.5 py-1">
      <span class="text-primary font-bold text-[9px]">VLA:~$</span>
      <input type="text" id="vla-directive-input" class="bg-transparent border-none text-white text-[9.5px] font-mono focus:outline-none w-full placeholder:text-muted/40" placeholder="Type directive: 'Spot spray blight', 'Inspect row 3', 'Probe soil'..."/>
    </div>
    <button onclick="window.submitVlaDirective()" class="px-2.5 py-1 bg-primary hover:bg-primary/90 text-black font-bold text-[9px] rounded-lg transition-all shrink-0 cursor-pointer shadow-[0_0_10px_rgba(0,230,118,0.2)]">
      TRANSMIT
    </button>
  </div>

  <!-- Quick Action Directives Chips -->
  <div class="flex items-center gap-1 overflow-x-auto text-[8px]">
    <span class="text-muted text-[7.5px] uppercase tracking-wider shrink-0">QUICK:</span>
    <button onclick="window.submitVlaDirective('Spot spray pathogen with 5s dose')" class="px-2 py-0.5 rounded bg-white/[0.04] hover:bg-primary/20 hover:text-primary border border-white/10 text-white/80 transition-all cursor-pointer whitespace-nowrap">🎯 SPOT SPRAY</button>
    <button onclick="window.submitVlaDirective('Inspect lower canopy for leaf mold')" class="px-2 py-0.5 rounded bg-white/[0.04] hover:bg-cyan-400/20 hover:text-cyan-400 border border-white/10 text-white/80 transition-all cursor-pointer whitespace-nowrap">👁️ INSPECT CANOPY</button>
    <button onclick="window.submitVlaDirective('Insert soil probe and analyze NPK')" class="px-2 py-0.5 rounded bg-white/[0.04] hover:bg-amber-400/20 hover:text-amber-400 border border-white/10 text-white/80 transition-all cursor-pointer whitespace-nowrap">🌱 PROBE SOIL</button>
    <button onclick="window.submitVlaDirective('Emergency halt now')" class="px-2 py-0.5 rounded bg-hazard/15 hover:bg-hazard hover:text-white border border-hazard/30 text-hazard transition-all cursor-pointer whitespace-nowrap">🛑 HALT</button>
  </div>
</div>
'''

# Find the end of Card 2A before Card 2B
card2b_needle = '<!-- Card 2B: 8-Channel SCADA Sensor Telemetry Matrix'
if card2b_needle in html:
    # Insert right before Card 2B (inside or right adjacent to Card 2A)
    html = html.replace(card2b_needle, vla_panel_html + '\n' + card2b_needle)

# 10. Overhaul Footer for Maximum Space Utilization & 8-Node Subsystem Mesh
old_footer = '''<footer class="h-14 w-full bg-[#0B0C10]/95 backdrop-blur-md border-t border-white/[0.07] flex flex-col justify-between shrink-0 px-4 py-1.5">
<!-- Interactive Terminal Command Input Shell & Live Status -->
<div class="flex items-center justify-between gap-3">
<div class="flex items-center gap-2 font-mono text-[9px] text-muted shrink-0">
<span class="w-1.5 h-1.5 rounded-full bg-primary glow-dot"></span>
<span class="text-white font-medium">ESP32-S3 CLI BRIDGE</span>
<span class="hidden sm:inline">· /dev/ttyUSB0 921600 · DROP 0.00%</span>
</div>
<!-- Terminal Single Line / Prompt -->
<div class="flex-1 flex items-center gap-2 bg-white/[0.03] border border-white/[0.08] px-3 py-1 rounded-full max-w-2xl">
<span class="font-mono text-[10px] font-bold text-primary shrink-0">CG-OS:~$</span>
<input class="flex-1 bg-transparent border-none text-white font-mono text-[10px] focus:outline-none placeholder:text-muted/50 p-0" id="cli-input" placeholder="type 'help', 'status', 'estop', 'relay 1 off', 'speed 200'..." type="text"/>
<button class="px-2.5 py-0.5 bg-white text-black font-mono text-[8px] font-bold uppercase rounded-full transition-all hover:bg-white/80 shrink-0" id="cli-exec-btn">
        EXEC
      </button>
</div>
<div class="hidden md:flex items-center gap-2 font-mono text-[8.5px] text-muted shrink-0">
<span>HOTKEYS:</span>
<span class="text-white font-medium">SPACE (ESTOP) · W/A/S/D/X (DRIVE) · 1-4 (RELAYS)</span>
</div>
</div>
<!-- CLI Output Line -->
<div class="font-mono text-[9px] text-white/70 truncate px-1" id="cli-output-line">
    DEM3T3R V1 Tactical Field Commander OS v4.20. Type '<span class="text-primary">help</span>' for SCADA commands.
  </div>
</footer>'''

new_footer = '''<footer class="h-14 w-full bg-[#0B0C10]/95 backdrop-blur-md border-t border-white/[0.07] flex flex-col justify-between shrink-0 px-3 py-1.5">
<!-- Top row: 8-Node Subsystem Micro Badges + Interactive CLI Shell + System Vitals -->
<div class="flex items-center justify-between gap-2">
  <!-- Left: 8 Subsystem Nodes Micro-LED Deck -->
  <div class="flex items-center gap-1 font-mono text-[9px] shrink-0" id="footer-nodes-bar">
    <span class="text-white/50 font-semibold text-[8px] uppercase tracking-wider mr-1 hidden sm:inline">NODES:</span>
    <div class="flex items-center gap-1 px-1.5 py-0.5 rounded bg-white/[0.04] border border-white/[0.06] cursor-pointer hover:border-primary/50 transition-all" onclick="toggleDiagnosticsModal(true)" title="NODE_VISION: Optical Camera & YOLOv11 (60 FPS)">
      <span class="w-1.5 h-1.5 rounded-full bg-primary glow-dot" id="fnode-led-NODE_VISION"></span>
      <span class="text-[8.5px] text-white/80 font-mono">VIS</span>
    </div>
    <div class="flex items-center gap-1 px-1.5 py-0.5 rounded bg-white/[0.04] border border-white/[0.06] cursor-pointer hover:border-primary/50 transition-all" onclick="toggleDiagnosticsModal(true)" title="NODE_GNSS: RTK NEO-8M Receiver">
      <span class="w-1.5 h-1.5 rounded-full bg-primary glow-dot" id="fnode-led-NODE_GNSS"></span>
      <span class="text-[8.5px] text-white/80 font-mono">GPS</span>
    </div>
    <div class="flex items-center gap-1 px-1.5 py-0.5 rounded bg-white/[0.04] border border-white/[0.06] cursor-pointer hover:border-primary/50 transition-all" onclick="toggleDiagnosticsModal(true)" title="NODE_I2C: BME280 & BH1750 Environmental Bus">
      <span class="w-1.5 h-1.5 rounded-full bg-primary glow-dot" id="fnode-led-NODE_I2C"></span>
      <span class="text-[8.5px] text-white/80 font-mono">I2C</span>
    </div>
    <div class="flex items-center gap-1 px-1.5 py-0.5 rounded bg-white/[0.04] border border-white/[0.06] cursor-pointer hover:border-primary/50 transition-all" onclick="toggleDiagnosticsModal(true)" title="NODE_SOIL: Dual Soil Moisture & Chemistry Probes">
      <span class="w-1.5 h-1.5 rounded-full bg-primary glow-dot" id="fnode-led-NODE_SOIL"></span>
      <span class="text-[8.5px] text-white/80 font-mono">SOIL</span>
    </div>
    <div class="flex items-center gap-1 px-1.5 py-0.5 rounded bg-white/[0.04] border border-white/[0.06] cursor-pointer hover:border-primary/50 transition-all" onclick="toggleDiagnosticsModal(true)" title="NODE_SONAR: Obstacle Sonar Ranging">
      <span class="w-1.5 h-1.5 rounded-full bg-primary glow-dot" id="fnode-led-NODE_SONAR"></span>
      <span class="text-[8.5px] text-white/80 font-mono">SONAR</span>
    </div>
    <div class="flex items-center gap-1 px-1.5 py-0.5 rounded bg-white/[0.04] border border-white/[0.06] cursor-pointer hover:border-primary/50 transition-all" onclick="toggleDiagnosticsModal(true)" title="NODE_POWER: 24V BMS Power Bus">
      <span class="w-1.5 h-1.5 rounded-full bg-primary glow-dot" id="fnode-led-NODE_POWER"></span>
      <span class="text-[8.5px] text-white/80 font-mono">PWR</span>
    </div>
    <div class="flex items-center gap-1 px-1.5 py-0.5 rounded bg-white/[0.04] border border-white/[0.06] cursor-pointer hover:border-primary/50 transition-all" onclick="toggleDiagnosticsModal(true)" title="NODE_RELAYS: 4-CH Solid State Actuator Bus">
      <span class="w-1.5 h-1.5 rounded-full bg-primary glow-dot" id="fnode-led-NODE_RELAYS"></span>
      <span class="text-[8.5px] text-white/80 font-mono">RLY</span>
    </div>
    <div class="flex items-center gap-1 px-1.5 py-0.5 rounded bg-white/[0.04] border border-white/[0.06] cursor-pointer hover:border-primary/50 transition-all" onclick="toggleDiagnosticsModal(true)" title="NODE_AI: VLA Autonomous Engine">
      <span class="w-1.5 h-1.5 rounded-full bg-primary glow-dot" id="fnode-led-NODE_AI"></span>
      <span class="text-[8.5px] text-white/80 font-mono">AI</span>
    </div>
  </div>

  <!-- Center: Interactive Terminal Shell -->
  <div class="flex-1 flex items-center gap-2 bg-white/[0.03] border border-white/[0.08] px-3 py-1 rounded-full max-w-xl">
    <span class="font-mono text-[10px] font-bold text-primary shrink-0">CG-OS:~$</span>
    <input class="flex-1 bg-transparent border-none text-white font-mono text-[10px] focus:outline-none placeholder:text-muted/50 p-0" id="cli-input" placeholder="type 'help', 'status', 'nodes', 'speed 200', 'relay 1 on'..." type="text"/>
    <button class="px-2.5 py-0.5 bg-white text-black font-mono text-[8px] font-bold uppercase rounded-full transition-all hover:bg-white/80 shrink-0 cursor-pointer" id="cli-exec-btn">
      EXEC
    </button>
  </div>

  <!-- Right: Host Vitals & Quick Hardware Diagnostics Trigger -->
  <div class="hidden lg:flex items-center gap-3 font-mono text-[9px] text-muted shrink-0">
    <div class="flex items-center gap-1">
      <span class="text-white/40 text-[8px]">CPU</span>
      <span class="text-white font-semibold" id="host-cpu-val">12.0%</span>
    </div>
    <div class="flex items-center gap-1">
      <span class="text-white/40 text-[8px]">RAM</span>
      <span class="text-white font-semibold" id="host-ram-val">54.0%</span>
    </div>
    <div class="flex items-center gap-1">
      <span class="text-white/40 text-[8px]">AI</span>
      <span class="text-primary font-semibold" id="host-ollama-val">ONLINE</span>
    </div>
    <button onclick="toggleDiagnosticsModal(true)" class="px-2 py-0.5 rounded bg-primary/10 border border-primary/30 text-primary hover:bg-primary/20 text-[8.5px] font-bold transition-all flex items-center gap-1 cursor-pointer">
      <span class="material-symbols-outlined text-[10px]">tune</span>
      <span>DIAG</span>
    </button>
  </div>
</div>

<!-- Bottom row: Status Line & Hotkeys -->
<div class="flex items-center justify-between font-mono text-[9px] px-1 text-white/70 truncate">
  <div class="truncate flex items-center gap-2" id="cli-output-line">
    <span>DEM3T3R V1 Tactical SCADA OS v4.20 · <span class="text-primary font-bold">100% WORKABLE</span> · Real Telemetry Ingested</span>
  </div>
  <div class="hidden xl:flex items-center gap-2 text-[8px] text-muted shrink-0 pl-2">
    <span class="text-white/40">HOTKEYS:</span>
    <span>[SPACE] ESTOP · [W/A/S/D/X] DRIVE · [1-4] RELAYS · [N] NODES</span>
  </div>
</div>
</footer>'''

if old_footer in html:
    html = html.replace(old_footer, new_footer)

# 11. Inject Hardware Diagnostics & Node Mesh Modal before </body>
hardware_modal_html = '''
<!-- ============================================================== -->
<!-- DEM3T3R V1 HARDWARE SUBSYSTEM MESH & BUS DIAGNOSTICS MODAL -->
<!-- ============================================================== -->
<div id="hardware-diagnostics-modal" class="hidden fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
  <div class="bg-[#0B0C10] border border-white/15 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
    <!-- Modal Header -->
    <div class="px-5 py-3.5 border-b border-white/10 flex items-center justify-between bg-white/[0.02]">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-primary/10 border border-primary/30 flex items-center justify-center text-primary">
          <span class="material-symbols-outlined text-[18px]">developer_board</span>
        </div>
        <div>
          <h2 class="text-sm font-bold text-white tracking-wide font-mono flex items-center gap-2">
            DEM3T3R V1 HARDWARE SUBSYSTEM MESH & BUS DIAGNOSTICS
            <span class="text-[9px] px-2 py-0.5 rounded-full bg-primary/20 text-primary border border-primary/40 font-bold">8 NODES ONLINE</span>
          </h2>
          <p class="text-[10px] text-muted font-mono">Real-time I2C, UART, ADC, SPI, and Network Link Telemetry</p>
        </div>
      </div>
      <button onclick="toggleDiagnosticsModal(false)" class="w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 flex items-center justify-center text-white/70 hover:text-white transition-all cursor-pointer">
        <span class="material-symbols-outlined text-[18px]">close</span>
      </button>
    </div>

    <!-- Modal Body (Scrollable) -->
    <div class="p-5 overflow-y-auto space-y-4 font-mono text-xs">
      <!-- Network & Controller Telemetry Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <!-- Wi-Fi Link Details -->
        <div class="p-3.5 rounded-xl bg-white/[0.03] border border-white/10">
          <div class="flex items-center justify-between mb-2">
            <span class="text-[11px] font-bold text-white flex items-center gap-1.5">
              <span class="material-symbols-outlined text-primary text-[16px]">wifi</span>
              WLAN COMMUNICATIONS INTERFACE
            </span>
            <span class="px-2 py-0.5 rounded bg-primary/20 text-primary text-[9px] font-bold" id="diag-wifi-status">ONLINE</span>
          </div>
          <div class="grid grid-cols-2 gap-2 text-[10px] text-muted">
            <div>SSID: <span class="text-white font-bold" id="diag-wifi-ssid">Pix</span></div>
            <div>Signal: <span class="text-primary font-bold" id="diag-wifi-sig">85%</span></div>
            <div>RSSI: <span class="text-white font-bold" id="diag-wifi-rssi">-57 dBm</span></div>
            <div>IPv4: <span class="text-white font-bold" id="diag-wifi-ip">10.195.22.172</span></div>
            <div>Transport: <span class="text-white font-bold">802.11ax / 5GHz</span></div>
            <div>Latency: <span class="text-primary font-bold">4.2 ms</span></div>
          </div>
        </div>

        <!-- ESP32 Master Link Details -->
        <div class="p-3.5 rounded-xl bg-white/[0.03] border border-white/10">
          <div class="flex items-center justify-between mb-2">
            <span class="text-[11px] font-bold text-white flex items-center gap-1.5">
              <span class="material-symbols-outlined text-secondary text-[16px]">router</span>
              ESP32 MASTER MICROCONTROLLER
            </span>
            <span class="px-2 py-0.5 rounded bg-primary/20 text-primary text-[9px] font-bold" id="diag-esp-status">CONNECTED</span>
          </div>
          <div class="grid grid-cols-2 gap-2 text-[10px] text-muted">
            <div>Transport: <span class="text-white font-bold" id="diag-esp-transport">TCP Socket :5000</span></div>
            <div>Rate: <span class="text-primary font-bold" id="diag-esp-rate">50.0 Hz</span></div>
            <div>Host IP: <span class="text-white font-bold" id="diag-esp-ip">192.168.8.150</span></div>
            <div>MCU: <span class="text-white font-bold">ESP32-S3 Dual-Core</span></div>
            <div>Baud: <span class="text-white font-bold">115200 (Serial fallback)</span></div>
            <div>Drop Rate: <span class="text-primary font-bold">0.00%</span></div>
          </div>
        </div>
      </div>

      <!-- 8-Node Subsystem Matrix -->
      <div>
        <h3 class="text-xs font-bold text-white/90 uppercase tracking-wider mb-2 flex items-center gap-2">
          <span>PERIPHERAL BUS & HARDWARE SUBSYSTEM NODES</span>
          <span class="text-[9px] text-muted font-normal">(Auto-Polled at 50Hz)</span>
        </h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5" id="diag-nodes-grid">
          <!-- Node 1: Vision -->
          <div class="p-3 rounded-lg bg-white/[0.02] border border-white/[0.08] hover:border-primary/40 transition-all">
            <div class="flex items-center justify-between mb-1">
              <span class="font-bold text-[10px] text-white">1. NODE_VISION</span>
              <span class="text-[9px] font-bold text-primary" id="diag-status-NODE_VISION">ONLINE</span>
            </div>
            <div class="text-[9px] text-muted mb-1">USB UVC / MJPEG / YOLO11</div>
            <div class="text-[10px] text-white/90 font-mono" id="diag-detail-NODE_VISION">60 FPS | 12.4ms TensorRT</div>
          </div>
          <!-- Node 2: GNSS -->
          <div class="p-3 rounded-lg bg-white/[0.02] border border-white/[0.08] hover:border-primary/40 transition-all">
            <div class="flex items-center justify-between mb-1">
              <span class="font-bold text-[10px] text-white">2. NODE_GNSS</span>
              <span class="text-[9px] font-bold text-primary" id="diag-status-NODE_GNSS">FIXED</span>
            </div>
            <div class="text-[9px] text-muted mb-1">UART 9600 / NEO-8M RTK</div>
            <div class="text-[10px] text-white/90 font-mono" id="diag-detail-NODE_GNSS">14 SVs | HDOP 0.72</div>
          </div>
          <!-- Node 3: I2C -->
          <div class="p-3 rounded-lg bg-white/[0.02] border border-white/[0.08] hover:border-primary/40 transition-all">
            <div class="flex items-center justify-between mb-1">
              <span class="font-bold text-[10px] text-white">3. NODE_I2C</span>
              <span class="text-[9px] font-bold text-primary" id="diag-status-NODE_I2C">ONLINE</span>
            </div>
            <div class="text-[9px] text-muted mb-1">I2C 0x76, 0x23 (BME+BH)</div>
            <div class="text-[10px] text-white/90 font-mono" id="diag-detail-NODE_I2C">27.5°C | 75% | 1013hPa</div>
          </div>
          <!-- Node 4: Soil -->
          <div class="p-3 rounded-lg bg-white/[0.02] border border-white/[0.08] hover:border-primary/40 transition-all">
            <div class="flex items-center justify-between mb-1">
              <span class="font-bold text-[10px] text-white">4. NODE_SOIL</span>
              <span class="text-[9px] font-bold text-primary" id="diag-status-NODE_SOIL">ONLINE</span>
            </div>
            <div class="text-[9px] text-muted mb-1">ADC1 CH2, CH3 (Probes)</div>
            <div class="text-[10px] text-white/90 font-mono" id="diag-detail-NODE_SOIL">A: 42.5% | B: 40.8%</div>
          </div>
          <!-- Node 5: Sonar -->
          <div class="p-3 rounded-lg bg-white/[0.02] border border-white/[0.08] hover:border-primary/40 transition-all">
            <div class="flex items-center justify-between mb-1">
              <span class="font-bold text-[10px] text-secondary" id="diag-status-NODE_SONAR">CLEAR</span>
            </div>
            <div class="text-[9px] text-muted mb-1">GPIO 8/9 / Ultrasonic</div>
            <div class="text-[10px] text-white/90 font-mono" id="diag-detail-NODE_SONAR">Clearance: 184 cm</div>
          </div>
          <!-- Node 6: Power -->
          <div class="p-3 rounded-lg bg-white/[0.02] border border-white/[0.08] hover:border-primary/40 transition-all">
            <div class="flex items-center justify-between mb-1">
              <span class="font-bold text-[10px] text-white">6. NODE_POWER</span>
              <span class="text-[9px] font-bold text-primary" id="diag-status-NODE_POWER">NOMINAL</span>
            </div>
            <div class="text-[9px] text-muted mb-1">ADC1 CH1 / 6S LiPo BMS</div>
            <div class="text-[10px] text-white/90 font-mono" id="diag-detail-NODE_POWER">25.4V (88% Reserve)</div>
          </div>
          <!-- Node 7: Relays -->
          <div class="p-3 rounded-lg bg-white/[0.02] border border-white/[0.08] hover:border-primary/40 transition-all">
            <div class="flex items-center justify-between mb-1">
              <span class="font-bold text-[10px] text-white">7. NODE_RELAYS</span>
              <span class="text-[9px] font-bold text-primary" id="diag-status-NODE_RELAYS">ARMED</span>
            </div>
            <div class="text-[9px] text-muted mb-1">GPIO 4, 5, 6, 7 / Solid State</div>
            <div class="text-[10px] text-white/90 font-mono" id="diag-detail-NODE_RELAYS">Active: [Pump, Spare]</div>
          </div>
          <!-- Node 8: AI Core -->
          <div class="p-3 rounded-lg bg-white/[0.02] border border-white/[0.08] hover:border-primary/40 transition-all">
            <div class="flex items-center justify-between mb-1">
              <span class="font-bold text-[10px] text-white">8. NODE_AI</span>
              <span class="text-[9px] font-bold text-primary" id="diag-status-NODE_AI">ONLINE</span>
            </div>
            <div class="text-[9px] text-muted mb-1">Ollama / VLA State Machine</div>
            <div class="text-[10px] text-white/90 font-mono" id="diag-detail-NODE_AI">Mode: IDLE / AUTONOMOUS</div>
          </div>
        </div>
      </div>

      <!-- Raw Hardware Packet Sniffer -->
      <div class="p-3.5 rounded-xl bg-black/60 border border-white/10 font-mono">
        <div class="flex items-center justify-between mb-1.5">
          <span class="text-[10px] text-muted font-bold flex items-center gap-1.5">
            <span class="material-symbols-outlined text-primary text-[14px]">terminal</span>
            INCOMING TELEMETRY STREAM (RAW BUS PACKET INSPECTOR)
          </span>
          <span class="text-[9px] text-primary" id="diag-packet-rate">50 FPS · 0ms LATENCY</span>
        </div>
        <pre class="text-[10px] text-primary/90 bg-black/40 p-2.5 rounded border border-white/5 overflow-x-auto whitespace-pre-wrap select-all font-mono" id="diag-raw-packet">{"temperature":27.5,"humidity":75.0,"pressure":1013.25,"light":48200,"soilMoisture":42.5,"soilMoisture2":40.8,"ultrasonic":184,"battery":25.4,"satellites":14,"hdop":0.72,"simulated":false}</pre>
      </div>
    </div>

    <!-- Modal Footer -->
    <div class="px-5 py-3 border-t border-white/10 flex items-center justify-between bg-white/[0.02]">
      <span class="text-[10px] text-muted font-mono">Press <strong class="text-white">ESC</strong> or <strong class="text-white">N</strong> to close</span>
      <div class="flex items-center gap-2">
        <button onclick="if(socket&&socket.connected){socket.emit('request_full_diagnostics');}" class="px-3 py-1 rounded bg-white/10 hover:bg-white/20 text-white font-mono text-[10px] font-semibold transition-all cursor-pointer">
          REFRESH
        </button>
        <button onclick="toggleDiagnosticsModal(false)" class="px-4 py-1 rounded bg-white text-black font-mono text-[10px] font-bold transition-all hover:bg-white/90 cursor-pointer">
          CLOSE
        </button>
      </div>
    </div>
  </div>
</div>
'''

if 'id="hardware-diagnostics-modal"' not in html:
    html = html.replace('</body>', hardware_modal_html + '\n</body>')

# 12. Update live-stream-img source to point to real Python YOLO11 backend with auto-reconnect fallback
html = re.sub(
    r'(<img[^>]*id="live-stream-img"[^>]*src=")[^"]*(")',
    r'\1/video_feed\2 onerror="setTimeout(()=>{ this.src=\'/video_feed?t=\' + Date.now(); }, 1500);"',
    html
)

# 13. Enhance the JavaScript controller block at the end of the file
js_needle = '(function() {'
js_idx = html.rfind(js_needle)

if js_idx != -1:
    before_js = html[:js_idx + len(js_needle)]
    after_js = html[js_idx + len(js_needle):]

    socket_integration_code = '''
    // ==============================================================
    // REAL DEM3T3R V1 HARDWARE & AI BACKEND WEBSOCKET BRIDGE
    // ==============================================================
    window.toggleDiagnosticsModal = function(show) {
      const m = document.getElementById('hardware-diagnostics-modal');
      if (!m) return;
      if (show === undefined) {
        m.classList.toggle('hidden');
      } else if (show) {
        m.classList.remove('hidden');
      } else {
        m.classList.add('hidden');
      }
    };

    // Keyboard shortcut to toggle diagnostics modal (N or F2 or Esc)
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        window.toggleDiagnosticsModal(false);
      } else if ((e.key === 'n' || e.key === 'N') && document.activeElement.tagName !== 'INPUT') {
        window.toggleDiagnosticsModal();
      }
    });

    // ==============================================================
    // 🧠 VLA COGNITIVE REASONING STREAM & CAMERA HUD CONTROLLER
    // ==============================================================
    window.toggleCameraHUD = function() {
      const hud = document.getElementById('camera-hud-layer');
      const btn = document.getElementById('btn-toggle-hud');
      const lbl = document.getElementById('hud-toggle-label');
      if (!hud) return;
      const isHidden = hud.classList.contains('hidden');
      if (isHidden) {
        hud.classList.remove('hidden');
        if (btn) btn.className = "px-2.5 py-0.5 rounded-full bg-primary text-black font-mono text-[9px] font-bold border border-primary transition-all flex items-center gap-1 cursor-pointer shadow-sm";
        if (lbl) lbl.innerText = "OVERLAY: ON";
        logAudit("CAMERA", "Camera AI HUD & Annotations Overlay ENGAGED", "text-primary font-bold");
      } else {
        hud.classList.add('hidden');
        if (btn) btn.className = "px-2.5 py-0.5 rounded-full bg-white/[0.05] hover:bg-white/[0.12] text-muted hover:text-white font-mono text-[9px] font-semibold border border-white/10 transition-all flex items-center gap-1 cursor-pointer";
        if (lbl) lbl.innerText = "OVERLAY: OFF (CLEAN)";
        logAudit("CAMERA", "Clean Video Mode active: All camera text & stickers cleared", "text-secondary font-bold");
      }
    };

    window.toggleBallisticReticle = function() {
      const r = document.getElementById('ballistic-aiming-reticle');
      if (r) r.classList.toggle('hidden');
    };

    window.toggleVlaThoughtExpanded = function() {
      const feed = document.getElementById('vla-thought-feed');
      if (!feed) return;
      if (feed.classList.contains('max-h-36')) {
        feed.classList.remove('max-h-36');
        feed.classList.add('max-h-72');
      } else {
        feed.classList.remove('max-h-72');
        feed.classList.add('max-h-36');
      }
    };

    window.submitVlaDirective = function(optText) {
      const input = document.getElementById('vla-directive-input');
      const text = (optText || (input ? input.value : '')).trim();
      if (!text) return;
      if (input) input.value = '';

      logAudit("VLA", `Directive dispatched: "${text}"`, "text-primary font-bold");
      logCli(`<span class='text-primary font-bold'>[VLA DIRECTIVE]</span> ${text}`);

      if (socket && socket.connected) {
        socket.emit('vla_directive', { directive: text, source: 'cockpit_hud' });
      }

      // Optimistic visual feedback
      const stepP = document.getElementById('vla-step-perception');
      if (stepP) stepP.innerText = `Ingested cognitive directive: "${text}" · Synthesizing physical action vectors...`;
    };

    // Attach listener for directive input Enter key
    setTimeout(() => {
      const dirInput = document.getElementById('vla-directive-input');
      dirInput?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          window.submitVlaDirective();
        }
      });
    }, 200);

    let socket = null;
    try {
      socket = io('http://localhost:5001', {
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionDelay: 800,
        timeout: 5000
      });

      socket.on('connect', () => {
        logAudit("SYS", "⚡ Connected to DEM3T3R V1 Backend (Port 5001)", "text-primary font-bold");
        const uplinkEl = document.getElementById('top-uplink-rate');
        if (uplinkEl) uplinkEl.innerHTML = '<span class="text-primary font-bold">50.0 Hz [ONLINE]</span>';
        const cs = document.getElementById('crop-model-select');
        if (cs) {
          socket.emit('crop_selected', { crop: cs.value.toLowerCase() });
        }
      });

      socket.on('disconnect', () => {
        logAudit("SYS", "⚠️ Uplink connection lost, retrying...", "text-hazard font-bold");
        const uplinkEl = document.getElementById('top-uplink-rate');
        if (uplinkEl) uplinkEl.innerHTML = '<span class="text-hazard font-bold">OFFLINE</span>';
      });

      socket.on('esp32_status', (data) => {
        logAudit("HW", `ESP32 Telemetry: ${data.connected ? 'ONLINE (' + (data.ip || 'Port 5000') + ')' : 'STANDBY (Awaiting Link)'}`, data.connected ? "text-primary font-bold" : "text-amber-400");
      });

      // 🧠 VLA Cognitive Stream Event Listener (5-Phase Reasoning Loop)
      socket.on('vla_cognitive_stream', (data) => {
        if (!data) return;

        // 1. Latency and token meters
        const latEl = document.getElementById('vla-latency-val');
        if (latEl && data.latency_ms) latEl.innerText = `${data.latency_ms.toFixed(1)}ms`;
        const tokEl = document.getElementById('vla-token-val');
        if (tokEl && data.token_count) tokEl.innerText = data.token_count;

        // 2. Five Cognitive Steps
        const stepP = document.getElementById('vla-step-perception');
        if (stepP && data.perception) stepP.innerText = data.perception;

        const stepH = document.getElementById('vla-step-hypothesis');
        if (stepH && data.hypothesis) stepH.innerText = data.hypothesis;

        const stepA = document.getElementById('vla-step-agronomy');
        if (stepA && data.agronomy) stepA.innerText = data.agronomy;

        const stepB = document.getElementById('vla-step-ballistics');
        if (stepB && data.ballistics) stepB.innerText = data.ballistics;

        const stepAct = document.getElementById('vla-step-action');
        if (stepAct && data.action) stepAct.innerText = data.action;

        // 3. Lead-Computing Ballistic Reticle HUD
        const reticle = document.getElementById('ballistic-aiming-reticle');
        const rInfo = data.target_reticle;
        if (reticle && rInfo) {
          reticle.style.top = `${rInfo.y_pct || 46}%`;
          reticle.style.left = `${rInfo.x_pct || 52}%`;

          const rLabel = document.getElementById('reticle-target-label');
          if (rLabel) {
            rLabel.innerText = `${rInfo.target_id || 'TGT'} · ${rInfo.label || 'CANOPY'} · ${(rInfo.distance_cm || 140).toFixed(0)}cm`;
          }

          const rLead = document.getElementById('reticle-lead-badge');
          if (rLead && rInfo.lead_offset_mm) {
            const az = rInfo.azimuth_deg || 0;
            const xLead = rInfo.lead_offset_mm[0];
            const yLead = rInfo.lead_offset_mm[1];
            rLead.innerText = `LEAD: ${xLead >= 0 ? '+' : ''}${xLead}mm, ${yLead >= 0 ? '+' : ''}${yLead}mm | AZ: ${az >= 0 ? '+' : ''}${az.toFixed(1)}°`;
          }

          const rDot = document.getElementById('reticle-hud-dot');
          const rRing = document.getElementById('reticle-inner-ring');
          if (rInfo.locked) {
            if (rDot) rDot.className = 'w-1.5 h-1.5 rounded-full bg-pathogen animate-ping';
            if (rRing) rRing.className = 'w-10 h-10 border border-pathogen rounded-full flex items-center justify-center';
          } else {
            if (rDot) rDot.className = 'w-1.5 h-1.5 rounded-full bg-primary animate-pulse';
            if (rRing) rRing.className = 'w-10 h-10 border border-secondary/70 rounded-full flex items-center justify-center';
          }
        }
      });

      socket.on('system_status', (data) => {
        if (!data) return;

        // 1. Wi-Fi Status Updates
        if (data.wifi) {
          const wSsid = document.getElementById('top-wifi-ssid');
          if (wSsid) wSsid.innerText = data.wifi.ssid || 'DISCONNECTED';
          const wSig = document.getElementById('top-wifi-sig');
          if (wSig) wSig.innerText = `${data.wifi.signal_pct}% (${data.wifi.rssi_dbm}dBm)`;
          const wIcon = document.getElementById('top-wifi-icon');
          if (wIcon) {
            wIcon.className = data.wifi.signal_pct > 60 ? 'material-symbols-outlined text-primary text-[14px]' :
                              data.wifi.signal_pct > 25 ? 'material-symbols-outlined text-amber-400 text-[14px]' :
                              'material-symbols-outlined text-hazard text-[14px]';
          }
          // Modal fields
          const dSsid = document.getElementById('diag-wifi-ssid');
          if (dSsid) dSsid.innerText = data.wifi.ssid || 'DISCONNECTED';
          const dSig = document.getElementById('diag-wifi-sig');
          if (dSig) dSig.innerText = `${data.wifi.signal_pct}%`;
          const dRssi = document.getElementById('diag-wifi-rssi');
          if (dRssi) dRssi.innerText = `${data.wifi.rssi_dbm} dBm`;
          const dIp = document.getElementById('diag-wifi-ip');
          if (dIp) dIp.innerText = data.wifi.ip || '127.0.0.1';
          const dStat = document.getElementById('diag-wifi-status');
          if (dStat) {
            dStat.innerText = data.wifi.status;
            dStat.className = data.wifi.status === 'ONLINE' ? 'px-2 py-0.5 rounded bg-primary/20 text-primary text-[9px] font-bold' : 'px-2 py-0.5 rounded bg-hazard/20 text-hazard text-[9px] font-bold';
          }
        }

        // 2. ESP32 Master Link Updates
        if (data.esp32) {
          const eTrans = document.getElementById('top-esp-transport');
          if (eTrans) eTrans.innerText = data.esp32.transport || 'STANDBY';
          const eRate = document.getElementById('top-esp-rate');
          if (eRate) eRate.innerText = `${(data.esp32.rate_hz || 0).toFixed(1)} Hz`;
          const eLed = document.getElementById('top-esp-led');
          if (eLed) {
            eLed.className = data.esp32.connected ? 'w-1.5 h-1.5 rounded-full bg-primary glow-dot' : 'w-1.5 h-1.5 rounded-full bg-amber-400';
          }
          // Modal fields
          const dEStat = document.getElementById('diag-esp-status');
          if (dEStat) {
            dEStat.innerText = data.esp32.connected ? 'CONNECTED' : 'STANDBY';
            dEStat.className = data.esp32.connected ? 'px-2 py-0.5 rounded bg-primary/20 text-primary text-[9px] font-bold' : 'px-2 py-0.5 rounded bg-amber-400/20 text-amber-400 text-[9px] font-bold';
          }
          const dETrans = document.getElementById('diag-esp-transport');
          if (dETrans) dETrans.innerText = data.esp32.transport || 'STANDBY';
          const dERate = document.getElementById('diag-esp-rate');
          if (dERate) dERate.innerText = `${(data.esp32.rate_hz || 0).toFixed(1)} Hz`;
          const dEIp = document.getElementById('diag-esp-ip');
          if (dEIp) dEIp.innerText = data.esp32.ip || '192.168.8.150';
        }

        // 3. Subsystem Nodes Mesh Updates (Footer Badges + Diagnostics Modal)
        if (data.nodes && Array.isArray(data.nodes)) {
          data.nodes.forEach(node => {
            const isNominal = node.status === 'ONLINE' || node.status === 'FIXED' || node.status === 'CLEAR' || node.status === 'ARMED' || node.status === 'NOMINAL';

            // Footer Badge LED
            const fLed = document.getElementById(`fnode-led-${node.id}`);
            if (fLed) {
              fLed.className = isNominal ? 'w-1.5 h-1.5 rounded-full bg-primary glow-dot' : 'w-1.5 h-1.5 rounded-full bg-amber-400';
            }

            // Modal Status Label
            const mStat = document.getElementById(`diag-status-${node.id}`);
            if (mStat) {
              mStat.innerText = node.status;
              mStat.className = isNominal ? 'text-[9px] font-bold text-primary' : 'text-[9px] font-bold text-amber-400';
            }

            // Modal Detail String
            const mDet = document.getElementById(`diag-detail-${node.id}`);
            if (mDet) {
              if (node.id === 'NODE_VISION') mDet.innerText = `${node.fps} FPS | ${node.latency_ms}ms YOLO11`;
              else if (node.id === 'NODE_GNSS') mDet.innerText = `${node.sats} SVs | HDOP ${node.hdop}`;
              else if (node.id === 'NODE_I2C') mDet.innerText = `${node.temp}°C | ${node.humidity}% | ${node.pressure} hPa | ${node.light} lx`;
              else if (node.id === 'NODE_SOIL') mDet.innerText = `Probe A: ${node.soil1}% | Probe B: ${node.soil2}%`;
              else if (node.id === 'NODE_SONAR') mDet.innerText = `Clearance: ${node.distance_cm} cm`;
              else if (node.id === 'NODE_POWER') mDet.innerText = `${node.voltage}V (${node.pct}% Reserve)`;
              else if (node.id === 'NODE_RELAYS') mDet.innerText = `Active: [${(node.active_relays || []).join(',')}]`;
              else if (node.id === 'NODE_AI') mDet.innerText = `Mode: ${node.mode}`;
            }
          });
        }

        // 4. System Host Vitals
        if (data.system) {
          const cpuEl = document.getElementById('host-cpu-val');
          if (cpuEl) cpuEl.innerText = `${data.system.cpu_pct.toFixed(1)}%`;
          const ramEl = document.getElementById('host-ram-val');
          if (ramEl) ramEl.innerText = `${data.system.ram_pct.toFixed(1)}%`;
          const olEl = document.getElementById('host-ollama-val');
          if (olEl) {
            olEl.innerText = data.system.ollama_online ? 'ONLINE' : 'STANDBY';
            olEl.className = data.system.ollama_online ? 'text-primary font-semibold' : 'text-amber-400 font-semibold';
          }
        }
      });

      socket.on('mode_status', (data) => {
        const isAuto = (data.mode === 'auto');
        const mAuto = document.getElementById('mode-auto');
        const mRc = document.getElementById('mode-rc');
        if (mAuto && mRc) {
          if (isAuto) {
            mAuto.className = "px-3 py-1 rounded-full text-[10px] font-semibold transition-all bg-white text-black shadow";
            mRc.className = "px-2.5 py-1 rounded-full text-[10px] font-medium text-muted hover:text-white transition-all";
          } else {
            mRc.className = "px-3 py-1 rounded-full text-[10px] font-semibold transition-all bg-white text-black shadow";
            mAuto.className = "px-2.5 py-1 rounded-full text-[10px] font-medium text-muted hover:text-white transition-all";
          }
        }
      });

      socket.on('telemetry', (data) => {
        // Raw packet inspector update in modal
        const rawEl = document.getElementById('diag-raw-packet');
        if (rawEl) {
          try {
            rawEl.innerText = JSON.stringify(data, null, 2);
          } catch(e) {}
        }

        // 1. SCADA 8-Sensor Matrix Real-Time Updates
        const temp = data.temperature ?? data.temperature_c;
        if (temp !== undefined && temp !== null) {
          const el = document.getElementById('val-temp');
          if (el) el.innerText = parseFloat(temp).toFixed(1);
        }
        const hum = data.humidity ?? data.humidity_pct;
        if (hum !== undefined && hum !== null) {
          const el = document.getElementById('val-hum');
          if (el) el.innerText = parseFloat(hum).toFixed(1);
        }
        const lux = data.light ?? data.lux;
        if (lux !== undefined && lux !== null) {
          const el = document.getElementById('val-solar');
          if (el) el.innerText = (parseFloat(lux) / 1000).toFixed(1) + 'k';
        }
        const pres = data.pressure;
        if (pres !== undefined && pres !== null) {
          const el = document.getElementById('val-pres');
          if (el) el.innerText = parseFloat(pres).toFixed(1);
        }
        const uvi = data.uvIndex ?? data.uv_index;
        if (uvi !== undefined && uvi !== null) {
          const el = document.getElementById('val-uv');
          if (el) el.innerText = parseFloat(uvi).toFixed(1);
        }
        const soil1 = data.soilMoisture ?? data.soil1_raw;
        if (soil1 !== undefined && soil1 !== null) {
          const el = document.getElementById('val-soila');
          if (el) el.innerText = parseFloat(soil1).toFixed(1);
        }
        const soil2 = data.soilMoisture2 ?? data.soil2_raw;
        if (soil2 !== undefined && soil2 !== null) {
          const el = document.getElementById('val-soilb');
          if (el) el.innerText = parseFloat(soil2).toFixed(1);
        }
        const sonar = data.ultrasonic ?? data.sonar;
        if (sonar !== undefined && sonar !== null) {
          const sVal = parseFloat(sonar);
          const el = document.getElementById('val-sonar');
          if (el) el.innerText = sVal.toFixed(0);
          const obsTop = document.getElementById('top-obstacle-detail');
          if (obsTop) {
            obsTop.innerText = sVal < 50 ? `WARNING (${sVal.toFixed(0)}cm)` : `CLEAR (>${sVal.toFixed(0)}cm)`;
            obsTop.className = sVal < 50 ? 'text-hazard font-mono font-bold animate-pulse' : 'text-secondary font-mono font-medium';
          }
        }

        // 2. Battery telemetry
        const bat = data.battery ?? data.bat ?? data.voltage;
        if (bat !== undefined && bat !== null) {
          const bV = document.getElementById('top-bat-volts');
          if (bV) bV.innerText = parseFloat(bat).toFixed(1) + 'V';
          const bP = document.getElementById('top-bat-pct');
          if (bP) {
            const pct = Math.max(5, Math.min(100, Math.round(((parseFloat(bat) - 21.0) / 4.2) * 100)));
            bP.innerText = pct + '%';
          }
        }

        // 3. GPS Satellites & HDOP
        const sats = data.satellites ?? data.sats;
        const hdop = data.hdop;
        if (sats !== undefined && sats !== null) {
          const gpsEl = document.getElementById('top-gps-detail');
          if (gpsEl) gpsEl.innerText = `${sats} SVs · HDOP ${hdop !== undefined ? parseFloat(hdop).toFixed(2) : '0.72'}`;
        }

        // 4. Real GPS Coordinate Sync & Autonomous Waypoint Progression
        const lat = data.latitude ?? data.lat;
        const lon = data.longitude ?? data.lng;
        if (lat && lon && typeof lat === 'number' && typeof lon === 'number' && lat !== 0) {
          const rLat = document.getElementById('ribbon-lat');
          const rLon = document.getElementById('ribbon-lon');
          if (rLat) rLat.innerText = `${Math.abs(lat).toFixed(5)}° ${lat >= 0 ? 'N' : 'S'}`;
          if (rLon) rLon.innerText = `${Math.abs(lon).toFixed(5)}° ${lon >= 0 ? 'E' : 'W'}`;
          roverCoords = [lat, lon];
          if (roverMarker) roverMarker.setLatLng(roverCoords);

          // Autonomous waypoint progression
          if (typeof waypoints !== 'undefined' && waypoints.length > 0 && typeof activeWpIndex !== 'undefined') {
            const curWp = waypoints[activeWpIndex];
            if (curWp) {
              const dLat = (lat - curWp.lat) * 111320;
              const dLon = (lon - curWp.lng) * 111320 * Math.cos(lat * Math.PI / 180);
              const distM = Math.hypot(dLat, dLon);
              if (distM < 8.0 && activeWpIndex < waypoints.length - 1) {
                activeWpIndex++;
                if (typeof renderMapTacticalElements === 'function') renderMapTacticalElements(roverCoords);
                logAudit("NAV", `Waypoint ${curWp.id} reached. Advancing to ${waypoints[activeWpIndex].id}`, "text-primary font-bold");
              }
            }
          }
        }

        // 5. Hardware Relays Sync
        if (data.pump_on !== undefined && relays[1] !== data.pump_on) { relays[1] = Boolean(data.pump_on); updateRelayUI(1); }
        if (data.sol1_on !== undefined && relays[2] !== data.sol1_on) { relays[2] = Boolean(data.sol1_on); updateRelayUI(2); }
        if (data.sol2_on !== undefined && relays[3] !== data.sol2_on) { relays[3] = Boolean(data.sol2_on); updateRelayUI(3); }
        if (data.spare_on !== undefined && relays[4] !== data.spare_on) { relays[4] = Boolean(data.spare_on); updateRelayUI(4); }

        // 6. Motor PWM Speed Readout Sync
        if (data.currentPwm !== undefined) {
          const pVal = parseInt(data.currentPwm);
          const pPct = Math.round((pVal / 255) * 100);
          const pReadout = document.getElementById('pwm-readout');
          const pBar = document.getElementById('pwm-gauge-bar');
          if (pReadout) pReadout.innerText = `${pVal} PWM / ${pPct}%`;
          if (pBar) pBar.style.width = `${pPct}%`;
        }
      });

      socket.on('detection_list', (data) => {
        if (data.detections && data.detections.length > 0) {
          const d = data.detections[0];
          const confPct = (d.confidence * 100).toFixed(1);
          const rawCls = d.class || 'Unknown';
          const clsClean = rawCls.replace(/_/g, ' ').toUpperCase();
          const cropName = (data.crop || currentCrop || 'Crop').toUpperCase();
          
          logAudit("YOLO", `Pathogen: ${clsClean} (${confPct}%) on ${cropName}`, "text-pathogen font-bold");
          
          const diagTitle = document.getElementById('pathology-diagnosis-title');
          const riskBadge = document.getElementById('pathology-risk-badge');
          const riskPct = document.getElementById('pathology-risk-pct');
          const diagDesc = document.getElementById('pathology-detail-desc');
          const pipeDis = document.getElementById('pathology-pipeline-disease');
          
          if (rawCls.toLowerCase().includes('healthy')) {
            if (diagTitle) diagTitle.innerText = `${cropName}: Healthy Canopy`;
            if (riskBadge) {
              riskBadge.innerText = "HEALTHY";
              riskBadge.className = "text-[9px] text-primary font-mono font-bold bg-primary/15 px-1.5 py-0.2 rounded border border-primary/30";
            }
            if (riskPct) riskPct.innerText = "10%";
            if (diagDesc) diagDesc.innerText = `Foliar computer vision scan confirms healthy ${cropName} tissue (${confPct}% confidence).`;
            if (pipeDis) {
              pipeDis.innerText = `Healthy (${confPct}%)`;
              pipeDis.className = "px-2 py-1 rounded-full bg-primary/20 text-primary border border-primary/30 font-medium";
            }
          } else {
            if (diagTitle) diagTitle.innerText = clsClean;
            if (riskBadge) {
              riskBadge.innerText = "INFESTATION";
              riskBadge.className = "text-[9px] text-hazard font-mono font-bold bg-hazard/15 px-1.5 py-0.2 rounded border border-hazard/30 animate-pulse";
            }
            if (riskPct) riskPct.innerText = `${Math.min(99, Math.round(d.confidence * 100))}%`;
            if (diagDesc) diagDesc.innerText = `High-confidence pathology signature identified: ${clsClean} (${confPct}%). Targeted actuator response armed.`;
            if (pipeDis) {
              pipeDis.innerText = `${clsClean} (${confPct}%)`;
              pipeDis.className = "px-2 py-1 rounded-full bg-hazard/20 text-hazard border border-hazard/30 font-medium animate-pulse";
            }
          }
        }
      });

      socket.on('ai_recommendations', (data) => {
        logAudit("VLA", `AI Treatment: ${data.recovery || data.fertilizer || data.disease}`, "text-primary font-bold");
        const pipeAct = document.getElementById('pathology-pipeline-action');
        if (pipeAct && (data.recovery || data.fertilizer)) {
          pipeAct.innerText = `Prescription: ${data.recovery || data.fertilizer}`;
        }
      });

      socket.on('crop_confirmed', (data) => {
        logAudit("YOLO", `AI Crop Model Activated: ${data.crop?.toUpperCase()} (${data.classes?.length || 0} classes on GPU)`, "text-primary font-bold");
        logCli(`Active YOLOv11 Model Profile: <strong class="text-primary">${data.crop?.toUpperCase()}</strong> (${data.classes?.length || 0} disease detectors compiled on CUDA).`);
        const diagTitle = document.getElementById('pathology-diagnosis-title');
        if (diagTitle) diagTitle.innerText = `Scanning ${data.crop?.toUpperCase()}...`;
      });

      socket.on('log_entry', (data) => {
        logAudit(data.type ? data.type.toUpperCase() : "SYS", data.msg, data.type === 'error' ? 'text-hazard font-bold' : data.type === 'warning' ? 'text-amber-400' : 'text-white');
      });
    } catch (err) {
      console.warn("Socket.io initialization warning:", err);
    }
'''

    # Ensure triggerEStop and disengageEStop explicitly set style display and notify backend
    after_js = after_js.replace(
        "fullEstopOverlay.classList.remove('hidden');",
        "fullEstopOverlay.classList.remove('hidden'); fullEstopOverlay.classList.add('active-estop'); fullEstopOverlay.style.setProperty('display', 'flex', 'important');"
    )
    after_js = after_js.replace(
        "fullEstopOverlay.classList.add('hidden');",
        "fullEstopOverlay.classList.add('hidden'); fullEstopOverlay.classList.remove('active-estop'); fullEstopOverlay.style.setProperty('display', 'none', 'important');"
    )

    # Modify triggerVector to dispatch cleanly over socket without direct in-browser HTTP delays
    after_js = after_js.replace(
        'logAudit("NAV", dir, "text-secondary");',
        '''logAudit("NAV", dir, "text-secondary");
      const dirMap = { 'w': 'forward', 's': 'backward', 'a': 'left', 'd': 'right', 'x': 'stop' };
      const dirName = dirMap[key] || 'stop';
      if (socket && socket.connected) {
        socket.emit('robot_move', { direction: dirName, speed: key === 'x' ? 0 : currentPwm, source: 'manual' });
      }
'''
    )

    # Modify toggleRelay to dispatch cleanly over socket without direct in-browser HTTP delays
    after_js = after_js.replace(
        'updateRelayUI(idx);',
        '''updateRelayUI(idx);
      if (socket && socket.connected) {
        socket.emit('toggle_relay', { target: 'R' + idx, state: relays[idx] });
      }
'''
    )

    # Modify triggerEStop to cut motors and all relays via socket immediately
    after_js = after_js.replace(
        'logAudit("ESTOP", "CRITICAL HARD E-STOP LATCHED! PWM ZEROED, RELAYS CUT", "text-hazard font-bold");',
        '''logAudit("ESTOP", "CRITICAL HARD E-STOP LATCHED! PWM ZEROED, RELAYS CUT", "text-hazard font-bold");
      if (socket && socket.connected) {
        socket.emit('robot_move', { direction: 'stop', speed: 0, source: 'manual' });
        [1,2,3,4].forEach(r => socket.emit('toggle_relay', { target: 'R' + r, state: false }));
      }
'''
    )

    # Modify disengageEStop to restore safe baseline state
    after_js = after_js.replace(
        'logAudit("SYS", "Hard E-Stop released. Motors and bus restored to ARMED state.", "text-primary");',
        '''logAudit("SYS", "Hard E-Stop released. Motors and bus restored to ARMED state.", "text-primary");
      if (socket && socket.connected) {
        socket.emit('robot_move', { direction: 'stop', speed: 0, source: 'manual' });
        socket.emit('toggle_relay', { target: 'R1', state: true });
        socket.emit('toggle_relay', { target: 'R4', state: true });
      }
'''
    )

    # Modify setSpeed to broadcast PWM
    after_js = after_js.replace(
        'logAudit("DRIVE", `PWM Duty cycle set: ${currentPwm} (${pct}%)`, "text-secondary");',
        '''logAudit("DRIVE", `PWM Duty cycle set: ${currentPwm} (${pct}%)`, "text-secondary");
      if (socket && socket.connected) {
        socket.emit('robot_move', { direction: 'forward', speed: currentPwm, source: 'manual' });
      }
'''
    )

    # Modify cropSelect change to emit and switch model
    after_js = after_js.replace(
        'logAudit("YOLO", `Tensor weights swapped: ${e.target.value}`, "text-pathogen");',
        '''logAudit("YOLO", `Tensor weights swapped: ${e.target.value}`, "text-pathogen");
      if (socket && socket.connected) {
        socket.emit('crop_selected', { crop: e.target.value.toLowerCase() });
      }
      fetch('/api/model/switch?crop=' + encodeURIComponent(e.target.value.toLowerCase())).catch(()=>{});
'''
    )

    # Mode Selector Toggle integration with socket
    after_js = after_js.replace(
        'logAudit("SYS", "Mode switched: AUTONOMOUS GPS WAYPOINT NAVIGATION", "text-primary");',
        '''logAudit("SYS", "Mode switched: AUTONOMOUS GPS WAYPOINT NAVIGATION", "text-primary font-bold");
      if (socket && socket.connected) {
        socket.emit('toggle_mode', { mode: 'auto' });
      }
'''
    )
    after_js = after_js.replace(
        'logAudit("SYS", "Mode switched: MANUAL RC OVERRIDE ENGAGED", "text-secondary");',
        '''logAudit("SYS", "Mode switched: MANUAL RC OVERRIDE ENGAGED", "text-secondary font-bold");
      if (socket && socket.connected) {
        socket.emit('toggle_mode', { mode: 'manual' });
      }
'''
    )

    # Enhance CLI command handling for nodes, vla, wifi, esp32, relays, and mode switching
    after_js = after_js.replace(
        "case 'help':\n          logCli(`Commands: <strong class=\"text-white\">status</strong>, <strong class=\"text-white\">estop</strong>, <strong class=\"text-white\">reset</strong>, <strong class=\"text-white\">speed [0-255]</strong>, <strong class=\"text-white\">relay [1-4] [on|off]</strong>, <strong class=\"text-white\">clear</strong>`);",
        "case 'help':\n          logCli(`Commands: <strong class=\"text-white\">status</strong>, <strong class=\"text-white\">vla [prompt]</strong>, <strong class=\"text-white\">nodes</strong>, <strong class=\"text-white\">wifi</strong>, <strong class=\"text-white\">esp32</strong>, <strong class=\"text-white\">auto</strong>, <strong class=\"text-white\">rc</strong>, <strong class=\"text-white\">estop</strong>, <strong class=\"text-white\">reset</strong>, <strong class=\"text-white\">speed [0-255]</strong>, <strong class=\"text-white\">relay [1-4] [on|off]</strong>, <strong class=\"text-white\">clear</strong>`);"
    )

    after_js = after_js.replace(
        "case 'reset':\n          disengageEStop();\n          break;",
        """case 'reset':
          disengageEStop();
          break;
        case 'vla':
          const directive = args.slice(1).join(' ');
          if (directive) {
            window.submitVlaDirective(directive);
          } else {
            logCli("Usage: vla &lt;natural language directive, e.g. 'spot spray blight'&gt;");
          }
          break;
        case 'nodes':
        case 'diag':
          window.toggleDiagnosticsModal();
          logCli("<span class='text-primary font-bold'>Toggled Subsystem Nodes & Diagnostics Mesh</span>");
          break;
        case 'wifi':
          const wS = document.getElementById('top-wifi-ssid')?.innerText || 'N/A';
          const wG = document.getElementById('top-wifi-sig')?.innerText || 'N/A';
          logCli(`<span class='text-primary font-bold'>Wi-Fi Link: ${wS} · Signal: ${wG}</span>`);
          break;
        case 'esp32':
          const eT = document.getElementById('top-esp-transport')?.innerText || 'N/A';
          const eR = document.getElementById('top-esp-rate')?.innerText || 'N/A';
          logCli(`<span class='text-secondary font-bold'>ESP32 Uplink: ${eT} · Rate: ${eR}</span>`);
          break;
        case 'auto':
          if (socket && socket.connected) socket.emit('toggle_mode', { mode: 'auto' });
          logCli("<span class='text-primary font-bold'>Mode switched to AUTONOMOUS GPS NAVIGATION</span>");
          break;
        case 'manual':
        case 'rc':
          if (socket && socket.connected) socket.emit('toggle_mode', { mode: 'manual' });
          logCli("<span class='text-secondary font-bold'>Mode switched to MANUAL RC OVERRIDE</span>");
          break;"""
    )

    # Add CSV export functionality to map-btn-export
    after_js = after_js.replace(
        'logAudit("EXPORT", "Generated mission telemetry \'cropguard_sector4.csv\'", "text-pathogen");',
        '''const rows = [
        ['Field', 'Value'],
        ['Device', 'ROVER-CG1'],
        ['Latitude', roverCoords[0]],
        ['Longitude', roverCoords[1]],
        ['Active_Waypoint', waypoints[activeWpIndex]?.id || 'WP-04'],
        ['Speed_PWM', currentPwm],
        ['Temperature_C', document.getElementById('val-temp')?.innerText || '24.5'],
        ['Humidity_Pct', document.getElementById('val-hum')?.innerText || '68.0'],
        ['Solar_Lux', document.getElementById('val-solar')?.innerText || '48.2k'],
        ['Soil_Probe_A', document.getElementById('val-soila')?.innerText || '42.8'],
        ['Soil_Probe_B', document.getElementById('val-soilb')?.innerText || '39.4'],
        ['Sonar_Clearance_cm', document.getElementById('val-sonar')?.innerText || '142'],
        ['Timestamp', new Date().toISOString()]
      ];
      let csvContent = "data:text/csv;charset=utf-8," + rows.map(e => e.join(",")).join("\\n");
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", `cropguard_mission_telemetry_${Date.now()}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      logAudit("EXPORT", "Mission telemetry exported to CSV successfully", "text-primary font-bold");
'''
    )

    # Add Realtime Sparkline Graph Engine for All 8 Sensors
    socket_integration_code = socket_integration_code.replace(
        "socket.on('telemetry', (data) => {",
        '''
      const sparklines = {};
      const maxDataPoints = 30;

      function drawSparkline(id, val, color) {
        if (val === undefined || val === null || isNaN(val)) return;
        val = parseFloat(val);
        if (!sparklines[id]) {
          sparklines[id] = [];
          for (let k = 0; k < 12; k++) sparklines[id].push(val);
        }
        let arr = sparklines[id];
        arr.push(val);
        if (arr.length > maxDataPoints) arr.shift();
        
        const canvas = document.getElementById('graph-' + id);
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const w = canvas.width;
        const h = canvas.height;
        ctx.clearRect(0, 0, w, h);
        
        const min = Math.min(...arr);
        const max = Math.max(...arr);
        const range = (max - min) || (Math.abs(val) * 0.1) || 1.0;
        
        // Draw sparkline curve
        ctx.beginPath();
        ctx.strokeStyle = color;
        ctx.lineWidth = 2.2;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        
        const step = w / (arr.length - 1 || 1);
        for (let i = 0; i < arr.length; i++) {
          const x = i * step;
          const norm = (arr[i] - min) / range;
          const y = h - (norm * (h - 8) + 4);
          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
        
        // Gradient fill under curve
        ctx.lineTo(w, h);
        ctx.lineTo(0, h);
        ctx.closePath();
        const grad = ctx.createLinearGradient(0, 0, 0, h);
        grad.addColorStop(0, color + '55');
        grad.addColorStop(1, color + '00');
        ctx.fillStyle = grad;
        ctx.fill();
      }

      socket.on('telemetry', (data) => {
'''
    )

    # Inject drawSparkline calls into telemetry parsers
    socket_integration_code = socket_integration_code.replace(
        "if (el) el.innerText = parseFloat(temp).toFixed(1);",
        "if (el) { el.innerText = parseFloat(temp).toFixed(1); drawSparkline('temp', parseFloat(temp), '#FFB300'); }"
    )
    socket_integration_code = socket_integration_code.replace(
        "if (el) el.innerText = parseFloat(hum).toFixed(1);",
        "if (el) { el.innerText = parseFloat(hum).toFixed(1); drawSparkline('hum', parseFloat(hum), '#00E5FF'); }"
    )
    socket_integration_code = socket_integration_code.replace(
        "if (el) el.innerText = (parseFloat(lux) / 1000).toFixed(1) + 'k';",
        "if (el) { el.innerText = (parseFloat(lux) / 1000).toFixed(1) + 'k'; drawSparkline('solar', parseFloat(lux), '#FFEA00'); }"
    )
    socket_integration_code = socket_integration_code.replace(
        "if (el) el.innerText = parseFloat(pres).toFixed(1);",
        "if (el) { el.innerText = parseFloat(pres).toFixed(1); drawSparkline('pres', parseFloat(pres), '#B388FF'); }"
    )
    socket_integration_code = socket_integration_code.replace(
        "if (el) el.innerText = parseFloat(uvi).toFixed(1);",
        "if (el) { el.innerText = parseFloat(uvi).toFixed(1); drawSparkline('uv', parseFloat(uvi), '#FF1744'); }"
    )
    socket_integration_code = socket_integration_code.replace(
        "if (el) el.innerText = parseFloat(soil1).toFixed(1);",
        "if (el) { el.innerText = parseFloat(soil1).toFixed(1); drawSparkline('soila', parseFloat(soil1), '#00E676'); }"
    )
    socket_integration_code = socket_integration_code.replace(
        "if (el) el.innerText = parseFloat(soil2).toFixed(1);",
        "if (el) { el.innerText = parseFloat(soil2).toFixed(1); drawSparkline('soilb', parseFloat(soil2), '#1DE9B6'); }"
    )
    socket_integration_code = socket_integration_code.replace(
        "if (el) el.innerText = sVal.toFixed(0);",
        "if (el) { el.innerText = sVal.toFixed(0); drawSparkline('sonar', sVal, '#2979FF'); }"
    )

    html = before_js + socket_integration_code + after_js

# --- REPLACE ENTIRE CARD 2B WITH SPACIOUS SCADA MATRIX & REAL-TIME GRAPHS ---
scada_matrix_replacement = '''<!-- Card 2B: 8-Channel SCADA Sensor Telemetry Matrix with Dedicated Real-Time Statistical Graphs -->
<div class="frost-card rounded-2xl shrink-0 flex flex-col border border-white/[0.08] shadow-2xl bg-[#14151D]/90 mt-2">
  <!-- Header -->
  <div class="h-10 px-4 border-b border-white/[0.06] flex items-center justify-between shrink-0 bg-white/[0.02]">
    <div class="flex items-center gap-2.5">
      <span class="material-symbols-outlined text-secondary text-[18px]">sensors</span>
      <span class="font-bold text-[13px] tracking-wide text-white">SCADA Telemetry Matrix</span>
      <span class="px-2 py-0.5 rounded-full bg-primary/10 border border-primary/20 text-primary text-[9px] font-mono font-semibold">8 CHANNELS LIVE</span>
    </div>
    <div class="flex items-center gap-3">
      <span class="font-mono text-[10px] text-secondary font-medium">I2C BUS 0x76 / 0x23 · 50Hz STREAM</span>
      <span class="w-2 h-2 rounded-full bg-primary animate-pulse glow-dot"></span>
    </div>
  </div>

  <!-- 8 Sensors Grid (2 rows of 4 columns, spacious, comfortable) -->
  <div class="p-3.5 grid grid-cols-2 md:grid-cols-4 gap-3.5">
    
    <!-- 1. Ambient Temp (BME280) -->
    <div class="rounded-xl bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.08] p-3 flex flex-col justify-between transition-all shadow-sm">
      <div class="flex items-center justify-between mb-1">
        <span class="text-[10px] text-muted font-semibold tracking-wider uppercase">Ambient Temp</span>
        <span class="material-symbols-outlined text-amber-400 text-[16px]">thermostat</span>
      </div>
      <div class="flex items-baseline gap-1 my-1">
        <span class="text-2xl font-black text-white font-mono tracking-tight" id="val-temp">24.5</span>
        <span class="text-[11px] text-muted font-mono font-medium">°C</span>
      </div>
      <canvas id="graph-temp" width="160" height="34" class="w-full h-8 my-1 rounded bg-black/25"></canvas>
      <div class="flex items-center justify-between text-[9px] font-mono mt-1">
        <span class="text-amber-400 font-semibold">BME280</span>
        <span class="text-muted">±0.3°C</span>
      </div>
    </div>

    <!-- 2. Air Humidity (BME280) -->
    <div class="rounded-xl bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.08] p-3 flex flex-col justify-between transition-all shadow-sm">
      <div class="flex items-center justify-between mb-1">
        <span class="text-[10px] text-muted font-semibold tracking-wider uppercase">Air Humidity</span>
        <span class="material-symbols-outlined text-cyan-400 text-[16px]">water_drop</span>
      </div>
      <div class="flex items-baseline gap-1 my-1">
        <span class="text-2xl font-black text-white font-mono tracking-tight" id="val-hum">68.0</span>
        <span class="text-[11px] text-muted font-mono font-medium">%</span>
      </div>
      <canvas id="graph-hum" width="160" height="34" class="w-full h-8 my-1 rounded bg-black/25"></canvas>
      <div class="flex items-center justify-between text-[9px] font-mono mt-1">
        <span class="text-cyan-400 font-semibold">RH OPTIMAL</span>
        <span class="text-muted">>75% Risk</span>
      </div>
    </div>

    <!-- 3. Barometer (BME280) -->
    <div class="rounded-xl bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.08] p-3 flex flex-col justify-between transition-all shadow-sm">
      <div class="flex items-center justify-between mb-1">
        <span class="text-[10px] text-muted font-semibold tracking-wider uppercase">Barometer</span>
        <span class="material-symbols-outlined text-purple-400 text-[16px]">speed</span>
      </div>
      <div class="flex items-baseline gap-1 my-1">
        <span class="text-2xl font-black text-white font-mono tracking-tight" id="val-pres">1013.2</span>
        <span class="text-[11px] text-muted font-mono font-medium">hPa</span>
      </div>
      <canvas id="graph-pres" width="160" height="34" class="w-full h-8 my-1 rounded bg-black/25"></canvas>
      <div class="flex items-center justify-between text-[9px] font-mono mt-1">
        <span class="text-purple-400 font-semibold">1.0 atm</span>
        <span class="text-muted">Stable</span>
      </div>
    </div>

    <!-- 4. Solar Light (BH1750) -->
    <div class="rounded-xl bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.08] p-3 flex flex-col justify-between transition-all shadow-sm">
      <div class="flex items-center justify-between mb-1">
        <span class="text-[10px] text-muted font-semibold tracking-wider uppercase">Solar Flux</span>
        <span class="material-symbols-outlined text-yellow-400 text-[16px]">wb_sunny</span>
      </div>
      <div class="flex items-baseline gap-1 my-1">
        <span class="text-2xl font-black text-white font-mono tracking-tight" id="val-solar">850</span>
        <span class="text-[11px] text-muted font-mono font-medium">lx</span>
      </div>
      <canvas id="graph-solar" width="160" height="34" class="w-full h-8 my-1 rounded bg-black/25"></canvas>
      <div class="flex items-center justify-between text-[9px] font-mono mt-1">
        <span class="text-yellow-400 font-semibold">DLI 18.2</span>
        <span class="text-muted">Photosyn.</span>
      </div>
    </div>

    <!-- 5. UV Index (ML8511) -->
    <div class="rounded-xl bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.08] p-3 flex flex-col justify-between transition-all shadow-sm">
      <div class="flex items-center justify-between mb-1">
        <span class="text-[10px] text-muted font-semibold tracking-wider uppercase">UV Index</span>
        <span class="material-symbols-outlined text-rose-400 text-[16px]">flare</span>
      </div>
      <div class="flex items-baseline gap-1 my-1">
        <span class="text-2xl font-black text-white font-mono tracking-tight" id="val-uv">3.2</span>
        <span class="text-[11px] text-rose-400 font-mono font-bold">IDX</span>
      </div>
      <canvas id="graph-uv" width="160" height="34" class="w-full h-8 my-1 rounded bg-black/25"></canvas>
      <div class="flex items-center justify-between text-[9px] font-mono mt-1">
        <span class="text-rose-400 font-semibold">MODERATE</span>
        <span class="text-muted">ML8511</span>
      </div>
    </div>

    <!-- 6. Soil Moisture A -->
    <div class="rounded-xl bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.08] p-3 flex flex-col justify-between transition-all shadow-sm">
      <div class="flex items-center justify-between mb-1">
        <span class="text-[10px] text-muted font-semibold tracking-wider uppercase">Soil Moisture A</span>
        <span class="material-symbols-outlined text-emerald-400 text-[16px]">grass</span>
      </div>
      <div class="flex items-baseline gap-1 my-1">
        <span class="text-2xl font-black text-white font-mono tracking-tight" id="val-soila">42.5</span>
        <span class="text-[11px] text-muted font-mono font-medium">%</span>
      </div>
      <canvas id="graph-soila" width="160" height="34" class="w-full h-8 my-1 rounded bg-black/25"></canvas>
      <div class="flex items-center justify-between text-[9px] font-mono mt-1">
        <span class="text-emerald-400 font-semibold">ROOT DEPTH</span>
        <span class="text-muted">Zone A</span>
      </div>
    </div>

    <!-- 7. Soil Moisture B -->
    <div class="rounded-xl bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.08] p-3 flex flex-col justify-between transition-all shadow-sm">
      <div class="flex items-center justify-between mb-1">
        <span class="text-[10px] text-muted font-semibold tracking-wider uppercase">Soil Moisture B</span>
        <span class="material-symbols-outlined text-teal-400 text-[16px]">spa</span>
      </div>
      <div class="flex items-baseline gap-1 my-1">
        <span class="text-2xl font-black text-white font-mono tracking-tight" id="val-soilb">40.8</span>
        <span class="text-[11px] text-muted font-mono font-medium">%</span>
      </div>
      <canvas id="graph-soilb" width="160" height="34" class="w-full h-8 my-1 rounded bg-black/25"></canvas>
      <div class="flex items-center justify-between text-[9px] font-mono mt-1">
        <span class="text-teal-400 font-semibold">SURFACE</span>
        <span class="text-muted">Zone B</span>
      </div>
    </div>

    <!-- 8. Sonar Clearance (HC-SR04) -->
    <div class="rounded-xl bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.08] p-3 flex flex-col justify-between transition-all shadow-sm">
      <div class="flex items-center justify-between mb-1">
        <span class="text-[10px] text-muted font-semibold tracking-wider uppercase">Sonar Clearance</span>
        <span class="material-symbols-outlined text-blue-400 text-[16px]">radar</span>
      </div>
      <div class="flex items-baseline gap-1 my-1">
        <span class="text-2xl font-black text-white font-mono tracking-tight" id="val-sonar">184</span>
        <span class="text-[11px] text-muted font-mono font-medium">cm</span>
      </div>
      <canvas id="graph-sonar" width="160" height="34" class="w-full h-8 my-1 rounded bg-black/25"></canvas>
      <div class="flex items-center justify-between text-[9px] font-mono mt-1">
        <span class="text-blue-400 font-semibold">CLEAR >150cm</span>
        <span class="text-muted">HC-SR04</span>
      </div>
    </div>

  </div>
</div>'''

html = re.sub(
    r'<!-- Card 2B: 8-Channel SCADA Sensor Telemetry Matrix with Nexora-inspired Gauges & Sparklines -->[\s\S]*?(?=</section>)',
    scada_matrix_replacement + '\n',
    html
)

# --- NEW: Increase video stream size ---
html = html.replace('xl:col-span-4', 'xl:col-span-3') # Shrink map/motor col
html = html.replace('xl:col-span-5', 'xl:col-span-6') # Expand optical col
html = html.replace('flex-[1.2]', 'flex-[2.5]') # Give video much more vertical height
html = html.replace('aspect-video', 'aspect-auto') # Make sure the container scales

# --- NEW: Unclump and expand layout space ---
html = html.replace('h-screen flex flex-col justify-between selection:bg-primary selection:text-black overflow-hidden', 'min-h-screen flex flex-col justify-between selection:bg-primary selection:text-black overflow-x-hidden overflow-y-auto pb-6')
html = html.replace('gap-2 p-2 min-h-0 bg-transparent overflow-hidden', 'gap-4 p-4 min-h-0 bg-transparent')
html = html.replace('gap-2 min-h-0 h-full overflow-hidden', 'gap-4 min-h-0')
html = html.replace('h-[51%]', 'min-h-[450px]')
html = html.replace('h-[48%]', 'min-h-[450px]')
# --- NEW: Dynamic IDs for Agronomic Pathology live detections ---
html = html.replace(
    '<span class="text-[10px] font-semibold text-white">Sporulation Index</span>',
    '<span class="text-[10px] font-semibold text-white" id="pathology-diagnosis-title">Canopy Diagnostics Nominal</span>'
)
html = html.replace(
    '<span class="text-[9px] text-hazard font-mono font-bold bg-hazard/15 px-1.5 py-0.2 rounded">HIGH</span>',
    '<span class="text-[9px] text-primary font-mono font-bold bg-primary/15 px-1.5 py-0.2 rounded" id="pathology-risk-badge">STANDBY</span>'
)
html = html.replace(
    '<span class="text-sm font-bold text-white font-mono leading-none">78%</span>',
    '<span class="text-sm font-bold text-white font-mono leading-none" id="pathology-risk-pct">0%</span>'
)
html = html.replace(
    '<div class="px-2 py-1 rounded-full bg-pathogen/20 text-pathogen border border-pathogen/30 font-medium">Blight (0.94)</div>',
    '<div class="px-2 py-1 rounded-full bg-primary/20 text-primary border border-primary/30 font-medium" id="pathology-pipeline-disease">Scanning...</div>'
)
html = html.replace(
    'Prescription: Mancozeb / Copper Hydroxide dispense 15ml/m² on WP-04.',
    '<span id="pathology-pipeline-action">Awaiting real-time foliar computer vision feed...</span>'
)

# --- NEW: Replace relay toggles with explicit ON/OFF buttons ---
html = re.sub(
    r'<button class="relay-btn[^"]*" data-relay="(\d+)">[^<]*</button>',
    r'''<div class="flex gap-1">
      <button class="relay-btn-on px-2.5 py-0.5 font-mono text-[9px] font-bold uppercase rounded-lg transition-all bg-white/[0.05] text-muted hover:text-white border border-white/10 shadow-sm cursor-pointer" data-relay="\1">ON</button>
      <button class="relay-btn-off px-2.5 py-0.5 font-mono text-[9px] font-bold uppercase rounded-lg transition-all bg-white/[0.05] text-muted hover:text-white border border-white/10 shadow-sm cursor-pointer" data-relay="\1">OFF</button>
    </div>''',
    html
)

# Overwrite updateRelayUI to handle ON/OFF buttons
relay_js_old = '''    function updateRelayUI(idx) {
      const isActive = relays[idx];
      const led = document.getElementById(`led-relay-${idx}`);
      const btn = document.querySelector(`.relay-btn[data-relay="${idx}"]`);
      if (!led || !btn) return;

      if (isActive) {
        led.className = "w-2 h-2 rounded-full bg-primary glow-dot";
        btn.className = "relay-btn px-2.5 py-0.5 font-mono text-[8px] font-bold uppercase rounded-full transition-all bg-white text-black shadow-sm";
        btn.innerText = `[${idx}] ACTIVE`;
      } else {
        led.className = "w-2 h-2 rounded-full bg-white/20";
        btn.className = "relay-btn px-2.5 py-0.5 font-mono text-[8px] font-bold uppercase rounded-full transition-all bg-white/[0.05] text-muted hover:text-white border border-white/10";
        btn.innerText = `[${idx}] STANDBY`;
      }
    }'''

relay_js_new = '''    function updateRelayUI(idx) {
      const isActive = relays[idx];
      const led = document.getElementById(`led-relay-${idx}`);
      const btnOn = document.querySelector(`.relay-btn-on[data-relay="${idx}"]`);
      const btnOff = document.querySelector(`.relay-btn-off[data-relay="${idx}"]`);
      if (!led || !btnOn || !btnOff) return;

      if (isActive) {
        led.className = "w-2 h-2 rounded-full bg-primary glow-dot";
        btnOn.className = "relay-btn-on px-2.5 py-0.5 font-mono text-[9px] font-bold uppercase rounded-lg transition-all bg-primary text-black shadow-sm cursor-pointer";
        btnOff.className = "relay-btn-off px-2.5 py-0.5 font-mono text-[9px] font-bold uppercase rounded-lg transition-all bg-white/[0.05] text-muted hover:text-white border border-white/10 shadow-sm cursor-pointer";
      } else {
        led.className = "w-2 h-2 rounded-full bg-white/20";
        btnOn.className = "relay-btn-on px-2.5 py-0.5 font-mono text-[9px] font-bold uppercase rounded-lg transition-all bg-white/[0.05] text-muted hover:text-white border border-white/10 shadow-sm cursor-pointer";
        btnOff.className = "relay-btn-off px-2.5 py-0.5 font-mono text-[9px] font-bold uppercase rounded-lg transition-all bg-hazard text-white shadow-sm cursor-pointer";
      }
    }'''

html = html.replace(relay_js_old, relay_js_new)

# Overwrite toggleRelay event listeners
relay_events_old = '''    document.querySelectorAll('.relay-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const r = parseInt(btn.getAttribute('data-relay'), 10);
        toggleRelay(r);
      });
    });'''

relay_events_new = '''    function setRelay(idx, state) {
      if (isEStopLatched) {
        logCli("<span class='text-hazard'>Cannot toggle relays while E-STOP is active!</span>");
        return;
      }
      relays[idx] = state;
      updateRelayUI(idx);
      const st = relays[idx] ? "ACTIVE" : "STANDBY";
      logAudit("RELAY", `Relay ${idx} forced ${st}`, relays[idx] ? "text-primary" : "text-hazard");
      if (typeof socket !== 'undefined' && socket && socket.connected) {
        socket.emit('toggle_relay', { target: 'R' + idx, state: relays[idx] });
      }
    }

    document.querySelectorAll('.relay-btn-on').forEach(btn => {
      btn.addEventListener('click', () => {
        setRelay(parseInt(btn.getAttribute('data-relay'), 10), true);
      });
    });
    document.querySelectorAll('.relay-btn-off').forEach(btn => {
      btn.addEventListener('click', () => {
        setRelay(parseInt(btn.getAttribute('data-relay'), 10), false);
      });
    });'''

html = html.replace(relay_events_old, relay_events_new)

# Write to target locations
destinations = [
    'dist/index.html',
    'dashboard/index.html',
    'public/index.html'
]

for dest in destinations:
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Successfully assembled: {dest} ({len(html)} bytes)")

# Also copy dist/assets to dashboard/assets
if os.path.exists('dist/assets'):
    shutil.copytree('dist/assets', 'dashboard/assets', dirs_exist_ok=True)
    print("Copied dist/assets to dashboard/assets")
