/**
 * @file TelemetryMatrix.tsx
 * @description Core component for DEM3T3R V1 architecture.
 * 
 * @project DEM3T3R V1
 * @author Pasindu Pathirana
 * @contact https://github.com/ppnpathirana/DEM3T3R-VI
 * @version 1.0.0
 * @date 2026
 * 
 * All rights reserved.
 */

import { useEffect, useRef } from 'react';
import type { SensorData } from '../App';

function Sparkline({ value, live, label }: { value?: number; live: boolean; label: string }) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const samples = useRef<number[]>([]);
  useEffect(() => {
    if (!live) samples.current = [];
    else if (typeof value === 'number' && Number.isFinite(value)) samples.current = [...samples.current, value].slice(-90);
    const element = canvas.current;
    if (!element) return;
    const draw = () => {
      const width = element.clientWidth, height = 52, ratio = window.devicePixelRatio || 1;
      element.width = width * ratio; element.height = height * ratio;
      const ctx = element.getContext('2d'); if (!ctx) return;
      ctx.scale(ratio, ratio); ctx.clearRect(0, 0, width, height);
      const values = samples.current;
      ctx.strokeStyle = '#e2ebe4'; ctx.beginPath(); ctx.moveTo(0, 45); ctx.lineTo(width, 45); ctx.stroke();
      if (!values.length) return;
      const min = Math.min(...values), range = Math.max(1, Math.max(...values) - min);
      ctx.strokeStyle = '#338363'; ctx.lineWidth = 2; ctx.beginPath();
      values.forEach((v, i) => { const x = i * width / Math.max(1, values.length - 1), y = 42 - (v - min) / range * 32; if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y); }); ctx.stroke();
    };
    const frame = requestAnimationFrame(draw); const observer = new ResizeObserver(draw); observer.observe(element);
    return () => { cancelAnimationFrame(frame); observer.disconnect(); };
  }, [value, live]);
  return <canvas ref={canvas} style={{ width: '100%', height: 52 }} role="img" aria-label={`${label} recent telemetry trend`} />;
}

export default function TelemetryMatrix({ data, live }: { data: SensorData; live: boolean }) {
  const readings: [string, number | undefined, string][] = [['Temperature', data.temperature, '°C'], ['Humidity', data.humidity, '%'], ['Barometer', data.pressure, 'hPa'], ['Solar', data.light, 'lux'], ['UV', data.uvIndex, 'index'], ['Soil A', data.soil1Pct, '%'], ['Soil B', data.soil2Pct, '%'], ['Sonar', data.ultrasonic, 'cm']];
  return <section className="cg-card cg-telemetry"><div className="cg-card-heading"><div><h2>Sensor telemetry</h2><p>Eight channels · recent readings this session</p></div><span className="cg-pill">{live ? 'Live' : 'Offline'}</span></div><div className="cg-telemetry-grid">{readings.map(([label, value, unit]) => <article key={label}><span>{label}</span><strong>{live && Number.isFinite(value) ? value!.toLocaleString(undefined, { maximumFractionDigits: 1 }) : '—'} <small>{unit}</small></strong><Sparkline value={value} live={live} label={label} /></article>)}</div></section>;
}
