import { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { BACKEND_URL } from '../backendUrl';
import { DiseaseItem, LogEntry, Recommendation, SensorData } from '../App';
import { useSocketData, WeatherPayload } from '../hooks/useSocketData';
import './dashboard.css';
import LiveGpsMap from './LiveGpsMap';
import DiseaseCare from './DiseaseCare';
import AssistantChat from './AssistantChat';
import TelemetryMatrix from './TelemetryMatrix';

type IconName = 'leaf' | 'grid' | 'sensor' | 'robot' | 'clock' | 'gear' | 'arrow' | 'camera' | 'drop' | 'sun' | 'temp' | 'wifi' | 'stop' | 'refresh' | 'pin' | 'check' | 'chevron' | 'close';
const paths: Record<IconName, string> = {
  leaf: 'M20 4c-9-1-16 2-16 9a7 7 0 0 0 7 7c7 0 10-7 9-16ZM4 20 15 9M9 15v-5m0 5h5',
  grid: 'M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z',
  sensor: 'M4 7h16M4 17h16M8 4v6m8 4v6', robot: 'M7 7h10a3 3 0 0 1 3 3v8H4v-8a3 3 0 0 1 3-3ZM12 7V3m-4 9h.01M16 12h.01M8 16h8M2 11v4m20-4v4',
  clock: 'M12 8v5l3 2M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z', gear: 'M12 3v3m0 12v3M3 12h3m12 0h3M5.6 5.6l2.1 2.1m8.6 8.6 2.1 2.1M5.6 18.4l2.1-2.1m8.6-8.6 2.1-2.1M17 12a5 5 0 1 1-10 0 5 5 0 0 1 10 0Z',
  arrow: 'M5 12h14m-5-5 5 5-5 5', camera: 'M4 7h4l2-3h4l2 3h4v13H4ZM16 13a4 4 0 1 1-8 0 4 4 0 0 1 8 0Z',
  drop: 'M12 3s7 8 7 12a7 7 0 0 1-14 0c0-4 7-12 7-12Z', sun: 'M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5M17 12a5 5 0 1 1-10 0 5 5 0 0 1 10 0Z',
  temp: 'M9 14V5a3 3 0 0 1 6 0v9a5 5 0 1 1-6 0ZM12 8v10', wifi: 'M3 8a14 14 0 0 1 18 0M6 12a9 9 0 0 1 12 0m-9 4a4 4 0 0 1 6 0m-3 4h.01',
  stop: 'M8 3h8l5 5v8l-5 5H8l-5-5V8ZM9 9h6v6H9z', refresh: 'M20 7v5h-5M4 17v-5h5M6 6a8 8 0 0 1 13 3M5 15a8 8 0 0 0 13 3',
  pin: 'M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0ZM15 10a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z',
  check: 'm5 12 4 4L19 6', chevron: 'm9 5 7 7-7 7', close: 'm6 6 12 12M6 18 18 6',
};
function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.65" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name]} /></svg>;
}
const crops = ['tomato', 'potato', 'rice', 'corn', 'brinjal', 'cabbage', 'capsicum', 'carrot', 'cauliflower', 'chilli', 'lettuce', 'mushroom', 'radish', 'rose', 'tea', 'anthurium'];
const navigation: { id: string; label: string; icon: IconName }[] = [{ id: 'overview', label: 'Overview', icon: 'grid' }, { id: 'sensors', label: 'Field insights', icon: 'sensor' }, { id: 'controls', label: 'Robot controls', icon: 'robot' }, { id: 'activity', label: 'Activity', icon: 'clock' }];
const ignore = () => {};
const titleCase = (text: string) => text.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

export default function Dashboard({ selectedCrop = 'tomato', mode = 'manual' }: { selectedCrop?: string; mode?: 'auto' | 'manual' }) {
  const [appearance, setAppearance] = useState<'light' | 'dark' | 'system'>(() => {
    try { const saved = localStorage.getItem('demeter-appearance'); return saved === 'light' || saved === 'system' ? saved : 'dark'; } catch { return 'dark'; }
  });
  const [systemDark, setSystemDark] = useState(() => window.matchMedia('(prefers-color-scheme: dark)').matches);
  useEffect(() => {
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const update = () => setSystemDark(media.matches);
    media.addEventListener('change', update);
    return () => media.removeEventListener('change', update);
  }, []);
  const dark = appearance === 'dark' || (appearance === 'system' && systemDark);
  useEffect(() => {
    try { localStorage.setItem('demeter-appearance', appearance); } catch { /* Storage may be unavailable in private sessions. */ }
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', dark ? '#101816' : '#f6f8f7');
  }, [appearance, dark]);
  const [section, setSection] = useState('overview');
  const [crop, setCrop] = useState(selectedCrop);
  const [activeMode, setActiveMode] = useState(mode);
  const [connected, setConnected] = useState(false);
  const [hardware, setHardware] = useState(false);
  const [stopped, setStopped] = useState(false);
  const [data, setData] = useState<SensorData>({ temperature: 0, humidity: 0, pressure: 0, light: 0, uvVoltage: 0, soilMoisture: 0 });
  const [diseases, setDiseases] = useState<DiseaseItem[]>([]);
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [weather, setWeather] = useState<WeatherPayload | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [speed, setSpeed] = useState(100);
  const [cameraAspect, setCameraAspect] = useState(4 / 3);
  const [hud, setHud] = useState(false);
  const [brainState, setBrainState] = useState('IDLE');
  const [camera, setCamera] = useState(false);
  const [cameraKey, setCameraKey] = useState(Date.now());
  const [refreshing, setRefreshing] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null);
  const logId = useRef(0);
  const addLog = useCallback((msg: string, type: LogEntry['type']) => {
    setLogs(previous => [{ id: ++logId.current, msg, type, icon: '', time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }, ...previous].slice(0, 80));
  }, []);
  const controls = useSocketData(setData, setDiseases, setRecommendation, setConnected, ignore, addLog, crop,
    setActiveMode, setBrainState, undefined, undefined, setWeather, undefined, undefined, undefined, setHardware, undefined, setStopped);
  const live = connected && hardware;
  const canControl = live && !stopped && activeMode === 'manual';
  const moving = useRef(false);
  const controlRef = useRef(controls);
  controlRef.current = controls;
  const stopMotion = useCallback(() => {
    if (moving.current) { moving.current = false; controlRef.current.sendRobotControl('stop', 0); }
  }, []);
  useEffect(() => {
    const blur = () => stopMotion();
    const visibility = () => { if (document.hidden) stopMotion(); };
    window.addEventListener('blur', blur);
    document.addEventListener('visibilitychange', visibility);
    return () => { stopMotion(); window.removeEventListener('blur', blur); document.removeEventListener('visibilitychange', visibility); };
  }, [stopMotion]);
  useEffect(() => {
    const abort = new AbortController();
    const poll = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/api/health`, { signal: abort.signal });
        if (!response.ok) throw new Error('Unavailable');
        const health = await response.json();
        if (!abort.signal.aborted) setCamera(health.camera_connected === true);
      } catch { if (!abort.signal.aborted) setCamera(false); }
    };
    poll(); const timer = window.setInterval(poll, 6000);
    return () => { abort.abort(); clearInterval(timer); };
  }, []);
  useEffect(() => { stopMotion(); }, [section, activeMode, stopped, live, stopMotion]);
  useEffect(() => { if (!refreshing) return; const timer = setTimeout(() => setRefreshing(false), 1200); return () => clearTimeout(timer); }, [refreshing]);
  useEffect(() => {
    const direction: Record<string, 'forward' | 'left' | 'backward' | 'right'> = { KeyW: 'forward', KeyA: 'left', KeyS: 'backward', KeyD: 'right' };
    const keys = new Set<string>();
    const down = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement;
      if (target.closest('input,select,textarea,[contenteditable="true"],dialog[open]')) return;
      if (event.code === 'Space') { event.preventDefault(); if (!event.repeat) { stopMotion(); controlRef.current.emergencyStop(); } return; }
      if (!canControl || event.repeat) return;
      if (direction[event.code]) { event.preventDefault(); keys.add(event.code); moving.current = true; controlRef.current.sendRobotControl(direction[event.code], speed); }
      const relayIndex = ['Numpad1','Numpad2','Numpad3','Numpad4'].indexOf(event.code);
      if (relayIndex >= 0) { event.preventDefault(); const values = [data.pump_on,data.sol1_on,data.sol2_on,data.spare_on]; if (typeof values[relayIndex] === 'boolean') controlRef.current.sendRelayToggle('R' + (relayIndex + 1), !values[relayIndex]); }
    };
    const up = (event: KeyboardEvent) => { if (keys.has(event.code)) { keys.clear(); stopMotion(); } };
    window.addEventListener('keydown', down); window.addEventListener('keyup', up);
    return () => { window.removeEventListener('keydown', down); window.removeEventListener('keyup', up); stopMotion(); };
  }, [canControl, speed, data.pump_on, data.sol1_on, data.sol2_on, data.spare_on, stopMotion]);
  const refresh = () => { controls.refreshAll(); setCameraKey(key => key + 1); setRefreshing(true); };
  const reading = (value: number | undefined, digits = 1) => live && value !== undefined && Number.isFinite(value) ? value.toLocaleString(undefined, { maximumFractionDigits: digits }) : '—';
  const exportLog = () => {
    const text = ['time,type,message', ...logs.map(log => [log.time, log.type, log.msg].map(value => `"${value.replace(/"/g, '""')}"`).join(','))].join('\r\n');
    const url = URL.createObjectURL(new Blob([text], { type: 'text/csv;charset=utf-8;' }));
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'demeter-v1-activity.csv'; anchor.click(); URL.revokeObjectURL(url);
  };
  const stats: { label: string; value: number | undefined; unit: string; icon: IconName; color: string; note: string }[] = [
    { label: 'Temperature', value: data.temperature, unit: '°C', icon: 'temp', color: 'peach', note: 'Ambient air' },
    { label: 'Humidity', value: data.humidity, unit: '%', icon: 'drop', color: 'blue', note: 'Relative humidity' },
    { label: 'Soil moisture', value: data.soil1Pct, unit: '%', icon: 'leaf', color: 'mint', note: 'Probe 1 · calibrated' },
    { label: 'Light intensity', value: data.light, unit: 'lux', icon: 'sun', color: 'lavender', note: 'Available sunlight' },
  ];
  const relayRows: { name: string; detail: string; target: string; value?: boolean; icon: IconName }[] = [
    { name: 'Water pump', detail: 'Timed irrigation · R1', target: 'R1', value: data.pump_on, icon: 'drop' },
    { name: 'Soil probe A', detail: 'First actuator · R2', target: 'R2', value: data.sol1_on, icon: 'sensor' },
    { name: 'Soil probe B', detail: 'Second actuator · R3', target: 'R3', value: data.sol2_on, icon: 'sensor' },
    { name: 'Auxiliary relay', detail: 'Spare output · R4', target: 'R4', value: data.spare_on, icon: 'gear' },
  ];
  return <div className="cg-app" data-theme={dark ? 'dark' : 'light'}>
    <aside className="cg-sidebar">
      <a href="/" className="cg-brand"><span className="cg-brand-mark"><Icon name="leaf" size={24} /></span><span>DEM3T3R<span className="cg-brand-ai">V1</span></span></a>
      <div className="cg-workspace"><span className="cg-workspace-icon"><Icon name="leaf" /></span><div><strong>My workspace</strong><small>Precision agriculture</small></div></div>
      <span className="cg-nav-label">WORKSPACE</span>
      <nav aria-label="Main navigation">{navigation.map(item => <button key={item.id} aria-label={item.label} className={section === item.id ? 'selected' : ''} onClick={() => setSection(item.id)} aria-current={section === item.id ? 'page' : undefined}><Icon name={item.icon} /><span>{item.label}</span>{section === item.id && <span className="cg-nav-dot" />}</button>)}</nav>
      <div className="cg-sidebar-bottom"><div className="cg-side-note"><span className="cg-soft-icon mint"><Icon name="leaf" /></span><strong>A little care.<br />A healthier harvest.</strong><p>Your field, connected.</p></div><button className="cg-settings" onClick={() => dialog.current?.showModal()}><Icon name="gear" />Connection settings</button><Link className="cg-advanced" to="/advanced">Advanced workspace <Icon name="arrow" size={15} /></Link><div className="cg-profile"><span>DV</span><div><strong>DEMETER V1 Rover</strong><small>ESP32 · Field companion</small></div></div></div>
    </aside>
    <div className="cg-workarea">
      <header className="cg-topbar"><div className="cg-breadcrumb">Workspace <span>/</span> <strong>{navigation.find(item => item.id === section)?.label}</strong></div><div className="cg-top-actions"><label className="cg-appearance"><span>Appearance</span><select aria-label="Appearance" value={appearance} onChange={event => setAppearance(event.target.value as 'dark' | 'light' | 'system')}><option value="dark">Dark</option><option value="light">Light</option><option value="system">System</option></select></label><span className={`cg-status ${live ? 'online' : ''}`}><i />{live ? 'Robot connected' : connected ? 'Robot offline' : 'Connecting to app'}</span><button className="cg-icon-button" aria-label="Connection settings" onClick={() => dialog.current?.showModal()}><Icon name="gear" /></button><span className="cg-avatar">DV</span></div></header>
      <main className="cg-main">
        <div className="cg-page-heading"><div><p className="cg-eyebrow">YOUR FIELD, AT A GLANCE</p><h1>{section === 'overview' ? 'A fresh perspective.' : navigation.find(item => item.id === section)?.label}</h1><p>{section === 'overview' ? 'Everything you need to care for your crops, in one calm place.' : section === 'controls' ? 'Simple, deliberate control of your field companion.' : section === 'sensors' ? 'Understand your growing environment with live sensor readings.' : 'A clear record of connections, observations, and commands.'}</p></div><button className="cg-button secondary" onClick={refresh} disabled={refreshing}><Icon name="refresh" />{refreshing ? 'Refreshing…' : 'Refresh'}</button></div>
        {stopped && <div className="cg-stop-banner" role="alert"><Icon name="stop" /><div><strong>Emergency stop is active</strong><span>Robot commands are locked. Reset only when the area is clear.</span></div><button onClick={() => controls.resetEmergencyStop()} disabled={!connected}>Reset stop</button></div>}
        {section === 'overview' && <section className="cg-hero"><div className="cg-hero-copy"><span className="cg-hero-label"><span />GROW WITH CONFIDENCE</span><h2>Good care starts<br />with a closer look.</h2><p>Keep an eye on your crops.<br />Let every observation guide your next step.</p><button className="cg-button dark" onClick={() => setSection('controls')}>Open robot controls <Icon name="arrow" size={17} /></button></div><div className="cg-plant-art" aria-hidden="true"><div className="cg-orbit orbit-one" /><div className="cg-orbit orbit-two" /><svg viewBox="0 0 320 290"><defs><linearGradient id="leafShade" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#80b797" /><stop offset="1" stopColor="#205f46" /></linearGradient></defs><ellipse cx="160" cy="262" rx="76" ry="11" fill="#1b664b" opacity=".08" /><path d="M161 233c-6-65 5-111 20-153" stroke="#337554" strokeWidth="5" fill="none" /><path d="M165 191C86 195 64 144 79 111c52-11 92 24 86 80" fill="url(#leafShade)" /><path d="M168 151c-4-70 49-112 89-99 16 52-32 101-89 99" fill="url(#leafShade)" /><path d="M171 118C125 110 103 67 124 32c43 4 62 43 47 86" fill="#71a88b" /><path d="m165 191-66-60m69 20 65-73m-62 40-35-65" stroke="#dcebdd" strokeWidth="1.4" opacity=".5" /><path d="M119 219h87l-10 39a9 9 0 0 1-9 7h-47a9 9 0 0 1-9-7z" fill="#fdfefb" /><rect x="115" y="215" width="94" height="12" rx="5" fill="#fff" /></svg><div className="cg-art-label"><span className="cg-soft-icon mint"><Icon name="leaf" size={17} /></span><div><strong>Thoughtful by nature</strong><small>Smarter with DEM3T3R V1</small></div></div></div><span className="cg-hero-date">{new Date().toLocaleDateString(undefined, { month: 'long', day: 'numeric', year: 'numeric' })}</span></section>}
        {(section === 'overview' || section === 'sensors') && <><div className="cg-section-heading"><h2>Field conditions</h2><span><i className={`cg-live-dot ${live ? 'on' : ''}`} />{live ? 'Live from your robot' : 'Waiting for your robot'}</span></div><div className="cg-stats">{stats.map(stat => <article className="cg-card cg-stat" key={stat.label}><div className="cg-stat-top"><span>{stat.label}</span><span className={`cg-soft-icon ${stat.color}`}><Icon name={stat.icon} /></span></div><div className="cg-stat-value">{reading(stat.value)}<span>{stat.unit}</span></div><div className="cg-stat-bottom"><span>{stat.note}</span><span className={live ? 'cg-live-text' : ''}>{live ? 'Live' : 'No data'}</span></div></article>)}</div></>}
        {(section === 'overview' || section === 'controls') && <div className="cg-main-grid"><section className="cg-card cg-camera-card"><div className="cg-card-heading"><div><h2>Eyes on your crops</h2><p>Live camera · Pipeline: {connected ? brainState : 'Offline'}</p><button className="cg-text-button" aria-pressed={hud} onClick={() => setHud(!hud)}>OVERLAY: {hud ? 'ON' : 'OFF'}</button></div><label className="cg-crop-select"><Icon name="leaf" size={16} /><select aria-label="Select crop model" value={crop} onChange={event => { setDiseases([]); setRecommendation(null); setCrop(event.target.value); }}>{crops.map(name => <option key={name} value={name}>{titleCase(name)}</option>)}</select></label></div><div className={`cg-camera-stage ${camera ? 'has-feed' : ''}`} style={camera ? { aspectRatio: cameraAspect, height: 'auto' } : undefined}>
          {camera ? <img src={`${BACKEND_URL}/video_feed?view=${cameraKey}`} alt="Live view from the DEM3T3R V1 camera" onLoad={event => { const image = event.currentTarget; if (image.naturalHeight) setCameraAspect(image.naturalWidth / image.naturalHeight); }} onError={() => setCamera(false)} /> : <div className="cg-camera-empty"><span className="cg-camera-glyph"><Icon name="camera" size={34} /></span><h3>A closer look, when you’re ready.</h3><p>Connect your camera to see your crops here.</p><button onClick={refresh}>Check connection <Icon name="arrow" size={15} /></button></div>}
          <div id="camera-hud-layer" hidden={!hud || !camera} aria-hidden="true">{diseases.map((d, i) => typeof d.xmin === 'number' && typeof d.ymin === 'number' && typeof d.xmax === 'number' && typeof d.ymax === 'number' ? <div className="cg-detection-box" key={i} style={{left: d.xmin + '%', top: d.ymin + '%', width: (d.xmax - d.xmin) + '%', height: (d.ymax - d.ymin) + '%'}}><span>{titleCase(d.class)} · {Math.round(d.confidence * 100)}%</span></div> : null)}</div>
          <span className={`cg-camera-badge ${camera ? 'active' : ''}`}><i />{camera ? 'LIVE VIEW' : 'CAMERA STANDBY'}</span><span className="cg-camera-corner top-left" /><span className="cg-camera-corner bottom-right" /></div><div className="cg-camera-footer"><span><Icon name="pin" size={15} />{live && data.fix ? `${data.latitude?.toFixed(5)}, ${data.longitude?.toFixed(5)}` : 'Waiting for GPS fix'}</span><span>{titleCase(crop)} model</span></div></section>
          <section className="cg-card cg-robot-card"><div className="cg-card-heading"><div><h2>Your field companion</h2><p>DEMETER V1 Rover</p></div><span className="cg-soft-icon lavender"><Icon name="robot" /></span></div><div className="cg-robot-summary"><span className={`cg-robot-avatar ${live ? 'is-live' : ''}`}><Icon name="robot" size={37} /></span><div><strong>{stopped ? 'Safely stopped' : live ? 'Ready when you are' : 'Taking a little pause'}</strong><p>{live ? `${reading(data.battery)} V · ${activeMode === 'manual' ? 'Manual control' : 'Autonomous mode'}` : 'Connect your ESP32 to get started'}</p></div></div><div className="cg-segment" aria-label="Robot mode">{(['manual', 'auto'] as const).map(value => <button key={value} className={activeMode === value ? 'active' : ''} disabled={!live || stopped} onClick={() => controls.toggleMode(value)}>{value === 'manual' ? 'Manual' : 'Autonomous'}</button>)}</div><div className="cg-drive"><div className="cg-dpad">{(['forward', 'left', 'stop', 'right', 'backward'] as const).map(direction => <button key={direction} className={`direction-${direction}`} aria-label={direction === 'stop' ? 'Stop movement' : `Hold to move ${direction}`} disabled={direction === 'stop' ? !connected : !canControl} onPointerDown={event => { if (direction === 'stop') { controls.sendRobotControl('stop', 0); return; } event.currentTarget.setPointerCapture(event.pointerId); moving.current = true; controls.sendRobotControl(direction, speed); }} onPointerUp={stopMotion} onPointerCancel={stopMotion} onLostPointerCapture={stopMotion} onKeyDown={event => { if (!event.repeat && (event.key === ' ' || event.key === 'Enter')) { event.preventDefault(); if (direction === 'stop') controls.sendRobotControl('stop', 0); else { moving.current = true; controls.sendRobotControl(direction, speed); } } }} onKeyUp={stopMotion} onBlur={stopMotion}>{direction === 'stop' ? <span className="cg-stop-square" /> : <Icon name="arrow" size={19} />}</button>)}</div><div className="cg-drive-help"><strong>Move with care</strong><p>Hold a direction or WASD.<br />Release to stop. Space: E-stop.</p><span>{Math.round(speed / 255 * 100)}% speed</span></div></div><label className="cg-speed-label">Movement speed <span>{speed} PWM</span><input type="range" min="40" max="255" value={speed} onChange={event => setSpeed(Number(event.target.value))} aria-label="Movement speed" /></label><button className="cg-emergency" disabled={!connected} onClick={() => { stopMotion(); controls.emergencyStop(); }}><Icon name="stop" size={18} />Emergency stop<span>Stop all outputs</span></button></section></div>}
        {(section === 'overview' || section === 'sensors') && <TelemetryMatrix data={data} live={live} />}
        {(section === 'overview' || section === 'controls' || section === 'sensors') && <LiveGpsMap data={data} live={live} />}
        {(section === 'overview' || section === 'sensors') && <DiseaseCare diseases={diseases} crop={crop} request={controls.requestDiseaseDetail} />}
        {(section === 'overview' || section === 'controls') && <section className="cg-card cg-relays"><div className="cg-card-heading"><div><h2>Actuators & irrigation</h2><p>Confirmed by the robot · NumPad 1–4 toggles outputs.</p></div><span className="cg-pill">4 outputs</span></div>{relayRows.map(relay => <div className="cg-relay-row" key={relay.target}><span className="cg-soft-icon mint"><Icon name={relay.icon} /></span><div><strong>{relay.name}</strong><small>{relay.detail}</small></div><span className="cg-relay-state">{live ? relay.value ? 'On' : 'Off' : 'Unavailable'}</span><button className={`cg-toggle ${live && relay.value ? 'on' : ''}`} role="switch" aria-checked={live && !!relay.value} aria-label={relay.name} disabled={!canControl} onClick={() => controls.sendRelayToggle(relay.target, !relay.value)}><span /></button></div>)}</section>}
        {section === 'sensors' && <section className="cg-card cg-sensor-details"><div className="cg-card-heading"><div><h2>The full picture</h2><p>Readings from your ESP32</p></div><span className="cg-pill">{live ? 'Live readings' : 'Awaiting connection'}</span></div><div className="cg-sensor-grid">{[['Soil moisture · probe 2', reading(data.soil2Pct), '%'], ['Air pressure', reading(data.pressure), 'hPa'], ['UV index', reading(data.uvIndex), ''], ['UV sensor', reading(data.uvVoltage, 2), 'V'], ['Front clearance', reading(data.ultrasonic), 'cm'], ['Battery voltage', reading(data.battery), 'V'], ['GPS satellites', reading(data.satellites, 0), ''], ['Ground speed', reading(data.speed), 'km/h'], ['Heading', reading(data.heading), '°'], ['Left motor', reading(data.motor_left, 0), 'PWM'], ['Right motor', reading(data.motor_right, 0), 'PWM'], ['GPS altitude', reading(data.altitude), 'm']].map(([label, value, unit]) => <div key={label}><span>{label}</span><strong>{value} <small>{unit}</small></strong></div>)}</div>{weather && <div className="cg-weather-strip"><Icon name="sun" /><div><strong>{weather.location_name} · {weather.current.temperature}°C</strong><p>{weather.current.weather_condition} · Weather service, separate from robot sensors</p></div></div>}</section>}
        {section === 'activity' && <section className="cg-card cg-full-activity"><div className="cg-card-heading"><div><h2>Activity journal</h2><p>Latest {logs.length} events from this session</p></div><button className="cg-button secondary" disabled={!logs.length} onClick={exportLog}>Export CSV <Icon name="arrow" size={16} /></button></div>{logs.length ? logs.map(log => <div className="cg-log-row" key={log.id}><span className={`cg-log-dot ${log.type}`} /><div><p>{log.msg}</p><time>{log.time} · {titleCase(log.type)}</time></div></div>) : <div className="cg-large-empty"><Icon name="clock" size={32} /><h3>A clean slate.</h3><p>Connection events and commands will appear here.</p></div>}</section>}
        <footer className="cg-footer"><span><Icon name="leaf" size={14} />Made for better growing.</span><span>DEMETER V1 <span className="cg-footer-dot">·</span> {connected ? 'App connected' : 'App offline'}</span></footer>
      </main>
    </div>
    <AssistantChat crop={crop} connected={connected} send={(message, callback) => controls.sendChatMessage(message, callback, 'en', diseases)} />
    <dialog ref={dialog} className="cg-dialog"><div className="cg-dialog-heading"><span className="cg-soft-icon mint"><Icon name="wifi" /></span><button className="cg-icon-button" aria-label="Close connection settings" onClick={() => dialog.current?.close()}><Icon name="close" /></button></div><h2>Let’s get connected.</h2><p>The app, rover, and camera each have their own connection.</p><div className="cg-connection-list">{[['Dashboard service', connected], ['ESP32 rover', live], ['Camera stream', camera]].map(([name, status]) => <div key={String(name)}><span>{name}</span><strong className={status ? 'cg-live-text' : ''}>{status ? 'Connected' : 'Offline'}</strong></div>)}</div><p className="cg-connection-help">Power on your rover and connect this computer to the same Wi-Fi network. Hardware readings appear automatically when the ESP32 connects.</p><details><summary>Connection details</summary><code>{BACKEND_URL}</code><p>Robot TCP: 5000 · Optional ESP32 server: 8080<br />Set ESP32_HOST in the project’s .env to use the rover’s IP.</p></details><button className="cg-button dark" onClick={refresh}><Icon name="refresh" size={17} />Check again</button></dialog>
  </div>;
}
