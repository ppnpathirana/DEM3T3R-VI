/**
 * @file HardwareTelemetry.tsx
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

import { SensorData } from '../App';

export default function HardwareTelemetry({ data, connected }: { data: SensorData; connected: boolean }) {
  const reading = (value: unknown, unit = '') => connected && value !== undefined && value !== null
    ? `${value}${unit}` : 'Unavailable';
  const state = (value?: boolean) => reading(value === undefined ? undefined : value ? 'ON' : 'OFF');
  const rows = [
    ['Temperature', reading(data.temperature, ' °C')], ['Humidity', reading(data.humidity, ' %')],
    ['Pressure', reading(data.pressure, ' hPa')], ['Light', reading(data.light, ' lux')],
    ['UV voltage', reading(data.uvVoltage, ' V')], ['UV index', reading(data.uvIndex)],
    ['Soil 1 ADC / moisture', `${reading(data.soilMoisture)} / ${reading(data.soil1Pct, ' %')}`],
    ['Soil 2 ADC / moisture', `${reading(data.soilMoisture2)} / ${reading(data.soil2Pct, ' %')}`],
    ['Front distance', reading(data.ultrasonic, ' cm')], ['Battery', reading(data.battery, ' V')],
    ['GPS latitude / longitude', `${reading(data.latitude)} / ${reading(data.longitude)}`],
    ['GPS fix / satellites', `${reading(data.fix)} / ${reading(data.satellites)}`],
    ['GPS speed', reading(data.speed, ' km/h')], ['Heading', reading(data.heading, ' °')],
    ['Left / right PWM', `${reading(data.motor_left)} / ${reading(data.motor_right)}`],
    ['R1 pump', state(data.pump_on)], ['R2 solenoid', state(data.sol1_on)],
    ['R3 solenoid', state(data.sol2_on)], ['R4 spare', state(data.spare_on)],
  ];
  return <details className="mx-2 rounded border border-white/10 bg-black/60 p-2 text-xs">
    <summary className="cursor-pointer">ESP32 hardware readings — {connected ? `live (${data.source || 'device'})` : 'disconnected / awaiting telemetry'}</summary>
    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 max-h-48 overflow-auto py-2">
      {rows.map(([label, value]) => <div key={label}><span className="text-slate-400">{label}: </span>{value}</div>)}
    </div>
  </details>;
}
