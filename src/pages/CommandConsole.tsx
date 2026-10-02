import { BACKEND_URL } from '../backendUrl';
import HardwareTelemetry from '../components/HardwareTelemetry';
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useSocketData, WeatherPayload, WeatherAlertItem, DiseaseRiskData, GPSStatusData, ObstacleStatus, AIAnalysisReport } from '../hooks/useSocketData';
import { SensorData, DiseaseItem, Recommendation, LogEntry } from '../App';

declare const L: any; // Leaflet global loaded via index.html

interface CommandConsoleProps {
  selectedCrop?: string;
  mode?: 'auto' | 'manual';
}

interface Waypoint {
  id: string;
  lat: number;
  lng: number;
  active?: boolean;
}

const CROPS = [
  { id: 'tomato', name: 'Tomato', weights: 'tomato.pt' },
  { id: 'potato', name: 'Potato', weights: 'potato.pt' },
  { id: 'rice', name: 'Rice', weights: 'rice.pt' },
  { id: 'corn', name: 'Corn', weights: 'corn.pt' },
  { id: 'brinjal', name: 'Brinjal', weights: 'brinjai.pt' },
  { id: 'cabbage', name: 'Cabbage', weights: 'cabbage_best.pt' },
  { id: 'capsicum', name: 'Capsicum', weights: 'capsium.pt' },
  { id: 'carrot', name: 'Carrot', weights: 'carrot_best.pt' },
  { id: 'cauliflower', name: 'Cauliflower', weights: 'cauliflower_best.pt' },
  { id: 'chilli', name: 'Chilli', weights: 'chilli.pt' },
  { id: 'lettuce', name: 'Lettuce', weights: 'lettuce_best.pt' },
  { id: 'mushroom', name: 'Mushroom', weights: 'mushroom_best.pt' },
  { id: 'radish', name: 'Radish', weights: 'radish_best.pt' },
  { id: 'rose', name: 'Rose', weights: 'rose_best.pt' },
  { id: 'tea', name: 'Tea', weights: 'tea_best.pt' },
  { id: 'anthurium', name: 'Anthurium', weights: 'Anthurium_best.pt' },
];

export default function CommandConsole({ selectedCrop = 'tomato', mode = 'manual' }: CommandConsoleProps) {
  // State
  const [currentCrop, setCurrentCrop] = useState<string>(selectedCrop);
  const [activeMode, setActiveMode] = useState<'auto' | 'manual'>(mode);
  const [isEStopLatched, setIsEStopLatched] = useState<boolean>(false);
  const [currentPwm, setCurrentPwm] = useState<number>(170); // Default Cruise
  const [activeFilter, setActiveFilter] = useState<'raw' | 'ndvi' | 'biomass'>('raw');
  const [cliInputText, setCliInputText] = useState<string>('');
  const [cliOutput, setCliOutput] = useState<string>('DEM3T3R V1 Tactical Field Commander OS initialized. Type "help" for command matrix.');
  const [etaSeconds, setEtaSeconds] = useState<number>(99);
  const [activeWpIndex, setActiveWpIndex] = useState<number>(3); // WP-04
  const [streamError, setStreamError] = useState<boolean>(false);

  // Relay states (1-indexed for hardware consistency: R1=Pump, R2=SoilProbeA, R3=SoilProbeB, R4=SprayerBoom)
  const [relays, setRelays] = useState<Record<number, boolean>>({
    1: false,
    2: false,
    3: false,
    4: false,
  });

  // Telemetry & Hardware State
  const [sensorData, setSensorData] = useState<SensorData>({
    temperature: 0, humidity: 0, pressure: 0, light: 0,
    uvVoltage: 0, soilMoisture: 0, fix: false,
  });

  const [diseases, setDiseases] = useState<DiseaseItem[]>([]);
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [connected, setConnected] = useState<boolean>(false);
  const [esp32Connected, setEsp32Connected] = useState<boolean>(false);
  const [logs, setLogs] = useState<Array<{ id: number; tag: string; msg: string; color: string; time: string }>>([]);

  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<any>(null);
  const roverMarkerRef = useRef<any>(null);
  const waypointMarkersRef = useRef<any[]>([]);
  const completedPolylineRef = useRef<any>(null);
  const plannedPolylineRef = useRef<any>(null);
  const auditScrollRef = useRef<HTMLDivElement | null>(null);

  // Helper log function
  const addLog = useCallback((msg: string, type: LogEntry['type'] = 'info') => {
    const now = new Date();
    const time = now.toTimeString().split(' ')[0];
    let tag = 'SYS';
    let color = 'text-white';
    if (type === 'success') { tag = 'OK'; color = 'text-primary'; }
    else if (type === 'error') { tag = 'ERR'; color = 'text-hazard'; }
    else if (type === 'warning') { tag = 'WARN'; color = 'text-amber-400'; }

    setLogs((prev) => [...prev.slice(-49), { id: Date.now() + Math.random(), tag, msg, color, time }]);
  }, []);

  const {
    selectCrop,
    sendRobotControl,
    sendRelayToggle,
    emergencyStop,
    resetEmergencyStop,
    toggleMode: sendToggleMode,
  } = useSocketData(
    setSensorData,
    setDiseases,
    setRecommendation,
    setConnected,
    () => {},
    addLog,
    currentCrop,
    (m) => setActiveMode(m),
    undefined,
    undefined,
    undefined,
    undefined,
    undefined,
    undefined,
    undefined,
    setEsp32Connected,
    undefined,
    setIsEStopLatched
  );

  // Auto scroll audit logs
  useEffect(() => {
    if (auditScrollRef.current) {
      auditScrollRef.current.scrollTop = auditScrollRef.current.scrollHeight;
    }
  }, [logs]);

  // Sync sensor relays to state if present
  useEffect(() => {
    setRelays((prev) => ({
      1: sensorData.pump_on !== undefined ? sensorData.pump_on : prev[1],
      2: sensorData.sol1_on !== undefined ? sensorData.sol1_on : prev[2],
      3: sensorData.sol2_on !== undefined ? sensorData.sol2_on : prev[3],
      4: sensorData.spare_on !== undefined ? sensorData.spare_on : prev[4],
    }));
  }, [sensorData.pump_on, sensorData.sol1_on, sensorData.sol2_on, sensorData.spare_on]);

  // 1. Waypoint generation helper
  const generateWaypoints = useCallback((lat: number, lng: number): Waypoint[] => {
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
  }, []);

  const [waypoints, setWaypoints] = useState<Waypoint[]>(() =>
    generateWaypoints(sensorData.latitude || 6.92715, sensorData.longitude || 79.86124)
  );

  // 2. Leaflet Tactical Map Initializer
  useEffect(() => {
    if (typeof L === 'undefined' || !mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      if ((mapContainerRef.current as any)._leaflet_id) {
        delete (mapContainerRef.current as any)._leaflet_id;
      }

      const initLat = sensorData.latitude || 6.92715;
      const initLng = sensorData.longitude || 79.86124;

      try {
        const map = L.map(mapContainerRef.current, {
          zoomControl: false,
          attributionControl: false,
        }).setView([initLat, initLng], 17);

        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
          maxZoom: 20,
          subdomains: 'abcd',
        }).addTo(map);

        L.control.zoom({ position: 'bottomright' }).addTo(map);
        mapInstanceRef.current = map;

        // Geolocation sync on load
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(
            (pos) => {
              const liveLat = parseFloat(pos.coords.latitude.toFixed(5));
              const liveLng = parseFloat(pos.coords.longitude.toFixed(5));
              setSensorData((prev) => ({ ...prev, latitude: liveLat, longitude: liveLng }));
              try { map.setView([liveLat, liveLng], 17); } catch (_) {}
              const newWps = generateWaypoints(liveLat, liveLng);
              setWaypoints(newWps);
              addLog(`GPS RTK Position Locked: ${liveLat}°, ${liveLng}°`, 'success');
            },
            () => {
              addLog('GPS using default field origin (6.92715° N, 79.86124° E)', 'info');
            },
            { enableHighAccuracy: true, timeout: 5000 }
          );
        }
      } catch (err) {
        console.warn('[Leaflet] Initialization handled:', err);
      }
    }

    return () => {
      if (mapInstanceRef.current) {
        try {
          mapInstanceRef.current.remove();
        } catch (_) {}
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update map tactical layers when coordinates or waypoints change
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || typeof L === 'undefined') return;

    try {
      const currentPos: [number, number] = [sensorData.latitude || 6.92715, sensorData.longitude || 79.86124];

      // Remove old layers
      waypointMarkersRef.current.forEach((m) => {
        try { map.removeLayer(m); } catch (_) {}
      });
      waypointMarkersRef.current = [];
      if (roverMarkerRef.current) { try { map.removeLayer(roverMarkerRef.current); } catch (_) {} }
      if (completedPolylineRef.current) { try { map.removeLayer(completedPolylineRef.current); } catch (_) {} }
      if (plannedPolylineRef.current) { try { map.removeLayer(plannedPolylineRef.current); } catch (_) {} }

    const latLngs = waypoints.map((w) => [w.lat, w.lng] as [number, number]);

    if (latLngs.length >= 3) {
      // Completed Polyline
      const completedSegments = [latLngs[0], latLngs[1], latLngs[2], currentPos];
      completedPolylineRef.current = L.polyline(completedSegments, {
        color: '#00E676',
        weight: 3,
        opacity: 0.9,
        lineJoin: 'round',
      }).addTo(map);

      // Planned Polyline
      const plannedSegments = [currentPos, ...latLngs.slice(3)];
      plannedPolylineRef.current = L.polyline(plannedSegments, {
        color: '#00E5FF',
        weight: 2,
        opacity: 0.7,
        dashArray: '6, 6',
        lineJoin: 'round',
      }).addTo(map);
    }

    // Waypoints markers
    waypoints.forEach((wp, idx) => {
      const isActive = idx === activeWpIndex;
      const isDone = idx < activeWpIndex;
      const color = isActive ? '#FF334B' : isDone ? '#00E676' : '#7E8494';

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
        iconAnchor: [20, 6],
      });

      const m = L.marker([wp.lat, wp.lng], { icon: customIcon }).addTo(map);
      waypointMarkersRef.current.push(m);
    });

    // Rover Marker
    const roverHtml = `
      <div style="display:flex; flex-direction:column; align-items:center;">
        <div style="width:14px; height:14px; background:#00E676; border:2px solid #FFFFFF; border-radius:3px; transform:rotate(${sensorData.heading || 45}deg); box-shadow:0 0 14px #00E676; transition: transform 0.3s ease;"></div>
        <span style="font-family:'JetBrains Mono'; font-size:8px; font-weight:700; color:#00E676; background:#08090C; border:1px solid #00E676; border-radius:3px; padding:0 4px; margin-top:3px; white-space:nowrap;">ROVER-CG1</span>
      </div>
    `;
    const roverIcon = L.divIcon({
      html: roverHtml,
      className: '',
      iconSize: [60, 30],
      iconAnchor: [30, 7],
    });

    roverMarkerRef.current = L.marker(currentPos, { icon: roverIcon }).addTo(map);
    } catch (e) {
      console.warn('[Leaflet] Layer update handled:', e);
    }
  }, [waypoints, activeWpIndex, sensorData.latitude, sensorData.longitude, sensorData.heading]);

  // 3. E-STOP Handlers
  const triggerEStop = useCallback(() => {
    setIsEStopLatched(true);
    emergencyStop();
    addLog('Stop requested. Verify device telemetry and physical emergency stop.', 'error');
    setCliOutput('<span class="text-hazard font-bold">[E-STOP ENGAGED] Press [SPACE] or click Reset to re-arm.</span>');
  }, [addLog, emergencyStop]);

  const disengageEStop = useCallback(() => {
    resetEmergencyStop();
    setCurrentPwm(170);

    addLog('Dashboard stop released. Actuators remain off until commanded.', 'success');
    setCliOutput('<span class="text-primary font-bold">[OK] Emergency Stop released. Chassis re-armed at 170 PWM.</span>');
  }, [addLog, resetEmergencyStop]);

  const toggleEStop = useCallback(() => {
    if (isEStopLatched) disengageEStop();
    else triggerEStop();
  }, [isEStopLatched, disengageEStop, triggerEStop]);

  // 4. Relay Toggle Handler
  const handleToggleRelay = useCallback((idx: number) => {
    if (isEStopLatched) {
      setCliOutput('<span class="text-hazard">Cannot toggle relays while E-STOP is active!</span>');
      return;
    }
    const nextState = !relays[idx];
    sendRelayToggle(`R${idx}`, nextState);
    const targetNames: Record<number, string> = {
      1: 'Pump R1',
      2: 'Probe A Actuator R2',
      3: 'Probe B Actuator R3',
      4: 'Sprayer Boom R4',
    };
    addLog(`Relay [${targetNames[idx] || idx}] command requested: ${nextState ? 'ACTIVE' : 'STANDBY'}`, nextState ? 'success' : 'info');
    setCliOutput(`Relay ${idx} requested <strong class="${nextState ? 'text-primary' : 'text-muted'}">${nextState ? 'ACTIVE' : 'STANDBY'}</strong>`);
  }, [isEStopLatched, relays, sendRelayToggle, addLog]);

  // 5. Motor Drive Vector Handler
  const handleDriveVector = useCallback((key: 'w' | 'a' | 's' | 'd' | 'x') => {
    if (isEStopLatched) {
      setCliOutput('<span class="text-hazard">Chassis vector rejected: E-STOP active.</span>');
      return;
    }
    const dirMap: Record<string, { dir: 'forward' | 'backward' | 'left' | 'right' | 'stop'; label: string }> = {
      w: { dir: 'forward', label: `FORWARD vector engaged [${currentPwm} PWM]` },
      s: { dir: 'backward', label: `REVERSE vector engaged [${currentPwm} PWM]` },
      a: { dir: 'left', label: 'LEFT differential spin engaged' },
      d: { dir: 'right', label: 'RIGHT differential spin engaged' },
      x: { dir: 'stop', label: 'EMERGENCY BRAKE applied to dual H-Bridge' },
    };

    const cmd = dirMap[key];
    if (cmd) {
      sendRobotControl(cmd.dir, cmd.dir === 'stop' ? 0 : currentPwm, activeMode);
      addLog(cmd.label, 'info');
      setCliOutput(cmd.label);
    }
  }, [isEStopLatched, currentPwm, activeMode, sendRobotControl, addLog]);

  // 6. Speed Presets
  const handleSetSpeed = useCallback((speed: number) => {
    if (isEStopLatched) return;
    const clamped = Math.min(255, Math.max(0, speed));
    setCurrentPwm(clamped);
    const pct = Math.round((clamped / 255) * 100);
    addLog(`PWM Duty cycle set: ${clamped} (${pct}%)`, 'info');
  }, [isEStopLatched, addLog]);

  // 7. Crop Selector
  const handleCropChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    const cropId = e.target.value;
    setCurrentCrop(cropId);
    const item = CROPS.find((c) => c.id === cropId);
    if (item) {
      addLog(`YOLO11 weights swapped: ${item.weights} (${item.name})`, 'info');
      setCliOutput(`Active YOLOv11 Model Profile: <strong class="text-white">${item.name}</strong>`);
    }
  }, [selectCrop, addLog]);

  // 8. Mode Switcher
  const handleModeChange = useCallback((newMode: 'auto' | 'manual') => {
    sendToggleMode(newMode);
    addLog(`Mode switched to: ${newMode === 'auto' ? 'AUTONOMOUS GPS WAYPOINT NAVIGATION' : 'MANUAL RC OVERRIDE'}`, 'success');
  }, [sendToggleMode, addLog]);

  // 9. Map Actions
  const handleRecenterMap = useCallback(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const liveLat = parseFloat(pos.coords.latitude.toFixed(5));
          const liveLng = parseFloat(pos.coords.longitude.toFixed(5));
          setSensorData((prev) => ({ ...prev, latitude: liveLat, longitude: liveLng }));
          if (mapInstanceRef.current) {
            mapInstanceRef.current.setView([liveLat, liveLng], 18);
          }
          addLog(`Map recentered to live GPS: ${liveLat}°, ${liveLng}°`, 'success');
        },
        () => {
          if (mapInstanceRef.current) {
            mapInstanceRef.current.setView([sensorData.latitude || 6.92715, sensorData.longitude || 79.86124], 17);
          }
        }
      );
    } else if (mapInstanceRef.current) {
      mapInstanceRef.current.setView([sensorData.latitude || 6.92715, sensorData.longitude || 79.86124], 17);
    }
  }, [addLog, sensorData.latitude, sensorData.longitude]);

  const handleAddWaypoint = useCallback(() => {
    const nextIdx = waypoints.length + 1;
    const newWpId = `WP-${String(nextIdx).padStart(2, '0')}`;
    const lastWp = waypoints[waypoints.length - 1];
    const newWp: Waypoint = {
      id: newWpId,
      lat: lastWp ? lastWp.lat - 0.0006 : (sensorData.latitude || 6.92715) - 0.0006,
      lng: lastWp ? lastWp.lng + 0.0006 : (sensorData.longitude || 79.86124) + 0.0006,
    };
    setWaypoints((prev) => [...prev, newWp]);
    addLog(`Waypoint ${newWpId} appended to mission vector.`, 'info');
    setCliOutput(`<span class="text-secondary">[NAV] Waypoint ${newWpId} added.</span>`);
  }, [waypoints, sensorData.latitude, sensorData.longitude, addLog]);

  const handleSkipWaypoint = useCallback(() => {
    if (activeWpIndex < waypoints.length - 1) {
      setActiveWpIndex((prev) => {
        const next = prev + 1;
        const target = waypoints[next];
        if (target) {
          addLog(`Bypassed WP -> Now targeting ${target.id}.`, 'info');
        }
        return next;
      });
      setEtaSeconds(105);
    }
  }, [activeWpIndex, waypoints, addLog]);

  const handleExportCsv = useCallback(() => {
    const headers = 'id,latitude,longitude,temperature,humidity,pressure,soil_moisture_a,soil_moisture_b,solar_lux,timestamp\n';
    const row = `CG1,${sensorData.latitude},${sensorData.longitude},${sensorData.temperature},${sensorData.humidity},${sensorData.pressure},${sensorData.soilMoisture},${sensorData.soilMoisture2 || sensorData.soilMoisture},${sensorData.light},${new Date().toISOString()}\n`;
    const blob = new Blob([headers + row], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `cropguard_telemetry_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    addLog('Generated mission telemetry CSV export.', 'success');
    setCliOutput('<span class="text-primary">[EXPORT] Mission telemetry exported to CSV.</span>');
  }, [sensorData, addLog]);

  // 10. CLI Command Parser
  const executeCli = useCallback(() => {
    const raw = cliInputText.trim();
    if (!raw) return;
    setCliInputText('');

    const args = raw.split(' ').filter(Boolean);
    const cmd = args[0].toLowerCase();

    switch (cmd) {
      case 'help':
        setCliOutput('Commands: <strong class="text-white">status</strong>, <strong class="text-white">estop</strong>, <strong class="text-white">reset</strong>, <strong class="text-white">speed [0-255]</strong>, <strong class="text-white">relay [1-4] [on|off]</strong>, <strong class="text-white">mode [auto|rc]</strong>, <strong class="text-white">clear</strong>');
        break;
      case 'status':
        setCliOutput(`[ESP32]: Online: ${esp32Connected} | E-Stop: ${isEStopLatched} | PWM: ${currentPwm} | Relays: [1:${relays[1]}, 2:${relays[2]}, 3:${relays[3]}, 4:${relays[4]}] | Temp: ${sensorData.temperature}°C`);
        break;
      case 'estop':
      case 'halt':
        triggerEStop();
        break;
      case 'reset':
        disengageEStop();
        break;
      case 'mode':
        if (args[1]) {
          const m = args[1].toLowerCase() === 'auto' ? 'auto' : 'manual';
          handleModeChange(m);
        }
        break;
      case 'speed':
        if (args[1]) {
          const val = parseInt(args[1], 10);
          if (!isNaN(val)) {
            handleSetSpeed(val);
            setCliOutput(`PWM Speed set: ${val}`);
          }
        } else {
          setCliOutput(`Current speed: ${currentPwm} PWM`);
        }
        break;
      case 'relay':
        if (args[1] && args[2]) {
          const idx = parseInt(args[1], 10);
          const st = args[2].toLowerCase() === 'on';
          if ([1, 2, 3, 4].includes(idx)) {
            sendRelayToggle(`R${idx}`, st);
            setCliOutput(`Relay ${idx} forced ${st ? 'ON' : 'OFF'}`);
          } else {
            setCliOutput('<span class="text-hazard">Invalid relay #. Choose 1 to 4.</span>');
          }
        } else {
          setCliOutput('Usage: relay &lt;1-4&gt; &lt;on|off&gt;');
        }
        break;
      case 'clear':
        setCliOutput('DEM3T3R V1 Field Commander OS ready.');
        break;
      default:
        setCliOutput(`<span class="text-hazard">Command '${cmd}' not recognized. Type 'help'.</span>`);
        break;
    }
  }, [cliInputText, esp32Connected, isEStopLatched, currentPwm, relays, sensorData.temperature, triggerEStop, disengageEStop, handleModeChange, handleSetSpeed, sendRelayToggle]);

  // 11. Global Keyboard Listeners
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const activeEl = document.activeElement;
      const isInput = activeEl?.tagName === 'INPUT' || activeEl?.tagName === 'TEXTAREA' || activeEl?.tagName === 'SELECT';

      if (isInput) {
        if (e.key === 'Enter' && (activeEl as HTMLInputElement).id === 'cli-input') {
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
        handleToggleRelay(parseInt(k, 10));
        return;
      }

      if (['w', 'a', 's', 'd', 'x'].includes(k)) {
        e.preventDefault();
        handleDriveVector(k as 'w' | 'a' | 's' | 'd' | 'x');
        return;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [executeCli, toggleEStop, handleToggleRelay, handleDriveVector]);

  const etaMinutes = String(Math.floor(etaSeconds / 60)).padStart(2, '0');
  const etaSecs = String(etaSeconds % 60).padStart(2, '0');
  const pwmPercent = Math.round((currentPwm / 255) * 100);

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-obsidian text-slate-100 antialiased font-sans select-none">
      {/* 1. CRITICAL HARD E-STOP FULL OVERLAY */}
      {isEStopLatched && (
        <div
          id="full-estop-overlay"
          className="fixed inset-0 z-50 bg-black/90 backdrop-blur-xl flex flex-col items-center justify-center p-6 text-center animate-fade-in"
        >
          <div className="max-w-xl w-full p-8 rounded-3xl border border-hazard/40 bg-[#120507]/90 shadow-[0_0_80px_rgba(255,51,75,0.4)] flex flex-col items-center">
            <div className="w-20 h-20 rounded-full bg-hazard/20 border-2 border-hazard flex items-center justify-center mb-6 animate-pulse">
              <span className="material-symbols-outlined text-5xl text-hazard font-bold">warning</span>
            </div>
            <h1 className="text-3xl font-black tracking-wider text-hazard uppercase mb-2 font-mono">
              HARD E-STOP ACTIVATED
            </h1>
            <p className="text-sm text-slate-300 mb-6 font-mono">
              Chassis locomotion disabled. 4-Channel Relay bus de-energized.
              <br />
              Dual BTS7960 PWM output forced to 0.
            </p>
            <div className="p-4 rounded-xl bg-black/60 border border-hazard/30 w-full mb-8 font-mono text-xs text-left space-y-1">
              <div className="text-hazard flex justify-between">
                <span>[MOTOR BUS]</span>
                <span>INHIBITED (0 PWM)</span>
              </div>
              <div className="text-hazard flex justify-between">
                <span>[RELAY 1-4]</span>
                <span>DISCONNECTED</span>
              </div>
              <div className="text-amber-400 flex justify-between">
                <span>[RECOVERY]</span>
                <span>Press [SPACE] or click below to re-arm</span>
              </div>
            </div>
            <button
              id="overlay-reset-btn"
              onClick={disengageEStop}
              className="w-full py-4 rounded-xl bg-hazard text-white font-mono font-bold text-sm tracking-wider uppercase hover:bg-rose-600 transition-all shadow-lg shadow-hazard/40 active:scale-95 cursor-pointer"
            >
              RESET EMERGENCY STOP &amp; RE-ARM SYSTEM
            </button>
          </div>
        </div>
      )}

      {/* 2. TOP SCADA COMMAND HEADER */}
      <header className="h-11 w-full border-b border-white/[0.07] bg-[#0A0B0E]/90 backdrop-blur-md px-3 flex items-center justify-between shrink-0 z-20">
        {/* Left: Brand / System Identity */}
        <div className="flex items-center gap-2.5">
          <div className="w-6 h-6 rounded-md bg-white text-black flex items-center justify-center font-bold text-xs shadow-[0_0_12px_rgba(255,255,255,0.4)]">
            <span className="material-symbols-outlined text-[16px]">eco</span>
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="font-mono text-xs font-black tracking-tight text-white">DEM3T3R V1</span>
              <span className="font-mono text-[9px] px-1 rounded bg-white/[0.08] text-white/70 border border-white/10">v3.4-SCADA</span>
            </div>
            <span className="text-[9px] text-muted tracking-wide font-mono leading-none">TACTICAL FIELD COMMANDER</span>
          </div>
        </div>

        {/* Center: System Status & GNSS Ribbon */}
        <div className="hidden lg:flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-white/[0.03] border border-white/[0.06]">
            <span className={`w-2 h-2 rounded-full ${connected && esp32Connected ? 'bg-primary glow-dot' : 'bg-hazard animate-pulse'}`} />
            <span className="text-[10px] text-white/90">
              SYS: <strong className="text-primary">{connected && esp32Connected ? 'OPERATIONAL' : 'OFFLINE'}</strong>
            </span>
            <span className="text-white/20">|</span>
            <span className="text-[10px] text-muted">
              UPLINK: <span className="text-white font-medium">{connected ? '58ms / 50 Hz' : '0 Hz'}</span>
            </span>
          </div>

          <div className="flex items-center gap-3 px-3 py-1 rounded-full bg-white/[0.03] border border-white/[0.06] text-[10px]">
            <div className="flex items-center gap-1 text-muted">
              <span className="material-symbols-outlined text-[12px] text-secondary">explore</span>
              <span>LAT:</span>
              <span className="text-white font-mono">{Math.abs(sensorData.latitude || 6.92715).toFixed(5)}° {(sensorData.latitude || 0) >= 0 ? 'N' : 'S'}</span>
            </div>
            <span className="text-white/20">|</span>
            <div className="flex items-center gap-1 text-muted">
              <span>LON:</span>
              <span className="text-white font-mono">{Math.abs(sensorData.longitude || 79.86124).toFixed(5)}° {(sensorData.longitude || 0) >= 0 ? 'E' : 'W'}</span>
            </div>
          </div>
        </div>

        {/* Right: Mode Selector + Hard E-Stop */}
        <div className="flex items-center gap-2">
          {/* Mode Selector */}
          <div className="flex items-center p-0.5 rounded-full bg-white/[0.05] border border-white/[0.08] font-mono">
            <button
              onClick={() => handleModeChange('auto')}
              className={`px-3 py-1 rounded-full text-[10px] font-semibold transition-all ${
                activeMode === 'auto' ? 'bg-white text-black shadow' : 'text-muted hover:text-white'
              }`}
            >
              AUTONOMOUS
            </button>
            <button
              onClick={() => handleModeChange('manual')}
              className={`px-2.5 py-1 rounded-full text-[10px] font-semibold transition-all ${
                activeMode === 'manual' ? 'bg-white text-black shadow' : 'text-muted hover:text-white'
              }`}
            >
              MANUAL RC
            </button>
          </div>

          {/* Hard E-Stop Trigger */}
          <button
            onClick={toggleEStop}
            className={`px-3 py-1 rounded-full border text-[11px] font-mono font-black tracking-wider flex items-center gap-1.5 transition-all cursor-pointer ${
              isEStopLatched
                ? 'bg-hazard text-white border-hazard animate-pulse shadow-[0_0_15px_rgba(255,51,75,0.6)]'
                : 'bg-hazard/20 hover:bg-hazard text-hazard hover:text-white border-hazard/40'
            }`}
          >
            <span className="material-symbols-outlined text-[14px]">emergency_home</span>
            <span>{isEStopLatched ? 'E-STOPPED' : '[SPACE] HARD E-STOP'}</span>
          </button>
        </div>
      </header>
      <HardwareTelemetry data={sensorData} connected={connected && esp32Connected} />

      {/* 3. MAIN COCKPIT GRID (High-Density 3-Column Layout) */}
      <main className="w-full flex-1 grid grid-cols-1 xl:grid-cols-12 gap-2 p-2 min-h-0 bg-transparent overflow-hidden">
        {/* ============================================================== */}
        {/* COLUMN 1: TACTICAL NAVIGATION & BTS7960 DRIVE (4 COLS)        */}
        {/* ============================================================== */}
        <section className="xl:col-span-4 flex flex-col gap-2 min-h-0 h-full overflow-hidden">
          {/* Map Card */}
          <div className="frost-card rounded-2xl flex flex-col flex-[1.4] overflow-hidden min-h-0">
            {/* Header */}
            <div className="p-2.5 px-3 border-b border-white/[0.06] flex items-center justify-between bg-white/[0.01]">
              <div className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[15px] text-secondary">radar</span>
                <h3 className="font-mono text-[11px] font-bold tracking-wider uppercase text-white">TACTICAL GPS NAVIGATION</h3>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="font-mono text-[9px] px-1.5 py-0.5 rounded bg-secondary/10 border border-secondary/30 text-secondary font-semibold">
                  {waypoints[activeWpIndex]?.id || 'WP-04'} TARGET
                </span>
                <span className="font-mono text-[9px] text-muted">{etaMinutes}:{etaSecs} ETA</span>
              </div>
            </div>

            {/* Leaflet Map Canvas */}
            <div className="relative flex-1 w-full min-h-[160px] bg-[#07080B]">
              <div id="leaflet-map" ref={mapContainerRef} className="w-full h-full" />
              {/* Map Floating Telemetry HUD */}
              <div className="absolute top-2 left-2 z-[400] flex flex-col gap-1 pointer-events-none">
                <div className="px-2 py-1 rounded-md bg-black/80 backdrop-blur-md border border-white/10 font-mono text-[9px] text-slate-300 space-y-0.5 shadow-lg">
                  <div className="flex justify-between gap-2">
                    <span className="text-muted">SPEED:</span>
                    <span className="text-white font-bold">{(sensorData.speed || 0.42).toFixed(2)} m/s</span>
                  </div>
                  <div className="flex justify-between gap-2">
                    <span className="text-muted">ALTITUDE:</span>
                    <span className="text-white">{(sensorData.altitude || 14.2).toFixed(1)} m</span>
                  </div>
                  <div className="flex justify-between gap-2">
                    <span className="text-muted">HEADING:</span>
                    <span className="text-secondary">{sensorData.cardinal || 'NNE 024°'}</span>
                  </div>
                  <div className="flex justify-between gap-2">
                    <span className="text-muted">GNSS:</span>
                    <span className="text-primary font-bold">{sensorData.fix ? 'RTK FIX' : '3D FIX'} ({sensorData.satellites || 14} Sats)</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Map Action Ribbon */}
            <div className="p-1.5 px-2.5 border-t border-white/[0.06] bg-white/[0.02] flex items-center justify-between text-[10px] font-mono">
              <div className="flex items-center gap-1">
                <button
                  onClick={handleRecenterMap}
                  className="px-2 py-1 rounded-md bg-white/[0.05] hover:bg-white/10 border border-white/10 text-white transition-all flex items-center gap-1 cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[12px]">my_location</span>
                  <span>RECENTER</span>
                </button>
                <button
                  onClick={handleAddWaypoint}
                  className="px-2 py-1 rounded-md bg-white/[0.05] hover:bg-white/10 border border-white/10 text-white transition-all flex items-center gap-1 cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[12px]">add_location</span>
                  <span>ADD WP</span>
                </button>
                <button
                  onClick={handleSkipWaypoint}
                  className="px-2 py-1 rounded-md bg-white/[0.05] hover:bg-white/10 border border-white/10 text-white transition-all flex items-center gap-1 cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[12px]">fast_forward</span>
                  <span>BYPASS WP</span>
                </button>
              </div>
              <button
                onClick={handleExportCsv}
                className="px-2 py-1 rounded-md bg-secondary/15 hover:bg-secondary/25 border border-secondary/30 text-secondary transition-all flex items-center gap-1 cursor-pointer"
              >
                <span className="material-symbols-outlined text-[12px]">download</span>
                <span>EXPORT CSV</span>
              </button>
            </div>
          </div>

          {/* BTS7960 Motor Controller Card */}
          <div className="frost-card rounded-2xl flex-1 flex flex-col p-3 overflow-hidden min-h-0">
            {/* Header */}
            <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
              <div className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[15px] text-white">tune</span>
                <h3 className="font-mono text-[11px] font-bold tracking-wider uppercase text-white">BTS7960 DUAL H-BRIDGE MOTOR MIXER</h3>
              </div>
              <span
                className={`font-mono text-[9px] px-2 py-0.5 rounded-full font-bold ${
                  isEStopLatched
                    ? 'text-hazard bg-hazard/15 border border-hazard/40 animate-pulse'
                    : 'text-primary bg-primary/10 border border-primary/25'
                }`}
              >
                {isEStopLatched ? 'E-STOPPED' : 'ARMED'}
              </span>
            </div>

            {/* PWM Gauge & Speed Presets */}
            <div className="grid grid-cols-12 gap-2 my-2 items-center">
              <div className="col-span-6 flex flex-col gap-1">
                <div className="flex justify-between text-[9px] font-mono">
                  <span className="text-muted">PWM DUTY CYCLE:</span>
                  <span className="text-white font-bold">{currentPwm} PWM / {pwmPercent}%</span>
                </div>
                {/* Visual Bar */}
                <div className="w-full h-2 rounded-full bg-white/[0.06] overflow-hidden p-0.5 border border-white/10">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-secondary to-primary transition-all duration-200"
                    style={{ width: `${pwmPercent}%` }}
                  />
                </div>
              </div>

              {/* Speed Buttons */}
              <div className="col-span-6 grid grid-cols-3 gap-1 font-mono text-[9px]">
                <button
                  onClick={() => handleSetSpeed(100)}
                  className={`py-1.5 px-1 rounded-xl flex flex-col items-center text-center transition-all cursor-pointer ${
                    currentPwm <= 100
                      ? 'bg-white text-black font-semibold border border-white shadow-md'
                      : 'bg-white/[0.04] hover:bg-white/[0.09] border border-white/[0.06] text-white'
                  }`}
                >
                  <span>CRAWL</span>
                  <span className="text-[7px] opacity-70">100 PWM</span>
                </button>
                <button
                  onClick={() => handleSetSpeed(170)}
                  className={`py-1.5 px-1 rounded-xl flex flex-col items-center text-center transition-all cursor-pointer ${
                    currentPwm > 100 && currentPwm <= 190
                      ? 'bg-white text-black font-semibold border border-white shadow-md'
                      : 'bg-white/[0.04] hover:bg-white/[0.09] border border-white/[0.06] text-white'
                  }`}
                >
                  <span>CRUISE</span>
                  <span className="text-[7px] opacity-70">170 PWM</span>
                </button>
                <button
                  onClick={() => handleSetSpeed(255)}
                  className={`py-1.5 px-1 rounded-xl flex flex-col items-center text-center transition-all cursor-pointer ${
                    currentPwm > 190
                      ? 'bg-white text-black font-semibold border border-white shadow-md'
                      : 'bg-white/[0.04] hover:bg-white/[0.09] border border-white/[0.06] text-white'
                  }`}
                >
                  <span>TURBO</span>
                  <span className="text-[7px] opacity-70">255 PWM</span>
                </button>
              </div>
            </div>

            {/* D-Pad Vector Grid */}
            <div className="flex-1 flex items-center justify-center pt-1">
              <div className="grid grid-cols-3 gap-1.5 w-48 font-mono">
                <div />
                <button
                  onClick={() => handleDriveVector('w')}
                  className="h-10 rounded-xl bg-white/[0.05] hover:bg-white/20 active:bg-white active:text-black border border-white/10 flex flex-col items-center justify-center transition-all cursor-pointer"
                >
                  <span className="material-symbols-outlined text-sm">arrow_upward</span>
                  <span className="text-[7px] font-bold">[W] FWD</span>
                </button>
                <div />

                <button
                  onClick={() => handleDriveVector('a')}
                  className="h-10 rounded-xl bg-white/[0.05] hover:bg-white/20 active:bg-white active:text-black border border-white/10 flex flex-col items-center justify-center transition-all cursor-pointer"
                >
                  <span className="material-symbols-outlined text-sm">arrow_back</span>
                  <span className="text-[7px] font-bold">[A] LEFT</span>
                </button>
                <button
                  onClick={() => handleDriveVector('x')}
                  className="h-10 rounded-xl bg-hazard/20 hover:bg-hazard active:bg-rose-700 text-hazard hover:text-white border border-hazard/40 flex flex-col items-center justify-center transition-all cursor-pointer font-black"
                >
                  <span className="material-symbols-outlined text-sm">front_hand</span>
                  <span className="text-[7px] font-bold">[X] BRAKE</span>
                </button>
                <button
                  onClick={() => handleDriveVector('d')}
                  className="h-10 rounded-xl bg-white/[0.05] hover:bg-white/20 active:bg-white active:text-black border border-white/10 flex flex-col items-center justify-center transition-all cursor-pointer"
                >
                  <span className="material-symbols-outlined text-sm">arrow_forward</span>
                  <span className="text-[7px] font-bold">[D] RIGHT</span>
                </button>

                <div />
                <button
                  onClick={() => handleDriveVector('s')}
                  className="h-10 rounded-xl bg-white/[0.05] hover:bg-white/20 active:bg-white active:text-black border border-white/10 flex flex-col items-center justify-center transition-all cursor-pointer"
                >
                  <span className="material-symbols-outlined text-sm">arrow_downward</span>
                  <span className="text-[7px] font-bold">[S] REV</span>
                </button>
                <div />
              </div>
            </div>
          </div>
        </section>

        {/* ============================================================== */}
        {/* COLUMN 2: COMPUTER VISION & SCADA 8-SENSOR MATRIX (5 COLS)     */}
        {/* ============================================================== */}
        <section className="xl:col-span-5 flex flex-col gap-2 min-h-0 h-full overflow-hidden">
          {/* YOLO11 Live Stream Card */}
          <div className="frost-card rounded-2xl flex flex-col flex-[1.3] overflow-hidden min-h-0">
            {/* Header / Filter Toolbar */}
            <div className="p-2 px-3 border-b border-white/[0.06] flex items-center justify-between bg-white/[0.01]">
              {/* Crop Selector */}
              <div className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[15px] text-pathogen">psychology</span>
                <select
                  value={currentCrop}
                  onChange={handleCropChange}
                  className="bg-[#12131A] text-white font-mono text-[10px] font-bold rounded-lg border border-white/15 px-2 py-1 outline-none focus:border-white transition-all cursor-pointer"
                >
                  {CROPS.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Spectral Filters */}
              <div className="flex items-center gap-1 font-mono">
                <button
                  onClick={() => setActiveFilter('raw')}
                  className={`py-1 px-2 rounded-lg text-[9px] font-semibold uppercase transition-all cursor-pointer ${
                    activeFilter === 'raw'
                      ? 'bg-white text-black shadow-sm'
                      : 'bg-white/[0.04] text-muted hover:text-white border border-white/[0.08]'
                  }`}
                >
                  RAW RGB
                </button>
                <button
                  onClick={() => setActiveFilter('ndvi')}
                  className={`py-1 px-2 rounded-lg text-[9px] font-semibold uppercase transition-all cursor-pointer ${
                    activeFilter === 'ndvi'
                      ? 'bg-white text-black shadow-sm'
                      : 'bg-white/[0.04] text-muted hover:text-white border border-white/[0.08]'
                  }`}
                >
                  NDVI
                </button>
                <button
                  onClick={() => setActiveFilter('biomass')}
                  className={`py-1 px-2 rounded-lg text-[9px] font-semibold uppercase transition-all cursor-pointer ${
                    activeFilter === 'biomass'
                      ? 'bg-white text-black shadow-sm'
                      : 'bg-white/[0.04] text-muted hover:text-white border border-white/[0.08]'
                  }`}
                >
                  BIOMASS
                </button>
              </div>
            </div>

            {/* Video Stream Container */}
            <div className="relative flex-1 w-full min-h-[170px] bg-black flex items-center justify-center overflow-hidden">
              {!streamError ? (
                <img
                  src={`${BACKEND_URL}/video_feed`}
                  alt="Live YOLO11 Camera Stream"
                  onError={() => setStreamError(true)}
                  className="w-full h-full object-cover transition-all duration-300"
                  style={{
                    filter:
                      activeFilter === 'ndvi'
                        ? 'contrast(180%) hue-rotate(90deg) saturate(200%)'
                        : activeFilter === 'biomass'
                        ? 'contrast(150%) saturate(300%) brightness(90%)'
                        : 'none',
                  }}
                />
              ) : (
                <div className="flex flex-col items-center justify-center text-center p-4">
                  <span className="material-symbols-outlined text-4xl text-muted mb-2">videocam_off</span>
                  <span className="font-mono text-xs text-white/80">Camera Stream Connecting...</span>
                  <span className="font-mono text-[10px] text-muted mt-1">{`${BACKEND_URL}/video_feed`}</span>
                  <button
                    onClick={() => setStreamError(false)}
                    className="mt-3 px-3 py-1 rounded-md bg-white/10 hover:bg-white/20 text-white font-mono text-[10px] border border-white/20 cursor-pointer"
                  >
                    RECONNECT STREAM
                  </button>
                </div>
              )}

              {/* Live Overlay HUD */}
              <div className="absolute top-2 right-2 z-10 flex flex-col gap-1 items-end pointer-events-none">
                <div className="px-2 py-0.5 rounded bg-black/70 backdrop-blur-md border border-white/15 font-mono text-[9px] text-primary flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary glow-dot" />
                  <span>30.2 FPS | 18ms INFERENCE</span>
                </div>
                {diseases.length > 0 ? (
                  diseases.map((d, i) => (
                    <div
                      key={i}
                      className="px-2 py-0.5 rounded bg-pathogen/30 backdrop-blur-md border border-pathogen/60 font-mono text-[9px] text-pathogen font-bold"
                    >
                      {d.class.toUpperCase()} ({(d.confidence * 100).toFixed(1)}%)
                    </div>
                  ))
                ) : (
                  <div className="px-2 py-0.5 rounded bg-primary/20 backdrop-blur-md border border-primary/40 font-mono text-[9px] text-primary">
                    CANOPY HEALTHY (99.4%)
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* 8-Sensor SCADA Matrix Card */}
          <div className="frost-card rounded-2xl flex-1 flex flex-col p-3 overflow-hidden min-h-0">
            {/* Header */}
            <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
              <div className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[15px] text-secondary">sensors</span>
                <h3 className="font-mono text-[11px] font-bold tracking-wider uppercase text-white">
                  SCADA 8-SENSOR TELEMETRY MATRIX
                </h3>
              </div>
              <span className="font-mono text-[9px] text-muted">BUS: I2C + ADC + UART</span>
            </div>

            {/* 8 Sensors Grid */}
            <div className="flex-1 grid grid-cols-4 gap-2 pt-2 min-h-0">
              {/* 1. Temp */}
              <div className="p-2 rounded-xl bg-white/[0.03] border border-white/[0.06] flex flex-col justify-between">
                <span className="text-[9px] font-mono text-muted">BME280 TEMP</span>
                <div className="flex items-baseline gap-1">
                  <span className="text-lg font-mono font-black text-white">{sensorData.temperature.toFixed(1)}</span>
                  <span className="text-[10px] font-mono text-muted">°C</span>
                </div>
                <span className="text-[8px] font-mono text-primary font-semibold">OPTIMAL (22-28)</span>
              </div>

              {/* 2. Hum */}
              <div className="p-2 rounded-xl bg-white/[0.03] border border-white/[0.06] flex flex-col justify-between">
                <span className="text-[9px] font-mono text-muted">BME280 HUM</span>
                <div className="flex items-baseline gap-1">
                  <span className="text-lg font-mono font-black text-white">{sensorData.humidity.toFixed(1)}</span>
                  <span className="text-[10px] font-mono text-muted">%</span>
                </div>
                <span className="text-[8px] font-mono text-secondary font-semibold">NORMAL (60-75)</span>
              </div>

              {/* 3. Baro */}
              <div className="p-2 rounded-xl bg-white/[0.03] border border-white/[0.06] flex flex-col justify-between">
                <span className="text-[9px] font-mono text-muted">BME280 BARO</span>
                <div className="flex items-baseline gap-1">
                  <span className="text-lg font-mono font-black text-white">{sensorData.pressure.toFixed(0)}</span>
                  <span className="text-[10px] font-mono text-muted">hPa</span>
                </div>
                <span className="text-[8px] font-mono text-slate-400">STABLE BARO</span>
              </div>

              {/* 4. Solar Flux */}
              <div className="p-2 rounded-xl bg-white/[0.03] border border-white/[0.06] flex flex-col justify-between">
                <span className="text-[9px] font-mono text-muted">BH1750 LUX</span>
                <div className="flex items-baseline gap-1">
                  <span className="text-lg font-mono font-black text-white">{(sensorData.light / 1000).toFixed(1)}k</span>
                  <span className="text-[10px] font-mono text-muted">Lux</span>
                </div>
                <span className="text-[8px] font-mono text-amber-400 font-semibold">DIRECT SUN</span>
              </div>

              {/* 5. UV Index */}
              <div className="p-2 rounded-xl bg-white/[0.03] border border-white/[0.06] flex flex-col justify-between">
                <span className="text-[9px] font-mono text-muted">ML8511 UV</span>
                <div className="flex items-baseline gap-1">
                  <span className="text-lg font-mono font-black text-white">{sensorData.uvVoltage.toFixed(2)}</span>
                  <span className="text-[10px] font-mono text-muted">V</span>
                </div>
                <span className="text-[8px] font-mono text-purple-400 font-semibold">UV INDEX {esp32Connected ? sensorData.uvIndex ?? '—' : '—'}</span>
              </div>

              {/* 6. Soil Probe A */}
              <div className="p-2 rounded-xl bg-white/[0.03] border border-white/[0.06] flex flex-col justify-between">
                <span className="text-[9px] font-mono text-muted">SOIL PROBE A</span>
                <div className="flex items-baseline gap-1">
                  <span className="text-lg font-mono font-black text-white">{esp32Connected ? sensorData.soil1Pct?.toFixed(1) ?? '—' : '—'}</span>
                  <span className="text-[10px] font-mono text-muted">%</span>
                </div>
                <span className="text-[8px] font-mono text-primary font-semibold">CALIBRATED MOISTURE</span>
              </div>

              {/* 7. Soil Probe B */}
              <div className="p-2 rounded-xl bg-white/[0.03] border border-white/[0.06] flex flex-col justify-between">
                <span className="text-[9px] font-mono text-muted">SOIL PROBE B</span>
                <div className="flex items-baseline gap-1">
                  <span className="text-lg font-mono font-black text-white">{esp32Connected ? sensorData.soil2Pct?.toFixed(1) ?? '—' : '—'}</span>
                  <span className="text-[10px] font-mono text-muted">%</span>
                </div>
                <span className="text-[8px] font-mono text-primary font-semibold">CALIBRATED MOISTURE</span>
              </div>

              {/* 8. Sonar Obstacle */}
              <div className="p-2 rounded-xl bg-white/[0.03] border border-white/[0.06] flex flex-col justify-between">
                <span className="text-[9px] font-mono text-muted">HC-SR04 SONAR</span>
                <div className="flex items-baseline gap-1">
                  <span className="text-lg font-mono font-black text-white">{esp32Connected ? sensorData.ultrasonic?.toFixed(0) ?? '—' : '—'}</span>
                  <span className="text-[10px] font-mono text-muted">cm</span>
                </div>
                <span className="text-[8px] font-mono text-primary font-semibold">FRONT RANGE</span>
              </div>
            </div>
          </div>
        </section>

        {/* ============================================================== */}
        {/* COLUMN 3: PATHOLOGY, RELAYS & AUDIT LOG (3 COLS)               */}
        {/* ============================================================== */}
        <section className="xl:col-span-3 flex flex-col gap-2 min-h-0 h-full overflow-hidden">
          {/* Pathogen Detection Feed */}
          <div className="frost-card rounded-2xl flex flex-col p-3 overflow-hidden shrink-0">
            <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
              <div className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[15px] text-pathogen">coronavirus</span>
                <h3 className="font-mono text-[11px] font-bold tracking-wider uppercase text-white">PATHOGEN DETECTION</h3>
              </div>
              <span className="font-mono text-[9px] text-pathogen font-bold px-1.5 py-0.5 rounded bg-pathogen/15 border border-pathogen/30">
                {diseases.length > 0 ? `${diseases.length} FLAGGED` : 'CLEAR'}
              </span>
            </div>
            <div className="pt-2 flex flex-col gap-1.5">
              <div className="flex justify-between items-baseline font-mono text-[10px]">
                <span className="text-white font-semibold">
                  {diseases[0]?.class ? diseases[0].class.replace(/_/g, ' ').toUpperCase() : recommendation?.disease || 'Early Blight Warning'}
                </span>
                <span className="text-pathogen font-bold">
                  {diseases[0]?.confidence ? `${(diseases[0].confidence * 100).toFixed(1)}%` : '89.4% CONF'}
                </span>
              </div>
              <p className="text-[9px] text-slate-400 leading-tight">
                {recommendation?.reason || 'Localized leaf margin lesions and chlorosis identified via high-resolution RGB inference.'}
              </p>
            </div>
          </div>

          {/* VLA AI Decision / Treatment Advice */}
          <div className="frost-card rounded-2xl flex flex-col p-3 overflow-hidden shrink-0">
            <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
              <div className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[15px] text-primary">science</span>
                <h3 className="font-mono text-[11px] font-bold tracking-wider uppercase text-white">VLA AGRONOMIC AI DECISION</h3>
              </div>
              <span className="font-mono text-[9px] text-primary font-semibold">ACTUATION READY</span>
            </div>
            <p className="text-[9px] text-slate-300 font-mono pt-2 leading-tight">
              {recommendation?.recovery || 'Execute targeted foliar bio-fungicide dosing (Copper Hydroxide 40WP @ 2.5g/L). Maintain soil aeration.'}
            </p>
          </div>

          {/* 4-Channel Precision Solid-State Relays */}
          <div className="frost-card rounded-2xl flex flex-col p-3 overflow-hidden shrink-0">
            <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
              <div className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[15px] text-white">toggle_on</span>
                <h3 className="font-mono text-[11px] font-bold tracking-wider uppercase text-white">
                  4-CHANNEL SOLID-STATE RELAYS
                </h3>
              </div>
              <span className="font-mono text-[9px] text-muted">OPTO-ISOLATED</span>
            </div>

            <div className="grid grid-cols-2 gap-2 pt-2">
              {/* Relay 1 */}
              <div className="p-2 rounded-xl bg-white/[0.03] border border-white/[0.06] flex flex-col justify-between gap-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[9px] font-mono text-white font-bold">[1] PUMP R1</span>
                  <span className={`w-2 h-2 rounded-full ${relays[1] ? 'bg-primary glow-dot' : 'bg-white/20'}`} />
                </div>
                <button
                  onClick={() => handleToggleRelay(1)}
                  className={`py-1 px-2 font-mono text-[8px] font-bold uppercase rounded-full transition-all cursor-pointer ${
                    relays[1]
                      ? 'bg-white text-black shadow-sm'
                      : 'bg-white/[0.05] text-muted hover:text-white border border-white/10'
                  }`}
                >
                  {relays[1] ? '[1] ACTIVE' : '[1] STANDBY'}
                </button>
              </div>

              {/* Relay 2 */}
              <div className="p-2 rounded-xl bg-white/[0.03] border border-white/[0.06] flex flex-col justify-between gap-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[9px] font-mono text-white font-bold">[2] PROBE A R2</span>
                  <span className={`w-2 h-2 rounded-full ${relays[2] ? 'bg-primary glow-dot' : 'bg-white/20'}`} />
                </div>
                <button
                  onClick={() => handleToggleRelay(2)}
                  className={`py-1 px-2 font-mono text-[8px] font-bold uppercase rounded-full transition-all cursor-pointer ${
                    relays[2]
                      ? 'bg-white text-black shadow-sm'
                      : 'bg-white/[0.05] text-muted hover:text-white border border-white/10'
                  }`}
                >
                  {relays[2] ? '[2] ACTIVE' : '[2] STANDBY'}
                </button>
              </div>

              {/* Relay 3 */}
              <div className="p-2 rounded-xl bg-white/[0.03] border border-white/[0.06] flex flex-col justify-between gap-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[9px] font-mono text-white font-bold">[3] PROBE B R3</span>
                  <span className={`w-2 h-2 rounded-full ${relays[3] ? 'bg-primary glow-dot' : 'bg-white/20'}`} />
                </div>
                <button
                  onClick={() => handleToggleRelay(3)}
                  className={`py-1 px-2 font-mono text-[8px] font-bold uppercase rounded-full transition-all cursor-pointer ${
                    relays[3]
                      ? 'bg-white text-black shadow-sm'
                      : 'bg-white/[0.05] text-muted hover:text-white border border-white/10'
                  }`}
                >
                  {relays[3] ? '[3] ACTIVE' : '[3] STANDBY'}
                </button>
              </div>

              {/* Relay 4 */}
              <div className="p-2 rounded-xl bg-white/[0.03] border border-white/[0.06] flex flex-col justify-between gap-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[9px] font-mono text-white font-bold">[4] SPRAYER R4</span>
                  <span className={`w-2 h-2 rounded-full ${relays[4] ? 'bg-primary glow-dot' : 'bg-white/20'}`} />
                </div>
                <button
                  onClick={() => handleToggleRelay(4)}
                  className={`py-1 px-2 font-mono text-[8px] font-bold uppercase rounded-full transition-all cursor-pointer ${
                    relays[4]
                      ? 'bg-white text-black shadow-sm'
                      : 'bg-white/[0.05] text-muted hover:text-white border border-white/10'
                  }`}
                >
                  {relays[4] ? '[4] ACTIVE' : '[4] STANDBY'}
                </button>
              </div>
            </div>
          </div>

          {/* Real-Time Audit Log Stream */}
          <div className="frost-card rounded-2xl flex-1 flex flex-col p-3 overflow-hidden min-h-0">
            <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
              <div className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[15px] text-white">view_timeline</span>
                <h3 className="font-mono text-[11px] font-bold tracking-wider uppercase text-white">REAL-TIME AUDIT LOG</h3>
              </div>
              <span className="font-mono text-[9px] text-muted">STREAM</span>
            </div>

            <div
              ref={auditScrollRef}
              className="flex-1 overflow-y-auto space-y-1 font-mono text-[9px] pt-2 text-slate-300 select-text"
            >
              {logs.map((l) => (
                <div key={l.id} className="leading-tight">
                  <span className={`${l.color} font-semibold`}>[{l.tag} {l.time}]</span> {l.msg}
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      {/* 4. FOOTER CLI COMMAND LINE */}
      <footer className="h-14 w-full bg-[#0B0C10]/95 backdrop-blur-md border-t border-white/[0.07] flex flex-col justify-between shrink-0 px-4 py-1.5 z-20">
        {/* Output Line */}
        <div
          id="cli-output-line"
          dangerouslySetInnerHTML={{ __html: cliOutput }}
          className="font-mono text-[10px] text-slate-300 truncate"
        />

        {/* Input Field */}
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] text-secondary font-bold select-none">&gt;</span>
          <input
            id="cli-input"
            type="text"
            value={cliInputText}
            onChange={(e) => setCliInputText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && executeCli()}
            placeholder="Type 'help' for tactical commander instructions (e.g. status, speed 200, relay 1 on, estop)..."
            className="flex-1 bg-transparent text-white font-mono text-xs outline-none border-none placeholder-muted"
          />
          <button
            onClick={executeCli}
            className="px-3 py-1 rounded-md bg-white/[0.08] hover:bg-white/20 text-white font-mono text-[10px] font-semibold border border-white/10 transition-all cursor-pointer"
          >
            EXEC [ENTER]
          </button>
        </div>
      </footer>
    </div>
  );
}
