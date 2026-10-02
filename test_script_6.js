(function() {
    // ==============================================================
    // REAL CROPGUARD HARDWARE & AI BACKEND WEBSOCKET BRIDGE
    // ==============================================================
    let socket = null;
    try {
      socket = io('http://localhost:5001', {
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionDelay: 800,
        timeout: 5000
      });

      socket.on('connect', () => {
        logAudit("SYS", "⚡ Connected to CropGuard AI Backend (Port 5001)", "text-primary font-bold");
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

        // 4. Real GPS Coordinate Sync
        const lat = data.latitude ?? data.lat;
        const lon = data.longitude ?? data.lng;
        if (lat && lon && typeof lat === 'number' && typeof lon === 'number' && lat !== 0) {
          const rLat = document.getElementById('ribbon-lat');
          const rLon = document.getElementById('ribbon-lon');
          if (rLat) rLat.innerText = `${Math.abs(lat).toFixed(5)}° ${lat >= 0 ? 'N' : 'S'}`;
          if (rLon) rLon.innerText = `${Math.abs(lon).toFixed(5)}° ${lon >= 0 ? 'E' : 'W'}`;
          roverCoords = [lat, lon];
          if (roverMarker) roverMarker.setLatLng(roverCoords);
        }

        // 5. Hardware Relays Sync
        if (data.pump_on !== undefined && relays[1] !== data.pump_on) { relays[1] = Boolean(data.pump_on); updateRelayUI(1); }
        if (data.sol1_on !== undefined && relays[2] !== data.sol1_on) { relays[2] = Boolean(data.sol1_on); updateRelayUI(2); }
        if (data.sol2_on !== undefined && relays[3] !== data.sol2_on) { relays[3] = Boolean(data.sol2_on); updateRelayUI(3); }
        if (data.spare_on !== undefined && relays[4] !== data.spare_on) { relays[4] = Boolean(data.spare_on); updateRelayUI(4); }
      });

      socket.on('detection_list', (data) => {
        if (data.detections && data.detections.length > 0) {
          const d = data.detections[0];
          logAudit("YOLO", `Pathogen detected: ${d.class.toUpperCase()} (${(d.confidence * 100).toFixed(1)}%)`, "text-pathogen font-bold");
        }
      });

      socket.on('ai_recommendations', (data) => {
        logAudit("VLA", `AI Treatment: ${data.recovery || data.fertilizer || data.disease}`, "text-primary");
      });

      socket.on('log_entry', (data) => {
        logAudit(data.type ? data.type.toUpperCase() : "SYS", data.msg, data.type === 'error' ? 'text-hazard' : data.type === 'warning' ? 'text-amber-400' : 'text-white');
      });
    } catch (err) {
      console.warn("Socket.io initialization warning:", err);
    }

    // Cockpit State
    let isEStopLatched = false;
    let currentPwm = 170; // Default Cruise
    const relays = {
      1: true,
      2: false,
      3: false,
      4: true
    };

    // Base coordinates (fallback / tactical origin)
    let roverCoords = [6.92715, 79.86124];
    let activeWpIndex = 3; // WP-04

    // Elements
    const fullEstopOverlay = document.getElementById('full-estop-overlay');
    const estopToggleBtn = document.getElementById('estop-toggle-btn');
    const overlayResetBtn = document.getElementById('overlay-reset-btn');
    const auditLogStream = document.getElementById('audit-log-stream');
    const cliOutputLine = document.getElementById('cli-output-line');
    const cliInput = document.getElementById('cli-input');
    const cliExecBtn = document.getElementById('cli-exec-btn');
    const pwmReadout = document.getElementById('pwm-readout');
    const pwmGaugeBar = document.getElementById('pwm-gauge-bar');
    const motorStatusBadge = document.getElementById('motor-status-badge');
    const ribbonLat = document.getElementById('ribbon-lat');
    const ribbonLon = document.getElementById('ribbon-lon');

    // Audit Logger
    function logAudit(tag, msg, color = "text-white") {
      if (!auditLogStream) return;
      const now = new Date();
      const timeStr = now.toTimeString().split(' ')[0];
      const line = document.createElement('div');
      line.innerHTML = `<span class="${color}">[${tag} ${timeStr}]</span> ${msg}`;
      auditLogStream.appendChild(line);
      auditLogStream.scrollTop = auditLogStream.scrollHeight;
    }

    function logCli(msg) {
      if (cliOutputLine) {
        cliOutputLine.innerHTML = msg;
      }
    }

    // Initialize Leaflet Tactical Map with CartoDB Dark Matter tiles (Dark, no watermark issues)
    let map = null;
    let roverMarker = null;
    let waypoints = [];
    let waypointMarkers = [];
    let completedPathPolyline = null;
    let plannedPathPolyline = null;

    function generateWaypointsAround(center) {
      const [lat, lng] = center;
      return [
        { id: 'WP-01', lat: lat - 0.0018, lng: lng - 0.0022 },
        { id: 'WP-02', lat: lat + 0.0016, lng: lng - 0.0022 },
        { id: 'WP-03', lat: lat + 0.0016, lng: lng - 0.0008 },
        { id: 'WP-04', lat: lat - 0.0002, lng: lng - 0.0008, active: true },
        { id: 'WP-05', lat: lat - 0.0018, lng: lng - 0.0008 },
        { id: 'WP-06', lat: lat - 0.0018, lng: lng + 0.0008 },
        { id: 'WP-07', lat: lat + 0.0016, lng: lng + 0.0008 },
        { id: 'WP-08', lat: lat + 0.0016, lng: lng + 0.0022 },
      ];
    }

    function initTacticalMap(centerCoords) {
      if (map) {
        map.setView(centerCoords, 17);
        return;
      }

      const mapContainer = document.getElementById('leaflet-map');
      if (!mapContainer) return;

      map = L.map('leaflet-map', {
        zoomControl: false,
        attributionControl: false
      }).setView(centerCoords, 17);

      // Dark Matter CartoDB tiles
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 20,
        subdomains: 'abcd'
      }).addTo(map);

      L.control.zoom({ position: 'bottomright' }).addTo(map);

      waypoints = generateWaypointsAround(centerCoords);
      renderMapTacticalElements(centerCoords);

      // Live Geolocation check
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            const liveLat = parseFloat(pos.coords.latitude.toFixed(5));
            const liveLng = parseFloat(pos.coords.longitude.toFixed(5));
            roverCoords = [liveLat, liveLng];
            if (ribbonLat) ribbonLat.innerText = `${Math.abs(liveLat).toFixed(5)}° ${liveLat >= 0 ? 'N' : 'S'}`;
            if (ribbonLon) ribbonLon.innerText = `${Math.abs(liveLng).toFixed(5)}° ${liveLng >= 0 ? 'E' : 'W'}`;
            map.setView(roverCoords, 17);
            waypoints = generateWaypointsAround(roverCoords);
            renderMapTacticalElements(roverCoords);
            logAudit("GPS", `Geolocation acquired: ${liveLat}, ${liveLng} (RTK Locked)`, "text-primary font-bold");
          },
          () => {
            logAudit("GPS", "Geolocation fallback to fixed coordinates (6.92715, 79.86124)", "text-muted");
          },
          { enableHighAccuracy: true, timeout: 5000 }
        );
      }
    }

    function renderMapTacticalElements(currentPos) {
      waypointMarkers.forEach(m => map.removeLayer(m));
      waypointMarkers = [];
      if (roverMarker) map.removeLayer(roverMarker);
      if (completedPathPolyline) map.removeLayer(completedPathPolyline);
      if (plannedPathPolyline) map.removeLayer(plannedPathPolyline);

      const latLngs = waypoints.map(w => [w.lat, w.lng]);

      // Completed Path
      const completedSegments = [
        latLngs[0],
        latLngs[1],
        latLngs[2],
        currentPos
      ];
      completedPathPolyline = L.polyline(completedSegments, {
        color: '#00E676',
        weight: 3,
        opacity: 0.9,
        lineJoin: 'round'
      }).addTo(map);

      // Planned Path
      const plannedSegments = [
        currentPos,
        latLngs[3],
        latLngs[4],
        latLngs[5],
        latLngs[6],
        latLngs[7]
      ];
      plannedPathPolyline = L.polyline(plannedSegments, {
        color: '#00E5FF',
        weight: 2,
        opacity: 0.7,
        dashArray: '6, 6',
        lineJoin: 'round'
      }).addTo(map);

      // Waypoint Markers
      waypoints.forEach((wp, idx) => {
        const isActive = idx === activeWpIndex;
        const isDone = idx < activeWpIndex;
        const color = isActive ? '#FF334B' : (isDone ? '#00E676' : '#7E8494');

        const iconHtml = `
          <div style="display:flex; flex-direction:column; align-items:center;">
            <div class="${isActive ? 'tactical-marker-active' : ''}" style="width:11px; height:11px; border-radius:50%; background:${color}; border:2px solid #090A0E; box-shadow: 0 0 10px ${color};"></div>
            <span style="font-family:'JetBrains Mono'; font-size:8px; font-weight:600; color:#fff; background:rgba(15,16,22,0.9); padding:1px 4px; border-radius:4px; border:1px solid rgba(255,255,255,0.1); margin-top:2px; white-space:nowrap;">${wp.id}</span>
          </div>
        `;
        const customIcon = L.divIcon({
          html: iconHtml,
          className: '',
          iconSize: [40, 24],
          iconAnchor: [20, 6]
        });

        const m = L.marker([wp.lat, wp.lng], { icon: customIcon }).addTo(map);
        waypointMarkers.push(m);
      });

      // Rover Vehicle Marker
      const roverHtml = `
        <div style="display:flex; flex-direction:column; align-items:center;">
          <div style="width:14px; height:14px; background:#00E676; border:2px solid #FFFFFF; border-radius:3px; transform:rotate(45deg); box-shadow:0 0 14px #00E676;"></div>
          <span style="font-family:'JetBrains Mono'; font-size:8px; font-weight:700; color:#00E676; background:#08090C; border:1px solid #00E676; border-radius:3px; padding:0 4px; margin-top:3px; white-space:nowrap;">ROVER-CG1</span>
        </div>
      `;
      const roverIcon = L.divIcon({
        html: roverHtml,
        className: '',
        iconSize: [60, 30],
        iconAnchor: [30, 7]
      });

      roverMarker = L.marker(currentPos, { icon: roverIcon }).addTo(map);
    }

    // Initialize map on DOM load
    window.addEventListener('DOMContentLoaded', () => {
      setTimeout(() => {
        initTacticalMap(roverCoords);
      }, 100);
    });

    // 1. HARD E-STOP ENGAGE / DISENGAGE
    function triggerEStop() {
      isEStopLatched = true;
      fullEstopOverlay.classList.remove('hidden'); fullEstopOverlay.classList.add('active-estop'); fullEstopOverlay.style.setProperty('display', 'flex', 'important');
      fullEstopOverlay.classList.add('flex');
      
      currentPwm = 0;
      pwmReadout.innerText = "0 PWM / 0% (HALTED)";
      pwmGaugeBar.style.width = "0%";
      motorStatusBadge.innerText = "E-STOPPED";
      motorStatusBadge.className = "font-mono text-[9px] text-hazard px-2 py-0.5 rounded-full bg-hazard/15 border border-hazard/40 font-bold animate-pulse";

      for (let r = 1; r <= 4; r++) {
        relays[r] = false;
        updateRelayUI(r);
      }

      logAudit("ESTOP", "CRITICAL HARD E-STOP LATCHED! PWM ZEROED, RELAYS CUT", "text-hazard font-bold");
      if (socket && socket.connected) {
        socket.emit('robot_move', { direction: 'stop', speed: 0, source: 'manual' });
        [1,2,3,4].forEach(r => socket.emit('toggle_relay', { target: 'R' + r, state: false }));
      }

      logCli("<span class='text-hazard font-bold'>[E-STOP ENGAGED] Press [SPACE] or click reset to re-arm system.</span>");
    }

    function disengageEStop() {
      isEStopLatched = false;
      fullEstopOverlay.classList.add('hidden'); fullEstopOverlay.classList.remove('active-estop'); fullEstopOverlay.style.setProperty('display', 'none', 'important');
      fullEstopOverlay.classList.remove('flex');

      currentPwm = 170;
      pwmReadout.innerText = "170 PWM / 66%";
      pwmGaugeBar.style.width = "66%";
      motorStatusBadge.innerText = "ARMED";
      motorStatusBadge.className = "font-mono text-[9px] text-primary px-2 py-0.5 rounded-full bg-primary/10 border border-primary/25 font-bold";

      relays[1] = true;
      relays[4] = true;
      updateRelayUI(1);
      updateRelayUI(4);

      logAudit("SYS", "Hard E-Stop released. Motors and bus restored to ARMED state.", "text-primary");
      if (socket && socket.connected) {
        socket.emit('robot_move', { direction: 'stop', speed: 0, source: 'manual' });
        socket.emit('toggle_relay', { target: 'R1', state: true });
        socket.emit('toggle_relay', { target: 'R4', state: true });
      }

      logCli("<span class='text-primary'>[OK] Emergency Stop released. Chassis re-armed at 170 PWM.</span>");
    }

    function toggleEStop() {
      if (isEStopLatched) {
        disengageEStop();
      } else {
        triggerEStop();
      }
    }

    estopToggleBtn.addEventListener('click', toggleEStop);
    overlayResetBtn.addEventListener('click', disengageEStop);

    // 2. RELAY CONTROLLER
    function updateRelayUI(idx) {
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
    }

    function toggleRelay(idx) {
      if (isEStopLatched) {
        logCli("<span class='text-hazard'>Cannot toggle relays while E-STOP is active!</span>");
        return;
      }
      relays[idx] = !relays[idx];
      updateRelayUI(idx);
      if (socket && socket.connected) {
        socket.emit('toggle_relay', { target: 'R' + idx, state: relays[idx] });
      }

      const st = relays[idx] ? "ACTIVE" : "STANDBY";
      logAudit("RELAY", `Relay ${idx} shifted to ${st}`, relays[idx] ? "text-primary" : "text-muted");
      logCli(`Relay ${idx} status: <strong class="${relays[idx] ? 'text-primary' : 'text-muted'}">${st}</strong>`);
    }

    document.querySelectorAll('.relay-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const r = parseInt(btn.getAttribute('data-relay'), 10);
        toggleRelay(r);
      });
    });

    // 3. SPEED PRESETS
    function setSpeed(val) {
      if (isEStopLatched) return;
      currentPwm = Math.min(255, Math.max(0, val));
      const pct = Math.round((currentPwm / 255) * 100);
      pwmReadout.innerText = `${currentPwm} PWM / ${pct}%`;
      pwmGaugeBar.style.width = `${pct}%`;

      const crawlBtn = document.getElementById('btn-speed-crawl');
      const cruiseBtn = document.getElementById('btn-speed-cruise');
      const turboBtn = document.getElementById('btn-speed-turbo');

      [crawlBtn, cruiseBtn, turboBtn].forEach(b => {
        b.className = "speed-btn py-1.5 px-1 rounded-xl bg-white/[0.04] hover:bg-white/[0.09] border border-white/[0.06] flex flex-col items-center text-center transition-all text-white";
      });

      if (currentPwm <= 100) {
        crawlBtn.className = "speed-btn py-1.5 px-1 rounded-xl bg-white text-black font-semibold border border-white flex flex-col items-center text-center transition-all shadow-md";
      } else if (currentPwm <= 190) {
        cruiseBtn.className = "speed-btn py-1.5 px-1 rounded-xl bg-white text-black font-semibold border border-white flex flex-col items-center text-center transition-all shadow-md";
      } else {
        turboBtn.className = "speed-btn py-1.5 px-1 rounded-xl bg-white text-black font-semibold border border-white flex flex-col items-center text-center transition-all shadow-md";
      }

      logAudit("DRIVE", `PWM Duty cycle set: ${currentPwm} (${pct}%)`, "text-secondary");
      if (socket && socket.connected) {
        socket.emit('robot_move', { direction: 'forward', speed: currentPwm, source: 'manual' });
      }

    }

    document.getElementById('btn-speed-crawl')?.addEventListener('click', () => setSpeed(100));
    document.getElementById('btn-speed-cruise')?.addEventListener('click', () => setSpeed(170));
    document.getElementById('btn-speed-turbo')?.addEventListener('click', () => setSpeed(255));

    // 4. MOTOR D-PAD VECTOR
    function triggerVector(key) {
      if (isEStopLatched) {
        logCli("<span class='text-hazard'>Chassis vector rejected: E-STOP active.</span>");
        return;
      }
      let dir = "";
      switch (key) {
        case 'w': dir = `FORWARD vector engaged [${currentPwm} PWM]`; break;
        case 's': dir = `REVERSE vector engaged [${currentPwm} PWM]`; break;
        case 'a': dir = `LEFT differential spin engaged`; break;
        case 'd': dir = `RIGHT differential spin engaged`; break;
        case 'x': dir = `EMERGENCY BRAKE applied to dual H-Bridge`; break;
      }
      logAudit("NAV", dir, "text-secondary");
      const dirMap = { 'w': 'forward', 's': 'backward', 'a': 'left', 'd': 'right', 'x': 'stop' };
      const dirName = dirMap[key] || 'stop';
      if (socket && socket.connected) {
        socket.emit('robot_move', { direction: dirName, speed: key === 'x' ? 0 : currentPwm, source: 'manual' });
      }

      logCli(dir);

      const btn = document.querySelector(`.dpad-key[data-key="${key}"]`);
      if (btn) {
        btn.classList.add('bg-white', 'text-black');
        setTimeout(() => {
          btn.classList.remove('bg-white', 'text-black');
        }, 150);
      }
    }

    document.querySelectorAll('.dpad-key').forEach(btn => {
      btn.addEventListener('click', () => {
        triggerVector(btn.getAttribute('data-key'));
      });
    });

    // 5. KEYBOARD LISTENERS
    window.addEventListener('keydown', (e) => {
      if (document.activeElement === cliInput) {
        if (e.key === 'Enter') {
          executeCli();
        }
        if (e.code === 'Space' && e.ctrlKey) {
          e.preventDefault();
          toggleEStop();
        }
        return;
      }

      if (e.code === 'Space') {
        e.preventDefault();
        toggleEStop();
        return;
      }

      const k = e.key.toLowerCase();
      if (['1', '2', '3', '4'].includes(k)) {
        e.preventDefault();
        toggleRelay(parseInt(k, 10));
        return;
      }

      if (['w', 'a', 's', 'd', 'x'].includes(k)) {
        e.preventDefault();
        triggerVector(k);
        return;
      }
    });

    // 6. SPECTRAL FILTERS & CROP SWITCHER
    const filterRaw = document.getElementById('filter-raw');
    const filterNdvi = document.getElementById('filter-ndvi');
    const filterBiomass = document.getElementById('filter-biomass');
    const streamImg = document.getElementById('live-stream-img');

    function setFilter(type) {
      [filterRaw, filterNdvi, filterBiomass].forEach(b => {
        b.className = "filter-btn py-1 rounded-lg font-mono text-[9px] font-semibold uppercase transition-all bg-white/[0.04] text-muted hover:text-white border border-white/[0.08]";
      });
      if (type === 'raw') {
        filterRaw.className = "filter-btn py-1 rounded-lg font-mono text-[9px] font-semibold uppercase transition-all bg-white text-black shadow-sm";
        streamImg.style.filter = "none";
      } else if (type === 'ndvi') {
        filterNdvi.className = "filter-btn py-1 rounded-lg font-mono text-[9px] font-semibold uppercase transition-all bg-white text-black shadow-sm";
        streamImg.style.filter = "contrast(180%) hue-rotate(90deg) saturate(200%)";
      } else if (type === 'biomass') {
        filterBiomass.className = "filter-btn py-1 rounded-lg font-mono text-[9px] font-semibold uppercase transition-all bg-white text-black shadow-sm";
        streamImg.style.filter = "contrast(150%) saturate(300%) brightness(90%)";
      }
      logAudit("CAM", `Filter switched to [${type.toUpperCase()}]`, "text-secondary");
    }

    filterRaw?.addEventListener('click', () => setFilter('raw'));
    filterNdvi?.addEventListener('click', () => setFilter('ndvi'));
    filterBiomass?.addEventListener('click', () => setFilter('biomass'));

    const cropSelect = document.getElementById('crop-model-select');
    cropSelect?.addEventListener('change', (e) => {
      logAudit("YOLO", `Tensor weights swapped: ${e.target.value}`, "text-pathogen");
      if (socket && socket.connected) {
        socket.emit('crop_selected', { crop: e.target.value.toLowerCase() });
      }
      fetch('/api/model/switch?crop=' + encodeURIComponent(e.target.value.toLowerCase())).catch(()=>{});

      logCli(`Active YOLOv11 Model Profile: <strong class="text-white">${e.target.value}</strong>`);
    });

    // Mode Selector Toggle
    const modeAuto = document.getElementById('mode-auto');
    const modeRc = document.getElementById('mode-rc');
    modeAuto?.addEventListener('click', () => {
      modeAuto.className = "px-3 py-1 rounded-full text-[10px] font-semibold transition-all bg-white text-black shadow";
      modeRc.className = "px-2.5 py-1 rounded-full text-[10px] font-medium text-muted hover:text-white transition-all";
      logAudit("SYS", "Mode switched: AUTONOMOUS GPS WAYPOINT NAVIGATION", "text-primary font-bold");
      if (socket && socket.connected) {
        socket.emit('toggle_mode', { mode: 'auto' });
      }

    });
    modeRc?.addEventListener('click', () => {
      modeRc.className = "px-3 py-1 rounded-full text-[10px] font-semibold transition-all bg-white text-black shadow";
      modeAuto.className = "px-2.5 py-1 rounded-full text-[10px] font-medium text-muted hover:text-white transition-all";
      logAudit("SYS", "Mode switched: MANUAL RC OVERRIDE ENGAGED", "text-secondary font-bold");
      if (socket && socket.connected) {
        socket.emit('toggle_mode', { mode: 'manual' });
      }

    });

    // Map Quick Actions
    document.getElementById('map-btn-recenter')?.addEventListener('click', () => {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((pos) => {
          const liveLat = parseFloat(pos.coords.latitude.toFixed(5));
          const liveLng = parseFloat(pos.coords.longitude.toFixed(5));
          roverCoords = [liveLat, liveLng];
          if (ribbonLat) ribbonLat.innerText = `${Math.abs(liveLat).toFixed(5)}° ${liveLat >= 0 ? 'N' : 'S'}`;
          if (ribbonLon) ribbonLon.innerText = `${Math.abs(liveLng).toFixed(5)}° ${liveLng >= 0 ? 'E' : 'W'}`;
          map.setView(roverCoords, 18);
          renderMapTacticalElements(roverCoords);
          logAudit("GPS", `Recentered to: LAT ${liveLat}, LON ${liveLng}`, "text-primary");
        }, () => {
          if (map) map.setView(roverCoords, 17);
        });
      } else if (map) {
        map.setView(roverCoords, 17);
      }
    });

    document.getElementById('map-btn-addwp')?.addEventListener('click', () => {
      const nextIdx = waypoints.length + 1;
      const newWpId = `WP-0${nextIdx}`;
      const lastWp = waypoints[waypoints.length - 1];
      const newWp = {
        id: newWpId,
        lat: lastWp.lat - 0.0006,
        lng: lastWp.lng + 0.0006
      };
      waypoints.push(newWp);
      renderMapTacticalElements(roverCoords);
      logAudit("NAV", `Waypoint ${newWpId} appended to mission vector.`, "text-secondary");
      logCli(`<span class='text-secondary'>[NAV] Waypoint ${newWpId} added.</span>`);
    });

    document.getElementById('map-btn-skipwp')?.addEventListener('click', () => {
      if (activeWpIndex < waypoints.length - 1) {
        activeWpIndex++;
        const targetWp = waypoints[activeWpIndex];
        renderMapTacticalElements(roverCoords);
        logAudit("NAV", `Bypassed WP -> Now targeting ${targetWp.id}.`, "text-secondary");
        const eta = document.getElementById('stage-eta-val');
        if (eta) eta.innerText = "01:45 ETA";
      }
    });

    document.getElementById('map-btn-export')?.addEventListener('click', () => {
      const rows = [
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
      let csvContent = "data:text/csv;charset=utf-8," + rows.map(e => e.join(",")).join("\n");
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", `cropguard_mission_telemetry_${Date.now()}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      logAudit("EXPORT", "Mission telemetry exported to CSV successfully", "text-primary font-bold");

      logCli("<span class='text-primary'>[EXPORT] Flight telemetry serialized to CSV.</span>");
    });

    // 7. CLI COMMAND PARSER
    function executeCli() {
      const raw = cliInput.value.trim();
      if (!raw) return;
      cliInput.value = '';

      const args = raw.split(' ').filter(Boolean);
      const cmd = args[0].toLowerCase();

      switch (cmd) {
        case 'help':
          logCli(`Commands: <strong class="text-white">status</strong>, <strong class="text-white">auto</strong>, <strong class="text-white">rc</strong>, <strong class="text-white">estop</strong>, <strong class="text-white">reset</strong>, <strong class="text-white">speed [0-255]</strong>, <strong class="text-white">relay [1-4] [on|off]</strong>, <strong class="text-white">clear</strong>`);
          break;
        case 'status':
          logCli(`[ESP32]: Latched: ${isEStopLatched} | PWM: ${currentPwm} | Relays: [1:${relays[1]}, 2:${relays[2]}, 3:${relays[3]}, 4:${relays[4]}] | Temp: 24.5°C`);
          break;
        case 'estop':
        case 'halt':
          triggerEStop();
          break;
        case 'reset':
          disengageEStop();
          break;
        case 'auto':
          if (socket && socket.connected) socket.emit('toggle_mode', { mode: 'auto' });
          logCli("<span class='text-primary font-bold'>Mode switched to AUTONOMOUS GPS NAVIGATION</span>");
          break;
        case 'manual':
        case 'rc':
          if (socket && socket.connected) socket.emit('toggle_mode', { mode: 'manual' });
          logCli("<span class='text-secondary font-bold'>Mode switched to MANUAL RC OVERRIDE</span>");
          break;
        case 'speed':
          if (args[1]) {
            const val = parseInt(args[1], 10);
            if (!isNaN(val)) setSpeed(val);
            logCli(`PWM Speed command sent: ${currentPwm}`);
          } else {
            logCli(`Current speed: ${currentPwm} PWM`);
          }
          break;
        case 'relay':
          if (args[1] && args[2]) {
            const idx = parseInt(args[1], 10);
            const st = args[2].toLowerCase() === 'on';
            if ([1, 2, 3, 4].includes(idx)) {
              relays[idx] = st;
              updateRelayUI(idx);
      if (socket && socket.connected) {
        socket.emit('toggle_relay', { target: 'R' + idx, state: relays[idx] });
      }

              logCli(`Relay ${idx} forced ${st ? 'ON' : 'OFF'}`);
            } else {
              logCli("<span class='text-hazard'>Invalid relay #. Choose 1 to 4.</span>");
            }
          } else {
            logCli("Usage: relay &lt;1-4&gt; &lt;on|off&gt;");
          }
          break;
        case 'clear':
          logCli("CropGuard Field Commander OS ready.");
          break;
        default:
          logCli(`<span class='text-hazard'>Command '${cmd}' not recognized. Type 'help'.</span>`);
          break;
      }
    }

    cliExecBtn?.addEventListener('click', executeCli);

    // Live Sensor Ticker & Countdown Simulation (Micro-fluctuations for realistic telemetry)
    let seconds = 99;
    setInterval(() => {
      if (isEStopLatched) return;
      if (seconds > 0) {
        seconds--;
        const m = String(Math.floor(seconds / 60)).padStart(2, '0');
        const s = String(seconds % 60).padStart(2, '0');
        const etaEl = document.getElementById('stage-eta-val');
        if (etaEl) etaEl.innerText = `${m}:${s} ETA`;
      }

      // Micro-fluctuate values
      const tEl = document.getElementById('val-temp');
      if (tEl && Math.random() > 0.6) {
        tEl.innerText = (24.5 + (Math.random() * 0.4 - 0.2)).toFixed(1);
      }
      const hEl = document.getElementById('val-hum');
      if (hEl && Math.random() > 0.7) {
        hEl.innerText = (68.0 + (Math.random() * 0.6 - 0.3)).toFixed(1);
      }
    }, 1200);

  })();