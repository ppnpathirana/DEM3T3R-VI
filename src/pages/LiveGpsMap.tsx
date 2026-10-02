import { useEffect, useRef, useState } from 'react';
import type { SensorData } from '../App';

export default function LiveGpsMap({ data, live }: { data: SensorData; live: boolean }) {
  const host = useRef<HTMLDivElement>(null);
  const map = useRef<any>(null);
  const marker = useRef<any>(null);
  const trail = useRef<any>(null);
  const points = useRef<[number, number][]>([]);
  const [follow, setFollow] = useState(true);
  const [ready, setReady] = useState(false);
  const latitude = data.latitude;
  const longitude = data.longitude;
  const valid = live && data.fix === true && typeof latitude === 'number' && typeof longitude === 'number' && Number.isFinite(latitude) && Number.isFinite(longitude) && Math.abs(latitude) <= 90 && Math.abs(longitude) <= 180;
  useEffect(() => {
    const L = (window as any).L;
    if (!host.current || !L) return;
    const instance = L.map(host.current, { scrollWheelZoom: false }).setView([0, 0], 2);
    map.current = instance;
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' }).addTo(instance);
    trail.current = L.polyline([], { color: '#27765a', weight: 3 }).addTo(instance);
    const resize = new ResizeObserver(() => instance.invalidateSize());
    resize.observe(host.current);
    setReady(true);
    return () => { resize.disconnect(); instance.remove(); map.current = null; marker.current = null; points.current = []; };
  }, []);
  useEffect(() => {
    if (!ready || !valid || !map.current) return;
    const position: [number, number] = [latitude!, longitude!];
    const L = (window as any).L;
    if (!marker.current) marker.current = L.circleMarker(position, { radius: 9, color: '#fff', weight: 3, fillColor: '#27765a', fillOpacity: 1 }).addTo(map.current).bindTooltip('DEM3T3R V1 rover');
    else marker.current.setLatLng(position);
    const last = points.current.at(-1);
    if (!last || last[0] !== position[0] || last[1] !== position[1]) points.current = [...points.current, position].slice(-300);
    trail.current.setLatLngs(points.current);
    if (follow) map.current.setView(position, 18);
  }, [latitude, longitude, valid, ready, follow]);
  return <section className="cg-card cg-map-card"><div className="cg-card-heading"><div><h2>Live field map</h2><p>Position from the rover’s GPS module</p></div><button className="cg-button secondary" aria-pressed={follow} onClick={() => setFollow(!follow)}>{follow ? 'Following rover' : 'Follow rover'}</button></div><div className="cg-map-wrap"><div ref={host} className="cg-map" aria-label="Rover GPS map" />{(!valid || !ready) && <div className="cg-map-wait" role="status"><strong>{!ready ? 'Map unavailable' : 'Waiting for a GPS fix'}</strong><p>{!ready ? 'Map assets need an internet connection. GPS readings remain available below.' : 'The rover position appears when its GPS reports a valid fix.'}</p></div>}</div><div className="cg-map-readings"><span>Latitude<strong>{valid ? latitude!.toFixed(6) : '—'}</strong></span><span>Longitude<strong>{valid ? longitude!.toFixed(6) : '—'}</strong></span><span>Satellites<strong>{live ? data.satellites ?? '—' : '—'}</strong></span><span>GPS status<strong>{valid ? 'Live fix' : 'No fix'}</strong></span></div></section>;
}
