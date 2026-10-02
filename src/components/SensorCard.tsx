/**
 * @file SensorCard.tsx
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

import React from 'react';
import { SensorData } from '../App';
import { useLanguage } from '../context/LanguageContext';

type SensorCardProps = {
  data: SensorData;
};

export default function SensorCard({ data }: SensorCardProps) {
  const { t } = useLanguage();

  const sensors = [
    { icon: '🌡️', label: t('airTemperature') + ' (°C)', value: data.temperature ? data.temperature.toFixed(1) : '--', key: 'temp' },
    { icon: '💧', label: t('airHumidity') + ' (%)', value: data.humidity ? data.humidity.toFixed(1) : '--', key: 'hum' },
    { icon: '📊', label: t('atmosphericPressure') + ' (hPa)', value: data.pressure ? data.pressure.toFixed(1) : '--', key: 'pres' },
    { icon: '☀️', label: t('lightIntensity'), value: typeof data.light === 'number' ? Math.round(data.light).toLocaleString() : '--', key: 'lux' },
    { icon: '🧬', label: t('uvRadiation'), value: data.uvVoltage ? data.uvVoltage.toFixed(2) + 'V' : '--', key: 'uv' },
    { icon: '🌱', label: t('soilMoisture1'), value: typeof data.soilMoisture === 'number' ? data.soilMoisture : '--', key: 'soil1' },
    { icon: '☘️', label: t('soilMoisture2'), value: typeof data.soilMoisture2 === 'number' ? data.soilMoisture2 : (typeof data.soilMoisture === 'number' ? data.soilMoisture : '--'), key: 'soil2' },
  ];

  return (
    <div className="glass-card">
      <div className="card-header">
        <div className="card-header-dot" />
        {t('commandDashboard')} · Live ESP32 Sensor Telemetry
      </div>
      
      <div className="sensor-grid" style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', 
        gap: '12px' 
      }}>
        {sensors.map((sensor) => (
          <div className="sensor-card" key={sensor.key}>
            <div className="sensor-icon">{sensor.icon}</div>
            <div className="sensor-value gradient-text">{sensor.value}</div>
            <div className="sensor-label">{sensor.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
